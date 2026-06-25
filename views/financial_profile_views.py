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
from utils.financial_report import gerar_relatorio_consultivo_360
from utils.goal_roadmap import gerar_roadmap_metas
from utils.retirement_planning import calcular_planejamento_aposentadoria
from utils.stress_test import gerar_stress_test_financeiro
from utils.suitability import gerar_checklist_suitability


PERFIL_SESSION_FIELD = "perfil_financeiro_360"


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

    with st.expander("Perfil Financeiro 360\u00ba", expanded=False):
        st.caption(
            "Base consultiva para planejamento financeiro, aposentadoria, expansao "
            "patrimonial e sucessao. Os dados ficam nesta sessao por enquanto."
        )

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
                    "Reserva de emergencia (R$)",
                    min_value=0.0,
                    value=perfil_atual["reserva_emergencia"],
                    format="%.2f",
                )
                dividas = st.number_input(
                    "Dividas totais (R$)",
                    min_value=0.0,
                    value=perfil_atual["dividas"],
                    format="%.2f",
                )
            with col_3:
                patrimonio_investido = st.number_input(
                    "Patrimonio investido (R$)",
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
                    "Patrimonio em planejamento sucessorio (R$)",
                    min_value=0.0,
                    value=perfil_atual["patrimonio_sucessorio"],
                    format="%.2f",
                )
                possui_seguro = st.checkbox(
                    "Possui seguro/protecao familiar",
                    value=perfil_atual["possui_seguro"],
                )

            if st.form_submit_button("Salvar Perfil 360\u00ba"):
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
                st.toast("Perfil Financeiro 360\u00ba atualizado.", icon="\U0001f3af")
                st.rerun()

        perfil_salvo = normalizar_perfil_financeiro(
            st.session_state.get(PERFIL_SESSION_FIELD, perfil_atual)
        )
        diagnostico = calcular_diagnostico_360(perfil_salvo, resumo_transacoes)
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Maturidade 360\u00ba", f"{diagnostico['score']}/100")
        col_b.metric("Reserva", f"{diagnostico['meses_reserva']:.1f} meses")
        col_c.metric("Taxa de poupanca", f"{diagnostico['taxa_poupanca']*100:.1f}%")
        col_d.metric(
            "Patrimonio liquido",
            formatar_brl(diagnostico["patrimonio_liquido"]),
        )

        st.markdown(f"**Classificacao:** {diagnostico['classificacao'].title()}")
        st.markdown("**Prioridades consultivas:**")
        for prioridade in diagnostico["prioridades"]:
            st.markdown(f"- {prioridade}")

        relatorio = gerar_relatorio_consultivo_360(perfil_salvo, resumo_transacoes)
        st.markdown("### Relatorio Consultivo 360")
        st.markdown(f"**Resumo executivo:** {relatorio['resumo_executivo']}")
        _render_lista("Diagnostico patrimonial", relatorio["diagnostico_patrimonial"])
        _render_lista("Planejamento financeiro", relatorio["planejamento_financeiro"])
        _render_lista("Aposentadoria", relatorio["aposentadoria"])
        _render_lista("Expansao patrimonial", relatorio["expansao_patrimonial"])
        _render_lista("Sucessao", relatorio["sucessao"])
        st.markdown("**Plano 30/60/90:**")
        for periodo, acoes in relatorio["plano_30_60_90"].items():
            st.markdown(f"- **{periodo.replace('_', ' ')}:** {'; '.join(acoes)}")

        politica_cliente = gerar_politica_planejamento_cliente(
            perfil_salvo,
            resumo_transacoes,
        )
        st.markdown("### Politica de Planejamento do Cliente")
        st.markdown(f"**Perfil consultivo:** {politica_cliente['perfil_consultivo']}")
        _render_lista("Objetivos priorizados", politica_cliente["objetivos_priorizados"])
        _render_lista("Diretrizes de alocacao", politica_cliente["diretrizes_de_alocacao"])
        _render_lista("Restricoes e alertas", politica_cliente["restricoes_e_alertas"])
        st.caption(politica_cliente["cadencia_de_revisao"])

        checklist_suitability = gerar_checklist_suitability(
            perfil_salvo,
            resumo_transacoes,
        )
        st.markdown("### Suitability e Onboarding")
        st.markdown(f"**Status:** {checklist_suitability['status'].title()}")
        _render_lista("Pendencias", checklist_suitability["pendencias"])
        _render_lista("Alertas", checklist_suitability["alertas"])
        _render_lista("Proximas perguntas", checklist_suitability["proximas_perguntas"])
        _render_lista("Documentos sugeridos", checklist_suitability["documentos_sugeridos"])

        roadmap_metas = gerar_roadmap_metas(perfil_salvo, resumo_transacoes)
        st.markdown("### Roadmap de Metas")
        st.caption(
            f"Capacidade mensal de aporte observada: "
            f"{formatar_brl(roadmap_metas['capacidade_aporte'])}"
        )
        _render_metas("Curto prazo", roadmap_metas["curto_prazo"], formatar_brl)
        _render_metas("Medio prazo", roadmap_metas["medio_prazo"], formatar_brl)
        _render_metas("Longo prazo", roadmap_metas["longo_prazo"], formatar_brl)

        stress_test = gerar_stress_test_financeiro(perfil_salvo, resumo_transacoes)
        st.markdown("### Stress Test Financeiro")
        st.markdown(f"**Severidade geral:** {stress_test['severidade_geral'].title()}")
        _render_cenarios_stress(stress_test["cenarios"], formatar_brl)
        _render_lista("Acoes prioritarias", stress_test["acoes_prioritarias"])

        roteiro_reuniao = gerar_roteiro_reuniao_consultiva(
            perfil_salvo,
            resumo_transacoes,
        )
        st.markdown("### Roteiro de Reuniao Consultiva")
        st.markdown(f"**Abertura:** {roteiro_reuniao['abertura']}")
        _render_lista("Perguntas-chave", roteiro_reuniao["perguntas_chave"])
        _render_lista("Decisoes da reuniao", roteiro_reuniao["decisoes_da_reuniao"])
        st.caption(roteiro_reuniao["fechamento"])

        resumo_executivo_exportavel = gerar_resumo_executivo_markdown(
            perfil_salvo,
            resumo_transacoes,
        )
        st.download_button(
            "Baixar resumo executivo",
            data=resumo_executivo_exportavel,
            file_name="resumo-executivo-planejamento-360.md",
            mime="text/markdown",
            use_container_width=True,
        )

        plano_aposentadoria = calcular_planejamento_aposentadoria(perfil_salvo)
        st.markdown("### Planejamento de Aposentadoria")
        if not plano_aposentadoria["completo"]:
            st.info("Complete os dados abaixo para simular aposentadoria:")
            for pendencia in plano_aposentadoria["motivos_pendentes"]:
                st.markdown(f"- {pendencia}")
        else:
            st.markdown(
                f"Anos ate aposentadoria: **{plano_aposentadoria['anos_ate_aposentadoria']}**"
            )
            for nome, cenario in plano_aposentadoria["cenarios"].items():
                st.markdown(f"**Cenario {nome}:**")
                st.markdown(
                    "- Patrimonio necessario: "
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


def _indice_ou_zero(opcoes, valor):
    try:
        return opcoes.index(valor)
    except ValueError:
        return 0


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
    st.markdown("**Cenarios:**")
    for cenario in cenarios:
        st.markdown(
            f"- **{cenario['nome']} ({cenario['severidade']}):** "
            f"impacto {formatar_brl(cenario['impacto'])}. "
            f"{cenario['leitura']} {cenario['acao']}"
        )
