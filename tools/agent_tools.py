"""
Ferramentas (Tools) disponíveis para os agentes do Banco Ágil.

Define ferramentas que os agentes podem invocar para realizar ações
como autenticar clientes, calcular scores, buscar cotações, etc.
"""

from typing import Optional, Dict, Any
from langchain_core.tools import tool

from tools.data_manager import DataManager
from tools.score_calculator import ScoreCalculator
from tools.currency_fetcher import CurrencyFetcher


# ============================================================================
# FERRAMENTAS DO AGENTE DE TRIAGEM
# ============================================================================

@tool
def authenticate_client(cpf: str, data_nascimento: str) -> Dict[str, Any]:
    """
    Autentica um cliente verificando CPF e data de nascimento.

    Args:
        cpf: CPF do cliente (11 dígitos)
        data_nascimento: Data de nascimento no formato YYYY-MM-DD

    Returns:
        Dicionário com dados do cliente se autenticado, ou None se falhar
    """
    try:
        cliente = DataManager.authenticate_client(cpf, data_nascimento)
        if cliente:
            return {
                "success": True,
                "cliente": cliente,
                "message": f"Cliente {cliente['nome']} autenticado com sucesso!"
            }
        else:
            return {
                "success": False,
                "cliente": None,
                "message": "CPF ou data de nascimento incorretos."
            }
    except Exception as e:
        return {
            "success": False,
            "cliente": None,
            "message": f"Erro ao autenticar: {str(e)}"
        }


# ============================================================================
# FERRAMENTAS DO AGENTE DE CRÉDITO
# ============================================================================

@tool
def get_client_by_cpf(cpf: str) -> Optional[Dict[str, Any]]:
    """
    Busca dados de um cliente pelo CPF.

    Args:
        cpf: CPF do cliente

    Returns:
        Dicionário com dados do cliente ou None se não encontrado
    """
    try:
        return DataManager.get_client_by_cpf(cpf)
    except Exception as e:
        print(f"Erro ao buscar cliente: {e}")
        return None


@tool
def get_max_limit_by_score(score: float) -> Optional[float]:
    """
    Retorna o limite máximo de crédito permitido para um score.

    Args:
        score: Score de crédito do cliente (0-1000)

    Returns:
        Limite máximo permitido em reais
    """
    try:
        return DataManager.get_limit_by_score(score)
    except Exception as e:
        print(f"Erro ao obter limite por score: {e}")
        return None


@tool
def process_limit_request(
    cpf: str,
    limite_atual: float,
    novo_limite: float,
    score: float
) -> Dict[str, Any]:
    """
    Processa uma solicitação de aumento de limite de crédito.

    Valida o novo limite contra o score do cliente e registra a solicitação.

    Args:
        cpf: CPF do cliente
        limite_atual: Limite de crédito atual
        novo_limite: Novo limite solicitado
        score: Score de crédito do cliente

    Returns:
        Dicionário com resultado da solicitação
    """
    try:
        # Valida que novo limite é maior que atual
        if novo_limite <= limite_atual:
            return {
                "success": False,
                "status": "invalido",
                "message": "O novo limite deve ser maior que o limite atual.",
                "limite_maximo_permitido": None
            }

        # Obtém limite máximo permitido pelo score
        limite_maximo = DataManager.get_limit_by_score(score)

        if limite_maximo is None:
            return {
                "success": False,
                "status": "erro",
                "message": "Erro ao validar score.",
                "limite_maximo_permitido": None
            }

        # Decide status baseado no score
        if novo_limite <= limite_maximo:
            status = "aprovado"
            message = f"Solicitação APROVADA! Novo limite: R$ {novo_limite:,.2f}"
        else:
            status = "rejeitado"
            message = (
                f"Solicitação REJEITADA. Seu score ({score:.0f}) permite "
                f"um limite máximo de R$ {limite_maximo:,.2f}."
            )

        # Registra solicitação no CSV
        DataManager.register_limit_request(
            cpf=cpf,
            limite_atual=limite_atual,
            novo_limite=novo_limite,
            status=status
        )

        return {
            "success": True,
            "status": status,
            "message": message,
            "limite_maximo_permitido": limite_maximo,
            "novo_limite": novo_limite if status == "aprovado" else None
        }

    except Exception as e:
        return {
            "success": False,
            "status": "erro",
            "message": f"Erro ao processar solicitação: {str(e)}",
            "limite_maximo_permitido": None
        }


# ============================================================================
# FERRAMENTAS DO AGENTE DE ENTREVISTA
# ============================================================================

@tool
def calculate_credit_score(
    renda_mensal: float,
    tipo_emprego: str,
    despesas_fixas: float,
    num_dependentes: int,
    tem_dividas: str
) -> Dict[str, Any]:
    """
    Calcula novo score de crédito baseado em dados financeiros.

    Args:
        renda_mensal: Renda mensal em reais
        tipo_emprego: "formal", "autônomo" ou "desempregado"
        despesas_fixas: Despesas fixas mensais em reais
        num_dependentes: Número de dependentes (0, 1, 2, 3+)
        tem_dividas: "sim" ou "não"

    Returns:
        Dicionário com novo score e interpretação
    """
    try:
        novo_score = ScoreCalculator.calculate_score(
            renda_mensal=renda_mensal,
            tipo_emprego=tipo_emprego,
            despesas_fixas=despesas_fixas,
            num_dependentes=num_dependentes,
            tem_dividas=tem_dividas
        )

        interpretacao = ScoreCalculator.get_score_interpretation(novo_score)

        return {
            "success": True,
            "novo_score": novo_score,
            "interpretacao": interpretacao,
            "message": f"Novo score calculado: {novo_score:.0f} ({interpretacao})"
        }

    except Exception as e:
        return {
            "success": False,
            "novo_score": None,
            "interpretacao": None,
            "message": f"Erro ao calcular score: {str(e)}"
        }


@tool
def update_client_score(cpf: str, novo_score: float) -> Dict[str, Any]:
    """
    Atualiza o score de crédito de um cliente no banco de dados.

    Args:
        cpf: CPF do cliente
        novo_score: Novo score de crédito (0-1000)

    Returns:
        Dicionário indicando sucesso ou falha
    """
    try:
        success = DataManager.update_client_score(cpf, novo_score)

        if success:
            return {
                "success": True,
                "message": f"Score atualizado para {novo_score:.0f} com sucesso!"
            }
        else:
            return {
                "success": False,
                "message": "Erro ao atualizar score no banco de dados."
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao atualizar score: {str(e)}"
        }


# ============================================================================
# FERRAMENTAS DO AGENTE DE CÂMBIO
# ============================================================================

@tool
def get_exchange_rate(moeda: str = "USD") -> Dict[str, Any]:
    """
    Busca cotação de uma moeda em relação ao Real (BRL).

    Args:
        moeda: Código da moeda (USD, EUR, GBP, etc.). Padrão: USD

    Returns:
        Dicionário com taxa de câmbio e informações adicionais
    """
    try:
        # Busca cotação via CurrencyFetcher
        taxa = CurrencyFetcher.get_rate(moeda)

        if taxa is None:
            return {
                "success": False,
                "moeda": moeda,
                "taxa": None,
                "message": f"Não foi possível obter cotação para {moeda}."
            }

        return {
            "success": True,
            "moeda": moeda,
            "taxa": taxa,
            "message": f"Cotação {moeda}/BRL: R$ {taxa:.4f}",
            "exemplos": {
                "1": taxa,
                "100": taxa * 100,
                "1000": taxa * 1000
            }
        }

    except Exception as e:
        return {
            "success": False,
            "moeda": moeda,
            "taxa": None,
            "message": f"Erro ao buscar cotação: {str(e)}"
        }


# ============================================================================
# MAPEAMENTO DE FERRAMENTAS POR AGENTE
# ============================================================================

AGENT_TOOLS = {
    "triagem": [
        authenticate_client
    ],
    "credito": [
        get_client_by_cpf,
        get_max_limit_by_score,
        process_limit_request
    ],
    "entrevista_credito": [
        calculate_credit_score,
        update_client_score
    ],
    "cambio": [
        get_exchange_rate
    ]
}


def get_tools_for_agent(agent_name: str) -> list:
    """
    Retorna lista de ferramentas disponíveis para um agente.

    Args:
        agent_name: Nome do agente

    Returns:
        Lista de ferramentas (Tools)
    """
    return AGENT_TOOLS.get(agent_name, [])


if __name__ == "__main__":
    # Teste das ferramentas
    print("=" * 80)
    print("TESTE DAS FERRAMENTAS DOS AGENTES")
    print("=" * 80)

    print("\n1. Testando autenticação...")
    resultado = authenticate_client("12345678901", "1990-05-15")
    print(f"Resultado: {resultado}")

    print("\n2. Testando cálculo de score...")
    resultado = calculate_credit_score(
        renda_mensal=5000,
        tipo_emprego="formal",
        despesas_fixas=2000,
        num_dependentes=1,
        tem_dividas="não"
    )
    print(f"Resultado: {resultado}")

    print("\n3. Testando cotação de câmbio...")
    resultado = get_exchange_rate("USD")
    print(f"Resultado: {resultado}")

    print("\n✅ Testes concluídos!")
