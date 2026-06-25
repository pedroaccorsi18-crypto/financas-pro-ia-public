import unittest

from utils.goal_roadmap import gerar_roadmap_metas


class GoalRoadmapTests(unittest.TestCase):
    def test_roadmap_prioriza_reserva_e_dividas_no_curto_prazo(self):
        roadmap = gerar_roadmap_metas(
            {
                "idade": 38,
                "renda_mensal": 12000,
                "reserva_emergencia": 5000,
                "dividas": 60000,
                "patrimonio_investido": 20000,
            },
            {"despesas": 9000, "balanco": 500},
        )

        nomes_curto = [meta["nome"] for meta in roadmap["curto_prazo"]]
        self.assertEqual(roadmap["capacidade_aporte"], 500)
        self.assertIn("Reserva de emergencia", nomes_curto)
        self.assertIn("Reducao de dividas", nomes_curto)

    def test_roadmap_cria_meta_de_aposentadoria_com_gap_completo(self):
        roadmap = gerar_roadmap_metas(
            {
                "idade": 40,
                "renda_mensal": 20000,
                "reserva_emergencia": 150000,
                "patrimonio_investido": 300000,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 12000,
            },
            {"despesas": 12000, "balanco": 5000},
        )

        nomes_longo = [meta["nome"] for meta in roadmap["longo_prazo"]]
        self.assertIn("Aposentadoria", nomes_longo)
        self.assertGreater(roadmap["longo_prazo"][0]["valor_alvo"], 0)

    def test_roadmap_inclui_sucessao_quando_ha_dependentes(self):
        roadmap = gerar_roadmap_metas(
            {
                "idade": 45,
                "dependentes": 2,
                "renda_mensal": 25000,
                "reserva_emergencia": 200000,
                "patrimonio_investido": 800000,
            },
            {"despesas": 18000, "balanco": 7000},
        )

        nomes_medio = [meta["nome"] for meta in roadmap["medio_prazo"]]
        self.assertIn("Protecao e sucessao", nomes_medio)
        self.assertIn("Dados de aposentadoria", nomes_medio)


if __name__ == "__main__":
    unittest.main()
