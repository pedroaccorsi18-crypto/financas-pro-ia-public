"""Preparacao dos dados exibidos na central de auditoria."""

from finance_constants import TIPO_DESPESA


COLUNAS_AUDITORIA = [
    "descricao",
    "valor",
    "instituicao_financeira",
    "origem_importacao",
]

COLUNAS_AUDITORIA_EXIBICAO = {
    "descricao": "Estabelecimento / Compra",
    "valor": "Valor (R$)",
    "instituicao_financeira": "Banco/Cartão",
    "origem_importacao": "Origem",
}


def preparar_dataframe_auditoria_categoria(df_mes, categoria):
    df_filtrado_categoria = df_mes[
        (df_mes["categoria"] == categoria) & (df_mes["tipo"] == TIPO_DESPESA)
    ][COLUNAS_AUDITORIA]

    return df_filtrado_categoria.rename(columns=COLUNAS_AUDITORIA_EXIBICAO)
