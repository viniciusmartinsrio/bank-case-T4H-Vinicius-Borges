"""
Módulo de agentes especializados do Banco Ágil.
Cada agente é responsável por um domínio específico do atendimento.
"""

from .triagem_agent import TriagemAgent
from .credito_agent import CreditoAgent
from .entrevista_credito_agent import EntrevistaCreditoAgent
from .cambio_agent import CambioAgent

__all__ = [
    'TriagemAgent',
    'CreditoAgent',
    'EntrevistaCreditoAgent',
    'CambioAgent'
]
