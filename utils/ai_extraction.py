"""Contrato da extracao de documentos financeiros via IA."""

import json

from finance_categories import CATEGORIAS_VALIDAS
from finance_constants import TIPOS_TRANSACAO


TIPOS_DOCUMENTO_EXTRACAO = [
    "Fatura de Cart\u00e3o",
    "Extrato Banc\u00e1rio",
    "Comprovante",
    "Outro",
]


def montar_prompt_extracao_pdf() -> str:
    return (
        "Voc\u00ea \u00e9 um extrator de dados cont\u00e1beis de alt\u00edssima precis\u00e3o. "
        "Sua meta \u00e9 extrair transa\u00e7\u00f5es de faturas ou extratos com temperatura zero.\n"
        "O campo 'mes_fatura' deve obrigatoriamente usar o formato MM/AAAA, "
        "por exemplo 05/2026.\n"
        "Gere um JSON estrito contendo um \u00fanico objeto com os campos: "
        "'instituicao_financeira', 'tipo_documento', 'total_documento', "
        "'mes_fatura' e a lista 'transacoes' (descricao, valor, tipo, categoria)."
    )


def montar_schema_extracao_pdf(types):
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "instituicao_financeira": types.Schema(type=types.Type.STRING),
            "tipo_documento": types.Schema(
                type=types.Type.STRING,
                enum=TIPOS_DOCUMENTO_EXTRACAO,
            ),
            "total_documento": types.Schema(type=types.Type.NUMBER),
            "mes_fatura": types.Schema(
                type=types.Type.STRING,
                description="Mes no formato MM/AAAA",
            ),
            "transacoes": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "descricao": types.Schema(type=types.Type.STRING),
                        "valor": types.Schema(type=types.Type.NUMBER),
                        "tipo": types.Schema(
                            type=types.Type.STRING,
                            enum=TIPOS_TRANSACAO,
                        ),
                        "categoria": types.Schema(
                            type=types.Type.STRING,
                            enum=CATEGORIAS_VALIDAS,
                        ),
                    },
                    required=["descricao", "valor", "tipo", "categoria"],
                ),
            ),
        },
        required=[
            "instituicao_financeira",
            "tipo_documento",
            "total_documento",
            "mes_fatura",
            "transacoes",
        ],
    )


def montar_config_extracao_pdf(types):
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=montar_schema_extracao_pdf(types),
        temperature=0.0,
    )


def carregar_resultado_extracao(texto_resposta: str) -> dict:
    return json.loads(str(texto_resposta).strip())


def normalizar_resultado_extracao(resultado_ia: dict, dataframe_factory):
    return {
        "instituicao": resultado_ia["instituicao_financeira"],
        "tipo_documento": resultado_ia["tipo_documento"],
        "mes_referencia": resultado_ia["mes_fatura"],
        "total_documento": (
            float(resultado_ia["total_documento"])
            if resultado_ia["total_documento"]
            else 0.0
        ),
        "df_transacoes": dataframe_factory(resultado_ia["transacoes"]),
    }
