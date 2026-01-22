"""Tools para o sistema bancário de agentes de IA."""

from .data_manager import DataManager
from .score_calculator import ScoreCalculator
from .currency_fetcher import CurrencyFetcher
from .agent_tools import (
    authenticate_client,
    get_client_by_cpf,
    get_max_limit_by_score,
    process_limit_request,
    calculate_credit_score,
    update_client_score,
    get_exchange_rate,
    get_tools_for_agent,
    AGENT_TOOLS
)

__all__ = [
    "DataManager",
    "ScoreCalculator",
    "CurrencyFetcher",
    "authenticate_client",
    "get_client_by_cpf",
    "get_max_limit_by_score",
    "process_limit_request",
    "calculate_credit_score",
    "update_client_score",
    "get_exchange_rate",
    "get_tools_for_agent",
    "AGENT_TOOLS"
]
