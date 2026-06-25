import unittest

from utils.suitability import gerar_checklist_suitability


class SuitabilityTests(unittest.TestCase):
    def test_checklist_incompleto_quando_faltam_dados_centrais(self):
        checklist = gerar_checklist_suitability({}, {})

        self.assertEqual(checklist["status"], "incompleto")
        self.assertTrue(any("idade" in item for item in checklist["pendencias"]))
        self.assertTrue(any("renda mensal" in item for item in checklist["pendencias"]))
        self.assertTrue(any("despesas" in item for item in checklist["pendencias"]))

    def test_checklist_alerta_risco_arrojado_sem_liquidez(self):
        checklist = gerar_checklist_suitability(
            {
                "idade": 35,
                "renda_mensal": 20000,
                "reserva_emergencia": 10000,
                "patrimonio_investido": 150000,
                "perfil_risco": "Arrojado",
            },
            {"despesas": 12000, "balanco": 4000},
        )

        self.assertEqual(checklist["status"], "em validacao")
        self.assertTrue(any("Perfil arrojado" in item for item in checklist["alertas"]))
        self.assertTrue(any("liquidez" in item for item in checklist["alertas"]))

    def test_checklist_pronto_quando_dados_estao_consistentes(self):
        checklist = gerar_checklist_suitability(
            {
                "idade": 45,
                "renda_mensal": 30000,
                "reserva_emergencia": 240000,
                "patrimonio_investido": 900000,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 18000,
                "perfil_risco": "Moderado",
            },
            {"despesas": 20000, "balanco": 8000},
        )

        self.assertEqual(checklist["status"], "pronto para planejamento")
        self.assertEqual(checklist["pendencias"], [])
        self.assertEqual(checklist["alertas"], [])
        self.assertTrue(any("Extratos" in item for item in checklist["documentos_sugeridos"]))


if __name__ == "__main__":
    unittest.main()
