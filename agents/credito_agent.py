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
        """
        Define o cliente autenticado para operações de crédito.

        Este método deve ser chamado imediatamente após o cliente ser
        autenticado pelo TriagemAgent, antes de qualquer operação de crédito.

        Args:
            cliente: Dicionário contendo dados do cliente autenticado
                Estrutura esperada: {
                    'cpf': str,
                    'nome': str,
                    'limite_credito': float,
                    'score_credito': float,
                    'data_nascimento': str
                }
        """
        self.cliente = cliente

    def consultar_limite(self) -> str:
        """
        Retorna informações detalhadas do limite de crédito atual do cliente.

        Esta é sempre a primeira interação no fluxo de crédito, exibindo
        o limite atual e o score, e perguntando se o cliente deseja solicitar
        um aumento.

        Returns:
            str: Mensagem formatada com limite, score e pergunta sobre aumento

        Note:
            Este método é o ponto de entrada para o CreditoAgent, chamado
            automaticamente quando o cliente escolhe opções 1 ou 2 do menu.
        """
        if not self.cliente:
            return "❌ Cliente não autenticado."

        # Extrai dados do cliente para exibição
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
        """
        Solicita ao cliente o valor do novo limite desejado.

        Marca o início de uma solicitação de aumento de limite.
        O valor informado será validado e processado por processar_solicitacao().

        Returns:
            str: Mensagem solicitando o novo limite desejado
        """
        # Marca que há uma solicitação em andamento para controle de fluxo
        self.solicitacao_em_andamento = True
        return "Qual é o novo limite de crédito que você deseja? (valor em reais)"

    def processar_solicitacao(self, novo_limite_str: str) -> tuple[bool, str]:
        """
        Processa e decide sobre a solicitação de aumento de limite.

        O processo inclui:
        1. Validação do valor informado
        2. Verificação se é maior que o limite atual
        3. Registro da solicitação no CSV
        4. Consulta à tabela score_limite.csv
        5. Aprovação ou rejeição automática
        6. Atualização do status no CSV

        Args:
            novo_limite_str: Valor do novo limite como string (aceita formato "R$ X,XXX.XX")

        Returns:
            tuple contendo:
                - bool: True se processado com sucesso (aprovado ou rejeitado),
                       False se houve erro de validação
                - str: Mensagem de resultado para exibir ao cliente

        Note:
            Se rejeitado, a mensagem incluirá oferta de entrevista financeira.
        """
        if not self.cliente:
            return False, "❌ Cliente não autenticado."

        try:
            # Remove formatação monetária e converte para float
            novo_limite = float(novo_limite_str.replace("R$", "").replace(",", ".").strip())
            
            # Validação: limite deve ser positivo
            if novo_limite <= 0:
                return False, "❌ O novo limite deve ser maior que zero."

            # Validação: novo limite deve ser maior que o atual
            if novo_limite <= self.cliente["limite_credito"]:
                return False, "❌ O novo limite deve ser maior que o limite atual."

            # Armazena o valor solicitado para referência
            self.novo_limite_solicitado = novo_limite

            # Registra a solicitação no CSV com status inicial "pendente"
            DataManager.register_limit_request(
                cpf=self.cliente["cpf"],
                limite_atual=self.cliente["limite_credito"],
                novo_limite=novo_limite,
                status="pendente"
            )

            # Consulta a tabela score_limite.csv para obter o limite máximo permitido
            # para o score atual do cliente
            limite_maximo = DataManager.get_limit_by_score(self.cliente["score_credito"])
            
            if limite_maximo is None:
                return False, "❌ Não foi possível validar o score."

            # Decisão automática baseada na comparação: novo_limite vs limite_maximo
            if novo_limite <= limite_maximo:
                # APROVADO: O score atual do cliente permite o novo limite
                status = "aprovado"
                mensagem = f"""
✅ Solicitação APROVADA!

Seu novo limite de crédito é: R$ {novo_limite:,.2f}

Obrigado por usar o Banco Ágil!
                """
            else:
                # REJEITADO: O score atual não permite o limite solicitado
                status = "rejeitado"
                mensagem = f"""
❌ Solicitação REJEITADA

Seu score atual ({self.cliente['score_credito']:.0f}) permite um limite máximo de R$ {limite_maximo:,.2f}.

Você gostaria de fazer uma entrevista financeira para tentar melhorar seu score? (sim/não)
                """

            # Atualiza o status da solicitação no CSV (de "pendente" para "aprovado" ou "rejeitado")
            self._atualizar_status_solicitacao(status)
            
            return True, mensagem
        
        except ValueError:
            return False, "❌ Valor inválido. Por favor, forneça um número válido."
        except Exception as e:
            return False, f"❌ Erro ao processar solicitação: {str(e)}"

    def _atualizar_status_solicitacao(self, status: str):
        """
        Atualiza o status da solicitação mais recente do cliente no CSV.

        Percorre o arquivo de solicitações de trás para frente (reversed)
        para encontrar a última solicitação do cliente atual e atualizar
        seu status de "pendente" para "aprovado" ou "rejeitado".

        Args:
            status: Novo status ("aprovado" ou "rejeitado")

        Note:
            Este é um método auxiliar interno, chamado automaticamente
            por processar_solicitacao(). Usa leitura completa do CSV,
            modificação em memória e reescrita (adequado para arquivos pequenos).
        """
        try:
            filepath = DataManager._ensure_file_exists("solicitacoes_aumento_limite.csv")

            import csv

            # Lê todas as solicitações do CSV
            rows = []
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

            # Percorre de trás para frente para encontrar a solicitação mais recente
            # do cliente atual e atualizar seu status
            for row in reversed(rows):
                if row.get("cpf_cliente") == self.cliente["cpf"]:
                    row["status_pedido"] = status
                    break  # Atualiza apenas a mais recente

            # Reescreve o arquivo CSV completo com a atualização
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
        """
        Oferece ao cliente a opção de fazer entrevista financeira.

        Este método é chamado quando uma solicitação é rejeitada devido
        a score insuficiente. A entrevista permite ao cliente fornecer
        dados financeiros atualizados para recálculo do score.

        Returns:
            str: Mensagem oferecendo entrevista financeira
        """
        return """
Gostaria de fazer uma entrevista financeira para tentar melhorar seu score e requalificar para um limite maior? (sim/não)
        """

    def reset(self):
        """
        Reseta o estado do agente para nova operação.

        Limpa todas as informações temporárias da operação anterior,
        preparando o agente para um novo atendimento ou para retornar
        ao menu principal.
        """
        self.cliente = None
        self.solicitacao_em_andamento = False
        self.novo_limite_solicitado = None
