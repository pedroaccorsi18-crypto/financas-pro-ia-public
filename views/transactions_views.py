import pandas as pd
import streamlit as st

from finance_categories import CATEGORIAS_DESPESA
from repositories.finance_repository import inserir_transacao
from utils.audit import preparar_dataframe_auditoria_categoria
from utils.error_handling import mostrar_erro_seguro
from utils.history import formatar_linha_historico
from views.shared_view_helpers import selecionar_mes
from views.sidebar_views import render_lancamento_manual


def render_transacoes(lista_total_banco, usuario_id, email_usuario):
    render_lancamento_manual(
        usuario_id=usuario_id,
        email_usuario=email_usuario,
        inserir_transacao=inserir_transacao,
    )

    st.title("Transações")
    lista_transacoes, mes_selecionado, _ = selecionar_mes(
        lista_total_banco,
        key="mes_transacoes",
    )
    if not lista_transacoes:
        st.info("Nenhum dado disponível. Adicione um lançamento manual ou importe um PDF.")
        return

    df_mes = pd.DataFrame(lista_transacoes)
    st.subheader("Central de Auditoria Contábil")
    for categoria in CATEGORIAS_DESPESA:
        try:
            df_exibicao = preparar_dataframe_auditoria_categoria(df_mes, categoria)
            if not df_exibicao.empty:
                with st.expander(f"Linhas auditadas de '{categoria}' ({len(df_exibicao)} itens)"):
                    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            else:
                with st.expander(f"Linhas auditadas de '{categoria}' (zerado)"):
                    st.info(f"Nenhum gasto classificado em {categoria} para este período.")
        except Exception as e_audit:
            st.error(mostrar_erro_seguro(e_audit, email_usuario))

    st.markdown("---")
    st.subheader(f"Histórico Geral de Movimentações de {mes_selecionado}")
    for transacao in reversed(lista_transacoes):
        st.markdown(formatar_linha_historico(transacao))
