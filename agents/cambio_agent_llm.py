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
        # Inicializa agente base sem tools (chamadas Python diretas)
        super().__init__(
            agent_name="cambio",
            tools=[],  # Sem tool calling
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

        # DETECTA PRIMEIRA ENTRADA: Se acabou de entrar vindo de outro agente
        agente_anterior = estado.get("contexto_agente", {}).get("agente_anterior")

        # Se é a primeira entrada no agente (vindo de triagem)
        # Apresenta saudação inicial e pergunta qual moeda deseja consultar
        # IMPORTANTE: agente_anterior pode ser None (primeira entrada) ou outro agente
        if agente_anterior != "cambio":

            # Marca que já entrou
            estado["contexto_agente"]["agente_anterior"] = "cambio"

            # Saudação inicial
            resposta = self.invoke(
                "Cliente entrou no serviço de câmbio. "
                "Apresente-se como especialista em câmbio e pergunte qual moeda deseja consultar. "
                "Mencione moedas comuns (USD, EUR, GBP) e explique que fornece cotações em tempo real.",
                context={}
            )

            return resposta, estado

        # Identifica moedas na mensagem (pode ser conversão entre duas moedas)
        moedas_identificadas = self._identificar_moedas(mensagem_usuario)

        # Busca cotação usando CurrencyFetcher diretamente
        from tools.currency_fetcher import CurrencyFetcher

        try:
            # Se identificou 2 moedas, é conversão entre elas
            if len(moedas_identificadas) >= 2:
                moeda_origem = moedas_identificadas[0]
                moeda_destino = moedas_identificadas[1]

                cotacao = CurrencyFetcher.get_exchange_rate(
                    from_currency=moeda_origem,
                    to_currency=moeda_destino
                )

                if cotacao is None:
                    resultado = {
                        "success": False,
                        "moeda_origem": moeda_origem,
                        "moeda_destino": moeda_destino,
                        "taxa": None,
                        "message": f"Não foi possível obter cotação de {moeda_origem} para {moeda_destino}."
                    }
                else:
                    resultado = {
                        "success": True,
                        "moeda_origem": moeda_origem,
                        "moeda_destino": moeda_destino,
                        "taxa": cotacao["rate"],
                        "message": f"Cotação {moeda_origem}/{moeda_destino}: {cotacao['rate']:.4f}",
                        "timestamp": cotacao.get("timestamp", "N/A"),
                        "exemplos": {
                            "1": cotacao["rate"],
                            "100": cotacao["rate"] * 100,
                            "1000": cotacao["rate"] * 1000
                        }
                    }
            # Se identificou 1 moeda, converte para BRL (comportamento padrão)
            elif len(moedas_identificadas) == 1:
                codigo_moeda = moedas_identificadas[0]
                taxa = CurrencyFetcher.get_rate(codigo_moeda)

                if taxa is None:
                    resultado = {
                        "success": False,
                        "moeda": codigo_moeda,
                        "taxa": None,
                        "message": f"Não foi possível obter cotação para {codigo_moeda}."
                    }
                else:
                    resultado = {
                        "success": True,
                        "moeda": codigo_moeda,
                        "moeda_destino": "BRL",
                        "taxa": taxa,
                        "message": f"Cotação {codigo_moeda}/BRL: R$ {taxa:.4f}",
                        "exemplos": {
                            "1": taxa,
                            "100": taxa * 100,
                            "1000": taxa * 1000
                        }
                    }
            else:
                # Não identificou moeda, assume USD para BRL
                taxa = CurrencyFetcher.get_rate("USD")

                if taxa is None:
                    resultado = {
                        "success": False,
                        "moeda": "USD",
                        "taxa": None,
                        "message": "Não foi possível obter cotação."
                    }
                else:
                    resultado = {
                        "success": True,
                        "moeda": "USD",
                        "moeda_destino": "BRL",
                        "taxa": taxa,
                        "message": f"Cotação USD/BRL: R$ {taxa:.4f}",
                        "exemplos": {
                            "1": taxa,
                            "100": taxa * 100,
                            "1000": taxa * 1000
                        }
                    }
        except Exception as e:
            resultado = {
                "success": False,
                "taxa": None,
                "message": f"Erro ao buscar cotação: {str(e)}"
            }

        if not resultado["success"]:
            # Erro ao buscar cotação
            resposta = self.invoke(
                f"Erro ao buscar cotação: {resultado['message']}. "
                "Informe o cliente e sugira moedas principais (USD, EUR, GBP).",
                context={}
            )
            return resposta, estado

        # Cotação obtida com sucesso
        # Verifica se é conversão entre duas moedas ou para BRL
        if "moeda_origem" in resultado and "moeda_destino" in resultado:
            # Conversão entre duas moedas (ex: USD para EUR)
            moeda_origem = resultado["moeda_origem"]
            moeda_destino = resultado["moeda_destino"]
            self.ultima_moeda_consultada = f"{moeda_origem}/{moeda_destino}"

            # Prepara contexto com dados da cotação
            context = {
                "moeda_origem": moeda_origem,
                "moeda_destino": moeda_destino,
                "taxa": resultado["taxa"],
                "exemplo_1": resultado["exemplos"]["1"],
                "exemplo_100": resultado["exemplos"]["100"],
                "exemplo_1000": resultado["exemplos"]["1000"]
            }

            # LLM formata a resposta de forma clara para conversão entre moedas
            resposta = self.invoke(
                f"Apresente a cotação de {moeda_origem} para {moeda_destino} de forma clara: "
                f"taxa {resultado['taxa']:.4f}, com exemplos de conversão para "
                "1, 100 e 1000 unidades. Use formatação com emojis 💱.",
                context=context
            )
        else:
            # Conversão para BRL (comportamento padrão)
            codigo_moeda = resultado["moeda"]
            self.ultima_moeda_consultada = codigo_moeda

            # Prepara contexto com dados da cotação
            context = {
                "moeda": codigo_moeda,
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
        resposta += "\n\nGostaria de consultar outra cotação?"

        # Guarda no estado temporário
        estado["dados_temporarios"]["ultima_cotacao"] = resultado

        return resposta, estado

    def _identificar_moedas(self, texto: str) -> list:
        """
        Identifica códigos de moedas no texto (pode ser múltiplas).

        Args:
            texto: Texto do usuário

        Returns:
            Lista de códigos de moeda identificados (ex: ["USD", "EUR"])
        """
        texto_upper = texto.upper()
        moedas_encontradas = []

        # Mapeamento de palavras para códigos
        moedas_comuns = {
            "BRL": "BRL",
            "REAL": "BRL",
            "REAIS": "BRL",
            "R$": "BRL",
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

        # Procura por todas as moedas mencionadas
        for palavra, codigo in moedas_comuns.items():
            if palavra in texto_upper and codigo not in moedas_encontradas:
                moedas_encontradas.append(codigo)

        # Tenta encontrar códigos de 3 letras diretamente
        import re
        matches = re.findall(r'\b([A-Z]{3})\b', texto_upper)
        for match in matches:
            if match not in moedas_encontradas:
                # Verifica se é um código válido de moeda (evita siglas aleatórias)
                if match in moedas_comuns.values():
                    moedas_encontradas.append(match)

        return moedas_encontradas

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
