"""Relatório consultivo 360 derivado do perfil financeiro."""

from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro


def gerar_relatorio_consultivo_360(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)

    return {
        "resumo_executivo": _montar_resumo_executivo(perfil, diagnostico),
        "diagnostico_patrimonial": _montar_diagnostico_patrimonial(perfil, diagnostico),
        "planejamento_financeiro": _montar_planejamento_financeiro(perfil, diagnostico),
        "aposentadoria": _montar_aposentadoria(perfil),
        "expansao_patrimonial": _montar_expansao_patrimonial(perfil, diagnostico),
        "sucessao": _montar_sucessao(perfil),
        "plano_30_60_90": _montar_plano_30_60_90(perfil, diagnostico),
    }


def _montar_resumo_executivo(perfil, diagnostico):
    return (
        f"Cliente com maturidade financeira {diagnostico['classificacao']} "
        f"({diagnostico['score']}/100), objetivo principal em "
        f"{perfil['objetivo_principal'].lower()} e perfil de risco "
        f"{perfil['perfil_risco'].lower()}."
    )


def _montar_diagnostico_patrimonial(perfil, diagnostico):
    linhas = [
        f"Patrimônio líquido estimado: {diagnostico['patrimonio_liquido']:.2f}.",
        f"Reserva estimada: {diagnostico['meses_reserva']:.1f} meses de despesas.",
        f"Taxa de poupança mensal estimada: {diagnostico['taxa_poupanca']*100:.1f}%.",
    ]
    if perfil["dependentes"] > 0 and not perfil["possui_seguro"]:
        linhas.append("Há dependentes sem proteção familiar declarada.")
    return linhas


def _montar_planejamento_financeiro(perfil, diagnostico):
    linhas = list(diagnostico["prioridades"])
    if perfil["renda_mensal"] <= 0:
        linhas.append("Registrar renda mensal para calibrar capacidade de aporte.")
    if perfil["dividas"] > 0:
        linhas.append("Separar dívidas por custo, prazo e garantia antes de investir mais.")
    return _remover_duplicados(linhas)


def _montar_aposentadoria(perfil):
    if perfil["idade_aposentadoria"] and perfil["renda_aposentadoria_desejada"]:
        anos = max(0, perfil["idade_aposentadoria"] - perfil["idade"])
        return [
            f"Horizonte até aposentadoria: {anos} anos.",
            "Projetar patrimônio necessário usando renda desejada, inflação e retorno real.",
            "Comparar aporte atual com aporte necessário para fechar o gap.",
        ]
    return [
        "Definir idade alvo e renda desejada para aposentadoria.",
        "Levantar patrimônio previdenciário, investimentos e benefícios esperados.",
    ]


def _montar_expansao_patrimonial(perfil, diagnostico):
    linhas = [
        f"Horizonte declarado: {perfil['horizonte']}.",
        f"Perfil de risco declarado: {perfil['perfil_risco']}.",
    ]
    if diagnostico["taxa_poupanca"] < 0.10:
        linhas.append("A expansão patrimonial depende primeiro de elevar a taxa de aporte.")
    else:
        linhas.append("Mapear carteira atual por classe, liquidez, moeda e concentração.")
    return linhas


def _montar_sucessao(perfil):
    linhas = [
        "Organizar inventário patrimonial e documentos essenciais.",
        "Mapear beneficiários, dependentes e poderes de decisão.",
    ]
    if perfil["patrimonio_sucessorio"] > 0:
        linhas.append("Avaliar estrutura sucessória com apoio jurídico especializado.")
    if perfil["dependentes"] > 0:
        linhas.append("Revisar proteção familiar e continuidade de renda para dependentes.")
    return linhas


def _montar_plano_30_60_90(perfil, diagnostico):
    return {
        "30_dias": [
            "Validar dados de renda, despesas, patrimônio, dívidas e dependentes.",
            diagnostico["prioridades"][0],
        ],
        "60_dias": [
            "Definir metas mensais de aporte, reserva e redução de risco.",
            "Levantar carteira atual e separar objetivos por prazo.",
        ],
        "90_dias": [
            "Consolidar política de investimentos alinhada ao perfil 360.",
            "Preparar revisão de aposentadoria, proteção e sucessão.",
        ],
    }


def _remover_duplicados(itens):
    vistos = set()
    unicos = []
    for item in itens:
        if item not in vistos:
            vistos.add(item)
            unicos.append(item)
    return unicos
