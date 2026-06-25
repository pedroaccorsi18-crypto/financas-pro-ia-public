"""Matriz de estrategia patrimonial para planejamento financeiro 360."""

from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro
from utils.retirement_planning import calcular_planejamento_aposentadoria
from utils.stress_test import gerar_stress_test_financeiro
from utils.suitability import gerar_checklist_suitability


def gerar_matriz_estrategia_patrimonial(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    resumo_transacoes = resumo_transacoes or {}
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)
    aposentadoria = calcular_planejamento_aposentadoria(perfil)
    suitability = gerar_checklist_suitability(perfil, resumo_transacoes)
    stress = gerar_stress_test_financeiro(perfil, resumo_transacoes)

    frentes = [
        _frente_liquidez(diagnostico, stress),
        _frente_protecao(perfil, suitability),
        _frente_crescimento(perfil, diagnostico),
        _frente_aposentadoria(aposentadoria),
        _frente_sucessao(perfil),
    ]
    frentes_ordenadas = sorted(frentes, key=lambda frente: frente["prioridade"])
    return {
        "frentes": frentes_ordenadas,
        "foco_principal": frentes_ordenadas[0]["nome"],
        "postura_geral": _postura_geral(frentes_ordenadas, diagnostico),
    }


def _frente_liquidez(diagnostico, stress):
    if diagnostico["meses_reserva"] < 3 or stress["severidade_geral"] == "alto":
        return _frente(
            "Liquidez",
            "defensiva",
            "prioridade alta",
            "Reforcar reserva e preservar caixa antes de ampliar risco.",
            10,
        )
    if diagnostico["meses_reserva"] < 6:
        return _frente(
            "Liquidez",
            "equilibrada",
            "prioridade media",
            "Completar reserva ate nivel confortavel para o padrao de despesas.",
            25,
        )
    return _frente(
        "Liquidez",
        "monitoramento",
        "prioridade baixa",
        "Manter reserva segregada e revisar apenas diante de mudanca de vida.",
        60,
    )


def _frente_protecao(perfil, suitability):
    if perfil["dependentes"] > 0 and not perfil["possui_seguro"]:
        prioridade = 15
        postura = "defensiva"
        acao = "Avaliar protecao familiar, beneficiarios e continuidade de renda."
    elif suitability["alertas"]:
        prioridade = 35
        postura = "equilibrada"
        acao = "Resolver alertas de suitability antes de sofisticar a carteira."
    else:
        prioridade = 70
        postura = "monitoramento"
        acao = "Revisar protecao periodicamente e atualizar beneficiarios."
    return _frente("Protecao", postura, _texto_prioridade(prioridade), acao, prioridade)


def _frente_crescimento(perfil, diagnostico):
    if diagnostico["taxa_poupanca"] < 0.10:
        return _frente(
            "Crescimento patrimonial",
            "preparacao",
            "prioridade media",
            "Elevar capacidade de aporte antes de buscar expansao patrimonial.",
            40,
        )
    if perfil["perfil_risco"] == "Arrojado" and perfil["horizonte"] == "Acima de 10 anos":
        return _frente(
            "Crescimento patrimonial",
            "expansiva",
            "prioridade media",
            "Planejar diversificacao de longo prazo respeitando liquidez e concentracao.",
            45,
        )
    return _frente(
        "Crescimento patrimonial",
        "equilibrada",
        "prioridade media",
        "Alinhar carteira a objetivos, prazo, risco e rebalanceamento.",
        50,
    )


def _frente_aposentadoria(aposentadoria):
    if not aposentadoria["completo"]:
        return _frente(
            "Aposentadoria",
            "diagnostico",
            "prioridade media",
            "Definir idade e renda desejada para medir gap de aposentadoria.",
            30,
        )

    gap = aposentadoria["cenarios"]["Moderado"]["gap"]
    prioridade = 20 if gap > 0 else 55
    acao = (
        "Acompanhar gap e aporte mensal necessario para renda futura."
        if gap > 0
        else "Manter revisao periodica das premissas de renda, retorno e inflacao."
    )
    return _frente("Aposentadoria", "planejamento", _texto_prioridade(prioridade), acao, prioridade)


def _frente_sucessao(perfil):
    if perfil["patrimonio_sucessorio"] > 0 or perfil["dependentes"] > 0:
        return _frente(
            "Sucessao",
            "estruturacao",
            "prioridade media",
            "Mapear documentos, dependentes, beneficiarios e apoio juridico especializado.",
            35,
        )
    return _frente(
        "Sucessao",
        "monitoramento",
        "prioridade baixa",
        "Registrar inventario patrimonial basico e revisar eventos familiares.",
        80,
    )


def _postura_geral(frentes, diagnostico):
    primeira = frentes[0]
    if primeira["postura"] == "defensiva" or diagnostico["classificacao"] == "prioritario":
        return "Defensiva: estabilizar base financeira antes de expandir risco."
    if diagnostico["classificacao"] == "maduro":
        return "Estrategica: aprofundar eficiencia, crescimento e sucessao."
    return "Equilibrada: consolidar base e avancar por metas priorizadas."


def _texto_prioridade(prioridade):
    if prioridade <= 20:
        return "prioridade alta"
    if prioridade <= 55:
        return "prioridade media"
    return "prioridade baixa"


def _frente(nome, postura, prioridade_texto, acao, prioridade):
    return {
        "nome": nome,
        "postura": postura,
        "prioridade_texto": prioridade_texto,
        "acao": acao,
        "prioridade": prioridade,
    }
