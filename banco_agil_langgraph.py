"""
Orquestrador LangGraph para o Sistema Banco Ágil.
Gerencia o fluxo de conversação entre agentes especializados.

Este módulo substitui o banco_agil_system.py original, implementando
um grafo de estados com LangGraph para orquestração de agentes com LLM.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from state import EstadoConversacao, criar_estado_inicial
from agents.triagem_agent_llm import TriagemAgentLLM
from agents.credito_agent_llm import CreditoAgentLLM
from agents.entrevista_credito_agent_llm import EntrevistaCreditoAgentLLM
from agents.cambio_agent_llm import CambioAgentLLM


class BancoAgilLangGraph:
    """
    Orquestrador principal do sistema bancário usando LangGraph.

    Gerencia o fluxo de conversação entre agentes especializados:
    - Triagem: Autenticação e roteamento
    - Crédito: Consulta e solicitação de aumento de limite
    - Entrevista: Coleta de dados financeiros e recálculo de score
    - Câmbio: Consulta de cotações de moedas
    """

    def __init__(self, groq_api_key: str = None):
        """
        Inicializa o orquestrador LangGraph.

        Args:
            groq_api_key: API key do Groq (opcional, usa .env se não fornecido)
        """
        # Inicializa todos os agentes
        self.agente_triagem = TriagemAgentLLM(groq_api_key=groq_api_key)
        self.agente_credito = CreditoAgentLLM(groq_api_key=groq_api_key)
        self.agente_entrevista = EntrevistaCreditoAgentLLM(groq_api_key=groq_api_key)
        self.agente_cambio = CambioAgentLLM(groq_api_key=groq_api_key)

        # Cria o grafo de estados
        self.grafo = self._criar_grafo()

        # Estado atual
        self.estado: EstadoConversacao = criar_estado_inicial()

    def _criar_grafo(self) -> Any:
        """
        Cria o grafo de estados com LangGraph.

        Returns:
            Grafo compilado pronto para execução
        """
        workflow = StateGraph(EstadoConversacao)

        # Adiciona nó roteador como ponto de entrada
        workflow.add_node("roteador", self._node_roteador)

        # Adiciona nós para cada agente
        workflow.add_node("triagem", self._node_triagem)
        workflow.add_node("credito", self._node_credito)
        workflow.add_node("entrevista_credito", self._node_entrevista)
        workflow.add_node("cambio", self._node_cambio)
        workflow.add_node("encerramento", self._node_encerramento)

        # Define roteador como ponto de entrada
        workflow.set_entry_point("roteador")

        # Roteador decide qual nó executar baseado no agente_ativo
        workflow.add_conditional_edges(
            "roteador",
            self._decidir_ponto_entrada,
            {
                "triagem": "triagem",
                "credito": "credito",
                "entrevista_credito": "entrevista_credito",
                "cambio": "cambio",
                "encerramento": "encerramento"
            }
        )

        # Define roteamento condicional a partir da triagem
        workflow.add_conditional_edges(
            "triagem",
            self._decidir_proximo_passo,
            {
                "triagem": "triagem",  # Permanece na triagem (autenticação)
                "credito": "credito",
                "entrevista_credito": "entrevista_credito",
                "cambio": "cambio",
                "encerramento": "encerramento",
                END: END
            }
        )

        # Após crédito, pode ir para entrevista ou encerrar
        workflow.add_conditional_edges(
            "credito",
            self._decidir_proximo_passo,
            {
                "credito": "credito",  # Permanece no crédito
                "entrevista_credito": "entrevista_credito",
                "triagem": "triagem",  # Volta ao menu
                "encerramento": "encerramento",
                END: END
            }
        )

        # Após entrevista, volta para crédito
        workflow.add_conditional_edges(
            "entrevista_credito",
            self._decidir_proximo_passo,
            {
                "entrevista_credito": "entrevista_credito",  # Permanece na entrevista
                "credito": "credito",  # Redireciona para crédito após recalcular score
                "triagem": "triagem",  # Volta ao menu
                "encerramento": "encerramento",
                END: END
            }
        )

        # Após câmbio, pode consultar novamente ou voltar ao menu
        workflow.add_conditional_edges(
            "cambio",
            self._decidir_proximo_passo,
            {
                "cambio": "cambio",  # Permanece no câmbio
                "triagem": "triagem",  # Volta ao menu
                "encerramento": "encerramento",
                END: END
            }
        )

        # Encerramento sempre vai para END
        workflow.add_edge("encerramento", END)

        return workflow.compile()

    def _node_roteador(self, estado: EstadoConversacao) -> EstadoConversacao:
        """
        Nó roteador que apenas repassa o estado sem modificação.
        A decisão de rota é feita por _decidir_ponto_entrada.
        """
        return estado

    def _decidir_ponto_entrada(self, estado: EstadoConversacao) -> str:
        """
        Decide qual nó deve ser executado baseado no agente_ativo.
        Isso permite manter o contexto entre mensagens.
        """
        agente_ativo = estado.get("agente_ativo", "triagem")
        return agente_ativo

    def _node_triagem(self, estado: EstadoConversacao) -> EstadoConversacao:
        """
        Executa o nó do agente de triagem.

        Args:
            estado: Estado atual da conversa

        Returns:
            Estado atualizado
        """
        mensagem = estado["mensagem_atual"]

        try:
            resposta, estado_atualizado = self.agente_triagem.processar_mensagem(mensagem, estado)
        except Exception as e:
            raise

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "triagem"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "triagem"

        # CORREÇÃO: Identifica serviço e define proximo_passo se cliente autenticado
        # MAS só se não for um redirecionamento de outro agente
        skip_identificar = estado_atualizado.get("dados_temporarios", {}).get("skip_identificar_servico", False)

        if skip_identificar:
            # Cliente retornou ao menu, não processar mensagem como escolha
            estado_atualizado["dados_temporarios"]["skip_identificar_servico"] = False
        elif estado_atualizado.get("cliente_autenticado"):
            # Verifica se deve usar menu reduzido (sem crédito após aprovação)
            menu_reduzido = estado_atualizado.get("dados_temporarios", {}).get("menu_reduzido", False)
            servico = self.agente_triagem.identificar_servico(mensagem, menu_reduzido=menu_reduzido)
            if servico and servico != "encerramento":
                estado_atualizado["proximo_passo"] = servico
                # Limpa flag após usar
                if menu_reduzido:
                    estado_atualizado["dados_temporarios"]["menu_reduzido"] = False

        return estado_atualizado

    def _node_credito(self, estado: EstadoConversacao) -> EstadoConversacao:
        """
        Executa o nó do agente de crédito.

        Args:
            estado: Estado atual da conversa

        Returns:
            Estado atualizado
        """
        mensagem = estado["mensagem_atual"]

        # Salva proximo_passo ANTES do processamento
        proximo_passo_antes = estado.get("proximo_passo")

        try:
            resposta, estado_atualizado = self.agente_credito.processar_mensagem(mensagem, estado)
        except Exception as e:
            raise

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "credito"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "credito"

        # IMPORTANTE: Só preserva proximo_passo se o AGENTE mudou o valor
        # Se manteve igual ao valor de entrada, significa que não houve redirecionamento
        proximo_passo_depois = estado_atualizado.get("proximo_passo")

        if proximo_passo_depois == proximo_passo_antes:
            # Agente não mudou o valor → limpa para aguardar próximo input
            estado_atualizado["proximo_passo"] = None
        else:
            # Agente definiu novo redirecionamento → preserva
            pass  # Mantém o valor definido pelo agente

        return estado_atualizado

    def _node_entrevista(self, estado: EstadoConversacao) -> EstadoConversacao:
        """
        Executa o nó do agente de entrevista.

        Args:
            estado: Estado atual da conversa

        Returns:
            Estado atualizado
        """
        mensagem = estado["mensagem_atual"]

        proximo_passo_antes = estado.get("proximo_passo")

        try:
            resposta, estado_atualizado = self.agente_entrevista.processar_mensagem(mensagem, estado)
        except Exception as e:
            raise

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "entrevista_credito"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "entrevista_credito"

        # Só preserva se o agente mudou o valor
        proximo_passo_depois = estado_atualizado.get("proximo_passo")
        if proximo_passo_depois == proximo_passo_antes:
            estado_atualizado["proximo_passo"] = None
        else:
            pass  # Mantém o valor definido pelo agente

        return estado_atualizado

    def _node_cambio(self, estado: EstadoConversacao) -> EstadoConversacao:
        """
        Executa o nó do agente de câmbio.

        Args:
            estado: Estado atual da conversa

        Returns:
            Estado atualizado
        """
        mensagem = estado["mensagem_atual"]

        proximo_passo_antes = estado.get("proximo_passo")

        try:
            resposta, estado_atualizado = self.agente_cambio.processar_mensagem(mensagem, estado)
        except Exception as e:
            raise

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "cambio"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "cambio"

        # Só preserva se o agente mudou o valor
        proximo_passo_depois = estado_atualizado.get("proximo_passo")
        if proximo_passo_depois == proximo_passo_antes:
            estado_atualizado["proximo_passo"] = None
        else:
            pass  # Mantém o valor definido pelo agente

        return estado_atualizado

    def _node_encerramento(self, estado: EstadoConversacao) -> EstadoConversacao:
        """
        Executa o nó de encerramento.

        Args:
            estado: Estado atual da conversa

        Returns:
            Estado atualizado
        """
        resposta = (
            "Obrigado por usar o Banco Ágil! 🏦\n\n"
            "Sua sessão foi encerrada com sucesso.\n"
            "Até a próxima! 👋"
        )

        estado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "sistema"
        })

        estado["conversa_ativa"] = False
        estado["agente_ativo"] = "encerramento"

        return estado

    def _decidir_proximo_passo(
        self, estado: EstadoConversacao
    ) -> Literal["triagem", "credito", "entrevista_credito", "cambio", "encerramento", END]:
        """
        Decide qual deve ser o próximo passo no fluxo.

        Args:
            estado: Estado atual da conversa

        Returns:
            Nome do próximo nó ou END
        """

        # Se conversa foi encerrada, vai para END
        if not estado.get("conversa_ativa", True):
            return END

        # PRIORIDADE 1: Se tem próximo_passo definido, usa ele ANTES de checar loop
        if "proximo_passo" in estado and estado["proximo_passo"]:
            proximo = estado["proximo_passo"]
            estado["proximo_passo"] = None  # Limpa para próxima iteração
            # Reset contador pois está mudando de nó
            if hasattr(self, '_contador_loop'):
                self._contador_loop = 0
                self._ultimo_no = None
            return proximo

        # PROTEÇÃO CONTRA LOOP INFINITO (só checa se não há proximo_passo)
        # Conta quantas vezes o mesmo nó foi executado seguidas vezes
        if not hasattr(self, '_contador_loop'):
            self._contador_loop = 0
            self._ultimo_no = None

        if estado["agente_ativo"] == self._ultimo_no:
            self._contador_loop += 1
        else:
            self._contador_loop = 0
            self._ultimo_no = estado["agente_ativo"]

        # Se executou o mesmo nó mais de 3 vezes, força END para evitar loop infinito
        if self._contador_loop > 3:
            self._contador_loop = 0
            self._ultimo_no = None
            return END

        # Se está na triagem e ainda não autenticou
        if estado["agente_ativo"] == "triagem":
            if not estado.get("cliente_autenticado"):
                return END
            else:
                # Cliente autenticado
                # A lógica de identificação de serviço agora está no _node_triagem
                # que já definiu proximo_passo se necessário
                # Aqui apenas aguardamos input do usuário
                return END

        # Se está em algum agente específico
        agente_atual = estado["agente_ativo"]
        if agente_atual in ["credito", "entrevista_credito", "cambio"]:
            # Verifica se usuário quer voltar ao menu
            mensagem_lower = estado["mensagem_atual"].lower()
            if any(palavra in mensagem_lower for palavra in ["menu", "voltar", "sair", "encerrar"]):
                if "encerrar" in mensagem_lower or "sair" in mensagem_lower:
                    return "encerramento"
                else:
                    return "triagem"

            # Após processar mensagem, aguarda próximo input do usuário
            return END

        # Caso padrão: volta para triagem
        return "triagem"

    def processar_mensagem(self, mensagem: str) -> str:
        """
        Processa uma mensagem do usuário através do grafo.

        Args:
            mensagem: Mensagem do usuário

        Returns:
            Resposta do sistema
        """

        # Adiciona mensagem do usuário ao histórico
        self.estado["mensagens"].append({
            "role": "user",
            "content": mensagem
        })

        # Atualiza mensagem atual
        self.estado["mensagem_atual"] = mensagem


        # Executa o grafo
        try:
            resultado = self.grafo.invoke(self.estado)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

        # Atualiza estado interno
        self.estado = resultado


        # Retorna última mensagem do assistente
        mensagens_assistant = [
            msg for msg in self.estado["mensagens"]
            if msg["role"] == "assistant"
        ]

        if mensagens_assistant:
            resposta = mensagens_assistant[-1]["content"]
            return resposta
        else:
            return "Erro: Nenhuma resposta gerada."

    def reset(self):
        """Reseta o estado do sistema."""
        self.estado = criar_estado_inicial()
        self.agente_triagem.reset()
        self.agente_credito.reset()
        self.agente_entrevista.reset()
        self.agente_cambio.reset()

    def get_estado(self) -> EstadoConversacao:
        """Retorna o estado atual da conversa."""
        return self.estado


if __name__ == "__main__":
    # Teste básico do orquestrador

    try:
        sistema = BancoAgilLangGraph()
        resposta = sistema.processar_mensagem("Ola!")
        print(f"Resposta inicial: {resposta}")
    except ValueError as e:
        print(f"Erro ao inicializar: {e}")
