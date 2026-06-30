import unittest

from utils.financial_methodology import gerar_metodologia_financeira


class FinancialMethodologyTests(unittest.TestCase):
    def test_metodologia_explica_premissas_de_aposentadoria(self):
        metodologia = gerar_metodologia_financeira()

        cenarios = {item["cenario"] for item in metodologia["aposentadoria"]}
        self.assertEqual(cenarios, {"Conservador", "Moderado", "Arrojado"})
        self.assertTrue(
            all(item["retorno_real_anual"] > 0 for item in metodologia["aposentadoria"])
        )
        self.assertTrue(
            all(item["taxa_retirada_anual"] > 0 for item in metodologia["aposentadoria"])
        )

    def test_metodologia_explica_stress_test_e_limites(self):
        metodologia = gerar_metodologia_financeira()

        nomes_stress = {item["nome"] for item in metodologia["stress_test"]}
        self.assertIn("Perda de renda", nomes_stress)
        self.assertIn("Queda de carteira", nomes_stress)
        self.assertTrue(any("Não considera impostos" in item for item in metodologia["limites"]))


if __name__ == "__main__":
    unittest.main()
