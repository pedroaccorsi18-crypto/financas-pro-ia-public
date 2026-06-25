"""Premissas e metodologia dos calculos consultivos."""

from utils.retirement_planning import CENARIOS_APOSENTADORIA


PREMISSAS_STRESS_TEST = [
    {
        "nome": "Perda de renda",
        "premissa": "Reducao temporaria de 30% da renda mensal declarada.",
    },
    {
        "nome": "Aumento de despesas",
        "premissa": "Aumento de 20% nas despesas recorrentes informadas.",
    },
    {
        "nome": "Queda de carteira",
        "premissa": "Queda hipotetica de 15% no patrimonio investido.",
    },
    {
        "nome": "Emergencia familiar",
        "premissa": "Consumo de 1 a 2 meses de despesas, conforme dependentes.",
    },
]


def gerar_metodologia_financeira():
    return {
        "escopo": [
            "Diagnostico consultivo para planejamento financeiro pessoal e familiar.",
            "Valores tratados em termos reais quando envolvem aposentadoria.",
            "Resultados servem para conversa inicial, validacao de dados e priorizacao.",
        ],
        "aposentadoria": _premissas_aposentadoria(),
        "stress_test": PREMISSAS_STRESS_TEST,
        "limites": [
            "Nao considera impostos, taxas, inflacao futura especifica ou custos de produtos.",
            "Nao substitui suitability formal, analise juridica, tributaria ou recomendacao individualizada.",
            "Depende da qualidade dos dados declarados pelo cliente e das transacoes consolidadas.",
        ],
    }


def _premissas_aposentadoria():
    premissas = []
    for nome, cenario in CENARIOS_APOSENTADORIA.items():
        premissas.append(
            {
                "cenario": nome,
                "retorno_real_anual": cenario["retorno_real_anual"],
                "taxa_retirada_anual": cenario["taxa_retirada_anual"],
            }
        )
    return premissas
