"""
Interface Streamlit MELHORADA para o Sistema de Agentes Bancários com LLM - Banco Ágil
Versão com UX/UI aprimorada: loading feedback, quick replies, validação, etc.
"""

import streamlit as st
import re
import time
from datetime import datetime
from typing import Optional
from banco_agil_langgraph import BancoAgilLangGraph
from groq import RateLimitError


# ==================== FUNÇÕES DE VALIDAÇÃO ====================

def validar_cpf(cpf: str) -> bool:
    """Valida formato de CPF (11 dígitos)."""
    cpf_limpo = re.sub(r'\D', '', cpf)
    return len(cpf_limpo) == 11 and cpf_limpo.isdigit()


def validar_data(data: str) -> bool:
    """Valida formato de data (aceita DD/MM/YYYY, YYYY-MM-DD, etc.)."""
    padroes = [
        r'\d{2}/\d{2}/\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}-\d{2}-\d{4}'
    ]
    return any(re.match(p, data) for p in padroes)


def validar_valor_monetario(valor: str) -> Optional[float]:
    """Valida e extrai valor monetário."""
    try:
        valor_limpo = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        valor_float = float(valor_limpo)
        return valor_float if 100 <= valor_float <= 100000 else None
    except:
        return None


# ==================== CONFIGURAÇÃO DA PÁGINA ====================

def configurar_pagina():
    """Configura página do Streamlit."""
    st.set_page_config(
        page_title="Banco Ágil - Atendimento Inteligente com LLM",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )


# ==================== INICIALIZAÇÃO DO ESTADO ====================

def initialize_session_state():
    """Inicializa o estado da sessão Streamlit."""
    if "sistema" not in st.session_state:
        try:
            st.session_state.sistema = BancoAgilLangGraph()
            st.session_state.conversa_iniciada = False
            st.session_state.mensagens = []
            st.session_state.erro_inicializacao = None
            st.session_state.aguardando_confirmacao = None
            st.session_state.ultima_acao = None
        except ValueError as e:
            st.session_state.sistema = None
            st.session_state.erro_inicializacao = str(e)


# ==================== PROCESSAMENTO DE MENSAGENS ====================

def processar_mensagem_com_feedback(mensagem: str, mostrar_validacao: bool = True):
    """
    Processa mensagem com feedback visual e tratamento de erros.

    Args:
        mensagem: Mensagem do usuário
        mostrar_validacao: Se deve mostrar validação de input
    """
    estado = st.session_state.sistema.get_estado()
    agente_ativo = estado.get("agente_ativo", "triagem")

    # Validação de input contextual
    if mostrar_validacao and agente_ativo == "triagem":
        if not estado.get("cliente_autenticado"):
            # Pode ser CPF ou data
            if mensagem.replace('-', '').replace('.', '').isdigit():
                if len(re.sub(r'\D', '', mensagem)) == 11:
                    if not validar_cpf(mensagem):
                        st.error("❌ CPF inválido. Digite 11 dígitos válidos.")
                        return
                elif validar_data(mensagem):
                    pass  # Data válida
                else:
                    st.warning("⚠️ Formato não reconhecido. Digite um CPF ou data válida.")

    # Adiciona mensagem do usuário
    st.session_state.mensagens.append({
        "remetente": "Você",
        "mensagem": mensagem,
        "timestamp": datetime.now(),
        "agente": "user"
    })

    # Processa com feedback visual
    try:
        with st.spinner("🤖 Processando sua solicitação..."):
            resposta = st.session_state.sistema.processar_mensagem(mensagem)

        # Adiciona resposta do assistente
        estado_atualizado = st.session_state.sistema.get_estado()
        agente_atual = estado_atualizado.get("agente_ativo", "sistema")

        st.session_state.mensagens.append({
            "remetente": "Assistente",
            "mensagem": resposta,
            "timestamp": datetime.now(),
            "agente": agente_atual
        })

        # Animação de transição se mudou de agente
        if agente_atual != agente_ativo:
            st.success(f"🔄 Redirecionado para {agente_atual.replace('_', ' ').title()}")
            time.sleep(0.3)

        st.rerun()

    except RateLimitError as e:
        # Extrai tempo de espera do erro
        erro_msg = str(e)
        tempo_espera = "alguns minutos"

        # Tenta extrair tempo exato (ex: "13m18.336s")
        match = re.search(r'try again in (\d+[mhs\d.]+)', erro_msg)
        if match:
            tempo_espera = match.group(1)

        st.error(f"""
        🚫 **Limite de Tokens Atingido (Groq Free Tier)**

        Você atingiu o limite diário de 100.000 tokens do plano gratuito do Groq.

        ⏳ **Tempo de espera:** {tempo_espera}

        💡 **O que fazer:**
        - Aguarde o tempo indicado acima
        - Ou faça upgrade para o plano pago do Groq: https://console.groq.com/settings/billing
        - Ou use um modelo menor (modifique `llm_config.py` para usar `llama-3.1-8b-instant`)

        **Dica:** O limite reseta às 00:00 UTC (21:00 horário de Brasília).
        """)

        # Remove última mensagem do usuário para poder reenviar
        if st.session_state.mensagens and st.session_state.mensagens[-1]["remetente"] == "Você":
            st.session_state.mensagens.pop()

        # Adiciona informação no histórico
        st.session_state.mensagens.append({
            "remetente": "Sistema",
            "mensagem": f"⚠️ Limite de rate atingido. Aguarde {tempo_espera} ou reinicie amanhã.",
            "timestamp": datetime.now(),
            "agente": "sistema"
        })

    except ConnectionError:
        st.error("""
        🌐 **Erro de Conexão**

        Não conseguimos conectar ao servidor. Verifique sua internet e tente novamente.
        """)

    except Exception as e:
        st.error(f"""
        ❌ **Ops, algo deu errado!**

        Tente novamente ou reinicie a conversa.

        *Erro técnico: {type(e).__name__}*
        """)


# ==================== QUICK REPLIES ====================

def mostrar_quick_replies():
    """Mostra botões de resposta rápida baseados no contexto."""
    estado = st.session_state.sistema.get_estado()
    agente_ativo = estado.get("agente_ativo", "triagem")
    cliente_autenticado = estado.get("cliente_autenticado")

    # Menu principal após autenticação
    if agente_ativo == "triagem" and cliente_autenticado:
        st.markdown("### 🎯 Escolha um serviço:")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("💳 Crédito", use_container_width=True):
                processar_mensagem_com_feedback("Quero consultar meu crédito", mostrar_validacao=False)

        with col2:
            if st.button("💱 Câmbio", use_container_width=True):
                processar_mensagem_com_feedback("Consultar cotações de moedas", mostrar_validacao=False)

        with col3:
            if st.button("📋 Entrevista", use_container_width=True):
                processar_mensagem_com_feedback("Fazer entrevista financeira", mostrar_validacao=False)

        with col4:
            if st.button("👋 Encerrar", use_container_width=True, type="secondary"):
                st.session_state.aguardando_confirmacao = "encerrar"
                st.rerun()

    # Respostas Sim/Não
    elif agente_ativo == "credito":
        dados_temp = estado.get("dados_temporarios", {})
        if dados_temp.get("pode_fazer_entrevista"):
            st.markdown("### 💬 Deseja fazer a entrevista financeira?")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Sim, aceito", use_container_width=True):
                    processar_mensagem_com_feedback("Sim, aceito fazer a entrevista", mostrar_validacao=False)

            with col2:
                if st.button("❌ Não, obrigado", use_container_width=True):
                    processar_mensagem_com_feedback("Não quero fazer entrevista", mostrar_validacao=False)

    # Entrevista - respostas comuns
    elif agente_ativo == "entrevista_credito":
        # Verifica qual pergunta está sendo feita
        if st.session_state.mensagens:
            ultima_msg = st.session_state.mensagens[-1]["mensagem"].lower()

            # Pergunta sobre tipo de emprego
            if "emprego" in ultima_msg or "trabalho" in ultima_msg:
                st.markdown("### 💼 Tipo de emprego:")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("👔 CLT / Formal", use_container_width=True):
                        processar_mensagem_com_feedback("CLT formal", mostrar_validacao=False)

                with col2:
                    if st.button("💼 Autônomo / MEI", use_container_width=True):
                        processar_mensagem_com_feedback("Autônomo", mostrar_validacao=False)

                with col3:
                    if st.button("❌ Desempregado", use_container_width=True):
                        processar_mensagem_com_feedback("Desempregado", mostrar_validacao=False)

            # Pergunta sobre dívidas
            elif "dívida" in ultima_msg or "divida" in ultima_msg:
                st.markdown("### 💳 Possui dívidas ativas?")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Sim", use_container_width=True):
                        processar_mensagem_com_feedback("Sim, tenho dívidas", mostrar_validacao=False)

                with col2:
                    if st.button("❌ Não", use_container_width=True):
                        processar_mensagem_com_feedback("Não tenho dívidas", mostrar_validacao=False)

    # Câmbio - moedas comuns
    elif agente_ativo == "cambio":
        st.markdown("### 💱 Consultar cotação:")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🇺🇸 Dólar (USD)", use_container_width=True):
                processar_mensagem_com_feedback("Quanto está o dólar?", mostrar_validacao=False)

        with col2:
            if st.button("🇪🇺 Euro (EUR)", use_container_width=True):
                processar_mensagem_com_feedback("Quanto está o euro?", mostrar_validacao=False)

        with col3:
            if st.button("🇬🇧 Libra (GBP)", use_container_width=True):
                processar_mensagem_com_feedback("Quanto está a libra?", mostrar_validacao=False)

        with col4:
            if st.button("↩️ Voltar", use_container_width=True, type="secondary"):
                processar_mensagem_com_feedback("Voltar ao menu", mostrar_validacao=False)


# ==================== MODAL DE CONFIRMAÇÃO ====================

def mostrar_modal_confirmacao():
    """Mostra modal de confirmação para ações importantes."""
    if st.session_state.aguardando_confirmacao == "encerrar":
        st.warning("### ⚠️ Confirmar Encerramento")
        st.write("Tem certeza que deseja encerrar o atendimento?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Sim, encerrar", use_container_width=True, type="primary"):
                processar_mensagem_com_feedback("Encerrar atendimento", mostrar_validacao=False)
                st.session_state.aguardando_confirmacao = None

        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.aguardando_confirmacao = None
                st.rerun()


# ==================== PROGRESSO DA ENTREVISTA ====================

def mostrar_progresso_entrevista():
    """Mostra barra de progresso da entrevista."""
    estado = st.session_state.sistema.get_estado()

    if estado.get("agente_ativo") == "entrevista_credito":
        dados_temp = estado.get("dados_temporarios", {})
        entrevista_dados = dados_temp.get("dados_entrevista", {})

        # Conta quantas perguntas foram respondidas
        campos = ["renda_mensal", "tipo_emprego", "despesas_fixas", "num_dependentes", "tem_dividas"]
        respondidas = sum(1 for campo in campos if entrevista_dados.get(campo) is not None)
        total = len(campos)

        progresso = respondidas / total if total > 0 else 0

        st.markdown("### 📋 Progresso da Entrevista")
        st.progress(progresso)

        # Indicador visual
        bullets = "●" * respondidas + "○" * (total - respondidas)
        st.caption(f"Pergunta {respondidas + 1} de {total} | {bullets}")


# ==================== HISTÓRICO MELHORADO ====================

def exibir_historico():
    """Exibe histórico de conversação com avatares e timestamps."""
    st.markdown("### 💬 Conversa")

    chat_container = st.container(height=450)

    with chat_container:
        for msg in st.session_state.mensagens:
            timestamp = msg.get("timestamp", datetime.now())
            agente = msg.get("agente", "sistema")

            if msg["remetente"] == "Você":
                with st.chat_message("user", avatar="👤"):
                    st.write(msg["mensagem"])
                    st.caption(f"🕐 {timestamp.strftime('%H:%M:%S')}")
            else:
                # Avatar por agente
                avatar_map = {
                    "triagem": "🎯",
                    "credito": "💳",
                    "entrevista_credito": "📋",
                    "cambio": "💱",
                    "sistema": "🤖",
                    "encerramento": "👋"
                }

                avatar = avatar_map.get(agente, "🤖")

                with st.chat_message("assistant", avatar=avatar):
                    st.write(msg["mensagem"])
                    agente_nome = agente.replace("_", " ").title()
                    st.caption(f"🕐 {timestamp.strftime('%H:%M:%S')} | {agente_nome}")


# ==================== SIDEBAR CONTEXTUAL ====================

def exibir_sidebar():
    """Exibe sidebar com informações contextuais."""
    with st.sidebar:
        st.header("📊 Informações do Sistema")

        estado = st.session_state.sistema.get_estado()
        cliente_autenticado = estado.get("cliente_autenticado")
        agente_ativo = estado.get("agente_ativo", "triagem")

        # Informações do cliente
        if cliente_autenticado:
            st.subheader("👤 Cliente Autenticado")
            st.write(f"**Nome:** {cliente_autenticado['nome']}")
            st.write(f"**CPF:** {cliente_autenticado['cpf']}")

            # Gauge visual do score
            score = cliente_autenticado['score_credito']
            score_percentual = score / 1000

            st.write(f"**Score de Crédito:**")
            st.progress(score_percentual)
            st.caption(f"{score:.0f}/1000")

            st.write(f"**Limite Atual:** R$ {cliente_autenticado['limite_credito']:,.2f}")
        else:
            st.info("👤 Nenhum cliente autenticado")

        st.markdown("---")

        # Agente Ativo
        st.subheader("🤖 Agente Ativo")
        agente_map = {
            "triagem": "🎯 Triagem",
            "credito": "💳 Crédito",
            "entrevista_credito": "📋 Entrevista de Crédito",
            "cambio": "💱 Câmbio",
            "encerramento": "👋 Encerrando"
        }
        agente_nome = agente_map.get(agente_ativo, "Nenhum")
        st.write(f"**{agente_nome}**")

        st.markdown("---")

        # Informações contextuais por agente
        if agente_ativo == "credito" and cliente_autenticado:
            st.subheader("💳 Limites por Score")

            st.markdown("""
            | Score | Limite Máximo |
            |-------|---------------|
            | < 600 | R$ 5.000 |
            | 600-700 | R$ 10.000 |
            | 700-850 | R$ 20.000 |
            | > 850 | R$ 50.000 |
            """)

        elif agente_ativo == "cambio":
            st.subheader("💱 Moedas Disponíveis")
            st.write("""
            - 🇺🇸 USD (Dólar)
            - 🇪🇺 EUR (Euro)
            - 🇬🇧 GBP (Libra)
            - 🇯🇵 JPY (Iene)
            - 🇨🇦 CAD (Dólar Canadense)
            - 🇦🇷 ARS (Peso Argentino)
            """)

        elif agente_ativo == "entrevista_credito":
            mostrar_progresso_entrevista()

        st.markdown("---")

        # Informações do sistema
        st.subheader("ℹ️ Sobre o Sistema")
        st.write("""
        Sistema de atendimento bancário com agentes de IA especializados usando LLM.

        **Tecnologias:**
        - 🤖 LangGraph
        - 🚀 Groq API (Llama 3.3 70B)
        - 💬 Conversação natural
        """)

        st.markdown("---")

        # Dados de teste
        st.subheader("🔑 Dados de Teste")
        with st.expander("Ver CPFs de teste"):
            st.code("""
CPF: 12345678901
Data: 1990-05-15
Score: 750

CPF: 98765432100
Data: 1985-03-20
Score: 580
            """)


# ==================== FUNÇÃO PRINCIPAL ====================

def main():
    """Função principal da aplicação."""
    configurar_pagina()
    initialize_session_state()

    # Verifica erro de inicialização
    if st.session_state.erro_inicializacao:
        st.error(f"❌ **Erro ao inicializar sistema**\n\n{st.session_state.erro_inicializacao}")
        st.info("💡 Configure a variável GROQ_API_KEY no arquivo .env para usar o sistema.")
        return

    # Layout principal
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("🏦 Banco Ágil")
        st.subheader("Sistema de Atendimento com Agentes de IA + LLM")

    with col2:
        if st.button("🔄 Reiniciar Conversa", use_container_width=True):
            st.session_state.sistema.reset()
            st.session_state.conversa_iniciada = False
            st.session_state.mensagens = []
            st.session_state.aguardando_confirmacao = None
            st.rerun()

    # Inicia conversa se não iniciada (sem chamar LLM imediatamente)
    if not st.session_state.conversa_iniciada:
        # Mensagem de boas-vindas estática (sem LLM)
        mensagem_inicial = """
👋 **Bem-vindo ao Banco Ágil!**

Sou seu assistente virtual inteligente, pronto para ajudá-lo com:
- 💳 Consultas e solicitações de crédito
- 💱 Cotações de moedas
- 📋 Atualização de dados financeiros
- E muito mais!

Para começar, por favor **informe seu CPF** (11 dígitos).
        """.strip()

        st.session_state.mensagens.append({
            "remetente": "Assistente",
            "mensagem": mensagem_inicial,
            "timestamp": datetime.now(),
            "agente": "triagem"
        })
        st.session_state.conversa_iniciada = True
        st.rerun()

    # Modal de confirmação
    if st.session_state.aguardando_confirmacao:
        mostrar_modal_confirmacao()

    # Histórico
    st.markdown("---")
    exibir_historico()

    # Quick Replies
    st.markdown("---")
    mostrar_quick_replies()

    # Input do usuário
    st.markdown("---")

    estado = st.session_state.sistema.get_estado()
    conversa_ativa = estado.get("conversa_ativa", True)

    if conversa_ativa and not st.session_state.aguardando_confirmacao:
        # Form para capturar Enter
        with st.form(key="message_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])

            with col1:
                entrada_usuario = st.text_input(
                    "Sua mensagem:",
                    placeholder="Digite sua mensagem ou use os botões acima...",
                    label_visibility="collapsed",
                    key="input_usuario"
                )

            with col2:
                enviar = st.form_submit_button("📤 Enviar", use_container_width=True)

            if enviar and entrada_usuario:
                processar_mensagem_com_feedback(entrada_usuario)

        st.caption("💡 Pressione Enter para enviar rapidamente")

    elif not conversa_ativa:
        st.success("✅ Atendimento encerrado. Clique em 'Reiniciar Conversa' para começar novamente.")

    # Sidebar
    exibir_sidebar()


if __name__ == "__main__":
    main()
