"""Preparacao dos dados da central de analise de grupos."""

from finance_constants import TIPO_DESPESA


def preparar_dados_analise_categorias(df_mes, df_despesas, categorias_despesa):
    df_grafico = (
        df_despesas.groupby("categoria")["valor"]
        .sum()
        .reset_index()
        .sort_values(by="valor", ascending=True)
        .rename(columns={"categoria": "Categoria", "valor": "Total (R$)"})
    )

    df_ordenado_lista = (
        df_despesas.groupby("categoria")["valor"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    categorias_ordenadas = df_ordenado_lista["categoria"].tolist()
    for categoria in categorias_despesa:
        if categoria not in categorias_ordenadas:
            categorias_ordenadas.append(categoria)

    subtotais = []
    for categoria in categorias_ordenadas:
        valor_categoria = df_mes[
            (df_mes["categoria"] == categoria) & (df_mes["tipo"] == TIPO_DESPESA)
        ]["valor"].sum()
        subtotais.append((categoria, valor_categoria))

    return df_grafico, subtotais
