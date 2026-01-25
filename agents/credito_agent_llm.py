"""
Agente de Crédito com LLM - Consulta e solicitação de aumento de limite.
Responsável por informar limites e processar solicitações.

Versão refatorada usando LLM para conversação natural e empática.
"""

from typing import Dict, Optional, Tuple
from agents.base_agent import BaseAgent
from tools.agent_tools import get_tools_for_agent
from state import EstadoConversacao


class CreditoAgentLLM(BaseAgent):
    """
    Agente de Crédito com capacidades de LLM.

    Processa consultas e solicitações de aumento de limite de crédito
    de forma conversacional e empática.
    """

    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Inicializa o Agente de Crédito com LLM.

        Args:
            groq_api_key: API key do Groq (opcional, usa .env se não fornecido)
        """
        # Inicializa agente base sem tools (chamadas Python diretas)
        super().__init__(
            agent_name="credito",
            tools=[],  # Sem tool calling
            groq_api_key=groq_api_key
        )

        # Estado específico do crédito
        self.cliente: Optional[Dict] = None
        self.solicitacao_em_andamento = False
        self.novo_limite_solicitado: Optional[float] = None
        self.limite_maximo_permitido: Optional[float] = None
        self.primeira_interacao = True  # Flag para saber se é entrada inicial

    def processar_mensagem(
        self,
        mensagem_usuario: str,
        estado: EstadoConversacao
    ) -> Tuple[str, EstadoConversacao]:
        """
        Processa mensagem do usuário no contexto de crédito.

        Args:
            mensagem_usuario: Mensagem do usuário
            estado: Estado atual da conversa

        Returns:
            Tupla (resposta_agente, estado_atualizado)
        """
        # Obtém dados do cliente do estado
        if not self.cliente and estado.get("cliente_autenticado"):
            self.cliente = estado["cliente_autenticado"]

        if not self.cliente:
            return "Erro: Cliente não autenticado.", estado

        # DETECTA PRIMEIRA INTERAÇÃO: Verifica se é entrada no agente
        # Isso acontece quando o agente anterior era diferente de "credito"
        agente_anterior = estado.get("contexto_agente", {}).get("agente_anterior")
        if agente_anterior != "credito":
            # Primeira vez entrando neste agente nesta sessão

            # Marca que estamos no crédito agora
            estado["contexto_agente"]["agente_anterior"] = "credito"

            # Apresenta saudação inicial do agente de crédito
            context = {
                "nome": self.cliente["nome"],
                "limite_atual": self.cliente["limite_credito"],
                "score": self.cliente["score_credito"],
                "valor": 0,
                "valor_solicitado": 0,
                "limite_max": 0
            }
            resposta = self.invoke(
                "Cliente entrou no serviço de crédito. "
                "Apresente-se como especialista, informe limite e score atuais. "
                "Pergunte: 'Como posso ajudar com seu crédito hoje?'",
                context=context
            )
            return resposta, estado

        # Prepara contexto com dados do cliente
        # Adiciona valores padrão para todos os placeholders do prompt
        context = {
            "nome": self.cliente["nome"],
            "limite_atual": self.cliente["limite_credito"],
            "score": self.cliente["score_credito"],
            "valor": 0,  # Placeholder padrão
            "valor_solicitado": 0,  # Placeholder padrão
            "limite_max": 0  # Placeholder padrão
        }

        # NOVO FLUXO: Só processa se já está aguardando valor
        # Evita processar automaticamente números aleatórios como "2"
        valor_detectado = None


        # Só tenta extrair valor se já está em modo de solicitação
        if self.solicitacao_em_andamento:
            valor_detectado = self._extrair_valor(mensagem_usuario)

        # Processa solicitação se tem valor E já estava aguardando
        if valor_detectado and self.solicitacao_em_andamento:
            self.solicitacao_em_andamento = True
            self.novo_limite_solicitado = valor_detectado

            # Usa DataManager diretamente ao invés do tool
            from tools.data_manager import DataManager

            # Valida que novo limite é maior que atual
            if valor_detectado <= self.cliente["limite_credito"]:
                resultado = {
                    "success": False,
                    "status": "invalido",
                    "message": "O novo limite deve ser maior que o limite atual.",
                    "limite_maximo_permitido": None
                }
            else:
                # Obtém limite máximo permitido pelo score
                limite_maximo = DataManager.get_limit_by_score(self.cliente["score_credito"])

                if limite_maximo is None:
                    resultado = {
                        "success": False,
                        "status": "erro",
                        "message": "Erro ao validar score.",
                        "limite_maximo_permitido": None
                    }
                elif valor_detectado <= limite_maximo:
                    # Aprovado
                    DataManager.register_limit_request(
                        cpf=self.cliente["cpf"],
                        limite_atual=self.cliente["limite_credito"],
                        novo_limite=valor_detectado,
                        status="aprovado"
                    )
                    resultado = {
                        "success": True,
                        "status": "aprovado",
                        "message": f"Solicitação APROVADA! Novo limite: R$ {valor_detectado:,.2f}",
                        "limite_maximo_permitido": limite_maximo,
                        "novo_limite": valor_detectado
                    }
                else:
                    # Rejeitado
                    DataManager.register_limit_request(
                        cpf=self.cliente["cpf"],
                        limite_atual=self.cliente["limite_credito"],
                        novo_limite=valor_detectado,
                        status="rejeitado"
                    )
                    resultado = {
                        "success": True,
                        "status": "rejeitado",
                        "message": (
                            f"Solicitação REJEITADA. Seu score ({self.cliente['score_credito']:.0f}) permite "
                            f"um limite máximo de R$ {limite_maximo:,.2f}."
                        ),
                        "limite_maximo_permitido": limite_maximo,
                        "novo_limite": None
                    }

            if not resultado["success"]:
                # Erro na validação
                resposta = self.invoke(
                    f"Erro ao processar: {resultado['message']}. "
                    "Explique ao cliente e peça um novo valor válido.",
                    context=context
                )
                self.solicitacao_em_andamento = False
                return resposta, estado

            # Guarda limite máximo permitido
            self.limite_maximo_permitido = resultado.get("limite_maximo_permitido")

            if resultado["status"] == "aprovado":
                # APROVADO - Atualiza contexto com valores reais
                context["valor"] = valor_detectado
                context["valor_solicitado"] = valor_detectado

                # Atualiza limite no CSV
                DataManager.update_client_limit(self.cliente["cpf"], valor_detectado)

                # Atualiza limite no estado
                estado["cliente_autenticado"]["limite_credito"] = valor_detectado

                # IMPORTANTE: Redireciona para triagem após aprovação
                estado["proximo_passo"] = "triagem"
                estado["contexto_agente"]["agente_anterior"] = "triagem"
                estado["dados_temporarios"]["credito_aprovado"] = True  # Flag para triagem saber
                estado["dados_temporarios"]["voltou_ao_menu"] = True  # Flag para evitar loop

                resposta = self.invoke(
                    f"Solicitação APROVADA para R$ {valor_detectado:,.2f}! "
                    "Parabenize o cliente de forma calorosa e informe que ele será "
                    "redirecionado ao menu principal.",
                    context=context
                )

                self.solicitacao_em_andamento = False
                return resposta, estado

            elif resultado["status"] == "rejeitado":
                # REJEITADO - Atualiza contexto com valores reais e oferece 3 opções
                context["valor_solicitado"] = valor_detectado
                context["limite_max"] = self.limite_maximo_permitido

                resposta = self.invoke(
                    f"Solicitação REJEITADA. Limite máximo permitido para score "
                    f"{self.cliente['score_credito']:.0f} é R$ {self.limite_maximo_permitido:,.2f}. "
                    "Seja empático e ofereça 3 opções: "
                    "1) Fazer entrevista para melhorar score, "
                    f"2) Aceitar limite máximo atual de R$ {self.limite_maximo_permitido:,.2f}, "
                    "3) Não aceitar nenhuma opção (volta ao menu principal).",
                    context=context
                )

                # Marca que pode redirecionar para entrevista OU aceitar limite máximo
                estado["dados_temporarios"]["pode_fazer_entrevista"] = True
                estado["dados_temporarios"]["limite_maximo_disponivel"] = self.limite_maximo_permitido

                self.solicitacao_em_andamento = False
                return resposta, estado

        # Detecta se cliente escolhe uma das 3 opções após rejeição
        if estado["dados_temporarios"].get("pode_fazer_entrevista"):
            mensagem_lower = mensagem_usuario.lower()

            # IMPORTANTE: Checar "não" ANTES de "sim" para evitar falsos positivos
            # "não quero" contém "quero", mas deve ser tratado como "não"

            # Opção 3: Cliente recusa tudo
            # Detecta "3", "opção 3", "não", "nao", "recuso", "voltar", "menu"
            mensagem_stripped = mensagem_usuario.strip()
            eh_opcao_3 = (mensagem_stripped == "3" or
                         "opção 3" in mensagem_lower or
                         "opcao 3" in mensagem_lower)
            eh_recusa = any(palavra in mensagem_lower for palavra in
                          ["não", "nao", "recuso", "não quero", "nao quero", "voltar", "menu"])

            if eh_opcao_3 or eh_recusa:
                # Cliente recusa - volta para triagem
                estado["dados_temporarios"]["pode_fazer_entrevista"] = False
                estado["dados_temporarios"]["limite_maximo_disponivel"] = None
                estado["proximo_passo"] = "triagem"
                # Atualiza contexto do agente para resetar ao voltar
                estado["contexto_agente"]["agente_anterior"] = "triagem"
                estado["dados_temporarios"]["voltou_ao_menu"] = True  # Flag para evitar loop
                resposta = self.invoke(
                    "Cliente recusou as opções. Agradeça e informe que ele será "
                    "redirecionado ao menu principal.",
                    context=context
                )
                return resposta, estado

            # Opção 2: Cliente aceita limite máximo atual
            eh_opcao_2 = (mensagem_stripped == "2" or
                         "opção 2" in mensagem_lower or
                         "opcao 2" in mensagem_lower)
            eh_aceitar_limite = any(palavra in mensagem_lower for palavra in
                                   ["aceitar limite", "limite máximo", "limite maximo"])

            if eh_opcao_2 or eh_aceitar_limite:
                limite_maximo = estado["dados_temporarios"].get("limite_maximo_disponivel")
                if limite_maximo:
                    # Aprova com limite máximo
                    from tools.data_manager import DataManager
                    DataManager.register_limit_request(
                        cpf=self.cliente["cpf"],
                        limite_atual=self.cliente["limite_credito"],
                        novo_limite=limite_maximo,
                        status="aprovado"
                    )

                    # Atualiza limite no CSV
                    DataManager.update_client_limit(self.cliente["cpf"], limite_maximo)

                    # Atualiza limite no estado
                    estado["cliente_autenticado"]["limite_credito"] = limite_maximo
                    estado["dados_temporarios"]["pode_fazer_entrevista"] = False
                    estado["dados_temporarios"]["limite_maximo_disponivel"] = None

                    # IMPORTANTE: Redireciona para triagem após aprovação
                    estado["proximo_passo"] = "triagem"
                    estado["contexto_agente"]["agente_anterior"] = "triagem"
                    estado["dados_temporarios"]["credito_aprovado"] = True  # Flag para triagem saber
                    estado["dados_temporarios"]["voltou_ao_menu"] = True  # Flag para evitar loop
    
                    context["valor"] = limite_maximo
                    resposta = self.invoke(
                        f"Cliente aceitou o limite máximo de R$ {limite_maximo:,.2f}. "
                        "APROVE a solicitação, parabenize o cliente e informe que ele será "
                        "redirecionado ao menu principal.",
                        context=context
                    )
                    return resposta, estado

            # Opção 1: Cliente aceita fazer entrevista
            eh_opcao_1 = (mensagem_stripped == "1" or
                         "opção 1" in mensagem_lower or
                         "opcao 1" in mensagem_lower)
            eh_aceitar_entrevista = any(palavra in mensagem_lower for palavra in
                                       ["sim", "aceito", "entrevista", "quero entrevista", "melhorar score"])

            if eh_opcao_1 or eh_aceitar_entrevista:
                # Cliente aceita entrevista
                estado["dados_temporarios"]["pode_fazer_entrevista"] = False
                estado["dados_temporarios"]["limite_maximo_disponivel"] = None
                estado["proximo_passo"] = "entrevista_credito"
                resposta = self.invoke(
                    "Cliente aceitou fazer entrevista. Informe que ele será "
                    "redirecionado para o especialista em análise financeira.",
                    context=context
                )
                return resposta, estado

        # Detecta se usuário quer INICIAR solicitação de aumento
        mensagem_lower = mensagem_usuario.lower()
        palavras_solicitar = ["solicitar", "aumento", "aumentar", "quero mais", "preciso mais", "elevar"]

        if not self.solicitacao_em_andamento and any(palavra in mensagem_lower for palavra in palavras_solicitar):
            # Ativa modo solicitação
            self.solicitacao_em_andamento = True
            resposta = self.invoke(
                "Cliente deseja solicitar aumento de limite. "
                "Pergunte qual é o novo valor de limite desejado. "
                "Informe o limite atual e peça o valor específico.",
                context=context
            )
            return resposta, estado

        # NOVO: Detecta se usuário informou um valor grande (provável limite desejado)
        # Isso cobre casos onde o usuário pula direto para o valor sem usar keywords
        if not self.solicitacao_em_andamento:
            valor_direto = self._extrair_valor(mensagem_usuario)
            if valor_direto and valor_direto > 1000:  # Valores acima de R$ 1000 são prováveis limites
                self.solicitacao_em_andamento = True
                # Reprocessa a mensagem agora com modo ativado - volta pro início
                return self.processar_mensagem(mensagem_usuario, estado)

        # Caso padrão: LLM decide o que responder
        resposta = self.invoke(mensagem_usuario, context=context)
        return resposta, estado

    def _extrair_valor(self, texto: str) -> Optional[float]:
        """
        Extrai valor monetário de um texto de forma rigorosa.

        Só aceita valores que pareçam ser limites de crédito realistas.

        Args:
            texto: Texto contendo possível valor

        Returns:
            Valor em float ou None se não encontrado
        """
        import re

        # Remove espaços extras
        texto = texto.strip()

        # IMPORTANTE: Ignora textos muito curtos (como "2", "10")
        # que provavelmente são opções de menu, não valores monetários
        if len(texto) <= 2:
            return None

        # Remove símbolos monetários e formatação
        texto_limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()

        # Busca por números (inteiros ou decimais) com pelo menos 3 dígitos
        # Isso evita pegar números como "2" ou "10"
        match = re.search(r'\b\d{3,}(?:\.\d+)?\b', texto_limpo)

        if match:
            try:
                valor = float(match.group())
                # Valida que é um valor razoável para limite de crédito
                # Mínimo R$ 1.000, máximo R$ 1.000.000
                if 1000 <= valor <= 1000000:
                    return valor
            except ValueError:
                pass

        return None

    def reset(self):
        """Reseta o estado do agente."""
        super().reset_history()
        self.cliente = None
        self.solicitacao_em_andamento = False
        self.novo_limite_solicitado = None
        self.limite_maximo_permitido = None
        self.primeira_interacao = True  # Reset da flag


if __name__ == "__main__":
    # Teste básico do agente
    print("=" * 80)
    print("TESTE DO AGENTE DE CRÉDITO COM LLM")
    print("=" * 80)

    try:
        agente = CreditoAgentLLM()
        print("\n✅ Agente inicializado com sucesso!")
        print(f"\nConfiguração: {agente.get_config_summary()}")

        # Simula cliente autenticado
        from state import criar_estado_inicial
        estado = criar_estado_inicial()
        estado["cliente_autenticado"] = {
            "cpf": "12345678901",
            "nome": "João Silva",
            "limite_credito": 5000.00,
            "score_credito": 750
        }

        agente.cliente = estado["cliente_autenticado"]

        print("\n" + "-" * 80)
        print("Teste: Consulta de limite")
        print("-" * 80)

        resposta, estado = agente.processar_mensagem(
            "Gostaria de saber meu limite",
            estado
        )
        print(f"\nResposta do agente:\n{resposta}")

    except ValueError as e:
        print(f"\n❌ Erro: {e}")
        print("\nConfigure GROQ_API_KEY no arquivo .env para testar o agente.")

    print("\n" + "=" * 80)
