"""
Interface Streamlit para o Sistema de Agentes Bancários com LLM - Banco Ágil
Permite testar o sistema de atendimento completo com LangGraph + Groq LLM.
"""

import streamlit as st
from banco_agil_langgraph import BancoAgilLangGraph


def initialize_session_state():
    """Inicializa o estado da sessão Streamlit."""
    if "sistema" not in st.session_state:
        try:
            st.session_state.sistema = BancoAgilLangGraph()
            st.session_state.conversa_iniciada = False
            st.session_state.mensagens = []
            st.session_state.erro_inicializacao = None
        except ValueError as e:
            st.session_state.sistema = None
            st.session_state.erro_inicializacao = str(e)


def main():
    """Função principal da aplicação."""
    st.set_page_config(
        page_title="Banco Ágil - Atendimento Inteligente com LLM",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inicializa estado
    initialize_session_state()

    # Verifica erro de inicialização
    if st.session_state.erro_inicializacao:
        st.error(f"❌ Erro ao inicializar sistema: {st.session_state.erro_inicializacao}")
        st.info("Configure a variável GROQ_API_KEY no arquivo .env para usar o sistema.")
        return

    # Layout
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("🏦 Banco Ágil")
        st.subheader("Sistema de Atendimento com Agentes de IA + LLM")

    with col2:
        if st.button("🔄 Reiniciar Conversa", use_container_width=True):
            st.session_state.sistema.reset()
            st.session_state.conversa_iniciada = False
            st.session_state.mensagens = []
            st.rerun()

    # Inicia conversa se não iniciada
    if not st.session_state.conversa_iniciada:
        mensagem_inicial = st.session_state.sistema.processar_mensagem("Olá!")
        st.session_state.mensagens.append({
            "remetente": "Assistente",
            "mensagem": mensagem_inicial
        })
        st.session_state.conversa_iniciada = True

    # Exibe histórico de mensagens
    st.markdown("---")
    st.subheader("💬 Conversa")

    chat_container = st.container(height=400)

    with chat_container:
        for msg in st.session_state.mensagens:
            if msg["remetente"] == "Você":
                st.chat_message("user").write(msg["mensagem"])
            else:
                st.chat_message("assistant").write(msg["mensagem"])

    # Input do usuário
    st.markdown("---")

    estado = st.session_state.sistema.get_estado()
    conversa_ativa = estado.get("conversa_ativa", True)

    if conversa_ativa:
        col1, col2 = st.columns([4, 1])

        with col1:
            entrada_usuario = st.text_input(
                "Sua resposta:",
                placeholder="Digite sua resposta aqui...",
                label_visibility="collapsed",
                key="input_usuario"
            )

        with col2:
            enviar = st.button("Enviar", use_container_width=True)

        if enviar and entrada_usuario:
            # Adiciona entrada do usuário
            st.session_state.mensagens.append({
                "remetente": "Você",
                "mensagem": entrada_usuario
            })

            # Processa entrada
            resposta = st.session_state.sistema.processar_mensagem(entrada_usuario)

            # Adiciona resposta
            st.session_state.mensagens.append({
                "remetente": "Assistente",
                "mensagem": resposta
            })

            # Limpa input e rerun
            st.rerun()
    else:
        st.info("✅ Atendimento encerrado. Clique em 'Reiniciar Conversa' para começar novamente.")

    # Sidebar com informações
    with st.sidebar:
        st.header("📊 Informações do Sistema")

        estado = st.session_state.sistema.get_estado()
        cliente_autenticado = estado.get("cliente_autenticado")

        if cliente_autenticado:
            st.subheader("👤 Cliente Autenticado")
            st.write(f"**Nome:** {cliente_autenticado['nome']}")
            st.write(f"**CPF:** {cliente_autenticado['cpf']}")
            st.write(f"**Limite Atual:** R$ {cliente_autenticado['limite_credito']:,.2f}")
            st.write(f"**Score de Crédito:** {cliente_autenticado['score_credito']:.0f}")
        else:
            st.info("Nenhum cliente autenticado")

        st.markdown("---")

        st.subheader("🤖 Agente Ativo")
        agente_map = {
            "triagem": "🎯 Triagem",
            "credito": "💳 Crédito",
            "entrevista_credito": "📋 Entrevista de Crédito",
            "cambio": "💱 Câmbio",
            "encerramento": "👋 Encerrando"
        }
        agente_nome = agente_map.get(
            estado.get("agente_ativo", "triagem"),
            "Nenhum"
        )
        st.write(f"**{agente_nome}**")

        st.markdown("---")

        st.subheader("ℹ️ Sobre o Sistema")
        st.write("""
Este é um sistema de atendimento bancário com múltiplos agentes de IA especializados **usando LLM**:

- **Agente de Triagem**: Autentica clientes de forma conversacional
- **Agente de Crédito**: Consulta e solicita aumento de limite com empatia
- **Agente de Entrevista**: Recalcula score de crédito através de entrevista natural
- **Agente de Câmbio**: Consulta cotações de moedas em tempo real

**Tecnologias:**
- 🤖 LangGraph para orquestração
- 🚀 Groq API (Llama 3.1 70B)
- 🔧 LangChain Tools
- 💬 Conversação natural

Cada agente tem responsabilidades bem definidas e trabalha de forma integrada.
        """)

        st.markdown("---")

        st.subheader("🔑 Dados de Teste")
        st.write("""
**Cliente Exemplo:**
- CPF: `12345678901`
- Data Nascimento: `1990-05-15`
- Limite: R$ 5.000,00
- Score: 750
        """)


if __name__ == "__main__":
    main()
