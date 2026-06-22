import streamlit as st


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
