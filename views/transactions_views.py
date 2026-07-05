import pandas as pd
import streamlit as st

from finance_categories import CATEGORIAS_DESPESA
from repositories.finance_repository import inserir_transacao
from utils.audit import preparar_dataframe_auditoria_categoria
from utils.error_handling import mostrar_erro_seguro
from utils.history import formatar_linha_historico
from views.shared_view_helpers import selecionar_mes
from views.sidebar_views import render_lancamento_manual


def _navegar_para_importacao():
    st.session_state.secao_principal = "Importação"
    st.rerun()


def _render_estado_vazio_transacoes():
    st.markdown(
        """
        <div style="border:1px solid #dbe4ee; border-radius:10px; padding:24px 28px; background:#ffffff;">
            <div style="color:#087443; font-size:0.82rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase;">Sem movimentações ainda</div>
            <h3 style="margin:8px 0 10px 0; color:#0f172a;">Escolha como quer começar</h3>
            <p style="max-width:760px; color:#475569; font-size:1rem; line-height:1.6; margin:0;">
                Use o formulário de lançamento manual na barra lateral para registrar uma receita ou despesa avulsa.
                Para carregar vários lançamentos de uma vez, importe um PDF com apoio da IA.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_manual, col_importacao = st.columns(2)
    with col_manual:
        st.markdown("**Lançamento manual**")
        st.caption("Ideal para um gasto, uma receita ou um ajuste pontual.")
        st.caption("O formulário fica na barra lateral desta página.")
    with col_importacao:
        st.markdown("**Importação por PDF**")
        st.caption("Melhor para extratos, faturas e grandes volumes de movimentações.")
        if st.button("Importar PDF", type="primary", use_container_width=True):
            _navegar_para_importacao()


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
        _render_estado_vazio_transacoes()
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
