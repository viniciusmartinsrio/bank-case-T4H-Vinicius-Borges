"""
Agente de Câmbio com LLM - Consulta de cotações de moedas.
Responsável por fornecer cotações em tempo real de forma clara e precisa.

Versão refatorada usando LLM para comunicação factual e educativa.
"""

from typing import Dict, Optional, Tuple
from agents.base_agent import BaseAgent
from tools.agent_tools import get_tools_for_agent
from state import EstadoConversacao


class CambioAgentLLM(BaseAgent):
    """
    Agente de Câmbio com capacidades de LLM.

    Fornece cotações de moedas em tempo real de forma clara,
    precisa e educativa quando necessário.
    """

    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Inicializa o Agente de Câmbio com LLM.

        Args:
            groq_api_key: API key do Groq (opcional, usa .env se não fornecido)
        """
        # Obtém ferramentas específicas para câmbio
        tools = get_tools_for_agent("cambio")

        # Inicializa agente base
        super().__init__(
            agent_name="cambio",
            tools=tools,
            groq_api_key=groq_api_key
        )

        # Estado específico do câmbio
        self.cliente: Optional[Dict] = None
        self.ultima_moeda_consultada: Optional[str] = None

    def processar_mensagem(
        self,
        mensagem_usuario: str,
        estado: EstadoConversacao
    ) -> Tuple[str, EstadoConversacao]:
        """
        Processa mensagem do usuário no contexto de câmbio.

        Args:
            mensagem_usuario: Mensagem do usuário
            estado: Estado atual da conversa

        Returns:
            Tupla (resposta_agente, estado_atualizado)
        """
        # Obtém dados do cliente do estado
        if not self.cliente and estado.get("cliente_autenticado"):
            self.cliente = estado["cliente_autenticado"]

        # Identifica código da moeda na mensagem
        codigo_moeda = self._identificar_moeda(mensagem_usuario)

        # Se não identificou moeda, assume USD (padrão)
        if not codigo_moeda:
            codigo_moeda = "USD"

        # Busca cotação usando ferramenta
        from tools.agent_tools import get_exchange_rate

        resultado = get_exchange_rate(codigo_moeda)

        if not resultado["success"]:
            # Erro ao buscar cotação
            resposta = self.invoke(
                f"Erro ao buscar cotação para {codigo_moeda}: {resultado['message']}. "
                "Informe o cliente e sugira moedas principais (USD, EUR, GBP).",
                context={}
            )
            return resposta, estado

        # Cotação obtida com sucesso
        self.ultima_moeda_consultada = codigo_moeda

        # Prepara contexto com dados da cotação
        context = {
            "moeda": resultado["moeda"],
            "taxa": resultado["taxa"],
            "exemplo_1": resultado["exemplos"]["1"],
            "exemplo_100": resultado["exemplos"]["100"],
            "exemplo_1000": resultado["exemplos"]["1000"]
        }

        # LLM formata a resposta de forma clara
        resposta = self.invoke(
            f"Apresente a cotação de {codigo_moeda} de forma clara: "
            f"taxa R$ {resultado['taxa']:.4f}, com exemplos de conversão para "
            "1, 100 e 1000 unidades. Use formatação com emojis 💱.",
            context=context
        )

        # Adiciona pergunta sobre outra consulta
        resposta += "\n\nGostaria de consultar a cotação de outra moeda?"

        # Guarda no estado temporário
        estado["dados_temporarios"]["ultima_cotacao"] = resultado

        return resposta, estado

    def _identificar_moeda(self, texto: str) -> Optional[str]:
        """
        Identifica código de moeda no texto.

        Args:
            texto: Texto do usuário

        Returns:
            Código da moeda (ex: "USD", "EUR") ou None
        """
        texto_upper = texto.upper()

        # Mapeamento de palavras para códigos
        moedas_comuns = {
            "DOLAR": "USD",
            "DÓLAR": "USD",
            "DOLLAR": "USD",
            "USD": "USD",
            "EURO": "EUR",
            "EUR": "EUR",
            "LIBRA": "GBP",
            "GBP": "GBP",
            "IENE": "JPY",
            "YUAN": "CNY",
            "YEN": "JPY",
            "JPY": "JPY",
            "PESO": "ARS",
            "ARS": "ARS",
            "CANADENSE": "CAD",
            "CAD": "CAD"
        }

        # Procura por matches
        for palavra, codigo in moedas_comuns.items():
            if palavra in texto_upper:
                return codigo

        # Tenta encontrar código de 3 letras diretamente
        import re
        match = re.search(r'\b([A-Z]{3})\b', texto_upper)
        if match:
            return match.group(1)

        return None

    def reset(self):
        """Reseta o estado do agente."""
        super().reset_history()
        self.cliente = None
        self.ultima_moeda_consultada = None


if __name__ == "__main__":
    # Teste básico do agente
    print("=" * 80)
    print("TESTE DO AGENTE DE CÂMBIO COM LLM")
    print("=" * 80)

    try:
        agente = CambioAgentLLM()
        print("\n✅ Agente inicializado com sucesso!")
        print(f"\nConfiguração: {agente.get_config_summary()}")

        # Teste de consulta
        print("\n" + "-" * 80)
        print("Teste: Consulta de cotação USD")
        print("-" * 80)

        from state import criar_estado_inicial
        estado = criar_estado_inicial()
        estado["cliente_autenticado"] = {
            "cpf": "12345678901",
            "nome": "João Silva"
        }

        agente.cliente = estado["cliente_autenticado"]

        resposta, estado = agente.processar_mensagem("Quanto está o dólar?", estado)
        print(f"\nResposta do agente:\n{resposta}")

    except ValueError as e:
        print(f"\n❌ Erro: {e}")
        print("\nConfigure GROQ_API_KEY no arquivo .env para testar o agente.")

    print("\n" + "=" * 80)
