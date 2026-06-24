import unittest

import pandas as pd

from finance_constants import TIPO_DESPESA, TIPO_RECEITA
from utils.category_analysis import preparar_dados_analise_categorias


class CategoryAnalysisTests(unittest.TestCase):
    def test_prepara_dataframe_do_grafico_ordenado_por_valor_crescente(self):
        df_mes = pd.DataFrame(
            [
                {"categoria": "Mercado", "valor": 120.0, "tipo": TIPO_DESPESA},
                {"categoria": "Transporte", "valor": 40.0, "tipo": TIPO_DESPESA},
                {"categoria": "Mercado", "valor": 30.0, "tipo": TIPO_DESPESA},
                {"categoria": "Salario", "valor": 1000.0, "tipo": TIPO_RECEITA},
            ]
        )
        df_despesas = df_mes[df_mes["tipo"] == TIPO_DESPESA]

        df_grafico, _ = preparar_dados_analise_categorias(
            df_mes,
            df_despesas,
            ["Mercado", "Transporte", "Lazer"],
        )

        self.assertEqual(df_grafico.columns.tolist(), ["Categoria", "Total (R$)"])
        self.assertEqual(df_grafico["Categoria"].tolist(), ["Transporte", "Mercado"])
        self.assertEqual(df_grafico["Total (R$)"].tolist(), [40.0, 150.0])

    def test_prepara_subtotais_com_categorias_zeradas_ao_final(self):
        df_mes = pd.DataFrame(
            [
                {"categoria": "Mercado", "valor": 120.0, "tipo": TIPO_DESPESA},
                {"categoria": "Transporte", "valor": 40.0, "tipo": TIPO_DESPESA},
                {"categoria": "Mercado", "valor": 30.0, "tipo": TIPO_DESPESA},
                {"categoria": "Mercado", "valor": 1000.0, "tipo": TIPO_RECEITA},
            ]
        )
        df_despesas = df_mes[df_mes["tipo"] == TIPO_DESPESA]

        _, subtotais = preparar_dados_analise_categorias(
            df_mes,
            df_despesas,
            ["Mercado", "Transporte", "Lazer"],
        )

        self.assertEqual(
            subtotais,
            [
                ("Mercado", 150.0),
                ("Transporte", 40.0),
                ("Lazer", 0.0),
            ],
        )


if __name__ == "__main__":
    unittest.main()
