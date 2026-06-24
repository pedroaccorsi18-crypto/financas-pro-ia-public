import unittest

import pandas as pd

from finance_constants import ORIGEM_AUTOMATICA, ORIGEM_MANUAL, TIPO_DESPESA, TIPO_RECEITA
from utils.audit import preparar_dataframe_auditoria_categoria


class AuditTests(unittest.TestCase):
    def test_prepara_dataframe_de_auditoria_da_categoria(self):
        df_mes = pd.DataFrame(
            [
                {
                    "descricao": "Mercado A",
                    "valor": 100.0,
                    "categoria": "Mercado",
                    "tipo": TIPO_DESPESA,
                    "instituicao_financeira": "Banco A",
                    "origem_importacao": ORIGEM_AUTOMATICA,
                },
                {
                    "descricao": "Salario",
                    "valor": 1000.0,
                    "categoria": "Mercado",
                    "tipo": TIPO_RECEITA,
                    "instituicao_financeira": "Empresa",
                    "origem_importacao": ORIGEM_MANUAL,
                },
                {
                    "descricao": "Metro",
                    "valor": 5.0,
                    "categoria": "Transporte",
                    "tipo": TIPO_DESPESA,
                    "instituicao_financeira": "Banco B",
                    "origem_importacao": ORIGEM_MANUAL,
                },
            ]
        )

        df_exibicao = preparar_dataframe_auditoria_categoria(df_mes, "Mercado")

        self.assertEqual(
            df_exibicao.columns.tolist(),
            ["Estabelecimento / Compra", "Valor (R$)", "Banco/Cartão", "Origem"],
        )
        self.assertEqual(df_exibicao["Estabelecimento / Compra"].tolist(), ["Mercado A"])
        self.assertEqual(df_exibicao["Valor (R$)"].tolist(), [100.0])
        self.assertEqual(df_exibicao["Banco/Cartão"].tolist(), ["Banco A"])
        self.assertEqual(df_exibicao["Origem"].tolist(), [ORIGEM_AUTOMATICA])

    def test_retorna_dataframe_vazio_quando_categoria_nao_tem_despesa(self):
        df_mes = pd.DataFrame(
            [
                {
                    "descricao": "Salario",
                    "valor": 1000.0,
                    "categoria": "Receita",
                    "tipo": TIPO_RECEITA,
                    "instituicao_financeira": "Empresa",
                    "origem_importacao": ORIGEM_MANUAL,
                }
            ]
        )

        df_exibicao = preparar_dataframe_auditoria_categoria(df_mes, "Mercado")

        self.assertTrue(df_exibicao.empty)
        self.assertEqual(
            df_exibicao.columns.tolist(),
            ["Estabelecimento / Compra", "Valor (R$)", "Banco/Cartão", "Origem"],
        )


if __name__ == "__main__":
    unittest.main()
