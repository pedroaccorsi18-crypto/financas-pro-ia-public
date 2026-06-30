import streamlit as st

from auth import cadastrar_usuario, enviar_email_recuperacao_senha, fazer_login
from session_state import iniciar_sessao_autenticada


PLANOS_PUBLICOS = (
    {
        "nome": "Gratuito",
        "preco": "R$ 0",
        "descricao": "Para organizar as primeiras movimentações e entender o fluxo mensal.",
        "itens": (
            "Lançamentos manuais",
            "Dashboard mensal",
            "Metas por categoria",
        ),
    },
    {
        "nome": "Pro",
        "preco": "R$ 19,90/mês",
        "descricao": "Para quem quer acompanhamento recorrente e mais clareza nas decisões.",
        "itens": (
            "Importação assistida",
            "Auditoria por categoria",
            "Histórico e evolução mensal",
        ),
    },
    {
        "nome": "Família",
        "preco": "R$ 29,90/mês",
        "descricao": "Para organizar a vida financeira da casa em uma visão mais completa.",
        "itens": (
            "Tudo do Pro",
            "Múltiplos objetivos",
            "Base preparada para recursos premium",
        ),
    },
)


def _render_plano(plano):
    st.markdown(f"### {plano['nome']}")
    st.subheader(plano["preco"])
    st.caption(plano["descricao"])
    for item in plano["itens"]:
        st.markdown(f"- {item}")


def render_tela_apresentacao():
    st.title("Finanças Pro IA")
    st.subheader("Organize suas finanças pessoais com clareza, segurança e apoio de IA.")
    st.caption(
        "Importe, revise e acompanhe suas movimentações em um painel simples, "
        "feito para transformar gastos soltos em decisões melhores."
    )

    col_primaria, col_secundaria = st.columns(2)
    with col_primaria:
        if st.button("Começar agora", type="primary", use_container_width=True):
            st.session_state.tela_atual = "cadastro"
            st.rerun()
    with col_secundaria:
        if st.button("Já tenho conta", use_container_width=True):
            st.session_state.tela_atual = "login"
            st.rerun()

    st.markdown("### O que a plataforma resolve")
    beneficios = (
        "Centraliza receitas e despesas em uma visão mensal.",
        "Ajuda a revisar lançamentos antes de gravar dados importados.",
        "Mostra categorias, metas e evolução financeira sem planilhas confusas.",
        "Mantém os módulos avançados preparados para uma futura versão premium.",
    )
    for beneficio in beneficios:
        st.markdown(f"- {beneficio}")

    st.markdown("### Planos sugeridos para o MVP")
    colunas_planos = st.columns(len(PLANOS_PUBLICOS))
    for coluna, plano in zip(colunas_planos, PLANOS_PUBLICOS):
        with coluna:
            _render_plano(plano)

    st.caption(
        "Os valores podem ser ajustados conforme uso real, feedback dos primeiros clientes "
        "e custos de infraestrutura."
    )


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
    if st.button("Voltar para a apresentação"):
        st.session_state.tela_atual = "apresentacao"
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
    if st.button("Voltar para a apresentação"):
        st.session_state.tela_atual = "apresentacao"
        st.rerun()


def render_fluxo_autenticacao():
    if aviso_sessao := st.session_state.pop("aviso_sessao", None):
        st.warning(aviso_sessao)

    if st.session_state.tela_atual == "recuperar_senha":
        render_tela_recuperar_senha()
    elif st.session_state.tela_atual == "cadastro":
        render_tela_cadastro()
    elif st.session_state.tela_atual == "login":
        render_tela_login()
    else:
        render_tela_apresentacao()
