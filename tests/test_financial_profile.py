import unittest

from utils.financial_profile import (
    calcular_diagnostico_360,
    normalizar_perfil_financeiro,
)
from views.financial_profile_views import ABAS_PLANEJAMENTO_360, _formatar_percentual


class FinancialProfileTests(unittest.TestCase):
    def test_normaliza_perfil_financeiro_com_fallbacks_seguros(self):
        perfil = normalizar_perfil_financeiro(
            {
                "idade": "40",
                "dependentes": "2",
                "renda_mensal": "15000.50",
                "reserva_emergencia": "-10",
                "perfil_risco": "Moderado",
            }
        )

        self.assertEqual(perfil["idade"], 40)
        self.assertEqual(perfil["dependentes"], 2)
        self.assertEqual(perfil["renda_mensal"], 15000.50)
        self.assertEqual(perfil["reserva_emergencia"], 0.0)
        self.assertEqual(perfil["perfil_risco"], "Moderado")
        self.assertFalse(perfil["possui_seguro"])

    def test_diagnostico_prioriza_reserva_dividas_e_aporte(self):
        diagnostico = calcular_diagnostico_360(
            {
                "renda_mensal": 10000,
                "reserva_emergencia": 5000,
                "dividas": 50000,
                "patrimonio_investido": 10000,
            },
            {"despesas": 8000, "balanco": 500},
        )

        self.assertEqual(diagnostico["classificacao"], "prioritario")
        self.assertLess(diagnostico["score"], 50)
        self.assertAlmostEqual(diagnostico["meses_reserva"], 0.625)
        self.assertAlmostEqual(diagnostico["taxa_poupanca"], 0.05)
        self.assertIn("reserva de emergência", diagnostico["prioridades"][0])
        self.assertTrue(any("dívidas" in item for item in diagnostico["prioridades"]))

    def test_diagnostico_reconhece_perfil_maduro(self):
        diagnostico = calcular_diagnostico_360(
            {
                "renda_mensal": 20000,
                "reserva_emergencia": 120000,
                "dividas": 0,
                "patrimonio_investido": 500000,
                "idade_aposentadoria": 60,
                "renda_aposentadoria_desejada": 18000,
            },
            {"despesas": 12000, "balanco": 5000},
        )

        self.assertEqual(diagnostico["classificacao"], "maduro")
        self.assertEqual(diagnostico["score"], 100)
        self.assertEqual(diagnostico["meses_reserva"], 10)
        self.assertAlmostEqual(diagnostico["taxa_poupanca"], 0.25)
        self.assertTrue(
            any("aposentadoria" in item for item in diagnostico["prioridades"])
        )

    def test_planejamento_360_organiza_subareas_consultivas(self):
        self.assertEqual(
            ABAS_PLANEJAMENTO_360,
            [
                "Diagnóstico",
                "Planejamento Financeiro",
                "Aposentadoria",
                "Expansão Patrimonial",
                "Sucessão",
                "Próxima Reunião",
            ],
        )

    def test_painel_executivo_exibe_percentual_consultivo(self):
        self.assertEqual(_formatar_percentual(0.1234), "12.3%")


if __name__ == "__main__":
    unittest.main()
