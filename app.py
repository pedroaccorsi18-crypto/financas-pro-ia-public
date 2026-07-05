import logging

import streamlit as st

from app_config import montar_opcoes_navegacao
from auth import (
    validar_chave_publica_supabase,
    validar_sessao_atual,
)
from repositories.finance_repository import (
    listar_transacoes_usuario,
    obter_ou_criar_assinatura_usuario,
)
from session_state import (
    encerrar_sessao_usuario,
    inicializar_estado_sessao,
    limpar_sessao_usuario,
)
from utils.authorization import eh_usuario_admin
from utils.error_handling import mostrar_erro_seguro
from utils.gemini_client import (
    criar_cliente_gemini,
    gerar_conteudo_gemini as gerar_com_cliente_gemini,
)
from utils.subscriptions import rotulo_plano
from views.admin_views import render_admin
from views.auth_views import render_fluxo_autenticacao
from views.dashboard_views import render_visao_geral
from views.import_views import render_importacao
from views.market_radar_views import render_radar_mercado
from views.oracle_views import render_oraculo
from views.planning_views import render_planejamento_360
from views.transactions_views import render_transacoes

logger = logging.getLogger(__name__)


st.set_page_config(page_title="Finanças Pro IA", page_icon="💰", layout="wide")

try:
    validar_chave_publica_supabase(st.secrets["SUPABASE_KEY"])
except Exception:
    logger.critical("Chave Supabase insegura ou inválida configurada", exc_info=True)
    st.error("A configuração de acesso do app é insegura ou inválida.")
    st.stop()


@st.cache_resource
def obter_cliente_gemini():
    """Cria o cliente Gemini somente quando um recurso de IA é acionado."""
    chave = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    if not chave:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    return criar_cliente_gemini(chave)


def gerar_conteudo_gemini(*, tentativas=3, **kwargs):
    return gerar_com_cliente_gemini(
        obter_cliente_gemini(),
        tentativas=tentativas,
        **kwargs,
    )


def _listar_transacoes_seguras(usuario_id, email_usuario):
    try:
        return listar_transacoes_usuario(usuario_id)
    except Exception as e_fetch:
        st.error(mostrar_erro_seguro(e_fetch, email_usuario))
        return []


def _garantir_assinatura_segura():
    try:
        assinatura = obter_ou_criar_assinatura_usuario()
        st.session_state.assinatura_atual = assinatura
        return assinatura
    except Exception:
        logger.warning("Nao foi possivel obter assinatura do usuario", exc_info=True)
        st.session_state.assinatura_atual = None
        return None


def render_app_autenticado():
    email_usuario = st.session_state.usuario_email
    usuario_id = st.session_state.usuario_id
    assinatura = _garantir_assinatura_segura()
    lista_total_banco = _listar_transacoes_seguras(usuario_id, email_usuario)
    is_admin = eh_usuario_admin(email_usuario, st.secrets.get("ADMIN_EMAILS", []))

    st.sidebar.title("Navegação")
    st.sidebar.write(f"Usuário ativo: **{email_usuario}**")
    if assinatura:
        st.sidebar.caption(f"Plano atual: {rotulo_plano(assinatura.get('plano'))}")
    opcoes = montar_opcoes_navegacao(st.secrets, is_admin=is_admin)
    secao = st.sidebar.radio("Área", opcoes, key="secao_principal")

    st.sidebar.markdown("---")
    if st.sidebar.button("Sair / Logout"):
        encerrar_sessao_usuario()
        st.rerun()

    if secao == "Visão Geral":
        render_visao_geral(lista_total_banco, usuario_id, email_usuario)
    elif secao == "Importação":
        render_importacao(lista_total_banco, usuario_id, email_usuario, is_admin, gerar_conteudo_gemini)
    elif secao == "Transações":
        render_transacoes(lista_total_banco, usuario_id, email_usuario)
    elif secao == "Planejamento 360":
        render_planejamento_360(lista_total_banco, usuario_id, email_usuario)
    elif secao == "Radar de Mercado":
        render_radar_mercado()
    elif secao == "Oráculo IA":
        render_oraculo(lista_total_banco, usuario_id, email_usuario, gerar_conteudo_gemini)
    elif secao == "Admin" and is_admin:
        render_admin(lista_total_banco, usuario_id, email_usuario, gerar_conteudo_gemini)


inicializar_estado_sessao()

if st.session_state.autenticado:
    identidade_revalidada = validar_sessao_atual()
    if not identidade_revalidada:
        limpar_sessao_usuario()
        st.session_state.autenticado = False
        st.session_state.tela_atual = "login"
        st.session_state.aviso_sessao = (
            "Sua sessão expirou ou foi revogada. Entre novamente para continuar."
        )
        st.rerun()
    else:
        st.session_state.usuario_id = identidade_revalidada["id"]
        st.session_state.usuario_email = identidade_revalidada["email"]

if not st.session_state.autenticado:
    render_fluxo_autenticacao()
elif st.session_state.autenticado:
    render_app_autenticado()
