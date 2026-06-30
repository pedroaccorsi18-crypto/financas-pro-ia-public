"""Perfil financeiro 360 para diagnóstico consultivo inicial."""


OBJETIVOS_360 = [
    "Organizar vida financeira",
    "Construir reserva de emergência",
    "Planejar aposentadoria",
    "Expandir patrimônio",
    "Preparar sucessão familiar",
]

PERFIS_RISCO = ["Conservador", "Moderado", "Arrojado"]

HORIZONTES_PLANEJAMENTO = ["Até 2 anos", "3 a 5 anos", "6 a 10 anos", "Acima de 10 anos"]


def _numero_nao_negativo(valor):
    try:
        return max(0.0, float(valor or 0))
    except (TypeError, ValueError):
        return 0.0


def _inteiro_nao_negativo(valor):
    try:
        return max(0, int(valor or 0))
    except (TypeError, ValueError):
        return 0


def normalizar_perfil_financeiro(dados):
    dados = dados or {}
    return {
        "idade": _inteiro_nao_negativo(dados.get("idade")),
        "dependentes": _inteiro_nao_negativo(dados.get("dependentes")),
        "renda_mensal": _numero_nao_negativo(dados.get("renda_mensal")),
        "reserva_emergencia": _numero_nao_negativo(dados.get("reserva_emergencia")),
        "patrimonio_investido": _numero_nao_negativo(dados.get("patrimonio_investido")),
        "dividas": _numero_nao_negativo(dados.get("dividas")),
        "idade_aposentadoria": _inteiro_nao_negativo(dados.get("idade_aposentadoria")),
        "renda_aposentadoria_desejada": _numero_nao_negativo(
            dados.get("renda_aposentadoria_desejada")
        ),
        "patrimonio_sucessorio": _numero_nao_negativo(dados.get("patrimonio_sucessorio")),
        "objetivo_principal": str(
            dados.get("objetivo_principal") or OBJETIVOS_360[0]
        ).strip(),
        "perfil_risco": str(dados.get("perfil_risco") or PERFIS_RISCO[1]).strip(),
        "horizonte": str(dados.get("horizonte") or HORIZONTES_PLANEJAMENTO[1]).strip(),
        "possui_seguro": bool(dados.get("possui_seguro")),
    }


def calcular_diagnostico_360(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    resumo_transacoes = resumo_transacoes or {}

    renda = perfil["renda_mensal"]
    despesas = _numero_nao_negativo(resumo_transacoes.get("despesas"))
    balanco = float(resumo_transacoes.get("balanco") or 0)
    reserva = perfil["reserva_emergencia"]
    dividas = perfil["dividas"]
    patrimonio = perfil["patrimonio_investido"]

    meses_reserva = reserva / despesas if despesas > 0 else 0.0
    taxa_poupanca = balanco / renda if renda > 0 else 0.0
    patrimonio_liquido = patrimonio + reserva - dividas

    score = 0
    if meses_reserva >= 6:
        score += 25
    elif meses_reserva >= 3:
        score += 18
    elif reserva > 0:
        score += 10

    if dividas == 0:
        score += 20
    elif renda > 0 and dividas <= renda * 3:
        score += 10

    if taxa_poupanca >= 0.20:
        score += 25
    elif taxa_poupanca >= 0.10:
        score += 18
    elif taxa_poupanca >= 0:
        score += 10

    if renda > 0 and patrimonio >= renda * 12:
        score += 20
    elif patrimonio > 0:
        score += 10

    if perfil["idade_aposentadoria"] and perfil["renda_aposentadoria_desejada"]:
        score += 10

    score = min(score, 100)
    if score >= 75:
        classificacao = "maduro"
    elif score >= 50:
        classificacao = "em evolução"
    else:
        classificacao = "prioritario"

    prioridades = []
    if despesas > 0 and meses_reserva < 3:
        prioridades.append("Reforçar reserva de emergência antes de assumir novos riscos.")
    if renda > 0 and dividas > renda * 3:
        prioridades.append("Estruturar plano de redução de dívidas de alto impacto.")
    if taxa_poupanca < 0.10:
        prioridades.append("Aumentar capacidade de aporte mensal para viabilizar objetivos.")
    if perfil["idade_aposentadoria"] and perfil["renda_aposentadoria_desejada"]:
        prioridades.append("Simular patrimônio necessário para aposentadoria desejada.")
    if perfil["patrimonio_sucessorio"] > 0:
        prioridades.append("Mapear documentos, beneficiários e riscos sucessórios.")
    if not prioridades:
        prioridades.append("Aprofundar alocação, proteção e eficiência tributária.")

    return {
        "score": score,
        "classificacao": classificacao,
        "meses_reserva": meses_reserva,
        "taxa_poupanca": taxa_poupanca,
        "patrimonio_liquido": patrimonio_liquido,
        "prioridades": prioridades,
    }
