"""Premissas e metodologia dos cálculos consultivos."""

from utils.retirement_planning import CENARIOS_APOSENTADORIA


PREMISSAS_STRESS_TEST = [
    {
        "nome": "Perda de renda",
        "premissa": "Redução temporária de 30% da renda mensal declarada.",
    },
    {
        "nome": "Aumento de despesas",
        "premissa": "Aumento de 20% nas despesas recorrentes informadas.",
    },
    {
        "nome": "Queda de carteira",
        "premissa": "Queda hipotética de 15% no patrimônio investido.",
    },
    {
        "nome": "Emergência familiar",
        "premissa": "Consumo de 1 a 2 meses de despesas, conforme dependentes.",
    },
]


def gerar_metodologia_financeira():
    return {
        "escopo": [
            "Diagnóstico consultivo para planejamento financeiro pessoal e familiar.",
            "Valores tratados em termos reais quando envolvem aposentadoria.",
            "Resultados servem para conversa inicial, validação de dados e priorização.",
        ],
        "aposentadoria": _premissas_aposentadoria(),
        "stress_test": PREMISSAS_STRESS_TEST,
        "limites": [
            "Não considera impostos, taxas, inflação futura específica ou custos de produtos.",
            "Não substitui suitability formal, análise jurídica, tributária ou recomendação individualizada.",
            "Depende da qualidade dos dados declarados pelo cliente e das transações consolidadas.",
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
