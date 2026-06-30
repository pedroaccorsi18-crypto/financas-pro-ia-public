"""Diretrizes consultivas para política de planejamento do cliente."""

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
        objetivos.append("Reduzir dívidas por custo, prazo e impacto no fluxo mensal.")
    if perfil["idade_aposentadoria"] and perfil["renda_aposentadoria_desejada"]:
        objetivos.append("Fechar plano de aposentadoria com meta de renda e aporte mensal.")
    if perfil["patrimonio_sucessorio"] > 0 or perfil["dependentes"] > 0:
        objetivos.append("Organizar proteção familiar e planejamento sucessório.")
    if not objetivos:
        objetivos.append("Aprofundar carteira, impostos, proteção e expansão patrimonial.")
    return objetivos


def _diretrizes_de_alocacao(perfil, diagnostico):
    diretrizes = [
        "Separar recursos por objetivo, prazo, liquidez e tolerância à oscilação.",
        "Evitar concentração excessiva em um único ativo, emissor, setor ou moeda.",
    ]

    if diagnostico["meses_reserva"] < 6:
        diretrizes.append("Priorizar caixa e liquidez até a reserva atingir nível adequado.")
    elif perfil["perfil_risco"] == "Conservador":
        diretrizes.append("Dar maior peso à preservação de capital e previsibilidade.")
    elif perfil["perfil_risco"] == "Arrojado":
        diretrizes.append("Aceitar maior volatilidade apenas para objetivos de longo prazo.")
    else:
        diretrizes.append("Equilibrar crescimento, renda, liquidez e controle de risco.")

    if perfil["horizonte"] in ("Até 2 anos", "3 a 5 anos"):
        diretrizes.append("Manter objetivos de curto e médio prazo em instrumentos de menor volatilidade.")
    else:
        diretrizes.append("Usar o horizonte longo para planejar diversificação e rebalanceamentos.")

    return diretrizes


def _restricoes_e_alertas(perfil, diagnostico):
    alertas = []
    if perfil["renda_mensal"] <= 0:
        alertas.append("Renda mensal ainda não informada; capacidade de aporte não está calibrada.")
    if diagnostico["taxa_poupanca"] < 0.10:
        alertas.append("Taxa de poupança baixa limita a execução dos objetivos.")
    if perfil["dependentes"] > 0 and not perfil["possui_seguro"]:
        alertas.append("Há dependentes sem proteção familiar declarada.")
    if perfil["patrimonio_sucessorio"] > 0:
        alertas.append("Validar documentos e estrutura sucessória com especialista jurídico.")
    if not alertas:
        alertas.append("Sem alertas críticos a partir dos dados informados.")
    return alertas


def _cadencia_de_revisao(diagnostico):
    if diagnostico["classificacao"] == "prioritario":
        return "Revisão mensal até estabilizar reserva, dívidas e capacidade de aporte."
    if diagnostico["classificacao"] == "em evolução":
        return "Revisão trimestral para acompanhar metas, riscos e mudanças de vida."
    return "Revisão semestral, com ajustes diante de eventos familiares, fiscais ou de mercado."
