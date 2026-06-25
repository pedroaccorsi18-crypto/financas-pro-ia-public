import streamlit as st

from auth import cadastrar_usuario, enviar_email_recuperacao_senha, fazer_login
from session_state import iniciar_sessao_autenticada


def render_tela_login():
    st.title("\U0001f4b0 Finan\u00e7as Pro IA")
    st.subheader("Fa\u00e7a seu login para acessar o painel")
    with st.form("formulario_login"):
        email = st.text_input("E-mail").strip().lower()
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if email and senha:
                usuario_autenticado = fazer_login(email, senha)
                if usuario_autenticado:
                    iniciar_sessao_autenticada(
                        usuario_autenticado["email"],
                        usuario_autenticado["id"],
                    )
                    st.toast(
                        "Autentica\u00e7\u00e3o autorizada com sucesso!",
                        icon="\U0001f510",
                    )
                    st.rerun()
                else:
                    st.error(
                        "E-mail ou senha incorretos. Se voc\u00ea acabou de criar a conta, "
                        "confirme o e-mail de confirma\u00e7\u00e3o antes de entrar."
                    )
            else:
                st.warning("Por favor, preencha todos os campos.")
    if st.button("N\u00e3o tem uma conta? Cadastre-se aqui"):
        st.session_state.tela_atual = "cadastro"
        st.rerun()
    if st.button("Esqueci minha senha"):
        st.session_state.tela_atual = "recuperar_senha"
        st.rerun()


def render_tela_recuperar_senha():
    st.title("Recuperar senha")
    st.caption(
        "Informe o e-mail da sua conta. Se ele estiver cadastrado, enviaremos "
        "as instru\u00e7\u00f5es de redefini\u00e7\u00e3o."
    )
    with st.form("formulario_recuperacao_senha"):
        email_recuperacao = st.text_input("E-mail").strip().lower()
        if st.form_submit_button("Enviar instru\u00e7\u00f5es"):
            if email_recuperacao:
                if enviar_email_recuperacao_senha(email_recuperacao):
                    st.success(
                        "Se houver uma conta associada a este e-mail, voc\u00ea receber\u00e1 "
                        "as instru\u00e7\u00f5es de recupera\u00e7\u00e3o em alguns minutos."
                    )
                else:
                    st.error(
                        "N\u00e3o foi poss\u00edvel solicitar a recupera\u00e7\u00e3o agora. "
                        "Tente novamente em alguns minutos."
                    )
            else:
                st.warning("Informe seu e-mail para continuar.")
    if st.button("Voltar para o login"):
        st.session_state.tela_atual = "login"
        st.rerun()


def render_tela_cadastro():
    st.title("\U0001f4dd Criar Nova Conta")
    with st.form("formulario_cadastro"):
        novo_email = st.text_input("E-mail").strip().lower()
        nova_senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirme a Senha", type="password")
        if st.form_submit_button("Criar Conta"):
            if novo_email and nova_senha and confirmar_senha:
                if nova_senha == confirmar_senha:
                    if len(nova_senha) < 10:
                        st.error("A senha deve ter pelo menos 10 caracteres.")
                    else:
                        resultado = cadastrar_usuario(novo_email, nova_senha)
                        if resultado == "existe":
                            st.error("Esse e-mail j\u00e1 est\u00e1 cadastrado!")
                        elif resultado == "confirmar_email":
                            st.session_state.aviso_sessao = (
                                "Conta criada! Verifique sua caixa de entrada ou spam, "
                                "confirme o e-mail de confirma\u00e7\u00e3o e depois entre "
                                "com seu e-mail e senha."
                            )
                            st.session_state.tela_atual = "login"
                            st.rerun()
                        elif resultado is True:
                            st.success("Conta criada! Redirecionando...")
                            st.session_state.tela_atual = "login"
                            st.rerun()
                else:
                    st.error("As senhas n\u00e3o coincidem.")
            else:
                st.warning("Preencha todos os campos.")
    if st.button("J\u00e1 tem uma conta? Voltar para o Login"):
        st.session_state.tela_atual = "login"
        st.rerun()


def render_fluxo_autenticacao():
    if aviso_sessao := st.session_state.pop("aviso_sessao", None):
        st.warning(aviso_sessao)

    if st.session_state.tela_atual == "recuperar_senha":
        render_tela_recuperar_senha()
    elif st.session_state.tela_atual == "cadastro":
        render_tela_cadastro()
    else:
        render_tela_login()
