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

        # Adiciona nós para cada agente
        workflow.add_node("triagem", self._node_triagem)
        workflow.add_node("credito", self._node_credito)
        workflow.add_node("entrevista_credito", self._node_entrevista)
        workflow.add_node("cambio", self._node_cambio)
        workflow.add_node("encerramento", self._node_encerramento)

        # Define ponto de entrada
        workflow.set_entry_point("triagem")

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

    def _node_triagem(self, estado: EstadoConversacao) -> EstadoConversacao:
        """
        Executa o nó do agente de triagem.

        Args:
            estado: Estado atual da conversa

        Returns:
            Estado atualizado
        """
        mensagem = estado["mensagem_atual"]
        resposta, estado_atualizado = self.agente_triagem.processar_mensagem(mensagem, estado)

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "triagem"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "triagem"

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
        resposta, estado_atualizado = self.agente_credito.processar_mensagem(mensagem, estado)

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "credito"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "credito"

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
        resposta, estado_atualizado = self.agente_entrevista.processar_mensagem(mensagem, estado)

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "entrevista_credito"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "entrevista_credito"

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
        resposta, estado_atualizado = self.agente_cambio.processar_mensagem(mensagem, estado)

        # Adiciona resposta ao histórico
        estado_atualizado["mensagens"].append({
            "role": "assistant",
            "content": resposta,
            "agent": "cambio"
        })

        # Atualiza agente ativo
        estado_atualizado["agente_ativo"] = "cambio"

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

        # Se tem próximo_passo definido, usa ele
        if "proximo_passo" in estado and estado["proximo_passo"]:
            proximo = estado["proximo_passo"]
            estado["proximo_passo"] = None  # Limpa para próxima iteração
            return proximo

        # Se está na triagem e ainda não autenticou
        if estado["agente_ativo"] == "triagem":
            if not estado.get("cliente_autenticado"):
                return "triagem"  # Permanece na triagem até autenticar
            else:
                # Cliente autenticado - analisa mensagem para decidir serviço
                servico = self.agente_triagem.identificar_servico(estado["mensagem_atual"])
                if servico == "encerramento":
                    return "encerramento"
                elif servico:
                    return servico
                else:
                    return "triagem"  # Não identificou serviço, mostra menu novamente

        # Se está em algum agente específico, permanece nele
        agente_atual = estado["agente_ativo"]
        if agente_atual in ["credito", "entrevista_credito", "cambio"]:
            # Verifica se usuário quer voltar ao menu
            mensagem_lower = estado["mensagem_atual"].lower()
            if any(palavra in mensagem_lower for palavra in ["menu", "voltar", "sair", "encerrar"]):
                if "encerrar" in mensagem_lower or "sair" in mensagem_lower:
                    return "encerramento"
                else:
                    return "triagem"

            # Permanece no agente atual
            return agente_atual

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
        resultado = self.grafo.invoke(self.estado)

        # Atualiza estado interno
        self.estado = resultado

        # Retorna última mensagem do assistente
        mensagens_assistant = [
            msg for msg in self.estado["mensagens"]
            if msg["role"] == "assistant"
        ]

        if mensagens_assistant:
            return mensagens_assistant[-1]["content"]
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
    print("=" * 80)
    print("TESTE DO ORQUESTRADOR LANGGRAPH")
    print("=" * 80)

    try:
        sistema = BancoAgilLangGraph()
        print("\nSistema inicializado com sucesso!")

        print("\n" + "-" * 80)
        print("Teste: Saudacao inicial")
        print("-" * 80)

        resposta = sistema.processar_mensagem("Ola!")
        print(f"\nResposta:\n{resposta}")

    except ValueError as e:
        print(f"\nErro: {e}")
        print("\nConfigure GROQ_API_KEY no arquivo .env para testar o sistema.")

    print("\n" + "=" * 80)
