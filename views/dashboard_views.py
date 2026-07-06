import pandas as pd
import plotly.express as px
import streamlit as st

from finance_categories import CATEGORIAS_DESPESA
from finance_constants import TIPO_DESPESA
from finance_core import calcular_resumo_financeiro
from repositories.finance_repository import (
    listar_metas_usuario_mes,
    salvar_meta_financeira,
)
from utils.category_analysis import preparar_dados_analise_categorias
from utils.error_handling import mostrar_erro_seguro
from utils.formatting import formatar_brl
from utils.goals import calcular_status_meta
from utils.trends import TENDENCIA_SEM_HISTORICO, calcular_textos_tendencia
from views.shared_view_helpers import selecionar_mes


def _calcular_tendencias(lista_total_banco, meses_disponiveis, mes_selecionado, resumo_mes, email_usuario):
    tendencias = [TENDENCIA_SEM_HISTORICO] * 3
    if not mes_selecionado or mes_selecionado not in meses_disponiveis:
        return tendencias

    idx_atual = meses_disponiveis.index(mes_selecionado)
    if idx_atual + 1 >= len(meses_disponiveis):
        return tendencias

    mes_anterior = meses_disponiveis[idx_atual + 1]
    lista_anterior = [
        transacao
        for transacao in lista_total_banco
        if transacao.get("mes_referencia") == mes_anterior
    ]
    if not lista_anterior:
        return tendencias

    try:
        resumo_anterior = calcular_resumo_financeiro(lista_anterior)
        return calcular_textos_tendencia(resumo_mes, resumo_anterior)
    except Exception as e_trend:
        st.error(mostrar_erro_seguro(e_trend, email_usuario))
        return tendencias


def _render_cards_resumo(total_compras, total_pagamentos, valor_balanco_final, tendencias):
    txt_tendencia_gastos, txt_tendencia_pagamentos, txt_tendencia_balanco = tendencias
    card_html_estrutura = f"""
    <div style="display: flex; gap: 24px; width: 100%; margin-bottom: 25px;">
        <div style="flex: 1; background: linear-gradient(145deg, #1e1e24, #141418); padding: 22px 24px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 125px;">
            <div>
                <div style="color: #a1a1aa; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">💳 Total de Gastos</div>
                <div style="color: #ffffff; font-size: 30px; font-weight: 800; margin-top: 6px;">{formatar_brl(total_compras)}</div>
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.03);">{txt_tendencia_gastos} <span style="color:#71717a; font-size:12px;">vs mês anterior</span></div>
        </div>
        <div style="flex: 1; background: linear-gradient(145deg, #1e1e24, #141418); padding: 22px 24px; border-radius: 16px; border: 1px solid rgba(163, 184, 153, 0.15); display: flex; flex-direction: column; justify-content: space-between; min-height: 125px;">
            <div>
                <div style="color: #a3b899; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">💰 Pagamentos / Créditos</div>
                <div style="color: #a3b899; font-size: 30px; font-weight: 800; margin-top: 6px;">{formatar_brl(total_pagamentos)}</div>
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(163, 184, 153, 0.03);">{txt_tendencia_pagamentos} <span style="color:#71717a; font-size:12px;">vs mês anterior</span></div>
        </div>
        <div style="flex: 1; background: linear-gradient(145deg, #1e1e24, #141418); padding: 22px 24px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 125px;">
            <div>
                <div style="color: #a1a1aa; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">🧾 Balanço Real Consolidado</div>
                <div style="color: #ffffff; font-size: 30px; font-weight: 800; margin-top: 6px;">{formatar_brl(valor_balanco_final)}</div>
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.03);">{txt_tendencia_balanco} <span style="color:#71717a; font-size:12px;">vs mês anterior</span></div>
        </div>
    </div>
    """
    st.markdown(card_html_estrutura, unsafe_allow_html=True)


def _render_metas(usuario_id, email_usuario, mes_selecionado, df_mes):
    if not mes_selecionado:
        return

    st.subheader(f"🎯 Gestão de Metas ({mes_selecionado})")
    try:
        with st.expander("Definir ou ajustar teto de gasto por grupo"):
            col_m1, col_m2, col_m3 = st.columns([40, 40, 20])
            with col_m1:
                cat_meta_sel = st.selectbox("Categoria", CATEGORIAS_DESPESA, key="cat_meta")
            with col_m2:
                valor_meta_sel = st.number_input(
                    "Teto desejado (R$)",
                    min_value=0.0,
                    format="%.2f",
                    key="val_meta",
                )
            with col_m3:
                st.write("<br>", unsafe_allow_html=True)
                if st.button("Definir meta", use_container_width=True):
                    try:
                        salvar_meta_financeira(
                            {
                                "user_id": usuario_id,
                                "usuario_email": email_usuario,
                                "categoria": cat_meta_sel,
                                "mes_referencia": mes_selecionado,
                                "valor_meta": valor_meta_sel,
                            }
                        )
                        st.toast(f"Meta de {cat_meta_sel} salva!", icon="🎯")
                        st.rerun()
                    except Exception as e_upsert:
                        st.error(mostrar_erro_seguro(e_upsert, email_usuario))

        metas_usuario = listar_metas_usuario_mes(usuario_id, mes_selecionado)
        dict_metas = {meta["categoria"]: float(meta["valor_meta"]) for meta in metas_usuario}
        df_despesas = df_mes[df_mes["tipo"] == TIPO_DESPESA]

        for categoria in CATEGORIAS_DESPESA:
            gasto_atual = (
                df_despesas[df_despesas["categoria"] == categoria]["valor"].sum()
                if not df_despesas.empty
                else 0.0
            )
            meta_cadastrada = dict_metas.get(categoria, 0.0)
            if meta_cadastrada > 0:
                pct, cor_barra, txt_status = calcular_status_meta(
                    gasto_atual,
                    meta_cadastrada,
                )
                st.markdown(
                    f"**{categoria}** | Gasto: {formatar_brl(gasto_atual)} "
                    f"de Meta: {formatar_brl(meta_cadastrada)} ({pct*100:.1f}%)"
                )
                st.progress(min(pct, 1.0))
                st.markdown(
                    f"<small style='color:{cor_barra}; font-weight:600;'>{txt_status}</small><br><br>",
                    unsafe_allow_html=True,
                )
    except Exception as e_metas:
        st.info(mostrar_erro_seguro(e_metas, email_usuario))


def _render_analise_categorias(df_mes, df_despesas, email_usuario):
    st.subheader("📊 Análise por Grupos")
    if df_despesas.empty:
        st.info("Nenhuma despesa para plotagem de gráficos.")
        return

    try:
        col_grafico, col_subtotais = st.columns([50, 50])
        with col_grafico:
            df_agrupado, subtotais_categorias = preparar_dados_analise_categorias(
                df_mes,
                df_despesas,
                CATEGORIAS_DESPESA,
            )
            fig_barras = px.bar(
                df_agrupado,
                x="Total (R$)",
                y="Categoria",
                orientation="h",
                text="Total (R$)",
                color="Total (R$)",
                color_continuous_scale="Plotly3",
            )
            fig_barras.update_traces(
                texttemplate="R$ %{text:,.2f}",
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
            )
            fig_barras.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=40),
                height=380,
                xaxis=dict(showgrid=False, title="", showticklabels=False, fixedrange=True),
                yaxis=dict(title="", tickfont=dict(size=12, color="#a1a1aa"), fixedrange=True),
                coloraxis_showscale=False,
                dragmode=False,
            )
            st.plotly_chart(fig_barras, use_container_width=True, config={"displayModeBar": False})

        with col_subtotais:
            for categoria, valor_categoria in subtotais_categorias:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(90deg, #16161a, #1a1a22); padding: 11px 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); margin-bottom: 7px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #a1a1aa; font-size: 13px; font-weight: 600; text-transform: uppercase;">{categoria}</span>
                        <span style="color: #ffffff; font-size: 15px; font-weight: 700;">{formatar_brl(valor_categoria)}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except Exception as e_plots:
        st.error(mostrar_erro_seguro(e_plots, email_usuario))


def _navegar_para_secao(secao):
    st.session_state.secao_principal = secao
    st.rerun()


def _render_estado_inicial():
    st.markdown(
        """
        <div style="border:1px solid #dbe4ee; border-radius:10px; padding:30px; background:linear-gradient(135deg,#ffffff,#f4f8ff);">
            <div style="display:flex; justify-content:space-between; gap:18px; align-items:flex-start; flex-wrap:wrap;">
                <div style="max-width:720px;">
                    <div style="color:#087443; font-size:0.82rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase;">Configuração inicial</div>
                    <h2 style="margin:8px 0 10px 0; color:#0f172a;">Comece seu primeiro resumo financeiro</h2>
                    <p style="color:#475569; font-size:1rem; line-height:1.6; margin:0;">
                        Em poucos minutos, você consegue importar um extrato ou lançar movimentos essenciais
                        para enxergar saldo, categorias, tendências e metas de gasto em uma visão simples.
                    </p>
                </div>
                <div style="min-width:190px; border:1px solid #dbe4ee; border-radius:8px; padding:16px; background:#ffffff;">
                    <div style="color:#64748b; font-size:0.82rem; font-weight:700;">Tempo estimado</div>
                    <div style="color:#0f172a; font-size:1.9rem; font-weight:900; line-height:1.2;">3 min</div>
                    <div style="color:#64748b; font-size:0.84rem; line-height:1.4; margin-top:8px;">para chegar ao primeiro diagnóstico</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Plano de ativação")
    col_importar, col_manual, col_resultado = st.columns(3)
    with col_importar:
        st.markdown("**1. Trazer movimentações**")
        st.caption("Comece pelo PDF se tiver extrato ou fatura. É o caminho mais rápido para montar o histórico.")
        if st.button("Importar PDF", type="primary", use_container_width=True):
            _navegar_para_secao("Importação")
    with col_manual:
        st.markdown("**2. Completar lacunas**")
        st.caption("Use lançamento manual para salário, PIX, dinheiro ou qualquer item que não esteja no arquivo.")
        if st.button("Lançar manualmente", use_container_width=True):
            _navegar_para_secao("Transações")
    with col_resultado:
        st.markdown("**3. Revisar o mês**")
        st.caption("Com dados salvos, o painel mostra balanço, categorias e metas para acompanhar sua evolução.")

    st.info(
        "Dica: comece com poucas movimentações. O importante é gerar o primeiro resumo mensal e depois refinar os detalhes."
    )


def render_visao_geral(lista_total_banco, usuario_id, email_usuario):
    st.title("Visão Geral")
    lista_transacoes, mes_selecionado, meses_disponiveis = selecionar_mes(
        lista_total_banco,
        key="mes_visao_geral",
    )
    if not lista_transacoes:
        _render_estado_inicial()
        return

    df_mes = pd.DataFrame(lista_transacoes)
    resumo_mes = calcular_resumo_financeiro(lista_transacoes)
    total_compras = resumo_mes["despesas"]
    total_pagamentos = resumo_mes["receitas"]
    valor_balanco_final = resumo_mes["balanco"]
    tendencias = _calcular_tendencias(
        lista_total_banco,
        meses_disponiveis,
        mes_selecionado,
        resumo_mes,
        email_usuario,
    )

    _render_cards_resumo(total_compras, total_pagamentos, valor_balanco_final, tendencias)
    st.markdown("---")
    _render_metas(usuario_id, email_usuario, mes_selecionado, df_mes)
    st.markdown("---")
    _render_analise_categorias(df_mes, df_mes[df_mes["tipo"] == TIPO_DESPESA], email_usuario)
