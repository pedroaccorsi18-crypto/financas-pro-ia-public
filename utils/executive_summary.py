"""Resumo executivo exportavel para conversa de planejamento financeiro."""

from utils.advisory_meeting import gerar_roteiro_reuniao_consultiva
from utils.client_policy import gerar_politica_planejamento_cliente
from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro
from utils.financial_report import gerar_relatorio_consultivo_360
from utils.goal_roadmap import gerar_roadmap_metas
from utils.retirement_planning import calcular_planejamento_aposentadoria
from utils.stress_test import gerar_stress_test_financeiro
from utils.suitability import gerar_checklist_suitability


def gerar_resumo_executivo_markdown(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    resumo_transacoes = resumo_transacoes or {}
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)
    relatorio = gerar_relatorio_consultivo_360(perfil, resumo_transacoes)
    politica = gerar_politica_planejamento_cliente(perfil, resumo_transacoes)
    aposentadoria = calcular_planejamento_aposentadoria(perfil)
    suitability = gerar_checklist_suitability(perfil, resumo_transacoes)
    roadmap = gerar_roadmap_metas(perfil, resumo_transacoes)
    stress = gerar_stress_test_financeiro(perfil, resumo_transacoes)
    reuniao = gerar_roteiro_reuniao_consultiva(perfil, resumo_transacoes)

    secoes = [
        "# Resumo Executivo - Planejamento Financeiro 360",
        "",
        "## 1. Perfil do cliente",
        f"- Maturidade financeira: {diagnostico['classificacao']} ({diagnostico['score']}/100)",
        f"- Objetivo principal: {perfil['objetivo_principal']}",
        f"- Perfil de risco: {perfil['perfil_risco']}",
        f"- Horizonte de planejamento: {perfil['horizonte']}",
        f"- Patrimonio liquido estimado: {_formatar_brl(diagnostico['patrimonio_liquido'])}",
        f"- Reserva estimada: {diagnostico['meses_reserva']:.1f} meses de despesas",
        "",
        "## 2. Tese consultiva",
        relatorio["resumo_executivo"],
        politica["perfil_consultivo"],
        "",
        "## 3. Prioridades",
        *_linhas_lista(diagnostico["prioridades"]),
        "",
        "## 4. Politica de planejamento",
        *_linhas_lista(politica["diretrizes_de_alocacao"]),
        "",
        "## 5. Aposentadoria",
        *_linhas_aposentadoria(aposentadoria),
        "",
        "## 6. Sucessao e protecao",
        *_linhas_lista(relatorio["sucessao"]),
        "",
        "## 7. Suitability e onboarding",
        f"- Status: {suitability['status']}",
        *_linhas_lista(suitability["pendencias"][:4]),
        *_linhas_lista(suitability["alertas"][:4]),
        "",
        "## 8. Roadmap de metas",
        *_linhas_roadmap(roadmap["metas"][:5]),
        "",
        "## 9. Stress test",
        f"- Severidade geral: {stress['severidade_geral']}",
        *_linhas_stress(stress["cenarios"]),
        "",
        "## 10. Preparacao da reuniao",
        f"- Abertura: {reuniao['abertura']}",
        *_linhas_lista(reuniao["perguntas_chave"][:3]),
        f"- Fechamento: {reuniao['fechamento']}",
        "",
        "## 11. Proximos 90 dias",
        *_linhas_plano_90(relatorio["plano_30_60_90"]),
        "",
        "## Observacao",
        (
            "Material consultivo para planejamento financeiro. "
            "Nao constitui recomendacao individualizada de investimento, juridica ou tributaria."
        ),
    ]
    return "\n".join(secoes).strip() + "\n"


def _linhas_lista(itens):
    return [f"- {item}" for item in itens]


def _linhas_plano_90(plano):
    linhas = []
    for periodo, acoes in plano.items():
        titulo = periodo.replace("_", " ")
        linhas.append(f"- {titulo}: {'; '.join(acoes)}")
    return linhas


def _linhas_roadmap(metas):
    if not metas:
        return ["- Sem metas pendentes a partir dos dados informados."]
    return [
        f"- {meta['prazo']}: {meta['nome']} - {meta['descricao']}"
        for meta in metas
    ]


def _linhas_stress(cenarios):
    return [
        f"- {cenario['nome']}: {cenario['severidade']} - {cenario['acao']}"
        for cenario in cenarios[:4]
    ]


def _linhas_aposentadoria(aposentadoria):
    if not aposentadoria["completo"]:
        return _linhas_lista(aposentadoria["motivos_pendentes"])

    moderado = aposentadoria["cenarios"]["Moderado"]
    return [
        f"- Anos ate aposentadoria: {aposentadoria['anos_ate_aposentadoria']}",
        f"- Renda mensal desejada: {_formatar_brl(aposentadoria['renda_mensal_desejada'])}",
        f"- Patrimonio necessario estimado: {_formatar_brl(moderado['patrimonio_necessario'])}",
        f"- Gap estimado no cenario moderado: {_formatar_brl(moderado['gap'])}",
        f"- Aporte mensal estimado: {_formatar_brl(moderado['aporte_mensal_necessario'])}",
    ]


def _formatar_brl(valor):
    numero = float(valor or 0)
    texto = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"
