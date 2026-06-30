"""Simulações simples para planejamento de aposentadoria."""

from utils.financial_profile import normalizar_perfil_financeiro


CENARIOS_APOSENTADORIA = {
    "Conservador": {"retorno_real_anual": 0.02, "taxa_retirada_anual": 0.035},
    "Moderado": {"retorno_real_anual": 0.04, "taxa_retirada_anual": 0.04},
    "Arrojado": {"retorno_real_anual": 0.055, "taxa_retirada_anual": 0.045},
}


def calcular_planejamento_aposentadoria(perfil):
    perfil = normalizar_perfil_financeiro(perfil)
    idade_atual = perfil["idade"]
    idade_alvo = perfil["idade_aposentadoria"]
    renda_desejada = perfil["renda_aposentadoria_desejada"]
    patrimonio_atual = perfil["patrimonio_investido"] + perfil["reserva_emergencia"]

    anos_ate_aposentadoria = max(0, idade_alvo - idade_atual) if idade_alvo else 0
    if not idade_atual or not idade_alvo or renda_desejada <= 0:
        return {
            "completo": False,
            "motivos_pendentes": _motivos_pendentes(perfil),
            "anos_ate_aposentadoria": anos_ate_aposentadoria,
            "cenarios": {},
        }

    cenarios = {}
    for nome, premissas in CENARIOS_APOSENTADORIA.items():
        patrimonio_necessario = _patrimonio_necessario(
            renda_desejada,
            premissas["taxa_retirada_anual"],
        )
        patrimonio_projetado = _valor_futuro(
            patrimonio_atual,
            premissas["retorno_real_anual"],
            anos_ate_aposentadoria,
        )
        gap = max(0.0, patrimonio_necessario - patrimonio_projetado)
        aporte_mensal = _aporte_mensal_necessario(
            gap,
            premissas["retorno_real_anual"],
            anos_ate_aposentadoria,
        )
        cenarios[nome] = {
            "retorno_real_anual": premissas["retorno_real_anual"],
            "taxa_retirada_anual": premissas["taxa_retirada_anual"],
            "patrimonio_necessario": patrimonio_necessario,
            "patrimonio_projetado": patrimonio_projetado,
            "gap": gap,
            "aporte_mensal_necessario": aporte_mensal,
        }

    return {
        "completo": True,
        "motivos_pendentes": [],
        "anos_ate_aposentadoria": anos_ate_aposentadoria,
        "renda_mensal_desejada": renda_desejada,
        "patrimonio_base": patrimonio_atual,
        "cenarios": cenarios,
        "observacoes": [
            "Valores em termos reais, antes de impostos, custos e mudanças familiares.",
            "Use como estimativa inicial para conversa consultiva, não como recomendação fechada.",
        ],
    }


def _motivos_pendentes(perfil):
    motivos = []
    if perfil["idade"] <= 0:
        motivos.append("Informar idade atual.")
    if perfil["idade_aposentadoria"] <= 0:
        motivos.append("Informar idade desejada para aposentadoria.")
    if perfil["renda_aposentadoria_desejada"] <= 0:
        motivos.append("Informar renda mensal desejada na aposentadoria.")
    return motivos


def _patrimonio_necessario(renda_mensal, taxa_retirada_anual):
    if taxa_retirada_anual <= 0:
        return 0.0
    return (renda_mensal * 12) / taxa_retirada_anual


def _valor_futuro(valor_presente, retorno_anual, anos):
    if anos <= 0:
        return valor_presente
    return valor_presente * ((1 + retorno_anual) ** anos)


def _aporte_mensal_necessario(gap, retorno_anual, anos):
    meses = anos * 12
    if gap <= 0:
        return 0.0
    if meses <= 0:
        return gap
    retorno_mensal = (1 + retorno_anual) ** (1 / 12) - 1
    if retorno_mensal <= 0:
        return gap / meses
    fator = (((1 + retorno_mensal) ** meses) - 1) / retorno_mensal
    return gap / fator
