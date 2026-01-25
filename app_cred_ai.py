"""
Interface Streamlit para o Sistema de Agentes Bancários com LLM - Banco Ágil
"""

import streamlit as st
import re
import time
from datetime import datetime
from typing import Optional
from banco_agil_langgraph import BancoAgilLangGraph


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

    # CSS customizado para reduzir espaço em branco no final da página
    st.markdown("""
        <style>
        /* Reduz drasticamente o padding inferior do container principal */
        .main .block-container {
            padding-bottom: 1rem !important;
            padding-top: 3rem !important;
        }

        /* Remove espaço extra de todos os elementos filhos */
        .main .block-container > div {
            padding-bottom: 0 !important;
            margin-bottom: 0 !important;
        }

        /* Força remoção de espaço do último elemento */
        .main .block-container > div:last-child {
            padding-bottom: 0 !important;
            margin-bottom: 0 !important;
        }

        /* Remove espaço extra do elemento root do Streamlit */
        .main {
            padding-bottom: 0 !important;
        }

        /* Reduz espaço entre elementos do formulário */
        .stForm {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        /* Caption mais próximo */
        .stCaption {
            margin-top: -0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Remove padding extra do footer do Streamlit */
        footer {
            padding: 0.5rem !important;
        }
        </style>
    """, unsafe_allow_html=True)


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
            st.session_state.input_counter = 0  # Contador para resetar input
        except ValueError as e:
            st.session_state.sistema = None
            st.session_state.erro_inicializacao = str(e)
        except Exception as e:
            st.session_state.sistema = None
            st.session_state.erro_inicializacao = f"Erro ao inicializar: {type(e).__name__}: {str(e)}"


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

        # Incrementa contador para resetar o input na próxima renderização
        st.session_state.input_counter += 1

        st.rerun()

    except ConnectionError:
        st.error("""
        🌐 **Erro de Conexão**

        Não conseguimos conectar ao servidor. Verifique sua internet e tente novamente.
        """)

    except TimeoutError:
        st.error("""
        ⏱️ **Timeout - Processamento Demorado**

        O processamento está demorando mais que o esperado. Possíveis causas:
        - API da Groq está lenta ou indisponível
        - Sua conexão com internet está instável
        - Chave de API pode estar inválida

        💡 **Tente:**
        - Aguardar alguns segundos e tentar novamente
        - Verificar se a GROQ_API_KEY está configurada corretamente no arquivo .env
        - Reiniciar a conversa
        """)

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)

        st.error(f"""
        ❌ **Ops, algo deu errado!**

        Tente novamente ou reinicie a conversa.

        *Erro técnico: {error_type}*
        """)

        # Em modo debug, exibe detalhes completos
        with st.expander("🔍 Detalhes técnicos (para debug)"):
            st.code(f"Tipo: {error_type}\nMensagem: {error_msg}", language="text")
            import traceback
            st.code(traceback.format_exc(), language="text")

        # Registra no console também
        import traceback
        traceback.print_exc()


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
            if st.button("📋 Entrevista - Aumento de Score", use_container_width=True):
                processar_mensagem_com_feedback("Fazer entrevista financeira", mostrar_validacao=False)

        with col4:
            if st.button("👋 Encerrar", use_container_width=True, type="secondary"):
                st.session_state.aguardando_confirmacao = "encerrar"
                st.rerun()


# ==================== MODAL DE CONFIRMAÇÃO ====================

def mostrar_modal_confirmacao():
    """Mostra modal de confirmação para ações importantes."""
    if st.session_state.aguardando_confirmacao == "encerrar":
        st.warning("### ⚠️ Confirmar Encerramento")
        st.write("Tem certeza que deseja encerrar o atendimento?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Sim, encerrar", use_container_width=True, type="primary"):
                # Reseta o sistema completamente (mesmo comportamento do botão "Reiniciar Conversa")
                st.session_state.sistema.reset()
                st.session_state.conversa_iniciada = False
                st.session_state.mensagens = []
                st.session_state.aguardando_confirmacao = None
                st.session_state.input_counter = 0
                st.rerun()

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

    chat_container = st.container(height=400)

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
            "entrevista_credito": "📋 Entrevista - Aumento de Score",
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
        """)

        st.markdown("### 🛠️ Tecnologias Principais")
        st.markdown("""
        - **Python 3.8+**: Linguagem base
        - **Streamlit**: Interface web interativa
        - **LangChain**: Framework para aplicações com LLM's e arquitetura multi agentes
        - **LangGraph**: Orquestração de agentes com máquina de estados
        - **Groq API**: Inferência com opções de LLM's sem custo para volumetrias baixas (Llama 3.1 8B)
        - **NLP**: Chat de conversação natural com IA
        - **External API**: exchangerate-api.com para cotações
        """)

        st.markdown("---")


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
        st.subheader("Sistema de Atendimento com Agentes de IA")

    with col2:
        if st.button("🔄 Reiniciar Conversa", use_container_width=True):
            st.session_state.sistema.reset()
            st.session_state.conversa_iniciada = False
            st.session_state.mensagens = []
            st.session_state.aguardando_confirmacao = None
            st.session_state.input_counter = 0  # Reseta contador também
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
- E mais!

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
    exibir_historico()

    # Quick Replies
    mostrar_quick_replies()

    # Input do usuário
    estado = st.session_state.sistema.get_estado()
    conversa_ativa = estado.get("conversa_ativa", True)

    if conversa_ativa and not st.session_state.aguardando_confirmacao:
        st.markdown("---")
        # Form para capturar Enter
        with st.form(key=f"message_form_{st.session_state.input_counter}", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])

            with col1:
                entrada_usuario = st.text_input(
                    "Sua mensagem:",
                    placeholder="Digite sua mensagem ou use os botões acima...",
                    label_visibility="collapsed",
                    key=f"input_usuario_{st.session_state.input_counter}"  # Key dinâmica para resetar
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
