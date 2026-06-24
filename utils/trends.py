"""Formatacao das tendencias exibidas nos cards mensais."""


TENDENCIA_SEM_HISTORICO = (
    '<span style="color: #a1a1aa; font-size: 12px; font-weight: 500;">'
    "• Sem histórico base"
    "</span>"
)


def _span_tendencia(cor, simbolo, percentual):
    return (
        f'<span style="color: {cor}; font-size: 12px; font-weight: 600;">'
        f"{simbolo} {percentual:.1f}%"
        "</span>"
    )


def calcular_textos_tendencia(resumo_atual, resumo_anterior):
    txt_tendencia_gastos = TENDENCIA_SEM_HISTORICO
    txt_tendencia_pagamentos = TENDENCIA_SEM_HISTORICO
    txt_tendencia_balanco = TENDENCIA_SEM_HISTORICO

    total_compras = resumo_atual["despesas"]
    total_pagamentos = resumo_atual["receitas"]
    valor_balanco_final = resumo_atual["balanco"]

    gastos_ant = resumo_anterior["despesas"]
    pag_ant = resumo_anterior["receitas"]
    bal_ant = resumo_anterior["balanco"]

    if gastos_ant > 0:
        var_gastos = ((total_compras - gastos_ant) / gastos_ant) * 100
        txt_tendencia_gastos = (
            _span_tendencia("#a3b899", "▼", abs(var_gastos))
            if var_gastos < 0
            else _span_tendencia("#ef4444", "▲", var_gastos)
        )

    if pag_ant > 0:
        var_pag = ((total_pagamentos - pag_ant) / pag_ant) * 100
        txt_tendencia_pagamentos = (
            _span_tendencia("#a3b899", "▲", var_pag)
            if var_pag > 0
            else _span_tendencia("#ef4444", "▼", abs(var_pag))
        )

    if bal_ant > 0:
        var_bal = ((valor_balanco_final - bal_ant) / bal_ant) * 100
        txt_tendencia_balanco = (
            _span_tendencia("#a3b899", "▲", var_bal)
            if var_bal > 0
            else _span_tendencia("#ef4444", "▼", abs(var_bal))
        )

    return txt_tendencia_gastos, txt_tendencia_pagamentos, txt_tendencia_balanco
