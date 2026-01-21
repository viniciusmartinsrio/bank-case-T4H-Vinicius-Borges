"""
Fetcher de cotações de moedas usando APIs públicas.
Suporta múltiplas fontes de dados.
"""

import requests
from typing import Dict, Optional


class CurrencyFetcher:
    """Busca cotações de moedas em tempo real."""

    # API pública de câmbio (sem autenticação necessária)
    EXCHANGERATE_API_URL = "https://api.exchangerate-api.com/v4/latest"

    @staticmethod
    def get_exchange_rate(
        from_currency: str = "USD",
        to_currency: str = "BRL"
    ) -> Optional[Dict]:
        """
        Obtém a taxa de câmbio entre duas moedas.
        
        Args:
            from_currency: Moeda de origem (ex: USD)
            to_currency: Moeda de destino (ex: BRL)
            
        Returns:
            Dict com informações de câmbio ou None se erro
            {
                "from": "USD",
                "to": "BRL",
                "rate": 5.25,
                "timestamp": "2024-01-21T10:30:00Z"
            }
        """
        try:
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            # Faz requisição para a API
            response = requests.get(
                f"{CurrencyFetcher.EXCHANGERATE_API_URL}/{from_currency}",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            if to_currency not in data.get("rates", {}):
                return None
            
            rate = data["rates"][to_currency]
            
            return {
                "from": from_currency,
                "to": to_currency,
                "rate": rate,
                "timestamp": data.get("time_last_updated", "N/A"),
                "base": data.get("base", from_currency)
            }
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar cotação: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado ao buscar cotação: {e}")
            return None

    @staticmethod
    def get_supported_currencies() -> Optional[Dict[str, str]]:
        """
        Obtém lista de moedas suportadas.
        
        Returns:
            Dict com códigos e nomes de moedas
        """
        try:
            response = requests.get(
                f"{CurrencyFetcher.EXCHANGERATE_API_URL}/USD",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            rates = data.get("rates", {})
            
            # Retorna apenas os códigos de moeda
            return {code: code for code in rates.keys()}
        except Exception as e:
            print(f"Erro ao obter moedas suportadas: {e}")
            return None

    @staticmethod
    def format_exchange_info(exchange_data: Dict) -> str:
        """Formata informações de câmbio para apresentação."""
        if not exchange_data:
            return "Não foi possível obter a cotação."
        
        from_curr = exchange_data.get("from", "N/A")
        to_curr = exchange_data.get("to", "N/A")
        rate = exchange_data.get("rate", "N/A")
        
        return f"1 {from_curr} = {rate:.2f} {to_curr}"
