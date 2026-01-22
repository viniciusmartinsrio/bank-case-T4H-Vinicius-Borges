"""
Agente de Entrevista de Crédito com LLM - Análise financeira personalizada.
Responsável por coletar dados financeiros e recalcular score de crédito.

Versão refatorada usando LLM para conduzir entrevista natural e conversacional.
"""

from typing import Dict, Optional, Tuple, Any
from agents.base_agent import BaseAgent
from tools.agent_tools import get_tools_for_agent
from state import EstadoConversacao, DadosEntrevista


class EntrevistaCreditoAgentLLM(BaseAgent):
    """
    Agente de Entrevista com capacidades de LLM.

    Conduz entrevista financeira estruturada de forma natural
    para recalcular score de crédito do cliente.
    """

    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Inicializa o Agente de Entrevista com LLM.

        Args:
            groq_api_key: API key do Groq (opcional, usa .env se não fornecido)
        """
        # Obtém ferramentas específicas para entrevista
        tools = get_tools_for_agent("entrevista_credito")

        # Inicializa agente base
        super().__init__(
            agent_name="entrevista_credito",
            tools=tools,
            groq_api_key=groq_api_key
        )

        # Estado específico da entrevista
        self.cliente: Optional[Dict] = None
        self.dados_coletados: DadosEntrevista = {
            "renda_mensal": None,
            "tipo_emprego": None,
            "despesas_fixas": None,
            "num_dependentes": None,
            "tem_dividas": None,
            "pergunta_atual": 1,
            "novo_score_calculado": None
        }

    def processar_mensagem(
        self,
        mensagem_usuario: str,
        estado: EstadoConversacao
    ) -> Tuple[str, EstadoConversacao]:
        """
        Processa mensagem do usuário no contexto de entrevista financeira.

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

        # Prepara contexto
        context = {
            "nome": self.cliente["nome"],
            "pergunta_atual": self.dados_coletados["pergunta_atual"],
            "total_perguntas": 5
        }

        # Processa resposta baseado na pergunta atual
        pergunta_atual = self.dados_coletados["pergunta_atual"]

        if pergunta_atual == 1:
            # Pergunta 1: Renda mensal
            valor = self._extrair_valor_monetario(mensagem_usuario)
            if valor:
                self.dados_coletados["renda_mensal"] = valor
                self.dados_coletados["pergunta_atual"] = 2

                resposta = self.invoke(
                    f"Renda mensal coletada: R$ {valor:,.2f}. "
                    "Confirme e faça a próxima pergunta (2/5): tipo de emprego.",
                    context=context
                )
                return resposta, estado

        elif pergunta_atual == 2:
            # Pergunta 2: Tipo de emprego
            tipo = self._identificar_tipo_emprego(mensagem_usuario)
            if tipo:
                self.dados_coletados["tipo_emprego"] = tipo
                self.dados_coletados["pergunta_atual"] = 3

                resposta = self.invoke(
                    f"Tipo de emprego coletado: {tipo}. "
                    "Confirme e faça a próxima pergunta (3/5): despesas fixas mensais.",
                    context=context
                )
                return resposta, estado

        elif pergunta_atual == 3:
            # Pergunta 3: Despesas fixas
            valor = self._extrair_valor_monetario(mensagem_usuario)
            if valor:
                self.dados_coletados["despesas_fixas"] = valor
                self.dados_coletados["pergunta_atual"] = 4

                resposta = self.invoke(
                    f"Despesas fixas coletadas: R$ {valor:,.2f}. "
                    "Confirme e faça a próxima pergunta (4/5): número de dependentes.",
                    context=context
                )
                return resposta, estado

        elif pergunta_atual == 4:
            # Pergunta 4: Número de dependentes
            num = self._extrair_numero(mensagem_usuario)
            if num is not None:
                self.dados_coletados["num_dependentes"] = num
                self.dados_coletados["pergunta_atual"] = 5

                resposta = self.invoke(
                    f"Número de dependentes coletado: {num}. "
                    "Confirme e faça a última pergunta (5/5): tem dívidas ativas?",
                    context=context
                )
                return resposta, estado

        elif pergunta_atual == 5:
            # Pergunta 5: Tem dívidas
            tem_dividas = self._identificar_sim_nao(mensagem_usuario)
            if tem_dividas:
                self.dados_coletados["tem_dividas"] = tem_dividas

                # Todas as perguntas respondidas - calcula score
                from tools.agent_tools import calculate_credit_score, update_client_score

                resultado_calculo = calculate_credit_score(
                    renda_mensal=self.dados_coletados["renda_mensal"],
                    tipo_emprego=self.dados_coletados["tipo_emprego"],
                    despesas_fixas=self.dados_coletados["despesas_fixas"],
                    num_dependentes=self.dados_coletados["num_dependentes"],
                    tem_dividas=self.dados_coletados["tem_dividas"]
                )

                if not resultado_calculo["success"]:
                    resposta = self.invoke(
                        f"Erro ao calcular score: {resultado_calculo['message']}",
                        context=context
                    )
                    return resposta, estado

                novo_score = resultado_calculo["novo_score"]
                interpretacao = resultado_calculo["interpretacao"]

                # Atualiza score no banco de dados
                update_client_score(self.cliente["cpf"], novo_score)

                # Atualiza no estado
                estado["cliente_autenticado"]["score_credito"] = novo_score
                self.dados_coletados["novo_score_calculado"] = novo_score

                # Prepara redirecionamento para crédito
                estado["proximo_passo"] = "credito"

                resposta = self.invoke(
                    f"Score recalculado com sucesso! Novo score: {novo_score:.0f} "
                    f"({interpretacao}). Informe ao cliente e explique que ele será "
                    "redirecionado ao agente de crédito para nova análise.",
                    context=context
                )

                return resposta, estado

        # Se chegou aqui, resposta não foi reconhecida - LLM pede esclarecimento
        resposta = self.invoke(
            f"Resposta não clara para pergunta {pergunta_atual}. "
            "Peça esclarecimento de forma educada.",
            context=context
        )
        return resposta, estado

    def _extrair_valor_monetario(self, texto: str) -> Optional[float]:
        """Extrai valor monetário do texto."""
        import re
        texto_limpo = texto.replace("R$", "").replace(".", "").replace(",", ".")
        match = re.search(r'\d+(?:\.\d+)?', texto_limpo)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        return None

    def _identificar_tipo_emprego(self, texto: str) -> Optional[str]:
        """Identifica tipo de emprego no texto."""
        texto_lower = texto.lower()

        if any(palavra in texto_lower for palavra in ["clt", "formal", "registrado", "empregado", "funcionário"]):
            return "formal"
        elif any(palavra in texto_lower for palavra in ["autônomo", "autonomo", "freelancer", "mei", "próprio"]):
            return "autônomo"
        elif any(palavra in texto_lower for palavra in ["desempregado", "desocupado", "sem emprego", "não trabalho"]):
            return "desempregado"

        return None

    def _extrair_numero(self, texto: str) -> Optional[int]:
        """Extrai número inteiro do texto."""
        import re

        # Mapeamento de texto para número
        texto_para_num = {
            "zero": 0, "nenhum": 0,
            "um": 1, "uma": 1,
            "dois": 2, "duas": 2,
            "três": 3, "tres": 3,
            "quatro": 4,
            "cinco": 5
        }

        texto_lower = texto.lower()
        for palavra, numero in texto_para_num.items():
            if palavra in texto_lower:
                return numero

        # Tenta extrair número diretamente
        match = re.search(r'\d+', texto)
        if match:
            try:
                num = int(match.group())
                if 0 <= num <= 10:  # Validação razoável
                    return num
            except ValueError:
                pass

        return None

    def _identificar_sim_nao(self, texto: str) -> Optional[str]:
        """Identifica resposta sim/não no texto."""
        texto_lower = texto.lower()

        if any(palavra in texto_lower for palavra in ["sim", "tenho", "possuo", "há", "existe"]):
            return "sim"
        elif any(palavra in texto_lower for palavra in ["não", "nao", "nenhuma", "sem", "zero"]):
            return "não"

        return None

    def reset(self):
        """Reseta o estado do agente."""
        super().reset_history()
        self.cliente = None
        self.dados_coletados = {
            "renda_mensal": None,
            "tipo_emprego": None,
            "despesas_fixas": None,
            "num_dependentes": None,
            "tem_dividas": None,
            "pergunta_atual": 1,
            "novo_score_calculado": None
        }


if __name__ == "__main__":
    # Teste básico do agente
    print("=" * 80)
    print("TESTE DO AGENTE DE ENTREVISTA COM LLM")
    print("=" * 80)

    try:
        agente = EntrevistaCreditoAgentLLM()
        print("\n✅ Agente inicializado com sucesso!")
        print(f"\nConfiguração: {agente.get_config_summary()}")

    except ValueError as e:
        print(f"\n❌ Erro: {e}")
        print("\nConfigure GROQ_API_KEY no arquivo .env para testar o agente.")

    print("\n" + "=" * 80)
