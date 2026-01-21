"""
Agente de Entrevista de Crédito - Conduz entrevista financeira.
Responsável por coletar dados e recalcular o score de crédito.
"""

from typing import Dict, Optional, Literal
from tools.data_manager import DataManager
from tools.score_calculator import ScoreCalculator


class EntrevistaCreditoAgent:
    """Agente responsável por entrevista financeira e cálculo de score."""

    def __init__(self):
        self.cliente: Optional[Dict] = None
        self.dados_entrevista: Dict = {}
        self.etapa_atual = 0
        self.etapas = [
            "renda_mensal",
            "tipo_emprego",
            "despesas_fixas",
            "num_dependentes",
            "tem_dividas"
        ]

    def definir_cliente(self, cliente: Dict):
        """Define o cliente para a entrevista."""
        self.cliente = cliente
        self.dados_entrevista = {}
        self.etapa_atual = 0

    def iniciar_entrevista(self) -> str:
        """Inicia a entrevista financeira."""
        if not self.cliente:
            return "❌ Cliente não autenticado."
        
        return f"""
📋 Entrevista Financeira - {self.cliente['nome']}

Vou fazer algumas perguntas sobre sua situação financeira para recalcular seu score de crédito.

Vamos começar?

{self._fazer_proxima_pergunta()}
        """

    def _fazer_proxima_pergunta(self) -> str:
        """Faz a próxima pergunta da entrevista."""
        if self.etapa_atual >= len(self.etapas):
            return ""
        
        etapa = self.etapas[self.etapa_atual]
        
        if etapa == "renda_mensal":
            return "1️⃣ Qual é sua renda mensal bruta? (em reais)"
        elif etapa == "tipo_emprego":
            return """2️⃣ Qual é seu tipo de emprego?
   - formal
   - autônomo
   - desempregado"""
        elif etapa == "despesas_fixas":
            return "3️⃣ Qual é o valor de suas despesas fixas mensais? (em reais)"
        elif etapa == "num_dependentes":
            return "4️⃣ Quantas pessoas dependem financeiramente de você?"
        elif etapa == "tem_dividas":
            return """5️⃣ Você tem dívidas ativas?
   - sim
   - não"""
        
        return ""

    def processar_resposta(self, resposta: str) -> tuple[bool, str]:
        """
        Processa a resposta do cliente.
        
        Returns:
            (sucesso, mensagem)
        """
        if self.etapa_atual >= len(self.etapas):
            return False, "❌ Entrevista já foi concluída."
        
        etapa = self.etapas[self.etapa_atual]
        resposta_limpa = resposta.strip().lower()
        
        try:
            if etapa == "renda_mensal":
                renda = float(resposta_limpa.replace("R$", "").replace(",", "."))
                if renda < 0:
                    return False, "❌ Renda não pode ser negativa."
                self.dados_entrevista["renda_mensal"] = renda
                
            elif etapa == "tipo_emprego":
                if resposta_limpa not in ["formal", "autônomo", "desempregado"]:
                    return False, "❌ Tipo de emprego inválido. Escolha: formal, autônomo ou desempregado."
                self.dados_entrevista["tipo_emprego"] = resposta_limpa
                
            elif etapa == "despesas_fixas":
                despesas = float(resposta_limpa.replace("R$", "").replace(",", "."))
                if despesas < 0:
                    return False, "❌ Despesas não podem ser negativas."
                self.dados_entrevista["despesas_fixas"] = despesas
                
            elif etapa == "num_dependentes":
                num_dep = int(resposta_limpa)
                if num_dep < 0:
                    return False, "❌ Número de dependentes não pode ser negativo."
                self.dados_entrevista["num_dependentes"] = num_dep
                
            elif etapa == "tem_dividas":
                if resposta_limpa not in ["sim", "não"]:
                    return False, "❌ Responda com 'sim' ou 'não'."
                self.dados_entrevista["tem_dividas"] = resposta_limpa
            
            self.etapa_atual += 1
            
            # Se entrevista concluída
            if self.etapa_atual >= len(self.etapas):
                return True, self._calcular_novo_score()
            else:
                # Próxima pergunta
                proxima_pergunta = self._fazer_proxima_pergunta()
                return True, f"✅ Resposta registrada.\n\n{proxima_pergunta}"
        
        except ValueError:
            return False, "❌ Valor inválido. Por favor, forneça um número válido."
        except Exception as e:
            return False, f"❌ Erro ao processar resposta: {str(e)}"

    def _calcular_novo_score(self) -> str:
        """Calcula o novo score e atualiza no banco de dados."""
        try:
            # Calcula novo score
            novo_score = ScoreCalculator.calculate_score(
                renda_mensal=self.dados_entrevista["renda_mensal"],
                tipo_emprego=self.dados_entrevista["tipo_emprego"],
                despesas_fixas=self.dados_entrevista["despesas_fixas"],
                num_dependentes=self.dados_entrevista["num_dependentes"],
                tem_dividas=self.dados_entrevista["tem_dividas"]
            )
            
            # Atualiza no banco de dados
            sucesso = DataManager.update_client_score(self.cliente["cpf"], novo_score)
            
            if not sucesso:
                return "❌ Erro ao atualizar score no banco de dados."
            
            # Atualiza cliente local
            self.cliente["score_credito"] = novo_score
            
            score_anterior = self.cliente.get("score_credito", 0)
            interpretacao = ScoreCalculator.get_score_interpretation(novo_score)
            diferenca = novo_score - score_anterior
            sinal = "+" if diferenca > 0 else ""
            
            return f"""
✅ Entrevista Concluída!

📊 Novo Score de Crédito: {novo_score:.0f}
   Interpretação: {interpretacao}
   Variação: {sinal}{diferenca:.0f}

Você será redirecionado para o Agente de Crédito para reanalisar sua solicitação de aumento de limite.
            """
        except Exception as e:
            return f"❌ Erro ao calcular novo score: {str(e)}"

    def entrevista_completa(self) -> bool:
        """Verifica se a entrevista foi completada."""
        return self.etapa_atual >= len(self.etapas)

    def reset(self):
        """Reseta o estado do agente."""
        self.cliente = None
        self.dados_entrevista = {}
        self.etapa_atual = 0
