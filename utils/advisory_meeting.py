"""Roteiro de conversa consultiva para planejamento financeiro."""

from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro
from utils.goal_roadmap import gerar_roadmap_metas
from utils.stress_test import gerar_stress_test_financeiro
from utils.suitability import gerar_checklist_suitability


def gerar_roteiro_reuniao_consultiva(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    resumo_transacoes = resumo_transacoes or {}
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)
    suitability = gerar_checklist_suitability(perfil, resumo_transacoes)
    roadmap = gerar_roadmap_metas(perfil, resumo_transacoes)
    stress = gerar_stress_test_financeiro(perfil, resumo_transacoes)

    return {
        "abertura": _abertura(perfil, diagnostico, suitability),
        "perguntas_chave": _perguntas_chave(perfil, suitability, stress),
        "pontos_de_atencao": _pontos_de_atencao(diagnostico, suitability, stress),
        "decisoes_da_reuniao": _decisoes_da_reuniao(roadmap, suitability),
        "fechamento": _fechamento(diagnostico, stress),
    }


def _abertura(perfil, diagnostico, suitability):
    return (
        f"Validar objetivo principal em {perfil['objetivo_principal'].lower()}, "
        f"maturidade {diagnostico['classificacao']} e status de onboarding "
        f"{suitability['status']} antes de propor proximos passos."
    )


def _perguntas_chave(perfil, suitability, stress):
    perguntas = list(suitability["proximas_perguntas"][:3])
    if perfil["idade_aposentadoria"] and perfil["renda_aposentadoria_desejada"]:
        perguntas.append("A renda desejada na aposentadoria considera inflacao, saude e dependentes?")
    else:
        perguntas.append("Qual idade e renda mensal fariam a aposentadoria ser confortavel?")
    if stress["severidade_geral"] != "baixo":
        perguntas.append("Qual choque financeiro seria mais dificil de absorver hoje?")
    return _remover_duplicados(perguntas)


def _pontos_de_atencao(diagnostico, suitability, stress):
    pontos = []
    pontos.extend(diagnostico["prioridades"][:2])
    pontos.extend(suitability["alertas"][:2])
    if stress["severidade_geral"] != "baixo":
        pontos.append(f"Stress test com severidade {stress['severidade_geral']}.")
    if not pontos:
        pontos.append("Cliente sem alertas criticos; aprofundar eficiencia e rebalanceamento.")
    return _remover_duplicados(pontos)


def _decisoes_da_reuniao(roadmap, suitability):
    decisoes = []
    for meta in roadmap["metas"][:3]:
        decisoes.append(f"Confirmar prioridade da meta: {meta['nome']}.")
    for pendencia in suitability["pendencias"][:2]:
        decisoes.append(f"Definir responsavel por: {pendencia}")
    if not decisoes:
        decisoes.append("Confirmar cadencia de revisao e indicadores de acompanhamento.")
    return _remover_duplicados(decisoes)


def _fechamento(diagnostico, stress):
    if stress["severidade_geral"] == "alto":
        return "Fechar com plano de estabilizacao antes de novas alocacoes de risco."
    if diagnostico["classificacao"] == "maduro":
        return "Fechar com revisao de carteira, sucessao e eficiencia tributaria."
    return "Fechar com plano de 30 dias para validar dados, metas e capacidade de aporte."


def _remover_duplicados(itens):
    vistos = set()
    unicos = []
    for item in itens:
        if item not in vistos:
            vistos.add(item)
            unicos.append(item)
    return unicos
