"""
Agente de Crédito - Consulta e solicitação de aumento de limite.
Responsável por informar limites e processar solicitações.
"""

from typing import Dict, Optional
from tools.data_manager import DataManager


class CreditoAgent:
    """Agente responsável por operações de crédito."""

    def __init__(self):
        self.cliente: Optional[Dict] = None
        self.solicitacao_em_andamento = False
        self.novo_limite_solicitado: Optional[float] = None

    def definir_cliente(self, cliente: Dict):
        """Define o cliente para operações."""
        self.cliente = cliente

    def consultar_limite(self) -> str:
        """Retorna informações do limite de crédito atual."""
        if not self.cliente:
            return "❌ Cliente não autenticado."
        
        nome = self.cliente["nome"]
        limite = self.cliente["limite_credito"]
        score = self.cliente["score_credito"]
        
        return f"""
📊 Informações de Crédito de {nome}:
- Limite Atual: R$ {limite:,.2f}
- Score de Crédito: {score:.0f}

Deseja solicitar um aumento de limite? (sim/não)
        """

    def solicitar_novo_limite(self) -> str:
        """Solicita o novo limite desejado."""
        self.solicitacao_em_andamento = True
        return "Qual é o novo limite de crédito que você deseja? (valor em reais)"

    def processar_solicitacao(self, novo_limite_str: str) -> tuple[bool, str]:
        """
        Processa a solicitação de aumento de limite.
        
        Returns:
            (sucesso, mensagem)
        """
        if not self.cliente:
            return False, "❌ Cliente não autenticado."
        
        try:
            novo_limite = float(novo_limite_str.replace("R$", "").replace(",", ".").strip())
            
            if novo_limite <= 0:
                return False, "❌ O novo limite deve ser maior que zero."
            
            if novo_limite <= self.cliente["limite_credito"]:
                return False, "❌ O novo limite deve ser maior que o limite atual."
            
            self.novo_limite_solicitado = novo_limite
            
            # Registra a solicitação
            DataManager.register_limit_request(
                cpf=self.cliente["cpf"],
                limite_atual=self.cliente["limite_credito"],
                novo_limite=novo_limite,
                status="pendente"
            )
            
            # Verifica se o score permite o novo limite
            limite_maximo = DataManager.get_limit_by_score(self.cliente["score_credito"])
            
            if limite_maximo is None:
                return False, "❌ Não foi possível validar o score."
            
            if novo_limite <= limite_maximo:
                # Aprovado
                status = "aprovado"
                mensagem = f"""
✅ Solicitação APROVADA!

Seu novo limite de crédito é: R$ {novo_limite:,.2f}

Obrigado por usar o Banco Ágil!
                """
            else:
                # Rejeitado
                status = "rejeitado"
                mensagem = f"""
❌ Solicitação REJEITADA

Seu score atual ({self.cliente['score_credito']:.0f}) permite um limite máximo de R$ {limite_maximo:,.2f}.

Você gostaria de fazer uma entrevista financeira para tentar melhorar seu score? (sim/não)
                """
            
            # Atualiza o status no arquivo
            self._atualizar_status_solicitacao(status)
            
            return True, mensagem
        
        except ValueError:
            return False, "❌ Valor inválido. Por favor, forneça um número válido."
        except Exception as e:
            return False, f"❌ Erro ao processar solicitação: {str(e)}"

    def _atualizar_status_solicitacao(self, status: str):
        """Atualiza o status da última solicitação."""
        try:
            filepath = DataManager._ensure_file_exists("solicitacoes_aumento_limite.csv")
            
            import csv
            
            # Lê todas as linhas
            rows = []
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            
            # Atualiza a última solicitação do cliente
            for row in reversed(rows):
                if row.get("cpf_cliente") == self.cliente["cpf"]:
                    row["status_pedido"] = status
                    break
            
            # Escreve de volta
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                fieldnames = [
                    "cpf_cliente",
                    "data_hora_solicitacao",
                    "limite_atual",
                    "novo_limite_solicitado",
                    "status_pedido"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")

    def oferecer_entrevista(self) -> str:
        """Oferece redirecionamento para entrevista de crédito."""
        return """
Gostaria de fazer uma entrevista financeira para tentar melhorar seu score e requalificar para um limite maior? (sim/não)
        """

    def reset(self):
        """Reseta o estado do agente."""
        self.cliente = None
        self.solicitacao_em_andamento = False
        self.novo_limite_solicitado = None
