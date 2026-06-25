"""Diretrizes consultivas para politica de planejamento do cliente."""

from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro


def gerar_politica_planejamento_cliente(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)

    return {
        "perfil_consultivo": _perfil_consultivo(perfil, diagnostico),
        "objetivos_priorizados": _objetivos_priorizados(perfil, diagnostico),
        "diretrizes_de_alocacao": _diretrizes_de_alocacao(perfil, diagnostico),
        "restricoes_e_alertas": _restricoes_e_alertas(perfil, diagnostico),
        "cadencia_de_revisao": _cadencia_de_revisao(diagnostico),
    }


def _perfil_consultivo(perfil, diagnostico):
    return (
        f"Perfil {perfil['perfil_risco'].lower()}, horizonte {perfil['horizonte'].lower()}, "
        f"maturidade {diagnostico['classificacao']} e objetivo central em "
        f"{perfil['objetivo_principal'].lower()}."
    )


def _objetivos_priorizados(perfil, diagnostico):
    objetivos = []
    if diagnostico["meses_reserva"] < 3:
        objetivos.append("Estabilizar liquidez antes de ampliar risco de mercado.")
    if perfil["dividas"] > 0:
        objetivos.append("Reduzir dividas por custo, prazo e impacto no fluxo mensal.")
    if perfil["idade_aposentadoria"] and perfil["renda_aposentadoria_desejada"]:
        objetivos.append("Fechar plano de aposentadoria com meta de renda e aporte mensal.")
    if perfil["patrimonio_sucessorio"] > 0 or perfil["dependentes"] > 0:
        objetivos.append("Organizar protecao familiar e planejamento sucessorio.")
    if not objetivos:
        objetivos.append("Aprofundar carteira, impostos, protecao e expansao patrimonial.")
    return objetivos


def _diretrizes_de_alocacao(perfil, diagnostico):
    diretrizes = [
        "Separar recursos por objetivo, prazo, liquidez e tolerancia a oscilacao.",
        "Evitar concentracao excessiva em um unico ativo, emissor, setor ou moeda.",
    ]

    if diagnostico["meses_reserva"] < 6:
        diretrizes.append("Priorizar caixa e liquidez ate a reserva atingir nivel adequado.")
    elif perfil["perfil_risco"] == "Conservador":
        diretrizes.append("Dar maior peso a preservacao de capital e previsibilidade.")
    elif perfil["perfil_risco"] == "Arrojado":
        diretrizes.append("Aceitar maior volatilidade apenas para objetivos de longo prazo.")
    else:
        diretrizes.append("Equilibrar crescimento, renda, liquidez e controle de risco.")

    if perfil["horizonte"] in ("Ate 2 anos", "3 a 5 anos"):
        diretrizes.append("Manter objetivos de curto e medio prazo em instrumentos de menor volatilidade.")
    else:
        diretrizes.append("Usar o horizonte longo para planejar diversificacao e rebalanceamentos.")

    return diretrizes


def _restricoes_e_alertas(perfil, diagnostico):
    alertas = []
    if perfil["renda_mensal"] <= 0:
        alertas.append("Renda mensal ainda nao informada; capacidade de aporte nao esta calibrada.")
    if diagnostico["taxa_poupanca"] < 0.10:
        alertas.append("Taxa de poupanca baixa limita a execucao dos objetivos.")
    if perfil["dependentes"] > 0 and not perfil["possui_seguro"]:
        alertas.append("Ha dependentes sem protecao familiar declarada.")
    if perfil["patrimonio_sucessorio"] > 0:
        alertas.append("Validar documentos e estrutura sucessoria com especialista juridico.")
    if not alertas:
        alertas.append("Sem alertas criticos a partir dos dados informados.")
    return alertas


def _cadencia_de_revisao(diagnostico):
    if diagnostico["classificacao"] == "prioritario":
        return "Revisao mensal ate estabilizar reserva, dividas e capacidade de aporte."
    if diagnostico["classificacao"] == "em evolucao":
        return "Revisao trimestral para acompanhar metas, riscos e mudancas de vida."
    return "Revisao semestral, com ajustes diante de eventos familiares, fiscais ou de mercado."
