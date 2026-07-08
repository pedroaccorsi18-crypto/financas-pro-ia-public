import logging

import streamlit as st

from repositories.finance_repository import buscar_perfil_cliente, salvar_perfil_cliente
from utils.customer_profile import (
    DORES_FINANCEIRAS,
    MOMENTOS_FINANCEIROS,
    NIVEIS_ORGANIZACAO,
    OBJETIVOS_PRINCIPAIS,
    PERFIS_DECISAO,
    PREFERENCIAS_ACOMPANHAMENTO,
    diagnosticar_perfil_cliente,
    montar_payload_perfil_cliente,
    normalizar_perfil_cliente,
)


logger = logging.getLogger(__name__)


def render_meu_perfil(usuario_id, email_usuario):
    st.title("Meu Perfil")
    st.caption(
        "Conte ao app o seu momento financeiro para receber uma experiência mais útil, "
        "menos genérica e mais alinhada aos seus objetivos."
    )

    perfil = _buscar_perfil_cliente_seguro(usuario_id, email_usuario)
    perfil_normalizado = normalizar_perfil_cliente(perfil, usuario_id)
    diagnostico = diagnosticar_perfil_cliente(perfil)

    col_nivel, col_acao = st.columns(2)
    col_nivel.metric("Personalização", diagnostico.nivel)
    col_acao.metric("Acompanhamento", perfil_normalizado["preferencia_acompanhamento"])
    st.info(diagnostico.mensagem)

    with st.form("form_perfil_cliente"):
        momento = st.selectbox(
            "Momento financeiro atual",
            MOMENTOS_FINANCEIROS,
            index=_indice(MOMENTOS_FINANCEIROS, perfil_normalizado["momento_financeiro"]),
        )
        objetivo = st.selectbox(
            "Principal objetivo agora",
            OBJETIVOS_PRINCIPAIS,
            index=_indice(OBJETIVOS_PRINCIPAIS, perfil_normalizado["objetivo_principal"]),
        )
        dor = st.selectbox(
            "Maior dor financeira hoje",
            DORES_FINANCEIRAS,
            index=_indice(DORES_FINANCEIRAS, perfil_normalizado["maior_dor"]),
        )
        nivel = st.selectbox(
            "Nível de organização",
            NIVEIS_ORGANIZACAO,
            index=_indice(NIVEIS_ORGANIZACAO, perfil_normalizado["nivel_organizacao"]),
        )
        perfil_decisao = st.selectbox(
            "Como você prefere tomar decisões?",
            PERFIS_DECISAO,
            index=_indice(PERFIS_DECISAO, perfil_normalizado["perfil_decisao"]),
        )
        acompanhamento = st.selectbox(
            "Frequência ideal de acompanhamento",
            PREFERENCIAS_ACOMPANHAMENTO,
            index=_indice(
                PREFERENCIAS_ACOMPANHAMENTO,
                perfil_normalizado["preferencia_acompanhamento"],
            ),
        )
        aceita_personalizacao = st.checkbox(
            "Usar estas respostas para personalizar recomendações",
            value=perfil_normalizado["aceita_personalizacao"],
        )

        if st.form_submit_button("Salvar perfil"):
            _salvar_perfil_cliente_seguro(
                usuario_id=usuario_id,
                email_usuario=email_usuario,
                momento_financeiro=momento,
                objetivo_principal=objetivo,
                maior_dor=dor,
                nivel_organizacao=nivel,
                perfil_decisao=perfil_decisao,
                preferencia_acompanhamento=acompanhamento,
                aceita_personalizacao=aceita_personalizacao,
            )

    st.markdown("### Próxima orientação")
    st.caption(diagnostico.proxima_acao)


def _buscar_perfil_cliente_seguro(usuario_id, email_usuario):
    try:
        return buscar_perfil_cliente(usuario_id)
    except Exception as erro:
        logger.warning(
            "Nao foi possivel buscar perfil do cliente",
            extra={"tipo_erro": type(erro).__name__, "usuario": _mascarar_email(email_usuario)},
        )
        st.warning("Não foi possível carregar seu perfil agora. Você ainda pode revisar as opções padrão.")
        return None


def _salvar_perfil_cliente_seguro(
    *,
    usuario_id,
    email_usuario,
    momento_financeiro,
    objetivo_principal,
    maior_dor,
    nivel_organizacao,
    perfil_decisao,
    preferencia_acompanhamento,
    aceita_personalizacao,
):
    try:
        payload = montar_payload_perfil_cliente(
            usuario_id=usuario_id,
            momento_financeiro=momento_financeiro,
            objetivo_principal=objetivo_principal,
            maior_dor=maior_dor,
            nivel_organizacao=nivel_organizacao,
            perfil_decisao=perfil_decisao,
            preferencia_acompanhamento=preferencia_acompanhamento,
            aceita_personalizacao=aceita_personalizacao,
        )
        salvar_perfil_cliente(payload)
        st.success("Perfil salvo. Vamos usar esse contexto para melhorar sua experiência.")
    except ValueError as erro:
        st.error(str(erro))
    except Exception as erro:
        logger.warning(
            "Nao foi possivel salvar perfil do cliente",
            extra={"tipo_erro": type(erro).__name__, "usuario": _mascarar_email(email_usuario)},
        )
        st.error("Não foi possível salvar seu perfil agora. Tente novamente em alguns minutos.")


def _indice(opcoes, valor):
    try:
        return opcoes.index(valor)
    except ValueError:
        return 0


def _mascarar_email(email):
    texto = str(email or "")
    if "@" not in texto:
        return "desconhecido"
    inicio, dominio = texto.split("@", 1)
    return f"{inicio[:2]}***@{dominio}"
