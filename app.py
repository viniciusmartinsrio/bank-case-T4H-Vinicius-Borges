"""
Interface Streamlit para o Sistema de Agentes Bancários - Banco Ágil
Permite testar o sistema de atendimento completo.
"""

import streamlit as st
from banco_agil_system import BancoAgilSystem


def initialize_session_state():
    """Inicializa o estado da sessão Streamlit."""
    if "sistema" not in st.session_state:
        st.session_state.sistema = BancoAgilSystem()
        st.session_state.conversa_iniciada = False
        st.session_state.mensagens = []


def main():
    """Função principal da aplicação."""
    st.set_page_config(
        page_title="Banco Ágil - Atendimento Inteligente",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inicializa estado
    initialize_session_state()
    
    # Layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🏦 Banco Ágil")
        st.subtitle("Sistema de Atendimento com Agentes de IA")
    
    with col2:
        if st.button("🔄 Reiniciar Conversa", use_container_width=True):
            st.session_state.sistema = BancoAgilSystem()
            st.session_state.conversa_iniciada = False
            st.session_state.mensagens = []
            st.rerun()
    
    # Inicia conversa se não iniciada
    if not st.session_state.conversa_iniciada:
        mensagem_inicial = st.session_state.sistema.iniciar_atendimento()
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
    
    if st.session_state.sistema.conversa_ativa:
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
            resposta = st.session_state.sistema.processar_entrada(entrada_usuario)
            
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
        
        if st.session_state.sistema.cliente_autenticado:
            cliente = st.session_state.sistema.cliente_autenticado
            st.subheader("👤 Cliente Autenticado")
            st.write(f"**Nome:** {cliente['nome']}")
            st.write(f"**CPF:** {cliente['cpf']}")
            st.write(f"**Limite Atual:** R$ {cliente['limite_credito']:,.2f}")
            st.write(f"**Score de Crédito:** {cliente['score_credito']:.0f}")
        else:
            st.info("Nenhum cliente autenticado")
        
        st.markdown("---")
        
        st.subheader("🤖 Agente Ativo")
        agente_map = {
            "triagem": "🎯 Triagem",
            "credito": "💳 Crédito",
            "entrevista_credito": "📋 Entrevista de Crédito",
            "cambio": "💱 Câmbio"
        }
        agente_nome = agente_map.get(
            st.session_state.sistema.agente_ativo,
            "Nenhum"
        )
        st.write(f"**{agente_nome}**")
        
        st.markdown("---")
        
        st.subheader("ℹ️ Sobre o Sistema")
        st.write("""
Este é um sistema de atendimento bancário com múltiplos agentes de IA especializados:

- **Agente de Triagem**: Autentica clientes
- **Agente de Crédito**: Consulta e solicita aumento de limite
- **Agente de Entrevista**: Recalcula score de crédito
- **Agente de Câmbio**: Consulta cotações de moedas

Cada agente tem responsabilidades bem definidas e trabalha de forma integrada.
        """)


if __name__ == "__main__":
    main()
