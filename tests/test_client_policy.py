import unittest

from utils.client_policy import gerar_politica_planejamento_cliente


class ClientPolicyTests(unittest.TestCase):
    def test_politica_prioriza_liquidez_quando_reserva_e_baixa(self):
        politica = gerar_politica_planejamento_cliente(
            {
                "renda_mensal": 15000,
                "reserva_emergencia": 5000,
                "dividas": 30000,
                "perfil_risco": "Arrojado",
                "horizonte": "Acima de 10 anos",
            },
            {"despesas": 10000, "balanco": 500},
        )

        self.assertTrue(
            any("liquidez" in item for item in politica["objetivos_priorizados"])
        )
        self.assertTrue(
            any("Priorizar caixa" in item for item in politica["diretrizes_de_alocacao"])
        )
        self.assertIn("Revisão mensal", politica["cadencia_de_revisao"])

    def test_politica_inclui_aposentadoria_e_sucessao_quando_perfil_tem_dados(self):
        politica = gerar_politica_planejamento_cliente(
            {
                "idade": 42,
                "dependentes": 2,
                "renda_mensal": 25000,
                "reserva_emergencia": 160000,
                "patrimonio_investido": 600000,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 18000,
                "patrimonio_sucessorio": 800000,
                "possui_seguro": False,
            },
            {"despesas": 18000, "balanco": 6000},
        )

        self.assertTrue(
            any("aposentadoria" in item for item in politica["objetivos_priorizados"])
        )
        self.assertTrue(
            any("sucessório" in item for item in politica["objetivos_priorizados"])
        )
        self.assertTrue(
            any("dependentes" in item for item in politica["restricoes_e_alertas"])
        )

    def test_politica_madura_tem_revisao_semestral(self):
        politica = gerar_politica_planejamento_cliente(
            {
                "renda_mensal": 20000,
                "reserva_emergencia": 180000,
                "patrimonio_investido": 500000,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 12000,
                "perfil_risco": "Moderado",
                "horizonte": "6 a 10 anos",
            },
            {"despesas": 10000, "balanco": 5000},
        )

        self.assertIn("Revisão semestral", politica["cadencia_de_revisao"])
        self.assertTrue(
            any("diversificação" in item for item in politica["diretrizes_de_alocacao"])
        )


if __name__ == "__main__":
    unittest.main()
