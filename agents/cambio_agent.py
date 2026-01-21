"""
Agente de Câmbio - Consulta de cotações de moedas.
Responsável por buscar e apresentar cotações em tempo real.
"""

from typing import Dict, Optional
from tools.currency_fetcher import CurrencyFetcher


class CambioAgent:
    """Agente responsável por operações de câmbio."""

    def __init__(self):
        self.cliente: Optional[Dict] = None
        self.ultima_consulta: Optional[Dict] = None

    def definir_cliente(self, cliente: Dict):
        """Define o cliente para operações."""
        self.cliente = cliente

    def solicitar_moeda(self) -> str:
        """Solicita qual moeda o cliente deseja consultar."""
        return """
💱 Consulta de Cotação de Moedas

Qual moeda você gostaria de consultar?
Digite o código da moeda (ex: USD, EUR, GBP, JPY, AUD, etc.)
Ou deixe em branco para consultar USD (padrão):
        """

    def consultar_cotacao(self, moeda_origem: str = "USD", moeda_destino: str = "BRL") -> str:
        """
        Consulta a cotação de uma moeda.
        
        Args:
            moeda_origem: Moeda de origem (padrão: USD)
            moeda_destino: Moeda de destino (padrão: BRL)
            
        Returns:
            Mensagem com a cotação
        """
        # Se moeda_origem vazia, usa padrão
        if not moeda_origem or moeda_origem.strip() == "":
            moeda_origem = "USD"
        
        moeda_origem = moeda_origem.strip().upper()
        moeda_destino = moeda_destino.strip().upper()
        
        # Busca cotação
        cotacao = CurrencyFetcher.get_exchange_rate(moeda_origem, moeda_destino)
        
        if not cotacao:
            return f"""
❌ Não foi possível obter a cotação de {moeda_origem} para {moeda_destino}.

Possíveis motivos:
- Moeda não suportada
- Problema de conectividade
- Serviço temporariamente indisponível

Deseja tentar outra moeda? (sim/não)
            """
        
        self.ultima_consulta = cotacao
        
        taxa = cotacao.get("rate", "N/A")
        timestamp = cotacao.get("timestamp", "N/A")
        
        return f"""
💱 Cotação Atual

{moeda_origem} → {moeda_destino}
Taxa: 1 {moeda_origem} = {taxa:.4f} {moeda_destino}

Atualizado em: {timestamp}

Exemplos de conversão:
- 100 {moeda_origem} = {100 * taxa:.2f} {moeda_destino}
- 1.000 {moeda_origem} = {1000 * taxa:.2f} {moeda_destino}

Deseja consultar outra moeda? (sim/não)
        """

    def calcular_conversao(self, valor: float, moeda_origem: str = "USD", moeda_destino: str = "BRL") -> str:
        """
        Calcula a conversão de um valor.
        
        Args:
            valor: Valor a converter
            moeda_origem: Moeda de origem
            moeda_destino: Moeda de destino
            
        Returns:
            Mensagem com o resultado da conversão
        """
        try:
            valor = float(valor)
            
            if valor < 0:
                return "❌ O valor não pode ser negativo."
            
            moeda_origem = moeda_origem.strip().upper()
            moeda_destino = moeda_destino.strip().upper()
            
            cotacao = CurrencyFetcher.get_exchange_rate(moeda_origem, moeda_destino)
            
            if not cotacao:
                return f"❌ Não foi possível obter a cotação de {moeda_origem} para {moeda_destino}."
            
            taxa = cotacao.get("rate", 0)
            valor_convertido = valor * taxa
            
            return f"""
💱 Resultado da Conversão

{valor:.2f} {moeda_origem} = {valor_convertido:.2f} {moeda_destino}

Taxa utilizada: 1 {moeda_origem} = {taxa:.4f} {moeda_destino}
            """
        except ValueError:
            return "❌ Valor inválido. Por favor, forneça um número válido."
        except Exception as e:
            return f"❌ Erro ao calcular conversão: {str(e)}"

    def encerrar_atendimento_cambio(self) -> str:
        """Encerra o atendimento de câmbio."""
        return """
✅ Obrigado por usar o serviço de câmbio do Banco Ágil!

Deseja voltar ao menu principal? (sim/não)
        """

    def reset(self):
        """Reseta o estado do agente."""
        self.cliente = None
        self.ultima_consulta = None
