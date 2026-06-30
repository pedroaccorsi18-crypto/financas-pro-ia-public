import streamlit as st

from finance_core import ordenar_meses_cronologicamente


def selecionar_mes(lista_total_banco, *, key):
    meses_disponiveis = ordenar_meses_cronologicamente(
        [transacao.get("mes_referencia") for transacao in lista_total_banco]
    )
    if not lista_total_banco:
        return [], None, meses_disponiveis
    if not meses_disponiveis:
        return lista_total_banco, "Geral", meses_disponiveis

    mes_selecionado = st.selectbox(
        "Filtrar por mês",
        meses_disponiveis,
        key=key,
    )
    lista_transacoes = [
        transacao
        for transacao in lista_total_banco
        if transacao.get("mes_referencia") == mes_selecionado
    ]
    return lista_transacoes, mes_selecionado, meses_disponiveis
