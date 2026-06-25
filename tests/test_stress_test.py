import unittest

from utils.stress_test import gerar_stress_test_financeiro


class StressTestTests(unittest.TestCase):
    def test_stress_test_sinaliza_alto_risco_com_reserva_baixa(self):
        stress = gerar_stress_test_financeiro(
            {
                "renda_mensal": 10000,
                "reserva_emergencia": 5000,
                "patrimonio_investido": 20000,
            },
            {"despesas": 9000, "balanco": 1000},
        )

        self.assertEqual(stress["severidade_geral"], "alto")
        self.assertTrue(any(cenario["severidade"] == "alto" for cenario in stress["cenarios"]))
        self.assertTrue(any("Reforcar reserva" in acao for acao in stress["acoes_prioritarias"]))

    def test_stress_test_alerta_conservador_com_queda_de_carteira(self):
        stress = gerar_stress_test_financeiro(
            {
                "renda_mensal": 20000,
                "reserva_emergencia": 200000,
                "patrimonio_investido": 500000,
                "perfil_risco": "Conservador",
            },
            {"despesas": 15000, "balanco": 5000},
        )

        queda_carteira = next(
            cenario for cenario in stress["cenarios"] if cenario["nome"] == "Queda de 15% da carteira"
        )
        self.assertEqual(queda_carteira["severidade"], "alto")
        self.assertEqual(queda_carteira["impacto"], 75000)

    def test_stress_test_maduro_fica_baixo_quando_ha_folga(self):
        stress = gerar_stress_test_financeiro(
            {
                "renda_mensal": 40000,
                "reserva_emergencia": 500000,
                "patrimonio_investido": 1000000,
                "perfil_risco": "Moderado",
                "horizonte": "Acima de 10 anos",
                "possui_seguro": True,
            },
            {"despesas": 15000, "balanco": 25000},
        )

        self.assertEqual(stress["severidade_geral"], "baixo")
        self.assertTrue(
            any("Manter revisao periodica" in acao for acao in stress["acoes_prioritarias"])
        )


if __name__ == "__main__":
    unittest.main()
