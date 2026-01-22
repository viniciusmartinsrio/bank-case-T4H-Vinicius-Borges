"""
Configurações de LLM para cada agente do Banco Ágil.

Define parâmetros específicos (temperature, top_p, max_tokens) para cada agente,
otimizados de acordo com suas responsabilidades e estilo de comunicação.
"""

from typing import Dict, Any

# Modelo base utilizado (Groq API - Llama 3.1 70B)
DEFAULT_MODEL = "llama-3.1-70b-versatile"

# Configurações específicas por agente
LLM_CONFIGS: Dict[str, Dict[str, Any]] = {
    "triagem": {
        "model_name": DEFAULT_MODEL,
        "temperature": 0.3,  # Baixa - precisa seguir protocolo rigoroso de autenticação
        "top_p": 0.9,        # Relativamente focado nas respostas mais prováveis
        "max_tokens": 200,   # Respostas curtas e diretas
        "streaming": False,
        "description": "Agente de Triagem - Autenticação e roteamento inicial"
    },
    "credito": {
        "model_name": DEFAULT_MODEL,
        "temperature": 0.4,  # Moderada-baixa - balance entre protocolo e empatia
        "top_p": 0.85,       # Focado mas permite alguma criatividade na comunicação
        "max_tokens": 250,   # Respostas médias, precisa explicar decisões
        "streaming": False,
        "description": "Agente de Crédito - Consulta e solicitação de limite"
    },
    "entrevista_credito": {
        "model_name": DEFAULT_MODEL,
        "temperature": 0.7,  # Alta - precisa ser conversacional e natural
        "top_p": 0.95,       # Permite maior diversidade nas respostas
        "max_tokens": 300,   # Respostas mais longas para conduzir entrevista
        "streaming": False,
        "description": "Agente de Entrevista - Coleta de dados financeiros"
    },
    "cambio": {
        "model_name": DEFAULT_MODEL,
        "temperature": 0.2,  # Muito baixa - precisa ser factual e preciso
        "top_p": 0.8,        # Bastante focado, evita "criatividade" com números
        "max_tokens": 150,   # Respostas curtas, apenas informações necessárias
        "streaming": False,
        "description": "Agente de Câmbio - Consulta de cotações"
    }
}


def get_llm_config(agent_name: str) -> Dict[str, Any]:
    """
    Retorna configuração de LLM para um agente específico.

    Args:
        agent_name: Nome do agente ("triagem", "credito", "entrevista_credito", "cambio")

    Returns:
        Dict com configurações do LLM (temperature, top_p, max_tokens, etc.)

    Raises:
        ValueError: Se o nome do agente não for reconhecido
    """
    if agent_name not in LLM_CONFIGS:
        raise ValueError(
            f"Agente '{agent_name}' não encontrado. "
            f"Agentes disponíveis: {list(LLM_CONFIGS.keys())}"
        )

    return LLM_CONFIGS[agent_name].copy()


def get_all_configs() -> Dict[str, Dict[str, Any]]:
    """Retorna todas as configurações de LLM disponíveis."""
    return LLM_CONFIGS.copy()


# Justificativas das escolhas de parâmetros
PARAMETER_JUSTIFICATIONS = {
    "triagem": {
        "temperature": "Baixa (0.3) para garantir que o agente siga rigorosamente "
                      "o protocolo de autenticação sem desvios ou criatividade excessiva.",
        "top_p": "Alto (0.9) para manter naturalidade na comunicação mesmo com "
                 "temperatura baixa.",
        "max_tokens": "Limitado (200) pois respostas devem ser diretas: solicitar "
                     "CPF, data, confirmar autenticação."
    },
    "credito": {
        "temperature": "Moderada (0.4) para balance entre seguir regras de negócio "
                      "e demonstrar empatia ao cliente, especialmente em rejeições.",
        "top_p": "Moderado (0.85) permitindo alguma variação na forma de comunicar "
                 "decisões sensíveis.",
        "max_tokens": "Médio (250) para explicar limites, scores e motivos de "
                     "aprovação/rejeição adequadamente."
    },
    "entrevista_credito": {
        "temperature": "Alta (0.7) para conversação natural e fluida durante a "
                      "entrevista financeira, fazendo cliente se sentir confortável.",
        "top_p": "Alto (0.95) permitindo diversidade nas perguntas e respostas, "
                 "tornando conversa menos robótica.",
        "max_tokens": "Alto (300) para conduzir entrevista completa com perguntas "
                     "elaboradas e follow-ups quando necessário."
    },
    "cambio": {
        "temperature": "Muito baixa (0.2) para garantir precisão absoluta ao reportar "
                      "valores monetários e cotações.",
        "top_p": "Baixo (0.8) para evitar qualquer 'criatividade' com números ou "
                 "informações financeiras.",
        "max_tokens": "Baixo (150) pois respostas são factuais: cotação atual, "
                     "conversão de valores."
    }
}


def print_config_summary():
    """Imprime resumo das configurações de todos os agentes."""
    print("=" * 80)
    print("CONFIGURAÇÕES DE LLM - BANCO ÁGIL")
    print("=" * 80)
    print(f"\nModelo Base: {DEFAULT_MODEL}")
    print("\n")

    for agent_name, config in LLM_CONFIGS.items():
        print(f"🤖 {agent_name.upper()}")
        print(f"   Descrição: {config['description']}")
        print(f"   Temperature: {config['temperature']}")
        print(f"   Top-P: {config['top_p']}")
        print(f"   Max Tokens: {config['max_tokens']}")

        if agent_name in PARAMETER_JUSTIFICATIONS:
            justif = PARAMETER_JUSTIFICATIONS[agent_name]
            print(f"\n   Justificativas:")
            for param, reason in justif.items():
                print(f"   • {param}: {reason}")
        print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    # Quando executado diretamente, mostra resumo das configurações
    print_config_summary()
