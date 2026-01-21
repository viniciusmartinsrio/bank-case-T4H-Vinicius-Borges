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
        
        Args:
            entrada_usuario: Entrada do usuário
            
        Returns:
            Resposta do sistema
        """
        self._adicionar_historico("usuario", entrada_usuario)
        
        if not self.conversa_ativa:
            return "Atendimento encerrado."
        
        # Se cliente não autenticado, processa triagem
        if not self.cliente_autenticado:
            resposta = self._processar_triagem(entrada_usuario)
        # Se cliente autenticado mas sem agente ativo, processa menu
        elif self.agente_ativo is None:
            resposta = self.processar_opcao_menu(entrada_usuario)
        # Roteia para o agente apropriado
        elif self.agente_ativo == "credito":
            resposta = self._processar_credito(entrada_usuario)
        elif self.agente_ativo == "entrevista_credito":
            resposta = self._processar_entrevista(entrada_usuario)
        elif self.agente_ativo == "cambio":
            resposta = self._processar_cambio(entrada_usuario)
        else:
            resposta = "❌ Estado inválido do sistema."
        
        self._adicionar_historico("sistema", resposta)
        return resposta

    def _processar_triagem(self, entrada: str) -> str:
        """Processa entrada na fase de triagem."""
        entrada_limpa = entrada.strip()
        
        # Verifica se é primeira vez (solicita CPF)
        if not hasattr(self, "_triagem_cpf_coletado"):
            self._triagem_cpf_coletado = False
            self._triagem_data_coletada = False
            self._triagem_cpf = None
            self._triagem_data = None
        
        # Coleta CPF
        if not self._triagem_cpf_coletado:
            self._triagem_cpf = entrada_limpa
            self._triagem_cpf_coletado = True
            return self.triagem.solicitar_data_nascimento()
        
        # Coleta data de nascimento e autentica
        if not self._triagem_data_coletada:
            self._triagem_data = entrada_limpa
            self._triagem_data_coletada = True
            
            sucesso, mensagem, cliente = self.triagem.autenticar(
                self._triagem_cpf,
                self._triagem_data
            )
            
            if sucesso:
                self.cliente_autenticado = cliente
                # Limpa flags
                self._triagem_cpf_coletado = False
                self._triagem_data_coletada = False
                self._triagem_cpf = None
                self._triagem_data = None
                
                # Próxima etapa: identificar assunto
                self.agente_ativo = None  # Sai do modo triagem
                return mensagem + "\n\n" + self.triagem.identificar_assunto()
            else:
                if self.triagem.pode_tentar_novamente():
                    # Reseta para tentar novamente
                    self._triagem_cpf_coletado = False
                    self._triagem_data_coletada = False
                    return mensagem + "\n\n" + self.triagem.solicitar_cpf()
                else:
                    # Encerra após 3 tentativas
                    self.conversa_ativa = False
                    return mensagem
        
        return "Estado inválido na triagem."

    def _processar_credito(self, entrada: str) -> str:
        """Processa entrada no agente de crédito."""
        entrada_limpa = entrada.strip().lower()
        
        # Inicializa agente se necessário
        if not self.credito.cliente:
            self.credito.definir_cliente(self.cliente_autenticado)
            return self.credito.consultar_limite()
        
        # Verifica se quer solicitar aumento
        if not self.credito.solicitacao_em_andamento:
            if entrada_limpa in ["sim", "s", "yes", "1"]:
                return self.credito.solicitar_novo_limite()
            elif entrada_limpa in ["não", "nao", "n", "no", "2"]:
                return self._oferecer_menu_principal()
            else:
                return "❌ Responda com 'sim' ou 'não'.\n\n" + self.credito.consultar_limite()
        
        # Processa a solicitação de novo limite
        sucesso, mensagem = self.credito.processar_solicitacao(entrada)
        
        if not sucesso:
            return mensagem + "\n\n" + self.credito.solicitar_novo_limite()
        
        # Verifica se foi rejeitado e oferece entrevista
        if "REJEITADA" in mensagem:
            if entrada_limpa in ["sim", "s", "yes", "1"]:
                self.agente_ativo = "entrevista_credito"
                self.entrevista.definir_cliente(self.cliente_autenticado)
                return self.entrevista.iniciar_entrevista()
            elif entrada_limpa in ["não", "nao", "n", "no", "2"]:
                return self._oferecer_menu_principal()
        
        # Se aprovado, oferece voltar ao menu
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
        """Processa a escolha de opção do menu principal."""
        agente, sucesso = self.triagem.direcionar_agente(opcao)
        
        if not sucesso:
            return "❌ Opção inválida. " + self.triagem.identificar_assunto()
        
        if agente == "encerramento":
            self.conversa_ativa = False
            return "✅ Obrigado por usar o Banco Ágil. Até logo!"
        
        # Reseta agentes anteriores
        self.credito.reset()
        self.entrevista.reset()
        self.cambio.reset()
        
        # Ativa novo agente
        self.agente_ativo = agente
        
        if agente == "credito":
            self.credito.definir_cliente(self.cliente_autenticado)
            return self.credito.consultar_limite()
        elif agente == "entrevista_credito":
            self.entrevista.definir_cliente(self.cliente_autenticado)
            return self.entrevista.iniciar_entrevista()
        elif agente == "cambio":
            self.cambio.definir_cliente(self.cliente_autenticado)
            return self.cambio.solicitar_moeda()
        
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
