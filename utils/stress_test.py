"""Stress tests consultivos para avaliar resiliencia financeira."""

from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro


def gerar_stress_test_financeiro(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    resumo_transacoes = resumo_transacoes or {}
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)

    cenarios = [
        _cenario_perda_renda(perfil, resumo_transacoes),
        _cenario_aumento_despesas(perfil, resumo_transacoes),
        _cenario_queda_carteira(perfil),
        _cenario_emergencia_familiar(perfil, resumo_transacoes),
    ]
    severidade_geral = _severidade_geral(cenarios)

    return {
        "severidade_geral": severidade_geral,
        "reserva_meses": diagnostico["meses_reserva"],
        "cenarios": cenarios,
        "acoes_prioritarias": _acoes_prioritarias(cenarios, diagnostico),
    }


def _cenario_perda_renda(perfil, resumo_transacoes):
    renda = perfil["renda_mensal"]
    despesas = float(resumo_transacoes.get("despesas") or 0)
    perda_renda = renda * 0.30
    novo_balanco = renda - perda_renda - despesas

    return _cenario(
        "Perda de 30% da renda",
        impacto=max(0.0, perda_renda),
        severidade=_classificar_fluxo(novo_balanco, renda),
        leitura=f"Fluxo mensal projetado apos choque: {novo_balanco:.2f}.",
        acao="Revisar despesas fixas, renda alternativa e prazo da reserva.",
    )


def _cenario_aumento_despesas(perfil, resumo_transacoes):
    despesas = float(resumo_transacoes.get("despesas") or 0)
    aumento = despesas * 0.20
    reserva = perfil["reserva_emergencia"]
    meses_pos_choque = reserva / (despesas + aumento) if despesas + aumento > 0 else 0.0

    return _cenario(
        "Aumento de 20% das despesas",
        impacto=aumento,
        severidade=_classificar_reserva(meses_pos_choque),
        leitura=f"Reserva cairia para {meses_pos_choque:.1f} meses de despesas.",
        acao="Recalibrar reserva alvo e separar despesas essenciais das discricionarias.",
    )


def _cenario_queda_carteira(perfil):
    patrimonio = perfil["patrimonio_investido"]
    queda = patrimonio * 0.15
    patrimonio_pos_choque = patrimonio - queda
    severidade = "baixo"
    if perfil["perfil_risco"] == "Conservador" and queda > 0:
        severidade = "alto"
    elif perfil["horizonte"] in ("Ate 2 anos", "3 a 5 anos") and queda > 0:
        severidade = "medio"

    return _cenario(
        "Queda de 15% da carteira",
        impacto=queda,
        severidade=severidade,
        leitura=f"Patrimonio investido projetado apos choque: {patrimonio_pos_choque:.2f}.",
        acao="Checar concentracao, liquidez e compatibilidade entre risco e horizonte.",
    )


def _cenario_emergencia_familiar(perfil, resumo_transacoes):
    despesas = float(resumo_transacoes.get("despesas") or 0)
    dependentes = perfil["dependentes"]
    impacto = despesas * (2 if dependentes > 0 else 1)
    reserva_restante = perfil["reserva_emergencia"] - impacto
    severidade = "baixo"
    if reserva_restante < 0:
        severidade = "alto"
    elif dependentes > 0 and not perfil["possui_seguro"]:
        severidade = "medio"

    return _cenario(
        "Emergencia familiar",
        impacto=max(0.0, impacto),
        severidade=severidade,
        leitura=f"Reserva projetada apos emergencia: {reserva_restante:.2f}.",
        acao="Revisar protecao familiar, seguros, beneficiarios e caixa imediato.",
    )


def _cenario(nome, impacto, severidade, leitura, acao):
    return {
        "nome": nome,
        "impacto": impacto,
        "severidade": severidade,
        "leitura": leitura,
        "acao": acao,
    }


def _classificar_fluxo(novo_balanco, renda):
    if novo_balanco < 0:
        return "alto"
    if renda > 0 and novo_balanco < renda * 0.05:
        return "medio"
    return "baixo"


def _classificar_reserva(meses_reserva):
    if meses_reserva < 3:
        return "alto"
    if meses_reserva < 6:
        return "medio"
    return "baixo"


def _severidade_geral(cenarios):
    pesos = {"baixo": 1, "medio": 2, "alto": 3}
    maior = max(pesos[cenario["severidade"]] for cenario in cenarios)
    for nome, peso in pesos.items():
        if peso == maior:
            return nome
    return "baixo"


def _acoes_prioritarias(cenarios, diagnostico):
    acoes = []
    if diagnostico["meses_reserva"] < 6:
        acoes.append("Reforcar reserva antes de ampliar risco ou imobilizar capital.")
    for cenario in cenarios:
        if cenario["severidade"] == "alto":
            acoes.append(cenario["acao"])
    if not acoes:
        acoes.append("Manter revisao periodica dos choques e rebalancear premissas.")
    return _remover_duplicados(acoes)


def _remover_duplicados(itens):
    vistos = set()
    unicos = []
    for item in itens:
        if item not in vistos:
            vistos.add(item)
            unicos.append(item)
    return unicos
