import pandas as pd
import streamlit as st

from utils.market_radar import (
    filtrar_radar_mercado,
    gerar_radar_mercado,
    resumir_radar_mercado,
)


def render_radar_mercado():
    st.title("Radar de Mercado")
    st.caption(
        "Monitor demonstrativo de oportunidades em observacao. "
        "Nao usa dados em tempo real e nao constitui recomendacao individual de investimento."
    )

    radar = gerar_radar_mercado()
    resumo = resumir_radar_mercado(radar)

    col_total, col_forte, col_topo, col_risco = st.columns(4)
    col_total.metric("Ativos monitorados", resumo["total"])
    col_forte.metric("Radar forte", resumo["radar_forte"])
    col_topo.metric("Maior score", resumo["maior_score"] or "-")
    col_risco.metric("Risco medio", f"{resumo['risco_medio']}/100")

    st.markdown(
        """
        <div style="margin: 14px 0 18px; padding: 16px 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.10); background: rgba(255,255,255,0.035);">
            <strong>Como ler este radar:</strong> o score combina momentum, qualidade, valuation, liquidez e risco.
            Ele serve para priorizar estudos e conversas de planejamento, nao para indicar compra ou venda.
        </div>
        """,
        unsafe_allow_html=True,
    )

    classes = ["Todas", *sorted({item["classe"] for item in radar})]
    perfis = ["Todos", *sorted({item["perfil"] for item in radar})]
    col_classe, col_perfil = st.columns(2)
    with col_classe:
        classe = st.selectbox("Classe de ativo", classes)
    with col_perfil:
        perfil = st.selectbox("Perfil sugerido", perfis)

    radar_filtrado = filtrar_radar_mercado(radar, classe=classe, perfil=perfil)
    _render_tabela_radar(radar_filtrado)
    _render_cards_radar(radar_filtrado)

    st.info(
        "Versao demonstrativa: os dados sao simulados para validar produto e experiencia "
        "antes de contratar uma API de mercado."
    )


def _render_tabela_radar(radar):
    if not radar:
        st.warning("Nenhum ativo encontrado para os filtros selecionados.")
        return

    df = pd.DataFrame(
        [
            {
                "ticker": item["ticker"],
                "ativo": item["nome"],
                "classe": item["classe"],
                "mercado": item["mercado"],
                "perfil": item["perfil"],
                "score": item["score"],
                "status": item["status"],
                "risco": item["risco"],
            }
            for item in radar
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_cards_radar(radar):
    st.markdown("### Leituras do agente")
    for item in radar:
        cor = _cor_status(item["status"])
        st.markdown(
            f"""
            <div style="padding: 16px 18px; margin-bottom: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.09); background: linear-gradient(135deg, rgba(31,41,55,0.94), rgba(15,23,42,0.98));">
                <div style="display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap;">
                    <div>
                        <div style="font-size:13px; color:#a1a1aa; font-weight:700;">{item['ticker']} | {item['classe']} | {item['mercado']}</div>
                        <div style="font-size:20px; color:#ffffff; font-weight:900; margin-top:4px;">{item['nome']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:26px; color:{cor}; font-weight:900;">{item['score']}/100</div>
                        <div style="font-size:12px; color:#d4d4d8; font-weight:700;">{item['status']}</div>
                    </div>
                </div>
                <div style="margin-top:12px; color:#e5e7eb; line-height:1.45;">{item['tese']}</div>
                <div style="margin-top:10px; color:#fbbf24; line-height:1.4;"><strong>Riscos:</strong> {item['riscos']}</div>
                <div style="margin-top:10px; color:#a3b899; line-height:1.4;"><strong>Leitura operacional:</strong> {item['alerta']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _cor_status(status):
    if status == "Radar forte":
        return "#86efac"
    if status == "Monitorar":
        return "#facc15"
    return "#fca5a5"
