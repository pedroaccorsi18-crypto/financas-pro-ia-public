import unittest

import pandas as pd

from finance_constants import ORIGEM_AUTOMATICA, TIPO_DESPESA, TIPO_RECEITA
from utils.import_staging import preparar_transacoes_importadas


class ImportStagingTests(unittest.TestCase):
    def pre_visualizacao_base(self):
        return {
            "instituicao": "Banco Teste",
            "tipo_documento": "Fatura de Cartao",
            "mes_referencia": "06/2026",
            "total_documento": 150.0,
        }

    def test_monta_payload_e_totais_da_importacao_homologada(self):
        df_editavel = pd.DataFrame(
            [
                {
                    "descricao": " PMBMETRO Bilhete ",
                    "valor": "25.50",
                    "tipo": TIPO_DESPESA,
                    "categoria": "Compras Gerais",
                },
                {
                    "descricao": "Credito promocional",
                    "valor": 10,
                    "tipo": TIPO_RECEITA,
                    "categoria": "Compras Gerais",
                },
            ]
        )

        transacoes, gastos_reais, creditos_reais = preparar_transacoes_importadas(
            df_editavel,
            self.pre_visualizacao_base(),
            "user-123",
            "usuario@example.com",
        )

        self.assertEqual(gastos_reais, 25.5)
        self.assertEqual(creditos_reais, 10.0)
        self.assertEqual(len(transacoes), 2)
        self.assertEqual(transacoes[0]["descricao"], "PMBMETRO Bilhete")
        self.assertEqual(transacoes[0]["categoria"], "Transporte")
        self.assertEqual(transacoes[0]["origem_importacao"], ORIGEM_AUTOMATICA)
        self.assertEqual(transacoes[0]["user_id"], "user-123")
        self.assertEqual(transacoes[0]["usuario_email"], "usuario@example.com")
        self.assertEqual(transacoes[0]["mes_referencia"], "06/2026")
        self.assertEqual(transacoes[0]["meta_fatura"], 150.0)
        self.assertEqual(transacoes[0]["instituicao_financeira"], "Banco Teste")

    def test_rejeita_mes_de_referencia_invalido(self):
        pre_visualizacao = self.pre_visualizacao_base()
        pre_visualizacao["mes_referencia"] = "2026-06"

        with self.assertRaisesRegex(ValueError, "MM/AAAA"):
            preparar_transacoes_importadas(
                pd.DataFrame(
                    [
                        {
                            "descricao": "Mercado",
                            "valor": 10,
                            "tipo": TIPO_DESPESA,
                            "categoria": "Mercado",
                        }
                    ]
                ),
                pre_visualizacao,
                "user-123",
                "usuario@example.com",
            )

    def test_rejeita_valor_nulo_ou_negativo(self):
        with self.assertRaisesRegex(ValueError, "valor nulo ou negativo"):
            preparar_transacoes_importadas(
                pd.DataFrame(
                    [
                        {
                            "descricao": "Mercado",
                            "valor": 0,
                            "tipo": TIPO_DESPESA,
                            "categoria": "Mercado",
                        }
                    ]
                ),
                self.pre_visualizacao_base(),
                "user-123",
                "usuario@example.com",
            )


if __name__ == "__main__":
    unittest.main()
