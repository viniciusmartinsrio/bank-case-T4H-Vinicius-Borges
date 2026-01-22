"""
Agente de Crédito com LLM - Consulta e solicitação de aumento de limite.
Responsável por informar limites e processar solicitações.

Versão refatorada usando LLM para conversação natural e empática.
"""

from typing import Dict, Optional, Tuple
from agents.base_agent import BaseAgent
from tools.agent_tools import get_tools_for_agent
from state import EstadoConversacao


class CreditoAgentLLM(BaseAgent):
    """
    Agente de Crédito com capacidades de LLM.

    Processa consultas e solicitações de aumento de limite de crédito
    de forma conversacional e empática.
    """

    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Inicializa o Agente de Crédito com LLM.

        Args:
            groq_api_key: API key do Groq (opcional, usa .env se não fornecido)
        """
        # Obtém ferramentas específicas para crédito
        tools = get_tools_for_agent("credito")

        # Inicializa agente base
        super().__init__(
            agent_name="credito",
            tools=tools,
            groq_api_key=groq_api_key
        )

        # Estado específico do crédito
        self.cliente: Optional[Dict] = None
        self.solicitacao_em_andamento = False
        self.novo_limite_solicitado: Optional[float] = None
        self.limite_maximo_permitido: Optional[float] = None

    def processar_mensagem(
        self,
        mensagem_usuario: str,
        estado: EstadoConversacao
    ) -> Tuple[str, EstadoConversacao]:
        """
        Processa mensagem do usuário no contexto de crédito.

        Args:
            mensagem_usuario: Mensagem do usuário
            estado: Estado atual da conversa

        Returns:
            Tupla (resposta_agente, estado_atualizado)
        """
        # Obtém dados do cliente do estado
        if not self.cliente and estado.get("cliente_autenticado"):
            self.cliente = estado["cliente_autenticado"]

        if not self.cliente:
            return "Erro: Cliente não autenticado.", estado

        # Prepara contexto com dados do cliente
        context = {
            "nome": self.cliente["nome"],
            "limite_atual": self.cliente["limite_credito"],
            "score": self.cliente["score_credito"]
        }

        # Detecta se mensagem contém valor numérico (possível novo limite)
        valor_detectado = self._extrair_valor(mensagem_usuario)

        # Se detectou valor e não está em solicitação, inicia solicitação
        if valor_detectado and not self.solicitacao_em_andamento:
            self.solicitacao_em_andamento = True
            self.novo_limite_solicitado = valor_detectado

            # Usa ferramenta para processar solicitação
            from tools.agent_tools import process_limit_request

            resultado = process_limit_request(
                cpf=self.cliente["cpf"],
                limite_atual=self.cliente["limite_credito"],
                novo_limite=valor_detectado,
                score=self.cliente["score_credito"]
            )

            if not resultado["success"]:
                # Erro na validação
                resposta = self.invoke(
                    f"Erro ao processar: {resultado['message']}. "
                    "Explique ao cliente e peça um novo valor válido.",
                    context=context
                )
                self.solicitacao_em_andamento = False
                return resposta, estado

            # Guarda limite máximo permitido
            self.limite_maximo_permitido = resultado.get("limite_maximo_permitido")

            if resultado["status"] == "aprovado":
                # APROVADO
                resposta = self.invoke(
                    f"Solicitação APROVADA para R$ {valor_detectado:,.2f}! "
                    "Parabenize o cliente de forma calorosa.",
                    context=context
                )

                # Atualiza limite no estado (simulação - em produção seria atualizado no BD)
                estado["cliente_autenticado"]["limite_credito"] = valor_detectado

                self.solicitacao_em_andamento = False
                return resposta, estado

            elif resultado["status"] == "rejeitado":
                # REJEITADO - oferece entrevista
                resposta = self.invoke(
                    f"Solicitação REJEITADA. Limite máximo permitido para score "
                    f"{self.cliente['score_credito']:.0f} é R$ {self.limite_maximo_permitido:,.2f}. "
                    "Seja empático e ofereça entrevista financeira para melhorar o score.",
                    context=context
                )

                # Marca que pode redirecionar para entrevista
                estado["dados_temporarios"]["pode_fazer_entrevista"] = True

                self.solicitacao_em_andamento = False
                return resposta, estado

        # Detecta se cliente aceita ou recusa entrevista
        if estado["dados_temporarios"].get("pode_fazer_entrevista"):
            mensagem_lower = mensagem_usuario.lower()

            if any(palavra in mensagem_lower for palavra in ["sim", "aceito", "quero", "pode", "vamos"]):
                # Cliente aceita entrevista
                estado["proximo_passo"] = "entrevista_credito"
                resposta = self.invoke(
                    "Cliente aceitou fazer entrevista. Informe que ele será "
                    "redirecionado para o especialista em análise financeira.",
                    context=context
                )
                return resposta, estado

            elif any(palavra in mensagem_lower for palavra in ["não", "nao", "recuso", "não quero"]):
                # Cliente recusa
                estado["dados_temporarios"]["pode_fazer_entrevista"] = False
                resposta = self.invoke(
                    "Cliente recusou entrevista. Agradeça e pergunte se pode "
                    "ajudar com mais alguma coisa.",
                    context=context
                )
                return resposta, estado

        # Caso padrão: LLM decide o que responder
        resposta = self.invoke(mensagem_usuario, context=context)
        return resposta, estado

    def _extrair_valor(self, texto: str) -> Optional[float]:
        """
        Extrai valor monetário de um texto.

        Args:
            texto: Texto contendo possível valor

        Returns:
            Valor em float ou None se não encontrado
        """
        import re

        # Remove símbolos monetários e formatação
        texto_limpo = texto.replace("R$", "").replace(".", "").replace(",", ".")

        # Busca por números (inteiros ou decimais)
        match = re.search(r'\d+(?:\.\d+)?', texto_limpo)

        if match:
            try:
                valor = float(match.group())
                # Valida que é um valor razoável (> 100 e < 100000)
                if 100 <= valor <= 100000:
                    return valor
            except ValueError:
                pass

        return None

    def reset(self):
        """Reseta o estado do agente."""
        super().reset_history()
        self.cliente = None
        self.solicitacao_em_andamento = False
        self.novo_limite_solicitado = None
        self.limite_maximo_permitido = None


if __name__ == "__main__":
    # Teste básico do agente
    print("=" * 80)
    print("TESTE DO AGENTE DE CRÉDITO COM LLM")
    print("=" * 80)

    try:
        agente = CreditoAgentLLM()
        print("\n✅ Agente inicializado com sucesso!")
        print(f"\nConfiguração: {agente.get_config_summary()}")

        # Simula cliente autenticado
        from state import criar_estado_inicial
        estado = criar_estado_inicial()
        estado["cliente_autenticado"] = {
            "cpf": "12345678901",
            "nome": "João Silva",
            "limite_credito": 5000.00,
            "score_credito": 750
        }

        agente.cliente = estado["cliente_autenticado"]

        print("\n" + "-" * 80)
        print("Teste: Consulta de limite")
        print("-" * 80)

        resposta, estado = agente.processar_mensagem(
            "Gostaria de saber meu limite",
            estado
        )
        print(f"\nResposta do agente:\n{resposta}")

    except ValueError as e:
        print(f"\n❌ Erro: {e}")
        print("\nConfigure GROQ_API_KEY no arquivo .env para testar o agente.")

    print("\n" + "=" * 80)
