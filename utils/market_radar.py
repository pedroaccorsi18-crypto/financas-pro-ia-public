ATIVOS_DEMONSTRATIVOS = [
    {
        "ticker": "IVVB11",
        "nome": "ETF S&P 500",
        "classe": "ETF",
        "mercado": "Brasil / EUA",
        "horizonte": "Longo prazo",
        "perfil": "Moderado",
        "momentum": 82,
        "qualidade": 86,
        "valuation": 58,
        "risco": 46,
        "liquidez": 88,
        "tese": "Exposicao ampla a grandes empresas americanas com negociacao local.",
        "riscos": "Risco cambial, concentracao em EUA e volatilidade de renda variavel.",
    },
    {
        "ticker": "B5P211",
        "nome": "ETF Tesouro IPCA curto",
        "classe": "Renda fixa",
        "mercado": "Brasil",
        "horizonte": "Curto / medio prazo",
        "perfil": "Conservador",
        "momentum": 62,
        "qualidade": 78,
        "valuation": 72,
        "risco": 24,
        "liquidez": 74,
        "tese": "Exposicao a inflacao com menor duracao e oscilacao que vencimentos longos.",
        "riscos": "Marcacao a mercado, mudancas de juros reais e baixa diversificacao internacional.",
    },
    {
        "ticker": "NASDAQ-100",
        "nome": "Indice Nasdaq 100",
        "classe": "Indice",
        "mercado": "EUA",
        "horizonte": "Longo prazo",
        "perfil": "Arrojado",
        "momentum": 88,
        "qualidade": 82,
        "valuation": 42,
        "risco": 68,
        "liquidez": 92,
        "tese": "Radar para crescimento global em tecnologia e empresas de alta escala.",
        "riscos": "Valuation elevado, concentracao setorial e alta sensibilidade a juros.",
    },
    {
        "ticker": "GOLD",
        "nome": "Ouro",
        "classe": "Commodities",
        "mercado": "Global",
        "horizonte": "Protecao",
        "perfil": "Moderado",
        "momentum": 70,
        "qualidade": 66,
        "valuation": 55,
        "risco": 40,
        "liquidez": 80,
        "tese": "Ativo de protecao para cenarios de estresse, inflacao ou aversao a risco.",
        "riscos": "Nao gera fluxo de caixa, pode sofrer em ciclos de juros reais altos.",
    },
    {
        "ticker": "BTC",
        "nome": "Bitcoin",
        "classe": "Cripto",
        "mercado": "Global",
        "horizonte": "Especulativo",
        "perfil": "Arrojado",
        "momentum": 76,
        "qualidade": 45,
        "valuation": 38,
        "risco": 92,
        "liquidez": 82,
        "tese": "Ativo alternativo em observacao para perfis que aceitam alta volatilidade.",
        "riscos": "Volatilidade extrema, risco regulatorio, custodia e ausencia de fluxo de caixa.",
    },
    {
        "ticker": "ACWI",
        "nome": "ETF acoes globais",
        "classe": "ETF",
        "mercado": "Global",
        "horizonte": "Longo prazo",
        "perfil": "Moderado",
        "momentum": 74,
        "qualidade": 80,
        "valuation": 61,
        "risco": 52,
        "liquidez": 84,
        "tese": "Diversificacao global em acoes desenvolvidas e emergentes.",
        "riscos": "Exposicao cambial, ciclos globais de bolsa e concentracao em grandes mercados.",
    },
]


PESOS_SCORE_RADAR = {
    "momentum": 0.25,
    "qualidade": 0.30,
    "valuation": 0.20,
    "liquidez": 0.15,
    "risco": -0.10,
}


def calcular_score_radar(ativo):
    score = 0.0
    for campo, peso in PESOS_SCORE_RADAR.items():
        score += float(ativo.get(campo, 0)) * peso
    return max(0, min(100, round(score)))


def classificar_score_radar(score):
    if score >= 75:
        return "Radar forte"
    if score >= 60:
        return "Monitorar"
    return "Acompanhar com cautela"


def gerar_radar_mercado(ativos=None):
    universo = ativos or ATIVOS_DEMONSTRATIVOS
    radar = []
    for ativo in universo:
        score = calcular_score_radar(ativo)
        radar.append(
            {
                **ativo,
                "score": score,
                "status": classificar_score_radar(score),
                "alerta": _gerar_alerta(ativo, score),
            }
        )
    return sorted(radar, key=lambda item: item["score"], reverse=True)


def filtrar_radar_mercado(radar, *, classe="Todas", perfil="Todos"):
    itens = radar
    if classe != "Todas":
        itens = [item for item in itens if item["classe"] == classe]
    if perfil != "Todos":
        itens = [item for item in itens if item["perfil"] == perfil]
    return itens


def resumir_radar_mercado(radar):
    if not radar:
        return {
            "total": 0,
            "radar_forte": 0,
            "maior_score": None,
            "risco_medio": 0,
        }
    return {
        "total": len(radar),
        "radar_forte": sum(1 for item in radar if item["status"] == "Radar forte"),
        "maior_score": radar[0]["ticker"],
        "risco_medio": round(sum(item["risco"] for item in radar) / len(radar)),
    }


def _gerar_alerta(ativo, score):
    if ativo["risco"] >= 80:
        return "Exige limite de exposicao e perfil arrojado."
    if score >= 75:
        return "Boa combinacao de qualidade, liquidez e leitura de mercado."
    if ativo["valuation"] < 50:
        return "Entrou no radar, mas valuation pede disciplina."
    return "Monitorar antes de aumentar exposicao."
