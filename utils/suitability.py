"""Checklist de suitability e onboarding para planejamento financeiro."""

from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro


def gerar_checklist_suitability(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)

    pendencias = _pendencias(perfil, resumo_transacoes or {}, diagnostico)
    alertas = _alertas(perfil, diagnostico)
    proximas_perguntas = _proximas_perguntas(perfil, diagnostico)

    return {
        "status": _status(pendencias, alertas),
        "pendencias": pendencias,
        "alertas": alertas,
        "proximas_perguntas": proximas_perguntas,
        "documentos_sugeridos": _documentos_sugeridos(perfil),
    }


def _status(pendencias, alertas):
    if len(pendencias) >= 4 or len(alertas) >= 3:
        return "incompleto"
    if pendencias or alertas:
        return "em validacao"
    return "pronto para planejamento"


def _pendencias(perfil, resumo_transacoes, diagnostico):
    pendencias = []
    if perfil["idade"] <= 0:
        pendencias.append("Confirmar idade e fase de vida do cliente.")
    if perfil["renda_mensal"] <= 0:
        pendencias.append("Confirmar renda mensal familiar.")
    if resumo_transacoes.get("despesas", 0) <= 0:
        pendencias.append("Validar despesas mensais recorrentes.")
    if perfil["patrimonio_investido"] <= 0:
        pendencias.append("Levantar carteira atual e patrimonio investido.")
    if perfil["idade_aposentadoria"] <= 0 or perfil["renda_aposentadoria_desejada"] <= 0:
        pendencias.append("Definir meta de aposentadoria: idade e renda desejada.")
    if perfil["dependentes"] > 0 and not perfil["possui_seguro"]:
        pendencias.append("Mapear protecao familiar para dependentes.")
    if diagnostico["taxa_poupanca"] < 0:
        pendencias.append("Reconciliar fluxo mensal antes de definir novos aportes.")
    return pendencias


def _alertas(perfil, diagnostico):
    alertas = []
    if diagnostico["meses_reserva"] < 3:
        alertas.append("Reserva de emergencia abaixo de 3 meses.")
    if perfil["renda_mensal"] > 0 and perfil["dividas"] > perfil["renda_mensal"] * 3:
        alertas.append("Dividas acima de 3 meses de renda.")
    if perfil["perfil_risco"] == "Arrojado" and diagnostico["meses_reserva"] < 6:
        alertas.append("Perfil arrojado exige checagem de liquidez antes de elevar risco.")
    if perfil["patrimonio_sucessorio"] > 0:
        alertas.append("Planejamento sucessorio depende de validacao juridica especializada.")
    return alertas


def _proximas_perguntas(perfil, diagnostico):
    perguntas = [
        "Quais objetivos tem prazo, valor alvo e prioridade familiar?",
        "Existe concentracao relevante em empresa, imovel, moeda ou unico ativo?",
    ]
    if perfil["dividas"] > 0:
        perguntas.append("Qual custo efetivo, prazo e garantia das dividas atuais?")
    if diagnostico["taxa_poupanca"] < 0.10:
        perguntas.append("Quais despesas podem ser revistas para elevar capacidade de aporte?")
    if perfil["dependentes"] > 0:
        perguntas.append("Quem depende da renda do cliente e por quanto tempo?")
    return perguntas


def _documentos_sugeridos(perfil):
    documentos = [
        "Extratos consolidados de investimentos.",
        "Resumo de receitas e despesas dos ultimos 3 a 6 meses.",
        "Declaracao de imposto de renda mais recente.",
    ]
    if perfil["dividas"] > 0:
        documentos.append("Contratos ou demonstrativos das dividas.")
    if perfil["dependentes"] > 0 or perfil["possui_seguro"]:
        documentos.append("Apolices de seguro e beneficiarios cadastrados.")
    if perfil["patrimonio_sucessorio"] > 0:
        documentos.append("Documentos patrimoniais e sucessorios existentes.")
    return documentos
