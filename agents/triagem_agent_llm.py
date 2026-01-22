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
        # Obtém ferramentas específicas para triagem
        tools = get_tools_for_agent("triagem")

        # Inicializa agente base
        super().__init__(
            agent_name="triagem",
            tools=tools,
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
        # Prepara contexto para o LLM
        context = {
            "tentativas": self.tentativas_atuais,
            "max_tentativas": self.max_tentativas,
            "cpf_coletado": bool(self.cpf_coletado),
            "data_coletada": bool(self.data_coletada)
        }

        # Se já coletou ambos, tenta autenticar
        if self.cpf_coletado and self.data_coletada:
            # Usa ferramenta de autenticação
            from tools.agent_tools import authenticate_client

            resultado = authenticate_client(self.cpf_coletado, self.data_coletada)

            if resultado["success"]:
                # Autenticação bem-sucedida
                estado["cliente_autenticado"] = resultado["cliente"]
                estado["tentativas_autenticacao"] = 0

                # Reseta estado de triagem
                self.cpf_coletado = None
                self.data_coletada = None
                self.tentativas_atuais = 0

                # Prepara resposta com menu
                resposta = self.invoke(
                    f"Cliente autenticado: {resultado['cliente']['nome']}. "
                    "Agora apresente as opções de serviço disponíveis.",
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
                resposta = self.invoke(
                    "Data coletada. Autenticando...",
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

        # Remove espaços extras
        texto = texto.strip()

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

    def identificar_servico(self, mensagem_usuario: str) -> Optional[str]:
        """
        Identifica qual serviço o cliente deseja com base na mensagem.

        Args:
            mensagem_usuario: Mensagem do usuário

        Returns:
            Nome do agente ("credito", "entrevista_credito", "cambio") ou None
        """
        mensagem_lower = mensagem_usuario.lower()

        # Palavras-chave para cada serviço
        keywords = {
            "credito": ["crédito", "limite", "aumento", "empréstimo", "aumentar"],
            "entrevista_credito": ["entrevista", "score", "atualizar", "reavaliação"],
            "cambio": ["câmbio", "dólar", "moeda", "cotação", "euro", "libra"]
        }

        # Verifica números (opções do menu)
        if "1" in mensagem_usuario or "2" in mensagem_usuario:
            return "credito"
        if "3" in mensagem_usuario:
            return "entrevista_credito"
        if "4" in mensagem_usuario:
            return "cambio"
        if "5" in mensagem_usuario:
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
