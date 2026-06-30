"""Roadmap de metas financeiras para conduzir o plano consultivo."""

from utils.financial_profile import calcular_diagnostico_360, normalizar_perfil_financeiro
from utils.retirement_planning import calcular_planejamento_aposentadoria


def gerar_roadmap_metas(perfil, resumo_transacoes=None):
    perfil = normalizar_perfil_financeiro(perfil)
    resumo_transacoes = resumo_transacoes or {}
    diagnostico = calcular_diagnostico_360(perfil, resumo_transacoes)
    aposentadoria = calcular_planejamento_aposentadoria(perfil)

    metas = []
    metas.extend(_metas_base(perfil, resumo_transacoes, diagnostico))
    metas.extend(_metas_aposentadoria(aposentadoria))
    metas.extend(_metas_sucessao(perfil))

    metas_ordenadas = sorted(metas, key=lambda meta: meta["prioridade"])
    return {
        "capacidade_aporte": max(0.0, float(resumo_transacoes.get("balanco") or 0)),
        "metas": metas_ordenadas,
        "curto_prazo": [meta for meta in metas_ordenadas if meta["prazo"] == "curto"],
        "medio_prazo": [meta for meta in metas_ordenadas if meta["prazo"] == "médio"],
        "longo_prazo": [meta for meta in metas_ordenadas if meta["prazo"] == "longo"],
    }


def _metas_base(perfil, resumo_transacoes, diagnostico):
    despesas = max(0.0, float(resumo_transacoes.get("despesas") or 0))
    metas = []

    reserva_alvo = despesas * 6
    gap_reserva = max(0.0, reserva_alvo - perfil["reserva_emergencia"])
    if despesas > 0 and gap_reserva > 0:
        metas.append(
            _meta(
                "Reserva de emergência",
                "curto",
                "Elevar reserva para 6 meses de despesas recorrentes.",
                gap_reserva,
                "Liquidez antes de risco.",
                10,
            )
        )

    if perfil["dividas"] > 0:
        prioridade = 15 if perfil["renda_mensal"] and perfil["dividas"] > perfil["renda_mensal"] * 3 else 25
        metas.append(
            _meta(
                "Redução de dívidas",
                "curto",
                "Priorizar dívidas por custo efetivo, prazo e garantia.",
                perfil["dividas"],
                "Reduz fragilidade do fluxo mensal.",
                prioridade,
            )
        )

    if diagnostico["taxa_poupanca"] < 0.10:
        metas.append(
            _meta(
                "Capacidade de aporte",
                "médio",
                "Elevar taxa de poupança para pelo menos 10% da renda.",
                max(0.0, perfil["renda_mensal"] * 0.10),
                "Sem aporte recorrente, objetivos ficam dependentes de eventos pontuais.",
                30,
            )
        )

    if perfil["patrimonio_investido"] > 0:
        metas.append(
            _meta(
                "Arquitetura de carteira",
                "médio",
                "Separar carteira por objetivo, liquidez, moeda, classe e horizonte.",
                0.0,
                "Base para alinhar risco declarado com objetivos reais.",
                45,
            )
        )

    return metas


def _metas_aposentadoria(aposentadoria):
    if not aposentadoria["completo"]:
        return [
            _meta(
                "Dados de aposentadoria",
                "médio",
                "Definir idade alvo e renda mensal desejada para aposentadoria.",
                0.0,
                "Sem premissas, não há como medir gap de aposentadoria.",
                35,
            )
        ]

    moderado = aposentadoria["cenarios"]["Moderado"]
    return [
        _meta(
            "Aposentadoria",
            "longo",
            "Acompanhar gap e aporte mensal necessário no cenário moderado.",
            moderado["gap"],
            "Conecta renda futura desejada com patrimônio necessário.",
            55,
        )
    ]


def _metas_sucessao(perfil):
    if perfil["patrimonio_sucessorio"] <= 0 and perfil["dependentes"] <= 0:
        return []

    return [
        _meta(
            "Proteção e sucessão",
            "médio",
            "Mapear documentos, beneficiários, dependentes e poderes de decisão.",
            perfil["patrimonio_sucessorio"],
            "Reduz risco familiar, jurídico e operacional.",
            40,
        )
    ]


def _meta(nome, prazo, descricao, valor_alvo, racional, prioridade):
    return {
        "nome": nome,
        "prazo": prazo,
        "descricao": descricao,
        "valor_alvo": valor_alvo,
        "racional": racional,
        "prioridade": prioridade,
    }
