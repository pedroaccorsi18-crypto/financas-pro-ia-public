import datetime
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from finance_constants import TIPO_DESPESA, TIPO_RECEITA


CENTAVOS = Decimal("0.01")


def para_decimal(valor) -> Decimal:
    try:
        return Decimal(str(valor or 0)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def mes_referencia_valido(valor: str) -> bool:
    if not isinstance(valor, str) or not re.fullmatch(r"\d{2}/\d{4}", valor.strip()):
        return False
    try:
        datetime.datetime.strptime(valor.strip(), "%m/%Y")
        return True
    except ValueError:
        return False


def ordenar_meses_cronologicamente(meses) -> list[str]:
    meses_validos = {
        mes.strip()
        for mes in meses or []
        if mes_referencia_valido(mes)
    }
    return sorted(
        meses_validos,
        key=lambda mes: datetime.datetime.strptime(mes, "%m/%Y"),
        reverse=True,
    )


def calcular_resumo_financeiro(transacoes) -> dict[str, float]:
    despesas = Decimal("0.00")
    receitas = Decimal("0.00")
    despesas_manuais = Decimal("0.00")
    receitas_manuais = Decimal("0.00")
    totais_documentos = {}

    for transacao in transacoes or []:
        valor = para_decimal(transacao.get("valor"))
        tipo = transacao.get("tipo")
        meta_fatura = para_decimal(transacao.get("meta_fatura"))

        if tipo == TIPO_DESPESA:
            despesas += valor
            if meta_fatura == 0:
                despesas_manuais += valor
        elif tipo == TIPO_RECEITA:
            receitas += valor
            if meta_fatura == 0:
                receitas_manuais += valor

        if meta_fatura > 0:
            chave_documento = (
                str(transacao.get("instituicao_financeira", "")).strip(),
                str(transacao.get("tipo_documento", "")).strip(),
                str(transacao.get("mes_referencia", "")).strip(),
                meta_fatura,
            )
            totais_documentos[chave_documento] = meta_fatura

    total_documentos = sum(totais_documentos.values(), Decimal("0.00"))
    balanco = (
        receitas_manuais - (total_documentos + despesas_manuais)
        if totais_documentos
        else receitas - despesas
    )

    return {
        "despesas": float(despesas),
        "receitas": float(receitas),
        "balanco": float(balanco),
        "total_documentos": float(total_documentos),
    }


def assinatura_transacao(transacao) -> tuple:
    return (
        str(transacao.get("descricao", "")).strip(),
        para_decimal(transacao.get("valor")),
        str(transacao.get("tipo", "")).strip(),
        str(transacao.get("categoria", "")).strip(),
        str(transacao.get("mes_referencia", "")).strip(),
        para_decimal(transacao.get("meta_fatura")),
        str(transacao.get("instituicao_financeira", "")).strip(),
        str(transacao.get("tipo_documento", "")).strip(),
        str(transacao.get("origem_importacao", "")).strip(),
    )


def lotes_sao_iguais(lote_novo, lote_existente) -> bool:
    return sorted(assinatura_transacao(t) for t in lote_novo or []) == sorted(
        assinatura_transacao(t) for t in lote_existente or []
    )


def resumir_historico_para_ia(transacoes, limite=200) -> str:
    agrupado = defaultdict(lambda: {"despesas": Decimal("0.00"), "receitas": Decimal("0.00")})
    for transacao in (transacoes or [])[-limite:]:
        mes = str(transacao.get("mes_referencia") or "Sem mês")
        categoria = str(transacao.get("categoria") or "Sem categoria")
        tipo = transacao.get("tipo")
        if tipo == TIPO_DESPESA:
            agrupado[(mes, categoria)]["despesas"] += para_decimal(transacao.get("valor"))
        elif tipo == TIPO_RECEITA:
            agrupado[(mes, categoria)]["receitas"] += para_decimal(transacao.get("valor"))

    linhas = []
    for (mes, categoria), valores in sorted(agrupado.items()):
        linhas.append(
            f"- Mês: {mes} | Categoria: {categoria} | "
            f"Despesas: {valores['despesas']:.2f} | Receitas: {valores['receitas']:.2f}"
        )
    return "\n".join(linhas)


def criar_lote_demonstrativo(mes_referencia: str) -> dict:
    if not mes_referencia_valido(mes_referencia):
        raise ValueError("O mês demonstrativo deve usar o formato MM/AAAA.")

    transacoes = [
        {"descricao": "Mercado Demonstrativo", "valor": 125.50, "tipo": TIPO_DESPESA, "categoria": "Mercado"},
        {"descricao": "Transporte Demonstrativo", "valor": 24.90, "tipo": TIPO_DESPESA, "categoria": "Transporte"},
        {"descricao": "Crédito Demonstrativo", "valor": 50.00, "tipo": TIPO_RECEITA, "categoria": "Compras Gerais"},
    ]
    return {
        "instituicao": "Banco Demonstração",
        "tipo_documento": "Fatura de Teste",
        "mes_referencia": mes_referencia,
        "total_documento": 100.40,
        "transacoes": transacoes,
    }
