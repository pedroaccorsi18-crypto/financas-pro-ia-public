import streamlit as st

from auth import encerrar_autenticacao_supabase


def inicializar_estado_sessao():
    """Inicializa chaves esperadas do Session State sem sobrescrever valores existentes."""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "tela_atual" not in st.session_state:
        st.session_state.tela_atual = "apresentacao"
    if "resposta_oraculo_texto" not in st.session_state:
        st.session_state.resposta_oraculo_texto = None
    if "historico_oraculo_enviado" not in st.session_state:
        st.session_state.historico_oraculo_enviado = None
    if "feedback_enviado" not in st.session_state:
        st.session_state.feedback_enviado = False
    if "dados_pre_visualizacao" not in st.session_state:
        st.session_state.dados_pre_visualizacao = None


def limpar_sessao_usuario(preservar_cliente_supabase=False):
    """Remove dados do usuário anterior, incluindo estados automáticos de widgets."""
    cliente_supabase = st.session_state.get("_supabase_client") if preservar_cliente_supabase else None
    config_supabase = st.session_state.get("_supabase_config") if preservar_cliente_supabase else None
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]
    if cliente_supabase is not None:
        st.session_state["_supabase_client"] = cliente_supabase
    if config_supabase is not None:
        st.session_state["_supabase_config"] = config_supabase


def iniciar_sessao_autenticada(email_usuario, usuario_id):
    """Inicia uma sessão limpa e vinculada exclusivamente ao usuário autenticado."""
    limpar_sessao_usuario(preservar_cliente_supabase=True)
    st.session_state.autenticado = True
    st.session_state.tela_atual = "login"
    st.session_state.usuario_email = email_usuario
    st.session_state.usuario_id = usuario_id
    st.session_state.resposta_oraculo_texto = None
    st.session_state.historico_oraculo_enviado = None
    st.session_state.feedback_enviado = False
    st.session_state.dados_pre_visualizacao = None


def encerrar_sessao_usuario():
    """Encerra a sessão sem preservar dados sensíveis do usuário."""
    logout_confirmado = encerrar_autenticacao_supabase()
    limpar_sessao_usuario()
    st.session_state.autenticado = False
    st.session_state.tela_atual = "apresentacao"
    if not logout_confirmado:
        st.session_state.aviso_sessao = (
            "A sessao local foi encerrada, mas o Supabase nao confirmou a revogacao. "
            "Feche esta aba antes de tentar novamente."
        )
    return logout_confirmado
