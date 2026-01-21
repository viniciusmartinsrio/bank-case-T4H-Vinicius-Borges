"""
Agente de Triagem - Porta de entrada do atendimento.
Responsável por autenticar o cliente e direcioná-lo para o agente apropriado.
"""

from typing import Dict, Optional
from tools.data_manager import DataManager


class TriagemAgent:
    """Agente responsável pela triagem e autenticação de clientes."""

    def __init__(self):
        self.max_tentativas = 3
        self.tentativas_atuais = 0
        self.cliente_autenticado: Optional[Dict] = None

    def saudacao_inicial(self) -> str:
        """Retorna a saudação inicial."""
        return """
🏦 Bem-vindo ao Banco Ágil!

Sou seu assistente de atendimento. Estou aqui para ajudá-lo com:
- Consulta de limite de crédito
- Solicitação de aumento de limite
- Entrevista financeira para reajuste de score
- Consulta de cotação de moedas

Para começar, preciso autenticá-lo. Por favor, forneça seus dados.
        """

    def solicitar_cpf(self) -> str:
        """Solicita o CPF do cliente."""
        return "Por favor, informe seu CPF (11 dígitos, sem pontuação):"

    def solicitar_data_nascimento(self) -> str:
        """Solicita a data de nascimento."""
        return "Agora, informe sua data de nascimento (formato: YYYY-MM-DD, ex: 1990-05-15):"

    def autenticar(self, cpf: str, data_nascimento: str) -> tuple[bool, str, Optional[Dict]]:
        """
        Autentica o cliente.
        
        Returns:
            (sucesso, mensagem, dados_cliente)
        """
        self.tentativas_atuais += 1
        
        # Validação básica de CPF
        if not self._validar_cpf(cpf):
            mensagem = "CPF inválido. Por favor, forneça um CPF com 11 dígitos."
            return False, mensagem, None
        
        # Validação básica de data
        if not self._validar_data(data_nascimento):
            mensagem = "Data inválida. Por favor, use o formato YYYY-MM-DD."
            return False, mensagem, None
        
        # Busca cliente no banco de dados
        cliente = DataManager.authenticate_client(cpf, data_nascimento)
        
        if cliente:
            self.cliente_autenticado = cliente
            mensagem = f"✅ Autenticação bem-sucedida! Bem-vindo, {cliente['nome']}!"
            return True, mensagem, cliente
        else:
            tentativas_restantes = self.max_tentativas - self.tentativas_atuais
            
            if tentativas_restantes > 0:
                mensagem = f"❌ Dados incorretos. Tentativas restantes: {tentativas_restantes}"
                return False, mensagem, None
            else:
                mensagem = """
❌ Não foi possível autenticar após 3 tentativas.
Obrigado por usar o Banco Ágil. Encerrando atendimento.
                """
                return False, mensagem, None

    def identificar_assunto(self) -> str:
        """Solicita ao cliente que identifique o assunto da solicitação."""
        return """
Como posso ajudá-lo hoje? Escolha uma opção:
1. Consultar limite de crédito
2. Solicitar aumento de limite
3. Entrevista financeira (reajuste de score)
4. Consultar cotação de moedas
5. Encerrar atendimento

Digite o número da opção desejada:
        """

    def direcionar_agente(self, opcao: str) -> tuple[str, bool]:
        """
        Direciona para o agente apropriado.
        
        Returns:
            (nome_agente, sucesso)
        """
        opcoes = {
            "1": "credito",
            "2": "credito",
            "3": "entrevista_credito",
            "4": "cambio",
            "5": None  # Encerramento
        }
        
        agente = opcoes.get(opcao.strip())
        
        if agente is None and opcao.strip() == "5":
            return "encerramento", True
        elif agente:
            return agente, True
        else:
            return "", False

    def _validar_cpf(self, cpf: str) -> bool:
        """Valida formato básico do CPF."""
        # Remove caracteres especiais
        cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
        
        # Verifica se tem 11 dígitos
        if len(cpf_limpo) != 11:
            return False
        
        # Verifica se são todos dígitos
        if not cpf_limpo.isdigit():
            return False
        
        return True

    def _validar_data(self, data: str) -> bool:
        """Valida formato de data (YYYY-MM-DD)."""
        try:
            parts = data.strip().split("-")
            if len(parts) != 3:
                return False
            
            ano, mes, dia = parts
            
            if not (ano.isdigit() and mes.isdigit() and dia.isdigit()):
                return False
            
            ano_int = int(ano)
            mes_int = int(mes)
            dia_int = int(dia)
            
            # Validações básicas
            if not (1900 <= ano_int <= 2025):
                return False
            if not (1 <= mes_int <= 12):
                return False
            if not (1 <= dia_int <= 31):
                return False
            
            return True
        except:
            return False

    def pode_tentar_novamente(self) -> bool:
        """Verifica se ainda há tentativas disponíveis."""
        return self.tentativas_atuais < self.max_tentativas

    def reset(self):
        """Reseta o estado do agente."""
        self.tentativas_atuais = 0
        self.cliente_autenticado = None
