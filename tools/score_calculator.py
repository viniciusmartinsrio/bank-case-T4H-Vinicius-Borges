"""
Calculadora de score de crédito baseada em dados financeiros do cliente.
Implementa a fórmula ponderada especificada no desafio.
"""

from typing import Dict, Literal


class ScoreCalculator:
    """Calcula score de crédito usando fórmula ponderada."""

    # Pesos da fórmula
    PESO_RENDA = 30
    PESO_EMPREGO = {
        "formal": 300,
        "autônomo": 200,
        "desempregado": 0
    }
    PESO_DEPENDENTES = {
        0: 100,
        1: 80,
        2: 60,
        "3+": 30
    }
    PESO_DIVIDAS = {
        "sim": -100,
        "não": 100
    }

    @staticmethod
    def calculate_score(
        renda_mensal: float,
        tipo_emprego: Literal["formal", "autônomo", "desempregado"],
        despesas_fixas: float,
        num_dependentes: int,
        tem_dividas: Literal["sim", "não"]
    ) -> float:
        """
        Calcula o score de crédito usando a fórmula ponderada.
        
        Fórmula:
        score = (
            (renda_mensal / (despesas + 1)) * peso_renda +
            peso_emprego[tipo_emprego] +
            peso_dependentes[num_dependentes] +
            peso_dividas[tem_dividas]
        )
        
        Args:
            renda_mensal: Renda mensal em reais (float)
            tipo_emprego: Tipo de emprego (formal, autônomo, desempregado)
            despesas_fixas: Despesas fixas mensais em reais (float)
            num_dependentes: Número de dependentes (int)
            tem_dividas: Se tem dívidas ativas (sim/não)
            
        Returns:
            Score de crédito normalizado entre 0 e 1000
            
        Raises:
            ValueError: Se algum parâmetro for inválido
        """
        # Validações
        if renda_mensal < 0:
            raise ValueError("Renda mensal não pode ser negativa")
        if despesas_fixas < 0:
            raise ValueError("Despesas fixas não podem ser negativas")
        if num_dependentes < 0:
            raise ValueError("Número de dependentes não pode ser negativo")
        if tipo_emprego not in ScoreCalculator.PESO_EMPREGO:
            raise ValueError(f"Tipo de emprego inválido: {tipo_emprego}")
        if tem_dividas not in ScoreCalculator.PESO_DIVIDAS:
            raise ValueError(f"Valor de dívidas inválido: {tem_dividas}")

        # Normaliza número de dependentes para a chave correta
        dependentes_key = num_dependentes if num_dependentes <= 2 else "3+"

        # Calcula componentes da fórmula
        razao_renda_despesa = renda_mensal / (despesas_fixas + 1)
        componente_renda = razao_renda_despesa * ScoreCalculator.PESO_RENDA
        componente_emprego = ScoreCalculator.PESO_EMPREGO[tipo_emprego]
        componente_dependentes = ScoreCalculator.PESO_DEPENDENTES[dependentes_key]
        componente_dividas = ScoreCalculator.PESO_DIVIDAS[tem_dividas]

        # Score bruto
        score_bruto = (
            componente_renda +
            componente_emprego +
            componente_dependentes +
            componente_dividas
        )

        # Normaliza para escala 0-1000
        # O score máximo teórico é aproximadamente 1000 com renda alta e sem dívidas
        score_normalizado = max(0, min(1000, score_bruto))

        return round(score_normalizado, 2)

    @staticmethod
    def get_score_interpretation(score: float) -> str:
        """Retorna uma interpretação textual do score."""
        if score < 300:
            return "Muito baixo - Acesso limitado a crédito"
        elif score < 500:
            return "Baixo - Acesso restrito a crédito"
        elif score < 700:
            return "Médio - Acesso moderado a crédito"
        elif score < 850:
            return "Bom - Acesso a crédito com boas condições"
        else:
            return "Excelente - Acesso a crédito com melhores condições"
