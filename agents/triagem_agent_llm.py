"""
Agente de Triagem com LLM - Porta de entrada do atendimento.
Responsável por autenticar o cliente e direcioná-lo para o agente apropriado.

Versão refatorada usando LLM para conversação natural.
"""

from typing import Dict, Optional, Tuple
from agents.base_agent import BaseAgent
from tools.agent_tools import get_tools_for_agent
from state import EstadoConversacao, DadosCliente


class TriagemAgentLLM(BaseAgent):
    """
    Agente de Triagem com capacidades de LLM.

    Realiza autenticação conversacional e direciona clientes
    para agentes especializados de forma natural.
    """

    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Inicializa o Agente de Triagem com LLM.

        Args:
            groq_api_key: API key do Groq (opcional, usa .env se não fornecido)
        """
        # Inicializa agente base sem tools (chamadas Python diretas)
        super().__init__(
            agent_name="triagem",
            tools=[],  # Sem tool calling
            groq_api_key=groq_api_key
        )

        # Estado específico da triagem
        self.max_tentativas = 3
        self.tentativas_atuais = 0
        self.cpf_coletado: Optional[str] = None
        self.data_coletada: Optional[str] = None

    def processar_mensagem(
        self,
        mensagem_usuario: str,
        estado: EstadoConversacao
    ) -> Tuple[str, EstadoConversacao]:
        """
        Processa mensagem do usuário no contexto de triagem.

        Args:
            mensagem_usuario: Mensagem do usuário
            estado: Estado atual da conversa

        Returns:
            Tupla (resposta_agente, estado_atualizado)
        """
        # DETECTA REDIRECIONAMENTO: Se está vindo de outro agente, apenas apresenta menu
        # Isso evita processar a mensagem anterior como se fosse uma escolha de menu
        # USA FLAG DE UMA VEZ SÓ ao invés de checar agente_anterior
        voltou_ao_menu = estado.get("dados_temporarios", {}).get("voltou_ao_menu", False)
        cliente_autenticado = estado.get("cliente_autenticado")

        if voltou_ao_menu and cliente_autenticado:
            # Cliente autenticado retornou ao menu principal

            # LIMPA flag de retorno ao menu (uma vez só!)
            estado["dados_temporarios"]["voltou_ao_menu"] = False

            # IMPORTANTE: Define flag para que o node não tente identificar serviço
            estado["dados_temporarios"]["skip_identificar_servico"] = True

            # CRÍTICO: Limpa proximo_passo para evitar loop de volta à triagem
            estado["proximo_passo"] = None

            # DIFERENCIA: Crédito aprovado vs cliente recusou
            credito_aprovado = estado["dados_temporarios"].get("credito_aprovado", False)

            if credito_aprovado:
                # Limpa flag
                estado["dados_temporarios"]["credito_aprovado"] = False
                # MARCA menu reduzido (sem opção de crédito novamente)
                estado["dados_temporarios"]["menu_reduzido"] = True
                # Mensagem específica para sucesso
                resposta = self.invoke(
                    "Cliente teve seu limite de crédito APROVADO e voltou ao menu principal. "
                    "Parabenize brevemente e apresente CLARAMENTE as 3 opções disponíveis:\n"
                    "1. Score - Para fazer entrevista financeira\n"
                    "2. Câmbio - Para consultar cotações de moedas\n"
                    "3. Encerrar atendimento\n"
                    "Pergunte qual opção deseja.",
                    context={}
                )
            else:
                # Mensagem padrão para quando cliente decidiu voltar
                # Menu completo disponível
                estado["dados_temporarios"]["menu_reduzido"] = False
                resposta = self.invoke(
                    "Cliente retornou ao menu principal. "
                    "Apresente CLARAMENTE as 4 opções do menu:\n"
                    "1. Crédito - Para consultas de limite e solicitações de aumento\n"
                    "2. Score - Para fazer entrevista financeira e atualizar score\n"
                    "3. Câmbio - Para consultar cotações de moedas\n"
                    "4. Encerrar atendimento\n"
                    "Pergunte qual opção o cliente deseja.",
                    context={}
                )

            return resposta, estado

        # Prepara contexto para o LLM
        context = {
            "tentativas": self.tentativas_atuais,
            "max_tentativas": self.max_tentativas,
            "cpf_coletado": bool(self.cpf_coletado),
            "data_coletada": bool(self.data_coletada)
        }

        # Detecta se mensagem contém CPF ou data
        mensagem_limpa = mensagem_usuario.strip().replace(".", "").replace("-", "").replace("/", "")

        # Tenta extrair CPF (11 dígitos)
        if not self.cpf_coletado and mensagem_limpa.isdigit() and len(mensagem_limpa) == 11:
            self.cpf_coletado = mensagem_limpa
            resposta = self.invoke(
                "CPF coletado com sucesso. Agora solicite a data de nascimento.",
                context=context
            )
            return resposta, estado

        # Tenta extrair data (formato YYYY-MM-DD ou variações)
        if self.cpf_coletado and not self.data_coletada:
            # Tenta normalizar data
            data_normalizada = self._normalizar_data(mensagem_usuario)

            if data_normalizada:
                self.data_coletada = data_normalizada

                # CORREÇÃO: Autenticar imediatamente ao invés de esperar próxima mensagem
                # Importa DataManager diretamente ao invés do tool
                from tools.data_manager import DataManager

                # Autentica usando DataManager
                cliente = DataManager.authenticate_client(self.cpf_coletado, self.data_coletada)

                # Formata resultado no mesmo padrão do tool
                if cliente:
                    resultado = {
                        "success": True,
                        "cliente": cliente,
                        "message": f"Cliente {cliente['nome']} autenticado com sucesso!"
                    }
                else:
                    resultado = {
                        "success": False,
                        "cliente": None,
                        "message": "CPF ou data de nascimento incorretos."
                    }

                if resultado["success"]:
                    # Autenticação bem-sucedida
                    estado["cliente_autenticado"] = resultado["cliente"]
                    estado["tentativas_autenticacao"] = 0

                    # Reseta estado de triagem
                    self.cpf_coletado = None
                    self.data_coletada = None
                    self.tentativas_atuais = 0

                    # Prepara resposta com menu explícito
                    resposta = self.invoke(
                        f"Cliente autenticado com sucesso: {resultado['cliente']['nome']}. "
                        "Cumprimente o cliente pelo nome e apresente CLARAMENTE as 4 opções do menu principal:\n"
                        "1. Crédito - Para consultas de limite e solicitações de aumento\n"
                        "2. Score - Para fazer entrevista financeira e atualizar score\n"
                        "3. Câmbio - Para consultar cotações de moedas\n"
                        "4. Encerrar atendimento\n"
                        "Pergunte qual opção o cliente deseja.",
                        context=context
                    )
                    return resposta, estado

                else:
                    # Falha na autenticação
                    self.tentativas_atuais += 1
                    estado["tentativas_autenticacao"] = self.tentativas_atuais

                    # Reseta para nova tentativa
                    self.cpf_coletado = None
                    self.data_coletada = None

                    if self.tentativas_atuais >= self.max_tentativas:
                        # Esgotou tentativas
                        estado["conversa_ativa"] = False
                        resposta = self.invoke(
                            "Cliente esgotou 3 tentativas de autenticação. "
                            "Encerre educadamente.",
                            context=context
                        )
                        return resposta, estado
                    else:
                        # Permite nova tentativa
                        tentativas_restantes = self.max_tentativas - self.tentativas_atuais
                        resposta = self.invoke(
                            f"Autenticação falhou. Restam {tentativas_restantes} tentativas. "
                            "Peça os dados novamente.",
                            context=context
                        )
                        return resposta, estado

        # Caso padrão: LLM decide o que responder
        resposta = self.invoke(mensagem_usuario, context=context)
        return resposta, estado

    def _normalizar_data(self, texto: str) -> Optional[str]:
        """
        Tenta normalizar texto para formato YYYY-MM-DD.

        Args:
            texto: Texto contendo possível data

        Returns:
            Data normalizada ou None se inválido
        """
        import re

        # Remove espaços extras e aspas
        texto = texto.strip().replace('"', '').replace("'", "")

        # Padrão YYYY-MM-DD (já normalizado)
        if re.match(r'^\d{4}-\d{2}-\d{2}$', texto):
            return texto

        # Padrão DD/MM/YYYY
        match = re.search(r'(\d{2})[/-](\d{2})[/-](\d{4})', texto)
        if match:
            dia, mes, ano = match.groups()
            return f"{ano}-{mes}-{dia}"

        # Padrão DD-MM-YYYY ou DD.MM.YYYY
        match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', texto)
        if match:
            dia, mes, ano = match.groups()
            return f"{ano}-{mes}-{dia}"

        return None

    def identificar_servico(
        self,
        mensagem_usuario: str,
        menu_reduzido: bool = False
    ) -> Optional[str]:
        """
        Identifica qual serviço o cliente deseja com base na mensagem.

        Args:
            mensagem_usuario: Mensagem do usuário
            menu_reduzido: Se True, usa mapeamento do menu sem opção de crédito

        Returns:
            Nome do agente ("credito", "entrevista_credito", "cambio") ou None
        """
        mensagem_lower = mensagem_usuario.lower()
        mensagem_limpa = mensagem_usuario.strip()

        # Palavras-chave para cada serviço
        keywords = {
            "credito": ["crédito", "credito", "limite", "aumento", "empréstimo", "aumentar"],
            "entrevista_credito": ["entrevista", "score", "atualizar", "reavaliação", "avaliação"],
            "cambio": ["câmbio", "cambio", "dólar", "moeda", "cotação", "euro", "libra"]
        }

        # Verifica números (mapeamento depende do menu apresentado)
        # IMPORTANTE: Só aceita se for EXATAMENTE o número (evita detectar "1990-05-15" como "1")
        if menu_reduzido:
            # Menu reduzido (sem crédito): 1 = Score, 2 = Câmbio, 3 = Encerrar
            if mensagem_limpa == "1":
                return "entrevista_credito"
            if mensagem_limpa == "2":
                return "cambio"
            if mensagem_limpa == "3":
                return "encerramento"
        else:
            # Menu completo: 1 = Crédito, 2 = Score, 3 = Câmbio, 4 = Encerrar
            if mensagem_limpa == "1":
                return "credito"
            if mensagem_limpa == "2":
                return "entrevista_credito"
            if mensagem_limpa == "3":
                return "cambio"
            if mensagem_limpa == "4":
                return "encerramento"

        # Verifica keywords
        for servico, palavras in keywords.items():
            if any(palavra in mensagem_lower for palavra in palavras):
                return servico

        return None

    def reset(self):
        """Reseta o estado do agente."""
        super().reset_history()
        self.tentativas_atuais = 0
        self.cpf_coletado = None
        self.data_coletada = None


if __name__ == "__main__":
    # Teste básico do agente
    print("=" * 80)
    print("TESTE DO AGENTE DE TRIAGEM COM LLM")
    print("=" * 80)

    try:
        agente = TriagemAgentLLM()
        print("\n✅ Agente inicializado com sucesso!")
        print(f"\nConfiguração: {agente.get_config_summary()}")

        # Teste de saudação
        print("\n" + "-" * 80)
        print("Teste: Saudação inicial")
        print("-" * 80)

        from state import criar_estado_inicial
        estado = criar_estado_inicial()

        resposta, estado = agente.processar_mensagem("Olá!", estado)
        print(f"\nResposta do agente:\n{resposta}")

    except ValueError as e:
        print(f"\n❌ Erro: {e}")
        print("\nConfigure GROQ_API_KEY no arquivo .env para testar o agente.")

    print("\n" + "=" * 80)
