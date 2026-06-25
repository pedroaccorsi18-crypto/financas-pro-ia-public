import unittest

from utils.retirement_planning import calcular_planejamento_aposentadoria


class RetirementPlanningTests(unittest.TestCase):
    def test_retorna_pendencias_quando_dados_essenciais_faltam(self):
        plano = calcular_planejamento_aposentadoria(
            {
                "idade": 35,
                "idade_aposentadoria": 0,
                "renda_aposentadoria_desejada": 0,
            }
        )

        self.assertFalse(plano["completo"])
        self.assertIn("Informar idade desejada", plano["motivos_pendentes"][0])
        self.assertTrue(any("renda mensal desejada" in item for item in plano["motivos_pendentes"]))

    def test_calcula_gap_e_aporte_mensal_por_cenario(self):
        plano = calcular_planejamento_aposentadoria(
            {
                "idade": 40,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 12000,
                "patrimonio_investido": 250000,
                "reserva_emergencia": 50000,
            }
        )

        self.assertTrue(plano["completo"])
        self.assertEqual(plano["anos_ate_aposentadoria"], 25)
        self.assertEqual(set(plano["cenarios"]), {"Conservador", "Moderado", "Arrojado"})
        conservador = plano["cenarios"]["Conservador"]
        self.assertGreater(conservador["patrimonio_necessario"], 0)
        self.assertGreater(conservador["gap"], 0)
        self.assertGreater(conservador["aporte_mensal_necessario"], 0)

    def test_gap_zerado_quando_patrimonio_projetado_supera_necessario(self):
        plano = calcular_planejamento_aposentadoria(
            {
                "idade": 50,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 5000,
                "patrimonio_investido": 5000000,
            }
        )

        self.assertEqual(plano["cenarios"]["Moderado"]["gap"], 0.0)
        self.assertEqual(plano["cenarios"]["Moderado"]["aporte_mensal_necessario"], 0.0)


if __name__ == "__main__":
    unittest.main()
