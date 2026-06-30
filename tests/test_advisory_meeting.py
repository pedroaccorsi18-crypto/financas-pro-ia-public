import unittest

from utils.advisory_meeting import gerar_roteiro_reuniao_consultiva


class AdvisoryMeetingTests(unittest.TestCase):
    def test_roteiro_prioriza_estabilizacao_quando_stress_e_alto(self):
        roteiro = gerar_roteiro_reuniao_consultiva(
            {
                "renda_mensal": 10000,
                "reserva_emergencia": 5000,
                "dividas": 60000,
            },
            {"despesas": 9000, "balanco": 200},
        )

        self.assertIn("status de onboarding", roteiro["abertura"])
        self.assertTrue(any("choque financeiro" in item for item in roteiro["perguntas_chave"]))
        self.assertTrue(any("Stress test" in item for item in roteiro["pontos_de_atencao"]))
        self.assertIn("estabilização", roteiro["fechamento"])

    def test_roteiro_maduro_fecha_com_eficiencia(self):
        roteiro = gerar_roteiro_reuniao_consultiva(
            {
                "idade": 45,
                "renda_mensal": 35000,
                "reserva_emergencia": 300000,
                "patrimonio_investido": 900000,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 18000,
                "perfil_risco": "Moderado",
                "horizonte": "Acima de 10 anos",
                "possui_seguro": True,
            },
            {"despesas": 18000, "balanco": 10000},
        )

        self.assertIn("eficiência tributária", roteiro["fechamento"])
        self.assertTrue(any("aposentadoria" in item for item in roteiro["perguntas_chave"]))

    def test_roteiro_transforma_metas_em_decisoes(self):
        roteiro = gerar_roteiro_reuniao_consultiva(
            {
                "idade": 38,
                "renda_mensal": 15000,
                "reserva_emergencia": 10000,
                "patrimonio_investido": 100000,
            },
            {"despesas": 10000, "balanco": 1000},
        )

        self.assertTrue(
            any("Confirmar prioridade da meta" in item for item in roteiro["decisoes_da_reuniao"])
        )


if __name__ == "__main__":
    unittest.main()
