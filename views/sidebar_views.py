import datetime

import streamlit as st

from finance_categories import CATEGORIAS_DESPESA, CATEGORIAS_RECEITA
from finance_constants import ORIGEM_MANUAL, TIPO_RECEITA, TIPOS_TRANSACAO
from finance_core import mes_referencia_valido
from utils.error_handling import mostrar_erro_seguro
from utils.manual_entry import preparar_transacao_manual


def render_lancamento_manual(*, usuario_id, email_usuario, inserir_transacao):
    st.sidebar.subheader("\u2795 Lan\u00e7amento Manual")
    tipo_transacao = st.sidebar.selectbox(
        "Tipo",
        TIPOS_TRANSACAO,
        key="tipo_transacao_manual",
    )
    with st.sidebar.form("form_transacao", clear_on_submit=True):
        desc = st.text_input("Descri\u00e7\u00e3o (Ex: Uber)")
        val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        categorias_manuais = (
            CATEGORIAS_RECEITA if tipo_transacao == TIPO_RECEITA else CATEGORIAS_DESPESA
        )
        cat_manual = st.selectbox(
            "Categoria",
            categorias_manuais,
            key=f"categoria_manual_{tipo_transacao.lower()}",
        )

        ano_atual = datetime.datetime.now().year
        meses_ano = [f"{mes:02d}/{ano_atual}" for mes in range(1, 13)]
        mes_manual = st.selectbox(
            "M\u00eas de Refer\u00eancia",
            meses_ano,
            index=datetime.datetime.now().month - 1,
        )
        banco_manual = st.text_input(
            "Institui\u00e7\u00e3o (Opcional)",
            value=ORIGEM_MANUAL,
        ).strip()

        if st.form_submit_button("Salvar Lan\u00e7amento"):
            if desc and val > 0:
                try:
                    if not mes_referencia_valido(mes_manual):
                        st.error("Formato do m\u00eas de refer\u00eancia inv\u00e1lido.")
                    else:
                        inserir_transacao(
                            preparar_transacao_manual(
                                descricao=desc,
                                valor=val,
                                tipo_transacao=tipo_transacao,
                                categoria=cat_manual,
                                categorias_validas=categorias_manuais,
                                mes_referencia=mes_manual,
                                instituicao=banco_manual,
                                usuario_id=usuario_id,
                                email_usuario=email_usuario,
                            )
                        )
                        st.toast(
                            "Lan\u00e7amento computado com sucesso!",
                            icon="\u2705",
                        )
                        st.rerun()
                except Exception as e_insert:
                    msg = mostrar_erro_seguro(e_insert, email_usuario)
                    st.error(msg)
