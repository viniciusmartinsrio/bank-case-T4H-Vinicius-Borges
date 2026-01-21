"""
Sistema de Agentes Bancários - Banco Ágil
Orquestrador central que gerencia os agentes e fluxos de atendimento.
"""

from typing import Dict, Optional, Tuple
from agents import (
    TriagemAgent,
    CreditoAgent,
    EntrevistaCreditoAgent,
    CambioAgent
)


class BancoAgilSystem:
    """Sistema central de atendimento com múltiplos agentes."""

    def __init__(self):
        # Instancia todos os agentes
        self.triagem = TriagemAgent()
        self.credito = CreditoAgent()
        self.entrevista = EntrevistaCreditoAgent()
        self.cambio = CambioAgent()
        
        # Estado da conversa
        self.cliente_autenticado: Optional[Dict] = None
        self.agente_ativo: Optional[str] = None
        self.conversa_ativa = True
        self.historico_mensagens: list = []

    def iniciar_atendimento(self) -> str:
        """Inicia o atendimento com saudação e triagem."""
        self.agente_ativo = "triagem"
        mensagem = self.triagem.saudacao_inicial()
        self._adicionar_historico("sistema", mensagem)
        return mensagem

    def processar_entrada(self, entrada_usuario: str) -> str:
        """
        Processa a entrada do usuário e retorna a resposta apropriada.

        Este é o método central de roteamento do sistema. Baseado no estado
        atual (cliente autenticado, agente ativo), direciona a entrada para
        o agente apropriado.

        Fluxo de decisão:
        1. Cliente não autenticado → TriagemAgent
        2. Cliente autenticado, sem agente → Menu principal
        3. Agente ativo específico → Roteia para o agente

        Args:
            entrada_usuario: Entrada do usuário (texto livre)

        Returns:
            str: Resposta do sistema após processamento
        """
        # Registra a entrada do usuário no histórico
        self._adicionar_historico("usuario", entrada_usuario)

        # Verifica se a conversa ainda está ativa (pode ter sido encerrada)
        if not self.conversa_ativa:
            return "Atendimento encerrado."

        # ROTEAMENTO BASEADO EM ESTADO:

        # Caso 1: Cliente ainda não autenticado → processo de autenticação
        if not self.cliente_autenticado:
            resposta = self._processar_triagem(entrada_usuario)

        # Caso 2: Cliente autenticado mas escolhendo serviço → menu principal
        elif self.agente_ativo is None:
            resposta = self.processar_opcao_menu(entrada_usuario)

        # Caso 3: Agente de Crédito ativo → operações de limite
        elif self.agente_ativo == "credito":
            resposta = self._processar_credito(entrada_usuario)

        # Caso 4: Agente de Entrevista ativo → coleta de dados financeiros
        elif self.agente_ativo == "entrevista_credito":
            resposta = self._processar_entrevista(entrada_usuario)

        # Caso 5: Agente de Câmbio ativo → consultas de cotação
        elif self.agente_ativo == "cambio":
            resposta = self._processar_cambio(entrada_usuario)

        # Caso inesperado: estado inválido (não deveria acontecer)
        else:
            resposta = "❌ Estado inválido do sistema."

        # Registra a resposta do sistema no histórico
        self._adicionar_historico("sistema", resposta)
        return resposta

    def _processar_triagem(self, entrada: str) -> str:
        """
        Processa entrada durante a fase de triagem/autenticação.

        A triagem é um processo de 2 etapas:
        1. Coleta do CPF
        2. Coleta da data de nascimento e autenticação

        Mantém estado usando atributos temporários prefixados com _triagem_
        para controlar qual etapa está sendo executada.
        """
        entrada_limpa = entrada.strip()

        # Inicializa flags de controle na primeira execução
        # Estes atributos controlam o estado da coleta de dados
        if not hasattr(self, "_triagem_cpf_coletado"):
            self._triagem_cpf_coletado = False
            self._triagem_data_coletada = False
            self._triagem_cpf = None
            self._triagem_data = None

        # ETAPA 1: Coleta do CPF
        if not self._triagem_cpf_coletado:
            self._triagem_cpf = entrada_limpa  # Armazena CPF temporariamente
            self._triagem_cpf_coletado = True   # Marca CPF como coletado
            return self.triagem.solicitar_data_nascimento()  # Pede próximo dado

        # ETAPA 2: Coleta da data de nascimento e tentativa de autenticação
        if not self._triagem_data_coletada:
            self._triagem_data = entrada_limpa  # Armazena data temporariamente
            self._triagem_data_coletada = True  # Marca data como coletada

            # Tenta autenticar com CPF e data fornecidos
            sucesso, mensagem, cliente = self.triagem.autenticar(
                self._triagem_cpf,
                self._triagem_data
            )

            if sucesso:
                # AUTENTICAÇÃO BEM-SUCEDIDA
                self.cliente_autenticado = cliente  # Armazena dados do cliente

                # Limpa flags temporárias (não serão mais necessárias)
                self._triagem_cpf_coletado = False
                self._triagem_data_coletada = False
                self._triagem_cpf = None
                self._triagem_data = None

                # Sai do modo triagem e exibe menu principal
                self.agente_ativo = None  # None = modo menu
                return mensagem + "\n\n" + self.triagem.identificar_assunto()
            else:
                # AUTENTICAÇÃO FALHOU
                if self.triagem.pode_tentar_novamente():
                    # Ainda há tentativas disponíveis, permite tentar novamente
                    self._triagem_cpf_coletado = False
                    self._triagem_data_coletada = False
                    return mensagem + "\n\n" + self.triagem.solicitar_cpf()
                else:
                    # Tentativas esgotadas (3 falhas), encerra atendimento
                    self.conversa_ativa = False
                    return mensagem

        return "Estado inválido na triagem."

    def _processar_credito(self, entrada: str) -> str:
        """
        Processa entrada quando o CreditoAgent está ativo.

        Fluxo do CreditoAgent:
        1. Exibe limite atual e pergunta se quer solicitar aumento
        2. Se sim: coleta novo limite e processa solicitação
        3. Se aprovado: volta ao menu
        4. Se rejeitado: oferece entrevista financeira
        """
        entrada_limpa = entrada.strip().lower()

        # Primeira interação com o agente: define cliente e consulta limite
        if not self.credito.cliente:
            self.credito.definir_cliente(self.cliente_autenticado)
            return self.credito.consultar_limite()

        # FASE 1: Pergunta se quer solicitar aumento
        if not self.credito.solicitacao_em_andamento:
            # Cliente quer solicitar aumento
            if entrada_limpa in ["sim", "s", "yes", "1"]:
                return self.credito.solicitar_novo_limite()
            # Cliente não quer, volta ao menu
            elif entrada_limpa in ["não", "nao", "n", "no", "2"]:
                return self._oferecer_menu_principal()
            # Resposta inválida, repete a pergunta
            else:
                return "❌ Responda com 'sim' ou 'não'.\n\n" + self.credito.consultar_limite()

        # FASE 2: Processa o valor do novo limite solicitado
        sucesso, mensagem = self.credito.processar_solicitacao(entrada)

        # Validação falhou (valor inválido, não numérico, etc.)
        if not sucesso:
            return mensagem + "\n\n" + self.credito.solicitar_novo_limite()

        # FASE 3: Trata resultado da solicitação

        # Caso REJEITADO: Oferece entrevista para melhorar score
        if "REJEITADA" in mensagem:
            # Cliente aceita fazer entrevista
            if entrada_limpa in ["sim", "s", "yes", "1"]:
                self.agente_ativo = "entrevista_credito"  # Troca de agente
                self.entrevista.definir_cliente(self.cliente_autenticado)
                return self.entrevista.iniciar_entrevista()
            # Cliente recusa entrevista, volta ao menu
            elif entrada_limpa in ["não", "nao", "n", "no", "2"]:
                return self._oferecer_menu_principal()

        # Caso APROVADO: Volta ao menu principal
        return mensagem + "\n\n" + self._oferecer_menu_principal()

    def _processar_entrevista(self, entrada: str) -> str:
        """Processa entrada no agente de entrevista de crédito."""
        entrada_limpa = entrada.strip()
        
        # Inicializa agente se necessário
        if not self.entrevista.cliente:
            self.entrevista.definir_cliente(self.cliente_autenticado)
            return self.entrevista.iniciar_entrevista()
        
        # Processa resposta
        sucesso, mensagem = self.entrevista.processar_resposta(entrada_limpa)
        
        if not sucesso:
            return mensagem
        
        # Se entrevista completa, redireciona para crédito
        if self.entrevista.entrevista_completa():
            self.agente_ativo = "credito"
            self.credito.cliente = self.cliente_autenticado
            # Reseta para nova análise
            self.credito.solicitacao_em_andamento = False
            return mensagem + "\n\n" + self.credito.consultar_limite()
        
        return mensagem

    def _processar_cambio(self, entrada: str) -> str:
        """Processa entrada no agente de câmbio."""
        entrada_limpa = entrada.strip().lower()
        
        # Inicializa agente se necessário
        if not self.cambio.cliente:
            self.cambio.definir_cliente(self.cliente_autenticado)
            return self.cambio.solicitar_moeda()
        
        # Se não há consulta em andamento, solicita moeda
        if not hasattr(self, "_cambio_moeda_solicitada"):
            self._cambio_moeda_solicitada = True
            moeda = entrada_limpa if entrada_limpa else "usd"
            return self.cambio.consultar_cotacao(moeda)
        
        # Verifica se quer consultar outra moeda
        if entrada_limpa in ["sim", "s", "yes", "1"]:
            self._cambio_moeda_solicitada = False
            return self.cambio.solicitar_moeda()
        elif entrada_limpa in ["não", "nao", "n", "no", "2"]:
            del self._cambio_moeda_solicitada
            return self._oferecer_menu_principal()
        else:
            return "❌ Responda com 'sim' ou 'não'.\n\n" + self.cambio.encerrar_atendimento_cambio()

    def _oferecer_menu_principal(self) -> str:
        """Oferece o menu principal novamente."""
        return self.triagem.identificar_assunto()

    def processar_opcao_menu(self, opcao: str) -> str:
        """
        Processa a escolha do cliente no menu principal.

        Mapeia a opção escolhida (1-5) para o agente correspondente e
        inicializa o agente selecionado. Reseta todos os outros agentes
        para garantir estado limpo.

        Args:
            opcao: Número da opção escolhida pelo cliente (string "1" a "5")

        Returns:
            str: Resposta do agente selecionado ou mensagem de erro
        """
        # Delega ao TriagemAgent para mapear opção → nome do agente
        agente, sucesso = self.triagem.direcionar_agente(opcao)

        # Opção inválida (não é 1-5)
        if not sucesso:
            return "❌ Opção inválida. " + self.triagem.identificar_assunto()

        # Opção 5: Encerrar atendimento
        if agente == "encerramento":
            self.conversa_ativa = False
            return "✅ Obrigado por usar o Banco Ágil. Até logo!"

        # Reseta todos os agentes para garantir estado limpo
        # (importante quando cliente volta ao menu após usar um agente)
        self.credito.reset()
        self.entrevista.reset()
        self.cambio.reset()

        # Define qual agente está ativo agora
        self.agente_ativo = agente

        # Inicializa o agente selecionado e retorna primeira mensagem

        if agente == "credito":
            # Opções 1 ou 2: Consultar/Solicitar limite
            self.credito.definir_cliente(self.cliente_autenticado)
            return self.credito.consultar_limite()

        elif agente == "entrevista_credito":
            # Opção 3: Entrevista financeira direta
            self.entrevista.definir_cliente(self.cliente_autenticado)
            return self.entrevista.iniciar_entrevista()

        elif agente == "cambio":
            # Opção 4: Consultar cotação de moedas
            self.cambio.definir_cliente(self.cliente_autenticado)
            return self.cambio.solicitar_moeda()

        # Estado inesperado (não deveria acontecer)
        return "❌ Erro ao direcionar para agente."

    def _adicionar_historico(self, remetente: str, mensagem: str):
        """Adiciona mensagem ao histórico."""
        self.historico_mensagens.append({
            "remetente": remetente,
            "mensagem": mensagem
        })

    def obter_historico(self) -> list:
        """Retorna o histórico de mensagens."""
        return self.historico_mensagens

    def encerrar_atendimento(self):
        """Encerra o atendimento."""
        self.conversa_ativa = False
        self.triagem.reset()
        self.credito.reset()
        self.entrevista.reset()
        self.cambio.reset()
        self.cliente_autenticado = None
        self.agente_ativo = None
