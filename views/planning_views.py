import streamlit as st

from finance_core import calcular_resumo_financeiro
from repositories.finance_repository import (
    buscar_perfil_financeiro_360,
    salvar_perfil_financeiro_360,
)
from utils.error_handling import mostrar_erro_seguro
from utils.formatting import formatar_brl
from views.financial_profile_views import render_perfil_financeiro_360


def render_planejamento_360(lista_total_banco, usuario_id, email_usuario):
    st.title("Planejamento 360")
    resumo_geral_360 = calcular_resumo_financeiro(lista_total_banco)
    try:
        perfil_financeiro_360 = buscar_perfil_financeiro_360(usuario_id)
    except Exception as e_perfil:
        st.warning(mostrar_erro_seguro(e_perfil, email_usuario))
        perfil_financeiro_360 = None

    render_perfil_financeiro_360(
        resumo_transacoes=resumo_geral_360,
        formatar_brl=formatar_brl,
        usuario_id=usuario_id,
        perfil_persistido=perfil_financeiro_360,
        salvar_perfil=salvar_perfil_financeiro_360,
        mostrar_erro=lambda erro: mostrar_erro_seguro(erro, email_usuario),
    )
