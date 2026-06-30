from html import escape

import streamlit as st

from utils.advisory_meeting import gerar_roteiro_reuniao_consultiva
from utils.financial_profile import (
    HORIZONTES_PLANEJAMENTO,
    OBJETIVOS_360,
    PERFIS_RISCO,
    calcular_diagnostico_360,
    normalizar_perfil_financeiro,
)
from utils.client_policy import gerar_politica_planejamento_cliente
from utils.executive_summary import gerar_resumo_executivo_markdown
from utils.financial_methodology import gerar_metodologia_financeira
from utils.financial_report import gerar_relatorio_consultivo_360
from utils.goal_roadmap import gerar_roadmap_metas
from utils.retirement_planning import calcular_planejamento_aposentadoria
from utils.stress_test import gerar_stress_test_financeiro
from utils.suitability import gerar_checklist_suitability
from utils.wealth_strategy import gerar_matriz_estrategia_patrimonial


PERFIL_SESSION_FIELD = "perfil_financeiro_360"
ABAS_PLANEJAMENTO_360 = [
    "Diagnóstico",
    "Planejamento Financeiro",
    "Aposentadoria",
    "Expansão Patrimonial",
    "Sucessão",
    "Próxima Reunião",
]


def render_perfil_financeiro_360(
    *,
    resumo_transacoes,
    formatar_brl,
    usuario_id=None,
    perfil_persistido=None,
    salvar_perfil=None,
    mostrar_erro=None,
):
    perfil_atual = normalizar_perfil_financeiro(
        st.session_state.get(PERFIL_SESSION_FIELD, perfil_persistido or {})
    )

    st.caption(
        "Visão consultiva para diagnóstico, planejamento financeiro, aposentadoria, "
        "expansão patrimonial, sucessão e preparação da próxima reunião."
    )

    with st.expander("Dados do Perfil Financeiro 360º", expanded=False):
        st.caption(
            "Atualize as informações de base do cliente. Estes campos alimentam "
            "as análises consultivas e são preservados no perfil 360."
        )
        _render_formulario_perfil_360(
            perfil_atual=perfil_atual,
            usuario_id=usuario_id,
            salvar_perfil=salvar_perfil,
            mostrar_erro=mostrar_erro,
        )

    perfil_salvo = normalizar_perfil_financeiro(
        st.session_state.get(PERFIL_SESSION_FIELD, perfil_atual)
    )
    dados_consultivos = _preparar_dados_consultivos(
        perfil_salvo,
        resumo_transacoes,
    )
    _render_painel_executivo_360(dados_consultivos, formatar_brl)

    (
        aba_diagnostico,
        aba_planejamento,
        aba_aposentadoria,
        aba_expansao,
        aba_sucessao,
        aba_reuniao,
    ) = st.tabs(ABAS_PLANEJAMENTO_360)

    with aba_diagnostico:
        _render_aba_diagnostico(dados_consultivos, formatar_brl)

    with aba_planejamento:
        _render_aba_planejamento_financeiro(dados_consultivos, formatar_brl)

    with aba_aposentadoria:
        _render_aba_aposentadoria(dados_consultivos, formatar_brl)

    with aba_expansao:
        _render_aba_expansao_patrimonial(dados_consultivos, formatar_brl)

    with aba_sucessao:
        _render_aba_sucessao(dados_consultivos)

    with aba_reuniao:
        _render_aba_proxima_reuniao(dados_consultivos)


def _render_formulario_perfil_360(
    *,
    perfil_atual,
    usuario_id=None,
    salvar_perfil=None,
    mostrar_erro=None,
):
    with st.form("form_perfil_financeiro_360"):
        col_1, col_2, col_3 = st.columns(3)
        with col_1:
            idade = st.number_input(
                "Idade",
                min_value=0,
                max_value=120,
                value=perfil_atual["idade"],
                step=1,
            )
            dependentes = st.number_input(
                "Dependentes",
                min_value=0,
                max_value=20,
                value=perfil_atual["dependentes"],
                step=1,
            )
            objetivo_principal = st.selectbox(
                "Objetivo principal",
                OBJETIVOS_360,
                index=_indice_ou_zero(
                    OBJETIVOS_360,
                    perfil_atual["objetivo_principal"],
                ),
            )
        with col_2:
            renda_mensal = st.number_input(
                "Renda mensal familiar (R$)",
                min_value=0.0,
                value=perfil_atual["renda_mensal"],
                format="%.2f",
            )
            reserva_emergencia = st.number_input(
                "Reserva de emergência (R$)",
                min_value=0.0,
                value=perfil_atual["reserva_emergencia"],
                format="%.2f",
            )
            dividas = st.number_input(
                "Dívidas totais (R$)",
                min_value=0.0,
                value=perfil_atual["dividas"],
                format="%.2f",
            )
        with col_3:
            patrimonio_investido = st.number_input(
                "Patrimônio investido (R$)",
                min_value=0.0,
                value=perfil_atual["patrimonio_investido"],
                format="%.2f",
            )
            perfil_risco = st.selectbox(
                "Perfil de risco",
                PERFIS_RISCO,
                index=_indice_ou_zero(PERFIS_RISCO, perfil_atual["perfil_risco"]),
            )
            horizonte = st.selectbox(
                "Horizonte de planejamento",
                HORIZONTES_PLANEJAMENTO,
                index=_indice_ou_zero(
                    HORIZONTES_PLANEJAMENTO,
                    perfil_atual["horizonte"],
                ),
            )

        col_4, col_5, col_6 = st.columns(3)
        with col_4:
            idade_aposentadoria = st.number_input(
                "Idade desejada para aposentadoria",
                min_value=0,
                max_value=120,
                value=perfil_atual["idade_aposentadoria"],
                step=1,
            )
        with col_5:
            renda_aposentadoria_desejada = st.number_input(
                "Renda desejada na aposentadoria (R$)",
                min_value=0.0,
                value=perfil_atual["renda_aposentadoria_desejada"],
                format="%.2f",
            )
        with col_6:
            patrimonio_sucessorio = st.number_input(
                "Patrimônio em planejamento sucessório (R$)",
                min_value=0.0,
                value=perfil_atual["patrimonio_sucessorio"],
                format="%.2f",
            )
            possui_seguro = st.checkbox(
                "Possui seguro/proteção familiar",
                value=perfil_atual["possui_seguro"],
            )

        if st.form_submit_button("Salvar Perfil 360º"):
            perfil_normalizado = normalizar_perfil_financeiro(
                {
                    "idade": idade,
                    "dependentes": dependentes,
                    "renda_mensal": renda_mensal,
                    "reserva_emergencia": reserva_emergencia,
                    "dividas": dividas,
                    "patrimonio_investido": patrimonio_investido,
                    "objetivo_principal": objetivo_principal,
                    "perfil_risco": perfil_risco,
                    "horizonte": horizonte,
                    "idade_aposentadoria": idade_aposentadoria,
                    "renda_aposentadoria_desejada": renda_aposentadoria_desejada,
                    "patrimonio_sucessorio": patrimonio_sucessorio,
                    "possui_seguro": possui_seguro,
                }
            )
            st.session_state[PERFIL_SESSION_FIELD] = perfil_normalizado
            if salvar_perfil is not None and usuario_id:
                try:
                    salvar_perfil(
                        {
                            "user_id": usuario_id,
                            **perfil_normalizado,
                        }
                    )
                except Exception as erro:
                    if mostrar_erro is not None:
                        st.error(mostrar_erro(erro))
                    else:
                        raise
            st.toast("Perfil Financeiro 360º atualizado.", icon="🎯")
            st.rerun()


def _preparar_dados_consultivos(perfil_salvo, resumo_transacoes):
    return {
        "diagnostico": calcular_diagnostico_360(perfil_salvo, resumo_transacoes),
        "relatorio": gerar_relatorio_consultivo_360(perfil_salvo, resumo_transacoes),
        "politica_cliente": gerar_politica_planejamento_cliente(
            perfil_salvo,
            resumo_transacoes,
        ),
        "checklist_suitability": gerar_checklist_suitability(
            perfil_salvo,
            resumo_transacoes,
        ),
        "roadmap_metas": gerar_roadmap_metas(perfil_salvo, resumo_transacoes),
        "stress_test": gerar_stress_test_financeiro(perfil_salvo, resumo_transacoes),
        "roteiro_reuniao": gerar_roteiro_reuniao_consultiva(
            perfil_salvo,
            resumo_transacoes,
        ),
        "matriz_estrategia": gerar_matriz_estrategia_patrimonial(
            perfil_salvo,
            resumo_transacoes,
        ),
        "plano_aposentadoria": calcular_planejamento_aposentadoria(perfil_salvo),
        "resumo_executivo_exportavel": gerar_resumo_executivo_markdown(
            perfil_salvo,
            resumo_transacoes,
        ),
        "metodologia": gerar_metodologia_financeira(),
    }


def _render_painel_executivo_360(dados_consultivos, formatar_brl):
    diagnostico = dados_consultivos["diagnostico"]
    checklist_suitability = dados_consultivos["checklist_suitability"]
    plano_aposentadoria = dados_consultivos["plano_aposentadoria"]
    matriz_estrategia = dados_consultivos["matriz_estrategia"]
    roteiro_reuniao = dados_consultivos["roteiro_reuniao"]

    prioridade_principal = diagnostico["prioridades"][0]
    status_onboarding = checklist_suitability["status"].title()
    status_aposentadoria = "Completo" if plano_aposentadoria["completo"] else "Pendente"

    st.markdown("### Painel executivo do cliente")
    st.caption(
        "Leitura rápida para orientar a conversa consultiva antes de entrar nas abas detalhadas."
    )

    score_col, reserva_col, aporte_col, patrimonio_col = st.columns(4)
    score_col.metric("Score 360", f"{diagnostico['score']}/100")
    reserva_col.metric("Reserva", f"{diagnostico['meses_reserva']:.1f} meses")
    aporte_col.metric("Taxa de poupança", _formatar_percentual(diagnostico["taxa_poupanca"]))
    patrimonio_col.metric("Patrimônio líquido", formatar_brl(diagnostico["patrimonio_liquido"]))

    status_class = _classe_visual_360(diagnostico["classificacao"])
    st.markdown(
        f"""
        <div style="margin: 18px 0 12px; padding: 18px 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.10); background: linear-gradient(135deg, rgba(31,41,55,0.92), rgba(15,23,42,0.96));">
            <div style="display:flex; justify-content:space-between; gap:18px; align-items:flex-start; flex-wrap:wrap;">
                <div style="min-width:260px; flex:1;">
                    <div style="font-size:12px; color:#a3b899; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Próximo foco consultivo</div>
                    <div style="font-size:20px; color:#ffffff; font-weight:800; margin-top:6px;">{escape(prioridade_principal)}</div>
                    <div style="font-size:13px; color:#a1a1aa; margin-top:8px;">Use esta prioridade para abrir a próxima conversa e orientar o plano de ação.</div>
                </div>
                <div style="min-width:190px; padding:12px 14px; border-radius:8px; background:{status_class['bg']}; border:1px solid {status_class['border']};">
                    <div style="font-size:12px; color:#d4d4d8; font-weight:700;">Classificação</div>
                    <div style="font-size:22px; color:{status_class['color']}; font-weight:900; margin-top:2px;">{escape(diagnostico['classificacao'].title())}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    trilha_a, trilha_b, trilha_c, trilha_d = st.columns(4)
    _render_sinal_acao(
        trilha_a,
        "Onboarding",
        status_onboarding,
        "Documentos, pendências e perguntas-chave.",
    )
    _render_sinal_acao(
        trilha_b,
        "Aposentadoria",
        status_aposentadoria,
        "Simulação de gap e aporte mensal.",
    )
    _render_sinal_acao(
        trilha_c,
        "Estratégia",
        matriz_estrategia["foco_principal"],
        "Frentes patrimoniais priorizadas.",
    )
    _render_sinal_acao(
        trilha_d,
        "Próxima reunião",
        roteiro_reuniao["fechamento"],
        "Roteiro e resumo executivo exportável.",
    )
    st.markdown("---")


def _render_aba_diagnostico(dados_consultivos, formatar_brl):
    diagnostico = dados_consultivos["diagnostico"]
    relatorio = dados_consultivos["relatorio"]

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Maturidade 360º", f"{diagnostico['score']}/100")
    col_b.metric("Reserva", f"{diagnostico['meses_reserva']:.1f} meses")
    col_c.metric("Taxa de poupança", f"{diagnostico['taxa_poupanca']*100:.1f}%")
    col_d.metric(
        "Patrimônio líquido",
        formatar_brl(diagnostico["patrimonio_liquido"]),
    )

    st.markdown(f"**Classificação:** {diagnostico['classificacao'].title()}")
    st.markdown("**Prioridades consultivas:**")
    for prioridade in diagnostico["prioridades"]:
        st.markdown(f"- {prioridade}")

    st.markdown("### Leitura consultiva 360")
    st.markdown(f"**Resumo executivo:** {relatorio['resumo_executivo']}")
    _render_lista("Diagnóstico patrimonial", relatorio["diagnostico_patrimonial"])


def _render_aba_planejamento_financeiro(dados_consultivos, formatar_brl):
    politica_cliente = dados_consultivos["politica_cliente"]
    roadmap_metas = dados_consultivos["roadmap_metas"]
    relatorio = dados_consultivos["relatorio"]

    st.markdown("### Política de Planejamento do Cliente")
    st.markdown(f"**Perfil consultivo:** {politica_cliente['perfil_consultivo']}")
    _render_lista("Objetivos priorizados", politica_cliente["objetivos_priorizados"])
    _render_lista("Diretrizes de alocação", politica_cliente["diretrizes_de_alocacao"])
    _render_lista("Restrições e alertas", politica_cliente["restricoes_e_alertas"])
    st.caption(politica_cliente["cadencia_de_revisao"])

    st.markdown("### Roadmap de Metas")
    st.caption(
        f"Capacidade mensal de aporte observada: "
        f"{formatar_brl(roadmap_metas['capacidade_aporte'])}"
    )
    _render_metas("Curto prazo", roadmap_metas["curto_prazo"], formatar_brl)
    _render_metas("Médio prazo", roadmap_metas["medio_prazo"], formatar_brl)
    _render_metas("Longo prazo", roadmap_metas["longo_prazo"], formatar_brl)

    _render_lista("Planejamento financeiro", relatorio["planejamento_financeiro"])
    st.markdown("### Plano 30/60/90")
    for periodo, acoes in relatorio["plano_30_60_90"].items():
        st.markdown(f"- **{periodo.replace('_', ' ')}:** {'; '.join(acoes)}")


def _render_aba_aposentadoria(dados_consultivos, formatar_brl):
    _render_lista("Análise de aposentadoria", dados_consultivos["relatorio"]["aposentadoria"])
    _render_planejamento_aposentadoria(
        dados_consultivos["plano_aposentadoria"],
        formatar_brl,
    )
    with st.expander("Premissas de aposentadoria", expanded=False):
        _render_premissas_aposentadoria(dados_consultivos["metodologia"]["aposentadoria"])


def _render_aba_expansao_patrimonial(dados_consultivos, formatar_brl):
    relatorio = dados_consultivos["relatorio"]
    matriz_estrategia = dados_consultivos["matriz_estrategia"]
    stress_test = dados_consultivos["stress_test"]

    _render_lista("Expansão patrimonial", relatorio["expansao_patrimonial"])

    st.markdown("### Matriz de Estratégia Patrimonial")
    st.markdown(f"**Foco principal:** {matriz_estrategia['foco_principal']}")
    st.caption(matriz_estrategia["postura_geral"])
    _render_frentes_estrategia(matriz_estrategia["frentes"])

    st.markdown("### Stress Test Financeiro")
    st.markdown(f"**Severidade geral:** {stress_test['severidade_geral'].title()}")
    _render_cenarios_stress(stress_test["cenarios"], formatar_brl)
    _render_lista("Ações prioritárias", stress_test["acoes_prioritarias"])


def _render_aba_sucessao(dados_consultivos):
    relatorio = dados_consultivos["relatorio"]
    checklist_suitability = dados_consultivos["checklist_suitability"]

    _render_lista("Sucessão", relatorio["sucessao"])

    st.markdown("### Suitability e Onboarding")
    st.markdown(f"**Status:** {checklist_suitability['status'].title()}")
    _render_lista("Pendências", checklist_suitability["pendencias"])
    _render_lista("Alertas", checklist_suitability["alertas"])
    _render_lista("Próximas perguntas", checklist_suitability["proximas_perguntas"])
    _render_lista("Documentos sugeridos", checklist_suitability["documentos_sugeridos"])


def _render_aba_proxima_reuniao(dados_consultivos):
    roteiro_reuniao = dados_consultivos["roteiro_reuniao"]
    metodologia = dados_consultivos["metodologia"]

    st.markdown("### Roteiro da Próxima Reunião")
    st.markdown(f"**Abertura:** {roteiro_reuniao['abertura']}")
    _render_lista("Perguntas-chave", roteiro_reuniao["perguntas_chave"])
    _render_lista("Pontos de atenção", roteiro_reuniao["pontos_de_atencao"])
    _render_lista("Decisões da reunião", roteiro_reuniao["decisoes_da_reuniao"])
    st.caption(roteiro_reuniao["fechamento"])

    st.markdown("### Resumo Executivo Exportável")
    st.caption(
        "Documento em Markdown para preparar reunião, entrevista ou registro consultivo."
    )
    st.download_button(
        "Baixar resumo executivo",
        data=dados_consultivos["resumo_executivo_exportavel"],
        file_name="resumo-executivo-planejamento-360.md",
        mime="text/markdown",
        use_container_width=True,
    )

    with st.expander("Metodologia e premissas", expanded=False):
        _render_lista("Escopo", metodologia["escopo"])
        _render_premissas_stress(metodologia["stress_test"])
        _render_lista("Limites", metodologia["limites"])


def _indice_ou_zero(opcoes, valor):
    try:
        return opcoes.index(valor)
    except ValueError:
        return 0


def _formatar_percentual(valor):
    return f"{valor * 100:.1f}%"


def _classe_visual_360(classificacao):
    if classificacao == "maduro":
        return {
            "bg": "rgba(22, 101, 52, 0.22)",
            "border": "rgba(74, 222, 128, 0.35)",
            "color": "#86efac",
        }
    if classificacao == "em evolução":
        return {
            "bg": "rgba(113, 63, 18, 0.24)",
            "border": "rgba(251, 191, 36, 0.32)",
            "color": "#facc15",
        }
    return {
        "bg": "rgba(127, 29, 29, 0.24)",
        "border": "rgba(248, 113, 113, 0.34)",
        "color": "#fca5a5",
    }


def _render_sinal_acao(coluna, titulo, valor, legenda):
    with coluna:
        st.markdown(
            f"""
            <div style="min-height:128px; padding:15px 16px; border-radius:9px; border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.035);">
                <div style="font-size:12px; color:#a3b899; font-weight:800; text-transform:uppercase; letter-spacing:.06em;">{escape(titulo)}</div>
                <div style="font-size:16px; color:#ffffff; font-weight:800; margin-top:8px; line-height:1.25;">{escape(valor)}</div>
                <div style="font-size:12px; color:#a1a1aa; margin-top:8px; line-height:1.35;">{escape(legenda)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_lista(titulo, itens):
    st.markdown(f"**{titulo}:**")
    for item in itens:
        st.markdown(f"- {item}")


def _render_metas(titulo, metas, formatar_brl):
    if not metas:
        return
    st.markdown(f"**{titulo}:**")
    for meta in metas:
        st.markdown(
            f"- **{meta['nome']}:** {meta['descricao']} "
            f"Alvo: {formatar_brl(meta['valor_alvo'])}. {meta['racional']}"
        )


def _render_cenarios_stress(cenarios, formatar_brl):
    st.markdown("**Cenários:**")
    for cenario in cenarios:
        st.markdown(
            f"- **{cenario['nome']} ({cenario['severidade']}):** "
            f"impacto {formatar_brl(cenario['impacto'])}. "
            f"{cenario['leitura']} {cenario['acao']}"
        )


def _render_planejamento_aposentadoria(plano_aposentadoria, formatar_brl):
    st.markdown("### Planejamento de Aposentadoria")
    if not plano_aposentadoria["completo"]:
        st.info("Complete os dados abaixo para simular aposentadoria:")
        for pendencia in plano_aposentadoria["motivos_pendentes"]:
            st.markdown(f"- {pendencia}")
        return

    st.markdown(
        f"Anos até aposentadoria: **{plano_aposentadoria['anos_ate_aposentadoria']}**"
    )
    for nome, cenario in plano_aposentadoria["cenarios"].items():
        st.markdown(f"**Cenário {nome}:**")
        st.markdown(
            "- Patrimônio necessário: "
            f"{formatar_brl(cenario['patrimonio_necessario'])}"
        )
        st.markdown(
            "- Gap estimado: "
            f"{formatar_brl(cenario['gap'])}"
        )
        st.markdown(
            "- Aporte mensal estimado: "
            f"{formatar_brl(cenario['aporte_mensal_necessario'])}"
        )
    for observacao in plano_aposentadoria["observacoes"]:
        st.caption(observacao)


def _render_premissas_aposentadoria(premissas):
    st.markdown("**Aposentadoria:**")
    for item in premissas:
        retorno = item["retorno_real_anual"] * 100
        retirada = item["taxa_retirada_anual"] * 100
        st.markdown(
            f"- **{item['cenario']}:** retorno real anual {retorno:.1f}% "
            f"e taxa de retirada {retirada:.1f}% ao ano."
        )


def _render_premissas_stress(premissas):
    st.markdown("**Stress test:**")
    for item in premissas:
        st.markdown(f"- **{item['nome']}:** {item['premissa']}")


def _render_frentes_estrategia(frentes):
    st.markdown("**Frentes:**")
    for frente in frentes:
        st.markdown(
            f"- **{frente['nome']}:** {frente['prioridade_texto']}, "
            f"postura {frente['postura']}. {frente['acao']}"
        )
