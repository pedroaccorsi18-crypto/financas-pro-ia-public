"""Regras de saneamento retroativo de categorias."""

import json

from finance_categories import CATEGORIAS_VALIDAS


CATEGORIA_FALLBACK_RECLASSIFICACAO = "Compras Gerais"
CATEGORIA_TRANSPORTE = "Transporte"
CATEGORIAS_RECLASSIFICAVEIS = ["Compras & Assinaturas", "Geral", None]
TERMOS_TRANSPORTE = ["pmbmetro", "metro", "cptm", "autopass"]


def selecionar_transacoes_de_transporte(transacoes):
    return [
        transacao
        for transacao in transacoes
        if _descricao_tem_termo_transporte(transacao)
        and transacao.get("categoria") != CATEGORIA_TRANSPORTE
    ]


def selecionar_linhas_para_reclassificar(transacoes):
    return [
        transacao
        for transacao in transacoes
        if transacao.get("categoria") in CATEGORIAS_RECLASSIFICAVEIS
        and transacao.get("descricao")
    ]


def extrair_descricoes_para_reclassificar(transacoes):
    return [transacao["descricao"] for transacao in transacoes]


def montar_prompt_reclassificacao_categorias(descricoes):
    return (
        "Classifique estritamente cada item da lista abaixo nas seguintes "
        f"categorias permitidas:\n{str(CATEGORIAS_VALIDAS)}\n\n"
        f"LISTA DE ITENS:\n{json.dumps(descricoes)}\n\n"
        "Retorne a resposta estritamente em um JSON plano no formato: "
        '{"item_descricao": "Categoria"}'
    )


def carregar_mapa_reclassificacao(texto_resposta):
    return json.loads(str(texto_resposta).strip())


def preparar_atualizacoes_reclassificacao(transacoes, mapa_categorias):
    atualizacoes = []
    for transacao in transacoes:
        categoria = mapa_categorias.get(
            transacao["descricao"],
            CATEGORIA_FALLBACK_RECLASSIFICACAO,
        )
        if categoria not in CATEGORIAS_VALIDAS:
            categoria = CATEGORIA_FALLBACK_RECLASSIFICACAO
        atualizacoes.append((transacao["id"], categoria))
    return atualizacoes


def _descricao_tem_termo_transporte(transacao):
    descricao = str(transacao.get("descricao", "")).lower()
    return any(termo in descricao for termo in TERMOS_TRANSPORTE)
