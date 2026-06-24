import unittest

from utils.trends import TENDENCIA_SEM_HISTORICO, calcular_textos_tendencia


class TrendsTests(unittest.TestCase):
    def test_formata_tendencias_com_aumento_e_queda(self):
        gastos, pagamentos, balanco = calcular_textos_tendencia(
            {"despesas": 80.0, "receitas": 150.0, "balanco": 120.0},
            {"despesas": 100.0, "receitas": 100.0, "balanco": 100.0},
        )

        self.assertIn("#a3b899", gastos)
        self.assertIn("▼ 20.0%", gastos)
        self.assertIn("#a3b899", pagamentos)
        self.assertIn("▲ 50.0%", pagamentos)
        self.assertIn("#a3b899", balanco)
        self.assertIn("▲ 20.0%", balanco)

    def test_formata_tendencias_desfavoraveis(self):
        gastos, pagamentos, balanco = calcular_textos_tendencia(
            {"despesas": 125.0, "receitas": 80.0, "balanco": 75.0},
            {"despesas": 100.0, "receitas": 100.0, "balanco": 100.0},
        )

        self.assertIn("#ef4444", gastos)
        self.assertIn("▲ 25.0%", gastos)
        self.assertIn("#ef4444", pagamentos)
        self.assertIn("▼ 20.0%", pagamentos)
        self.assertIn("#ef4444", balanco)
        self.assertIn("▼ 25.0%", balanco)

    def test_preserva_fallback_quando_base_anterior_nao_e_positiva(self):
        self.assertEqual(
            calcular_textos_tendencia(
                {"despesas": 125.0, "receitas": 80.0, "balanco": 75.0},
                {"despesas": 0.0, "receitas": 0.0, "balanco": -10.0},
            ),
            (
                TENDENCIA_SEM_HISTORICO,
                TENDENCIA_SEM_HISTORICO,
                TENDENCIA_SEM_HISTORICO,
            ),
        )


if __name__ == "__main__":
    unittest.main()
