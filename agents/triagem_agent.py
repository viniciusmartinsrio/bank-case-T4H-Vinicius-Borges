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
        """
        Retorna a saudação inicial do sistema de atendimento.

        Esta é a primeira mensagem que o cliente vê ao iniciar o atendimento.
        Apresenta os serviços disponíveis e prepara o cliente para o processo
        de autenticação.

        Returns:
            str: Mensagem de boas-vindas formatada com lista de serviços disponíveis
        """
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
        """
        Solicita o CPF do cliente para autenticação.

        O CPF deve ser fornecido com 11 dígitos numéricos. O sistema aceita
        CPF com ou sem pontuação (. e -), que será removida automaticamente
        durante a validação.

        Returns:
            str: Mensagem solicitando o CPF com formato esperado

        Examples:
            Formatos aceitos:
            - "12345678901" (sem pontuação)
            - "123.456.789-01" (com pontuação - será limpo)
        """
        return "Por favor, informe seu CPF (11 dígitos, sem pontuação):"

    def solicitar_data_nascimento(self) -> str:
        """
        Solicita a data de nascimento do cliente para autenticação.

        A data deve ser fornecida no formato ISO 8601 (YYYY-MM-DD) para
        garantir compatibilidade internacional e evitar ambiguidade.

        Returns:
            str: Mensagem solicitando a data de nascimento com formato e exemplo

        Examples:
            - "1990-05-15" (15 de maio de 1990)
            - "1985-08-22" (22 de agosto de 1985)
        """
        return "Agora, informe sua data de nascimento (formato: YYYY-MM-DD, ex: 1990-05-15):"

    def autenticar(self, cpf: str, data_nascimento: str) -> tuple[bool, str, Optional[Dict]]:
        """
        Autentica o cliente verificando CPF e data de nascimento contra a base de dados.

        O processo de autenticação inclui:
        1. Validação do formato do CPF (11 dígitos)
        2. Validação do formato da data (YYYY-MM-DD)
        3. Busca na base de dados (clientes.csv)
        4. Controle de tentativas (máximo 3)

        Args:
            cpf: CPF do cliente (11 dígitos, com ou sem pontuação)
            data_nascimento: Data de nascimento no formato YYYY-MM-DD

        Returns:
            tuple contendo:
                - bool: True se autenticado com sucesso, False caso contrário
                - str: Mensagem de sucesso ou erro para exibir ao cliente
                - Optional[Dict]: Dados do cliente se autenticado, None caso contrário
                    Estrutura do dict: {
                        'cpf': str,
                        'nome': str,
                        'limite_credito': float,
                        'score_credito': float,
                        'data_nascimento': str
                    }

        Examples:
            >>> agente = TriagemAgent()
            >>> sucesso, msg, cliente = agente.autenticar("12345678901", "1990-05-15")
            >>> if sucesso:
            ...     print(f"Bem-vindo, {cliente['nome']}")
        """
        # Incrementa contador de tentativas de autenticação
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
        """
        Apresenta menu principal de opções após autenticação bem-sucedida.

        Este é o ponto de decisão onde o cliente escolhe qual serviço deseja
        utilizar. Com base na escolha, o sistema direciona para o agente
        especializado apropriado.

        Returns:
            str: Menu formatado com 5 opções numeradas de serviços disponíveis

        Note:
            As opções 1 e 2 direcionam para o mesmo agente (CreditoAgent),
            pois consulta de limite é o primeiro passo antes de solicitar aumento.
        """
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
        Mapeia a opção escolhida pelo cliente para o agente especializado correspondente.

        Este método implementa a lógica de roteamento do sistema, determinando
        qual agente deve assumir o atendimento com base na necessidade do cliente.

        Args:
            opcao: Número da opção escolhida (string de "1" a "5")

        Returns:
            tuple contendo:
                - str: Nome do agente ("credito", "entrevista_credito", "cambio",
                       "encerramento", ou "" se opção inválida)
                - bool: True se opção válida, False se inválida

        Note:
            Opções 1 e 2 mapeiam para o mesmo agente (credito) porque a consulta
            de limite é sempre o primeiro passo antes de solicitar aumento.
        """
        # Mapeamento de opções do menu para agentes especializados
        opcoes = {
            "1": "credito",            # Consultar limite
            "2": "credito",            # Solicitar aumento (começa consultando)
            "3": "entrevista_credito", # Entrevista financeira
            "4": "cambio",             # Consultar câmbio
            "5": None                  # Encerramento do atendimento
        }
        
        agente = opcoes.get(opcao.strip())
        
        if agente is None and opcao.strip() == "5":
            return "encerramento", True
        elif agente:
            return agente, True
        else:
            return "", False

    def _validar_cpf(self, cpf: str) -> bool:
        """
        Valida o formato básico do CPF fornecido.

        Realiza validação de formato apenas, não verifica dígitos verificadores.
        Aceita CPF com ou sem pontuação, que é removida automaticamente.

        Args:
            cpf: CPF a ser validado (pode conter . e -)

        Returns:
            bool: True se formato válido (11 dígitos numéricos), False caso contrário

        Note:
            Esta é uma validação simplificada para o escopo do projeto.
            Em produção, deveria incluir validação de dígitos verificadores
            e verificação de CPFs com todos os dígitos iguais (ex: 111.111.111-11).
        """
        # Remove caracteres especiais comuns em CPF (pontos e traços)
        cpf_limpo = cpf.replace(".", "").replace("-", "").strip()

        # Verifica se tem exatamente 11 dígitos
        if len(cpf_limpo) != 11:
            return False

        # Verifica se todos os caracteres são dígitos numéricos
        if not cpf_limpo.isdigit():
            return False

        return True

    def _validar_data(self, data: str) -> bool:
        """
        Valida o formato da data de nascimento (YYYY-MM-DD).

        Verifica se a data está no formato ISO 8601 e se os valores de
        ano, mês e dia estão dentro de faixas razoáveis.

        Args:
            data: Data a ser validada no formato YYYY-MM-DD

        Returns:
            bool: True se formato e valores válidos, False caso contrário

        Note:
            Validação simplificada que não verifica:
            - Meses com 28/29/30/31 dias especificamente
            - Anos bissextos
            - Datas futuras (para data de nascimento)
            Em produção, considere usar datetime.strptime() ou biblioteca dateutil.
        """
        try:
            # Separa a data em componentes
            parts = data.strip().split("-")
            if len(parts) != 3:
                return False

            ano, mes, dia = parts

            # Verifica se todos os componentes são numéricos
            if not (ano.isdigit() and mes.isdigit() and dia.isdigit()):
                return False

            # Converte para inteiros para validação de faixas
            ano_int = int(ano)
            mes_int = int(mes)
            dia_int = int(dia)

            # Validações de faixas razoáveis
            if not (1900 <= ano_int <= 2025):  # Ano entre 1900 e 2025
                return False
            if not (1 <= mes_int <= 12):       # Mês entre 1 e 12
                return False
            if not (1 <= dia_int <= 31):       # Dia entre 1 e 31
                return False

            return True
        except:
            # Captura qualquer exceção inesperada durante validação
            return False

    def pode_tentar_novamente(self) -> bool:
        """
        Verifica se o cliente ainda pode tentar se autenticar novamente.

        O sistema permite até 3 tentativas de autenticação para evitar
        bloqueio acidental, mas também proteger contra tentativas maliciosas.

        Returns:
            bool: True se ainda há tentativas disponíveis, False se esgotadas
        """
        return self.tentativas_atuais < self.max_tentativas

    def reset(self):
        """
        Reseta o estado do agente para nova sessão de atendimento.

        Limpa todas as informações temporárias da sessão anterior,
        incluindo tentativas de autenticação e dados do cliente.
        Deve ser chamado ao iniciar novo atendimento ou após encerramento.
        """
        self.tentativas_atuais = 0
        self.cliente_autenticado = None
