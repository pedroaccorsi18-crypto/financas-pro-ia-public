from textwrap import dedent

import streamlit as st

from auth import cadastrar_usuario, enviar_email_recuperacao_senha, fazer_login
from session_state import iniciar_sessao_autenticada


PLANOS_PUBLICOS = (
    {
        "nome": "Gratuito",
        "preco": "R$ 0",
        "periodo": "para começar",
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
        "periodo": "melhor ponto de entrada",
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
        "periodo": "organização da casa",
        "descricao": "Para organizar a vida financeira da casa em uma visão mais completa.",
        "itens": (
            "Tudo do Pro",
            "Múltiplos objetivos",
            "Visão familiar mais completa",
        ),
    },
)


def _render_landing_styles():
    st.markdown(
        dedent(
            """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }

            [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at 12% 8%, rgba(37, 99, 235, 0.13), transparent 28rem),
                    radial-gradient(circle at 88% 20%, rgba(20, 184, 166, 0.12), transparent 24rem),
                    #f8fafc;
            }

            [data-testid="stHeader"] {
                background: rgba(248, 250, 252, 0);
            }

            .block-container {
                max-width: 1200px;
                padding-top: 1.4rem;
                padding-bottom: 4rem;
            }

            .fp-nav {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 18px;
                color: #0f172a;
            }

            .fp-brand {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 800;
                letter-spacing: 0;
            }

            .fp-brand-mark {
                width: 34px;
                height: 34px;
                border-radius: 8px;
                display: grid;
                place-items: center;
                color: #ffffff;
                background: linear-gradient(135deg, #2563eb, #14b8a6);
                box-shadow: 0 12px 28px rgba(37, 99, 235, 0.25);
            }

            .fp-nav-note {
                color: #64748b;
                font-size: 0.92rem;
            }

            .fp-hero {
                display: grid;
                grid-template-columns: minmax(0, 1.05fr) minmax(340px, 0.95fr);
                gap: 34px;
                align-items: center;
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 8px;
                padding: 44px;
                background:
                    linear-gradient(135deg, rgba(37, 99, 235, 0.18), rgba(20, 184, 166, 0.10)),
                    #0b1120;
                color: #f8fafc;
                box-shadow: 0 18px 50px rgba(2, 6, 23, 0.24);
                overflow: hidden;
            }

            .fp-hero h1 {
                margin: 0;
                max-width: 720px;
                font-size: 3.45rem;
                line-height: 1.02;
                letter-spacing: 0;
                color: #f8fafc;
            }

            .fp-hero p {
                max-width: 690px;
                margin: 20px 0 0;
                font-size: 1.08rem;
                line-height: 1.7;
                color: #cbd5e1;
            }

            .fp-hero-actions {
                display: flex;
                gap: 10px;
                margin-top: 28px;
                flex-wrap: wrap;
            }

            .fp-trust {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 22px;
                color: #cbd5e1;
                font-size: 0.92rem;
            }

            .fp-trust span {
                border: 1px solid rgba(226, 232, 240, 0.14);
                border-radius: 999px;
                padding: 7px 11px;
                background: rgba(15, 23, 42, 0.65);
            }

            .fp-product-shot {
                border: 1px solid rgba(226, 232, 240, 0.14);
                border-radius: 8px;
                padding: 18px;
                background: rgba(15, 23, 42, 0.72);
                box-shadow: 0 24px 70px rgba(2, 6, 23, 0.36);
            }

            .fp-shot-top {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 16px;
                color: #cbd5e1;
                font-size: 0.88rem;
            }

            .fp-shot-status {
                color: #86efac;
            }

            .fp-shot-metric {
                border: 1px solid rgba(226, 232, 240, 0.12);
                border-radius: 8px;
                padding: 14px;
                margin-bottom: 12px;
                background: rgba(2, 6, 23, 0.34);
            }

            .fp-shot-metric small {
                display: block;
                color: #94a3b8;
                margin-bottom: 7px;
            }

            .fp-shot-metric strong {
                color: #ffffff;
                font-size: 1.45rem;
            }

            .fp-bars {
                display: grid;
                gap: 10px;
                margin-top: 16px;
            }

            .fp-bar {
                display: grid;
                grid-template-columns: 90px 1fr 52px;
                align-items: center;
                gap: 10px;
                color: #cbd5e1;
                font-size: 0.84rem;
            }

            .fp-bar-track {
                height: 8px;
                overflow: hidden;
                border-radius: 999px;
                background: rgba(148, 163, 184, 0.22);
            }

            .fp-bar-fill {
                height: 100%;
                border-radius: 999px;
                background: linear-gradient(90deg, #60a5fa, #2dd4bf);
            }

            .fp-proof-row {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
                margin-top: 30px;
            }

            .fp-proof {
                border: 1px solid rgba(226, 232, 240, 0.18);
                border-radius: 8px;
                padding: 16px;
                background: rgba(15, 23, 42, 0.72);
            }

            .fp-proof strong {
                display: block;
                color: #ffffff;
                font-size: 1rem;
                margin-bottom: 4px;
            }

            .fp-proof span {
                color: #94a3b8;
                font-size: 0.92rem;
            }

            .fp-section {
                margin-top: 38px;
            }

            .fp-section h2 {
                margin: 0 0 12px;
                font-size: 1.75rem;
                letter-spacing: 0;
                color: #0f172a;
            }

            .fp-section-intro {
                max-width: 720px;
                color: #64748b;
                line-height: 1.65;
                margin-bottom: 22px;
            }

            .fp-benefits {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 14px;
            }

            .fp-benefit,
            .fp-plan {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: #ffffff;
                padding: 22px;
                min-height: 100%;
                box-shadow: 0 14px 34px rgba(15, 23, 42, 0.05);
            }

            .fp-benefit strong {
                display: block;
                margin-bottom: 8px;
                color: #0f172a;
            }

            .fp-benefit span,
            .fp-plan p,
            .fp-plan li {
                color: #64748b;
                line-height: 1.55;
            }

            .fp-pricing {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 16px;
            }

            .fp-plan.featured {
                border-color: #2563eb;
                box-shadow: 0 20px 46px rgba(37, 99, 235, 0.18);
                background: linear-gradient(180deg, #ffffff, #eff6ff);
                position: relative;
            }

            .fp-plan.featured::before {
                content: "Mais indicado";
                display: inline-block;
                margin-bottom: 14px;
                border-radius: 999px;
                padding: 5px 10px;
                color: #1d4ed8;
                background: #dbeafe;
                font-size: 0.78rem;
                font-weight: 800;
            }

            .fp-plan h3 {
                margin: 0;
                font-size: 1.16rem;
            }

            .fp-plan .price {
                margin: 12px 0 2px;
                color: #0f172a;
                font-size: 2rem;
                line-height: 1.1;
                font-weight: 800;
            }

            .fp-plan .period {
                margin-bottom: 14px;
                color: #2563eb;
                font-size: 0.88rem;
                font-weight: 700;
            }

            .fp-plan ul {
                padding-left: 18px;
                margin-bottom: 0;
            }

            .fp-footnote {
                color: #64748b;
                margin-top: 16px;
                font-size: 0.92rem;
            }

            @media (max-width: 900px) {
                .fp-hero {
                    grid-template-columns: 1fr;
                    padding: 30px;
                }

                .fp-hero h1 {
                    font-size: 2.25rem;
                }

                .fp-proof-row,
                .fp-benefits,
                .fp-pricing {
                    grid-template-columns: 1fr;
                }

                .fp-nav {
                    align-items: flex-start;
                    flex-direction: column;
                    gap: 8px;
                }
            }
        </style>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def _render_plano(plano):
    classe = "fp-plan featured" if plano["nome"] == "Pro" else "fp-plan"
    itens = "".join(f"<li>{item}</li>" for item in plano["itens"])
    st.markdown(
        (
            f'<div class="{classe}">'
            f"<h3>{plano['nome']}</h3>"
            f'<div class="price">{plano["preco"]}</div>'
            f'<div class="period">{plano["periodo"]}</div>'
            f"<p>{plano['descricao']}</p>"
            f"<ul>{itens}</ul>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_tela_apresentacao():
    _render_landing_styles()
    st.markdown(
        dedent(
            """
        <nav class="fp-nav">
            <div class="fp-brand">
                <div class="fp-brand-mark">F</div>
                <span>Finanças Pro IA</span>
            </div>
            <div class="fp-nav-note">Organização financeira simples para o dia a dia</div>
        </nav>
        <section class="fp-hero">
            <div>
                <h1>Assuma o controle do seu dinheiro com clareza.</h1>
                <p>
                    Entenda para onde seu dinheiro vai, acompanhe seus gastos por categoria
                    e tome decisões melhores sem depender de planilhas complicadas.
                </p>
                <div class="fp-trust">
                    <span>Organização mensal</span>
                    <span>Metas por categoria</span>
                    <span>Mais clareza antes de gastar</span>
                </div>
            </div>
            <div class="fp-product-shot">
                <div class="fp-shot-top">
                    <strong>Seu mês financeiro</strong>
                    <span class="fp-shot-status">Em equilíbrio</span>
                </div>
                <div class="fp-shot-metric">
                    <small>Saldo projetado</small>
                    <strong>R$ 2.840</strong>
                </div>
                <div class="fp-shot-metric">
                    <small>Economia do mês</small>
                    <strong>18%</strong>
                </div>
                <div class="fp-bars">
                    <div class="fp-bar">
                        <span>Moradia</span>
                        <div class="fp-bar-track"><div class="fp-bar-fill" style="width: 72%;"></div></div>
                        <span>72%</span>
                    </div>
                    <div class="fp-bar">
                        <span>Mercado</span>
                        <div class="fp-bar-track"><div class="fp-bar-fill" style="width: 54%;"></div></div>
                        <span>54%</span>
                    </div>
                    <div class="fp-bar">
                        <span>Lazer</span>
                        <div class="fp-bar-track"><div class="fp-bar-fill" style="width: 38%;"></div></div>
                        <span>38%</span>
                    </div>
                </div>
            </div>
        </section>
        """
        ).strip(),
        unsafe_allow_html=True,
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

    st.markdown(
        dedent(
            """
        <section class="fp-section">
            <h2>Menos dúvida, mais direção</h2>
            <p class="fp-section-intro">
                O Finanças Pro IA foi feito para quem quer enxergar a vida financeira
                com mais calma: entradas, saídas, categorias, metas e evolução em um
                só lugar.
            </p>
            <div class="fp-benefits">
                <div class="fp-benefit">
                    <strong>Veja o mês com clareza</strong>
                    <span>Acompanhe receitas, despesas e saldo em uma visão fácil de entender.</span>
                </div>
                <div class="fp-benefit">
                    <strong>Organize sem retrabalho</strong>
                    <span>Revise movimentações importadas antes de confirmar seus dados.</span>
                </div>
                <div class="fp-benefit">
                    <strong>Defina limites melhores</strong>
                    <span>Crie metas por categoria e acompanhe sua evolução ao longo do mês.</span>
                </div>
                <div class="fp-benefit">
                    <strong>Tome decisões com contexto</strong>
                    <span>Entenda padrões de consumo antes de cortar gastos no escuro.</span>
                </div>
            </div>
        </section>
        """
        ).strip(),
        unsafe_allow_html=True,
    )

    st.markdown(
        dedent(
            """
        <section class="fp-section">
            <h2>Escolha como quer começar</h2>
            <p class="fp-section-intro">
                Comece organizando o básico gratuitamente e avance quando quiser mais
                acompanhamento, importação e histórico financeiro.
            </p>
        </section>
        """
        ).strip(),
        unsafe_allow_html=True,
    )
    colunas_planos = st.columns(len(PLANOS_PUBLICOS))
    for coluna, plano in zip(colunas_planos, PLANOS_PUBLICOS):
        with coluna:
            _render_plano(plano)

    st.markdown(
        dedent(
            """
        <p class="fp-footnote">
            Você pode começar pelo plano gratuito e evoluir quando fizer sentido para sua rotina.
        </p>
        """
        ).strip(),
        unsafe_allow_html=True,
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
                elif not st.session_state.get("login_bloqueado_por_tentativas", False):
                    st.error(
                        "N\u00e3o foi poss\u00edvel entrar. Confira e-mail e senha. Se a conta foi "
                        "criada agora, verifique tamb\u00e9m se h\u00e1 uma confirma\u00e7\u00e3o pendente "
                        "na caixa de entrada ou spam."
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
