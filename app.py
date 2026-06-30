import datetime
import logging

import pandas as pd
import plotly.express as px
import streamlit as st
from google.genai import types

from auth import (
    auditar_saude_plataforma,
    supabase,
    validar_chave_publica_supabase,
    validar_sessao_atual,
)
from finance_categories import CATEGORIAS_DESPESA, CATEGORIAS_VALIDAS
from finance_constants import (
    TIPO_DESPESA,
    TIPOS_TRANSACAO,
)
from finance_core import (
    calcular_resumo_financeiro,
    criar_lote_demonstrativo,
    lotes_sao_iguais,
    ordenar_meses_cronologicamente,
    resumir_historico_para_ia,
)
from repositories.finance_repository import (
    atualizar_categoria_transacao,
    buscar_lote_importado,
    buscar_perfil_financeiro_360,
    inserir_transacao,
    listar_metas_usuario_mes,
    listar_transacoes_usuario,
    salvar_feedback_oraculo,
    salvar_meta_financeira,
    salvar_perfil_financeiro_360,
    substituir_lote_importado,
)
from session_state import (
    encerrar_sessao_usuario,
    inicializar_estado_sessao,
    limpar_sessao_usuario,
)
from utils.ai_extraction import (
    carregar_resultado_extracao,
    montar_config_extracao_pdf,
    montar_prompt_extracao_pdf,
    normalizar_resultado_extracao,
)
from utils.audit import preparar_dataframe_auditoria_categoria
from utils.authorization import eh_usuario_admin
from utils.bot_fiscal import disparar_bot_fiscal_email
from utils.category_analysis import preparar_dados_analise_categorias
from utils.category_maintenance import (
    CATEGORIA_TRANSPORTE,
    carregar_mapa_reclassificacao,
    extrair_descricoes_para_reclassificar,
    montar_prompt_reclassificacao_categorias,
    preparar_atualizacoes_reclassificacao,
    selecionar_linhas_para_reclassificar,
    selecionar_transacoes_de_transporte,
)
from utils.error_handling import mostrar_erro_seguro
from utils.formatting import formatar_brl
from utils.gemini_client import (
    criar_cliente_gemini,
    gerar_conteudo_gemini as gerar_com_cliente_gemini,
)
from utils.goals import calcular_status_meta
from utils.history import formatar_linha_historico
from utils.import_workflow import processar_importacao_homologada
from utils.oracle_analysis import (
    montar_payload_feedback_oraculo,
    montar_prompt_oraculo,
    reforcar_prompt_oraculo,
    resposta_oraculo_tem_secoes,
)
from utils.privacy import anonimizar_dados
from utils.platform_health import gerar_health_check_supabase, resumir_health_check
from utils.trends import TENDENCIA_SEM_HISTORICO, calcular_textos_tendencia
from views.auth_views import render_fluxo_autenticacao
from views.financial_profile_views import render_perfil_financeiro_360
from views.sidebar_views import render_lancamento_manual

logger = logging.getLogger(__name__)


st.set_page_config(page_title="Finanças Pro IA", page_icon="💰", layout="wide")

try:
    validar_chave_publica_supabase(st.secrets["SUPABASE_KEY"])
except Exception:
    logger.critical("Chave Supabase insegura ou inválida configurada", exc_info=True)
    st.error("A configuração de acesso ao Supabase é insegura ou inválida.")
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


def _selecionar_mes(lista_total_banco, *, key):
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


def render_visao_geral(lista_total_banco, usuario_id, email_usuario):
    st.title("Visão Geral")
    lista_transacoes, mes_selecionado, meses_disponiveis = _selecionar_mes(
        lista_total_banco,
        key="mes_visao_geral",
    )
    if not lista_transacoes:
        st.info("Nenhum dado disponível. Adicione lançamentos manuais ou suba um PDF.")
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


def render_importacao(lista_total_banco, usuario_id, email_usuario, is_admin):
    st.title("Importação")
    st.markdown("### Importação Inteligente por IA")
    arquivo_subido = st.file_uploader(
        "Suba aqui o seu extrato bancário, fatura ou comprovante em formato PDF",
        type=["pdf"],
    )
    consentimento_pdf_ia = st.checkbox(
        "Autorizo o envio temporário deste PDF ao Google Gemini para extração dos dados.",
        help="O documento pode conter informações financeiras sensíveis. Envie somente se concordar com o processamento externo.",
    )

    if is_admin:
        with st.expander("Modo de teste sem Gemini"):
            st.caption("Cria uma fatura fictícia e usa exatamente o mesmo fluxo de salvamento da importação real.")
            mes_teste = st.text_input(
                "Mês do teste (MM/AAAA)",
                value=datetime.datetime.now().strftime("%m/%Y"),
                key="mes_importacao_teste",
            )
            if st.button("Gerar importação demonstrativa", key="gerar_importacao_demonstrativa"):
                try:
                    lote_teste = criar_lote_demonstrativo(mes_teste)
                    st.session_state.dados_pre_visualizacao = {
                        "instituicao": lote_teste["instituicao"],
                        "tipo_documento": lote_teste["tipo_documento"],
                        "mes_referencia": lote_teste["mes_referencia"],
                        "total_documento": lote_teste["total_documento"],
                        "df_transacoes": pd.DataFrame(lote_teste["transacoes"]),
                    }
                    st.toast("Importação demonstrativa criada.", icon="🧪")
                    st.rerun()
                except ValueError as erro_teste:
                    st.warning(str(erro_teste))

    if arquivo_subido is not None and st.button("Extrair Dados com Gemini IA"):
        if not consentimento_pdf_ia:
            st.warning("Confirme a autorização de processamento externo antes de enviar o PDF.")
        else:
            with st.spinner("O parser de visão computacional da IA está varrendo o PDF..."):
                try:
                    dados_pdf = arquivo_subido.read()
                    if len(dados_pdf) > 10 * 1024 * 1024:
                        raise ValueError("O PDF excede o limite de 10 MB.")

                    response = gerar_conteudo_gemini(
                        model="gemini-2.5-flash",
                        contents=[
                            types.Part.from_bytes(data=dados_pdf, mime_type="application/pdf"),
                            montar_prompt_extracao_pdf(),
                        ],
                        config=montar_config_extracao_pdf(types),
                    )
                    resultado_ia = carregar_resultado_extracao(response.text)
                    st.session_state.dados_pre_visualizacao = normalizar_resultado_extracao(
                        resultado_ia,
                        pd.DataFrame,
                    )
                    st.toast("Extração contábil finalizada!", icon="🪄")
                except Exception as erro:
                    st.error(mostrar_erro_seguro(erro, email_usuario))

    if st.session_state.dados_pre_visualizacao is not None:
        _render_homologacao_importacao(usuario_id, email_usuario)
    elif lista_total_banco:
        st.caption("Nenhuma importação pendente de homologação.")


def _render_homologacao_importacao(usuario_id, email_usuario):
    st.markdown("---")
    st.subheader("Área de Homologação e Pré-visualização Contábil")
    pre_vis = st.session_state.dados_pre_visualizacao
    mes_corrigido = st.text_input(
        "Mês de referência da importação (MM/AAAA)",
        value=str(pre_vis["mes_referencia"]),
        help="Confira este campo antes de salvar. Exemplo: 05/2026.",
    ).strip()
    pre_vis["mes_referencia"] = mes_corrigido

    c_meta1, c_meta2, c_meta3, c_meta4 = st.columns(4)
    with c_meta1:
        st.metric("Instituição Identificada", pre_vis["instituicao"])
    with c_meta2:
        st.metric("Tipo de Documento", pre_vis["tipo_documento"])
    with c_meta3:
        st.metric("Mês de Referência", pre_vis["mes_referencia"])
    with c_meta4:
        st.metric("Total Declarado Oficial", formatar_brl(pre_vis["total_documento"]))

    df_editavel = st.data_editor(
        pre_vis["df_transacoes"],
        column_config={
            "descricao": st.column_config.TextColumn(
                "Descrição da Transação",
                disabled=True,
                width="medium",
            ),
            "valor": st.column_config.NumberColumn("Valor (R$)", disabled=True, format="R$ %.2f"),
            "tipo": st.column_config.SelectboxColumn("Fluxo", options=TIPOS_TRANSACAO, required=True),
            "categoria": st.column_config.SelectboxColumn(
                "Classificação IA",
                options=CATEGORIAS_VALIDAS,
                required=True,
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="staging_data_editor",
    )

    col_btn1, col_btn2, _ = st.columns([15, 15, 70])
    with col_btn1:
        if st.button("Confirmar e Salvar no Supabase", type="primary", use_container_width=True):
            with st.spinner("Consolidando dados no Supabase..."):
                try:
                    processar_importacao_homologada(
                        df_editavel=df_editavel,
                        pre_visualizacao=pre_vis,
                        usuario_id=usuario_id,
                        email_usuario=email_usuario,
                        secrets=st.secrets,
                        buscar_lote=buscar_lote_importado,
                        lotes_sao_iguais=lotes_sao_iguais,
                        substituir_lote=substituir_lote_importado,
                        disparar_alerta=disparar_bot_fiscal_email,
                    )
                    st.toast("Registros integrados com sucesso!", icon="⚡")
                    st.session_state.dados_pre_visualizacao = None
                    st.rerun()
                except Exception as e_save:
                    st.error(mostrar_erro_seguro(e_save, email_usuario))

    with col_btn2:
        if st.button("Descartar Importação", use_container_width=True):
            st.session_state.dados_pre_visualizacao = None
            st.rerun()


def render_transacoes(lista_total_banco, usuario_id, email_usuario):
    render_lancamento_manual(
        usuario_id=usuario_id,
        email_usuario=email_usuario,
        inserir_transacao=inserir_transacao,
    )

    st.title("Transações")
    lista_transacoes, mes_selecionado, _ = _selecionar_mes(
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


def render_oraculo(lista_total_banco, usuario_id, email_usuario):
    st.title("Oráculo IA")
    st.caption(
        "A análise envia somente totais agregados por mês e categoria, sem descrições de transações."
    )
    col_gatilho, _ = st.columns([3, 7])
    with col_gatilho:
        ativar_oraculo = st.button("Ativar Inteligência Preditiva", use_container_width=True)

    if ativar_oraculo:
        if not lista_total_banco:
            st.warning("Histórico de transações necessário para análise preditiva.")
        else:
            with st.spinner("O Oráculo está consolidando o relatório comportamental..."):
                try:
                    st.session_state.feedback_enviado = False
                    historico_formatado = resumir_historico_para_ia(lista_total_banco)
                    st.session_state.historico_oraculo_enviado = historico_formatado
                    prompt_oraculo = montar_prompt_oraculo(historico_formatado)
                    resposta_oraculo = gerar_conteudo_gemini(
                        model="gemini-2.5-flash",
                        contents=prompt_oraculo,
                        config=types.GenerateContentConfig(temperature=0.1),
                    )
                    texto_final = resposta_oraculo.text

                    if not resposta_oraculo_tem_secoes(texto_final):
                        resposta_oraculo = gerar_conteudo_gemini(
                            model="gemini-2.5-flash",
                            contents=reforcar_prompt_oraculo(prompt_oraculo),
                            config=types.GenerateContentConfig(temperature=0.0),
                        )
                        texto_final = resposta_oraculo.text

                    st.session_state.resposta_oraculo_texto = texto_final
                except Exception as erro:
                    st.error(mostrar_erro_seguro(erro, email_usuario))

    if st.session_state.resposta_oraculo_texto:
        st.markdown("---")
        st.success("Relatório preditivo gerado com sucesso!")
        st.markdown(st.session_state.resposta_oraculo_texto)
        st.markdown("##### Avalie essa resposta da IA para calibragem do sistema:")
        col_fb1, col_fb2, _ = st.columns([1.5, 2, 6.5])

        if not st.session_state.feedback_enviado:
            with col_fb1:
                if st.button("Ficou Top", use_container_width=True):
                    _salvar_feedback_oraculo(usuario_id, email_usuario, "TOP")
            with col_fb2:
                if st.button("Resposta Ruim/Falsa", use_container_width=True):
                    _salvar_feedback_oraculo(usuario_id, email_usuario, "RUIM")
        else:
            st.info("Obrigado pelo feedback! Dados salvos na tabela 'feedbacks_oraculo'.")


def _salvar_feedback_oraculo(usuario_id, email_usuario, status_resposta):
    try:
        salvar_feedback_oraculo(
            montar_payload_feedback_oraculo(
                usuario_id=usuario_id,
                email_usuario=email_usuario,
                status_resposta=status_resposta,
                resposta_ia=st.session_state.resposta_oraculo_texto,
                dados_enviados=st.session_state.historico_oraculo_enviado,
                anonimizar=anonimizar_dados,
            )
        )
        st.session_state.feedback_enviado = True
        st.rerun()
    except Exception as erro:
        st.error(mostrar_erro_seguro(erro, email_usuario))


def render_admin(lista_total_banco, usuario_id, email_usuario):
    st.title("Admin")
    st.subheader("Painel do Desenvolvedor")
    if st.button("Corrigir Histórico Retroativo"):
        if not lista_total_banco:
            st.warning("Nenhum dado encontrado para higienização.")
        else:
            with st.spinner("Higienizando e processando lote via inteligência analítica..."):
                try:
                    for item in selecionar_transacoes_de_transporte(lista_total_banco):
                        atualizar_categoria_transacao(item["id"], CATEGORIA_TRANSPORTE)

                    linhas_para_atualizar = selecionar_linhas_para_reclassificar(lista_total_banco)
                    if descricoes := extrair_descricoes_para_reclassificar(linhas_para_atualizar):
                        prompt_lote = montar_prompt_reclassificacao_categorias(descricoes)
                        response_batch = gerar_conteudo_gemini(
                            model="gemini-2.5-flash",
                            contents=prompt_lote,
                            config=types.GenerateContentConfig(response_mime_type="application/json"),
                        )
                        mapa_categorias = carregar_mapa_reclassificacao(response_batch.text)
                        for item_id, categoria in preparar_atualizacoes_reclassificacao(
                            linhas_para_atualizar,
                            mapa_categorias,
                        ):
                            atualizar_categoria_transacao(item_id, categoria)

                    st.success("Histórico totalmente saneado!")
                    st.rerun()
                except Exception as erro:
                    st.error(mostrar_erro_seguro(erro, email_usuario))

    st.markdown("---")
    st.subheader("Status da Infraestrutura")
    status_infra = auditar_saude_plataforma()
    st.markdown(f"**Banco Supabase:** {status_infra['supabase']}")
    st.markdown(f"**Criptografia/SSL:** {status_infra['seguranca']}")

    st.markdown("### Health Check de Banco e Migrações")
    with st.spinner("Verificando estrutura operacional do Supabase..."):
        resultados_health = gerar_health_check_supabase(supabase, usuario_id)
    resumo_health = resumir_health_check(resultados_health)
    if resumo_health == "OK":
        st.success("Banco e objetos essenciais prontos.")
    elif resumo_health == "Ação necessária":
        st.warning("Há migrações ou objetos obrigatórios pendentes.")
    else:
        st.info("Há itens que exigem atenção operacional.")
    st.dataframe(resultados_health, use_container_width=True, hide_index=True)


def render_app_autenticado():
    email_usuario = st.session_state.usuario_email
    usuario_id = st.session_state.usuario_id
    lista_total_banco = _listar_transacoes_seguras(usuario_id, email_usuario)
    is_admin = eh_usuario_admin(email_usuario, st.secrets.get("ADMIN_EMAILS", []))

    st.sidebar.title("Navegação")
    st.sidebar.write(f"Usuário ativo: **{email_usuario}**")
    opcoes = [
        "Visão Geral",
        "Importação",
        "Transações",
        "Planejamento 360",
        "Oráculo IA",
    ]
    if is_admin:
        opcoes.append("Admin")
    secao = st.sidebar.radio("Área", opcoes, key="secao_principal")

    st.sidebar.markdown("---")
    if st.sidebar.button("Sair / Logout"):
        encerrar_sessao_usuario()
        st.rerun()

    if secao == "Visão Geral":
        render_visao_geral(lista_total_banco, usuario_id, email_usuario)
    elif secao == "Importação":
        render_importacao(lista_total_banco, usuario_id, email_usuario, is_admin)
    elif secao == "Transações":
        render_transacoes(lista_total_banco, usuario_id, email_usuario)
    elif secao == "Planejamento 360":
        render_planejamento_360(lista_total_banco, usuario_id, email_usuario)
    elif secao == "Oráculo IA":
        render_oraculo(lista_total_banco, usuario_id, email_usuario)
    elif secao == "Admin" and is_admin:
        render_admin(lista_total_banco, usuario_id, email_usuario)


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
