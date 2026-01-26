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
        # Inicializa agente base sem tools (chamadas Python diretas)
        super().__init__(
            agent_name="entrevista_credito",
            tools=[],  # Sem tool calling
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

        # DETECTA SE ENTREVISTA FOI CONCLUÍDA: Usuário está vendo resultado e quer voltar
        entrevista_concluida = estado.get("dados_temporarios", {}).get("entrevista_concluida", False)
        if entrevista_concluida:
            # Limpa flag
            estado["dados_temporarios"]["entrevista_concluida"] = False
            # Redireciona para triagem
            estado["proximo_passo"] = "triagem"
            estado["contexto_agente"]["agente_anterior"] = "triagem"
            estado["dados_temporarios"]["voltou_ao_menu"] = True

            resposta = "Você será redirecionado ao menu principal..."
            return resposta, estado

        # DETECTA PRIMEIRA ENTRADA: Se acabou de entrar vindo de outro agente
        agente_anterior = estado.get("contexto_agente", {}).get("agente_anterior")

        # Se é a primeira entrada no agente (vindo de triagem ou crédito)
        # Apresenta saudação inicial e NÃO processa a mensagem como resposta
        # IMPORTANTE: agente_anterior pode ser None (primeira entrada) ou outro agente
        if agente_anterior != "entrevista_credito":

            # Marca que já entrou
            estado["contexto_agente"]["agente_anterior"] = "entrevista_credito"

            # Reseta dados da entrevista (nova entrevista)
            self.dados_coletados = {
                "renda_mensal": None,
                "tipo_emprego": None,
                "despesas_fixas": None,
                "num_dependentes": None,
                "tem_dividas": None,
                "pergunta_atual": 1,
                "novo_score_calculado": None
            }

            # Sincroniza dados da entrevista com o estado para exibição do progresso
            estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

            # Prepara contexto
            context = {
                "nome": self.cliente["nome"],
                "pergunta_atual": 1,
                "total_perguntas": 5
            }

            # Saudação inicial + Primeira pergunta
            resposta = self.invoke(
                "Cliente chegou para entrevista financeira. "
                "Dê boas-vindas, explique que serão 5 perguntas rápidas, "
                "e faça a PRIMEIRA pergunta (1/5): renda mensal aproximada.",
                context=context
            )

            return resposta, estado

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

                # Sincroniza dados da entrevista com o estado para exibição do progresso
                estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

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

                # Sincroniza dados da entrevista com o estado para exibição do progresso
                estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

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

                # Sincroniza dados da entrevista com o estado para exibição do progresso
                estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

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

                # Sincroniza dados da entrevista com o estado para exibição do progresso
                estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

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

                # Sincroniza dados da entrevista com o estado para exibição do progresso
                estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

                # Todas as perguntas respondidas - calcula score
                from tools.score_calculator import ScoreCalculator
                from tools.data_manager import DataManager

                try:
                    novo_score = ScoreCalculator.calculate_score(
                        renda_mensal=self.dados_coletados["renda_mensal"],
                        tipo_emprego=self.dados_coletados["tipo_emprego"],
                        despesas_fixas=self.dados_coletados["despesas_fixas"],
                        num_dependentes=self.dados_coletados["num_dependentes"],
                        tem_dividas=self.dados_coletados["tem_dividas"]
                    )

                    interpretacao = ScoreCalculator.get_score_interpretation(novo_score)

                    resultado_calculo = {
                        "success": True,
                        "novo_score": novo_score,
                        "interpretacao": interpretacao,
                        "message": f"Novo score calculado: {novo_score:.0f} ({interpretacao})"
                    }
                except Exception as e:
                    resultado_calculo = {
                        "success": False,
                        "novo_score": None,
                        "interpretacao": None,
                        "message": f"Erro ao calcular score: {str(e)}"
                    }

                if not resultado_calculo["success"]:
                    resposta = self.invoke(
                        f"Erro ao calcular score: {resultado_calculo['message']}",
                        context=context
                    )
                    return resposta, estado

                novo_score = resultado_calculo["novo_score"]
                interpretacao = resultado_calculo["interpretacao"]
                score_atual = self.cliente["score_credito"]

                # Compara novo score com o score atual
                if novo_score < score_atual:
                    # Novo score é menor - mantém o score atual
                    score_final = score_atual
                    interpretacao_final = ScoreCalculator.get_score_interpretation(score_atual)
                    score_foi_mantido = True

                    # Não atualiza o banco de dados nem o estado
                    # Score permanece inalterado

                    self.dados_coletados["novo_score_calculado"] = novo_score  # Guarda o calculado para referência

                    # Sincroniza dados da entrevista com o estado para exibição do progresso
                    estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

                    # Marca que entrevista foi concluída para que próxima interação volte ao menu
                    estado["dados_temporarios"]["entrevista_concluida"] = True

                    # Informa ao cliente que o score foi mantido
                    resposta = self.invoke(
                        f"Entrevista concluída! O score calculado foi {novo_score:.0f} ({interpretacao}), "
                        f"que é menor que seu score atual de {score_atual:.0f} ({interpretacao_final}). "
                        f"Boa notícia: mantivemos seu score atual de {score_atual:.0f} para seu benefício! "
                        f"Informe ao cliente de forma clara e positiva que o score dele foi preservado, "
                        f"e instrua que ele pode voltar ao menu principal digitando 'menu', 'voltar' ou 'opções'.",
                        context=context
                    )

                    return resposta, estado

                else:
                    # Novo score é maior ou igual - atualiza normalmente
                    score_final = novo_score
                    interpretacao_final = interpretacao
                    score_foi_mantido = False

                    # Atualiza score no banco de dados
                    success = DataManager.update_client_score(self.cliente["cpf"], novo_score)

                    if not success:
                        resposta = self.invoke(
                            "Erro ao atualizar score no banco de dados.",
                            context=context
                        )
                        return resposta, estado

                    # Atualiza no estado
                    estado["cliente_autenticado"]["score_credito"] = novo_score
                    self.dados_coletados["novo_score_calculado"] = novo_score

                    # Sincroniza dados da entrevista com o estado para exibição do progresso
                    estado["dados_temporarios"]["dados_entrevista"] = self.dados_coletados.copy()

                    # Marca que entrevista foi concluída para que próxima interação volte ao menu
                    estado["dados_temporarios"]["entrevista_concluida"] = True

                    # NÃO redireciona automaticamente - aguarda usuário ver resultado
                    # Na próxima mensagem, detectamos a flag e voltamos ao menu

                    resposta = self.invoke(
                        f"Score recalculado com sucesso! Novo score: {novo_score:.0f} "
                        f"({interpretacao}). Informe ao cliente de forma clara e objetiva, "
                        f"parabenize pelo resultado e instrua que ele pode voltar ao menu principal "
                        f"digitando 'menu', 'voltar' ou 'opções'.",
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
