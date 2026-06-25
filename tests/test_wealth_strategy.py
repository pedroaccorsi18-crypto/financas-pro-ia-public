import unittest

from utils.wealth_strategy import gerar_matriz_estrategia_patrimonial


class WealthStrategyTests(unittest.TestCase):
    def test_matriz_prioriza_liquidez_quando_reserva_e_fraca(self):
        matriz = gerar_matriz_estrategia_patrimonial(
            {
                "renda_mensal": 10000,
                "reserva_emergencia": 5000,
                "patrimonio_investido": 100000,
            },
            {"despesas": 9000, "balanco": 500},
        )

        self.assertEqual(matriz["foco_principal"], "Liquidez")
        self.assertIn("Defensiva", matriz["postura_geral"])
        self.assertEqual(matriz["frentes"][0]["prioridade_texto"], "prioridade alta")

    def test_matriz_prioriza_protecao_com_dependentes_sem_seguro(self):
        matriz = gerar_matriz_estrategia_patrimonial(
            {
                "idade": 42,
                "dependentes": 2,
                "renda_mensal": 25000,
                "reserva_emergencia": 200000,
                "patrimonio_investido": 700000,
                "possui_seguro": False,
            },
            {"despesas": 15000, "balanco": 8000},
        )

        protecao = next(frente for frente in matriz["frentes"] if frente["nome"] == "Protecao")
        self.assertEqual(protecao["postura"], "defensiva")
        self.assertEqual(protecao["prioridade_texto"], "prioridade alta")

    def test_matriz_madura_fica_estrategica(self):
        matriz = gerar_matriz_estrategia_patrimonial(
            {
                "idade": 45,
                "renda_mensal": 40000,
                "reserva_emergencia": 400000,
                "patrimonio_investido": 1200000,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 20000,
                "perfil_risco": "Moderado",
                "horizonte": "Acima de 10 anos",
                "possui_seguro": True,
            },
            {"despesas": 18000, "balanco": 12000},
        )

        self.assertIn("Estrategica", matriz["postura_geral"])
        self.assertTrue(any(frente["nome"] == "Crescimento patrimonial" for frente in matriz["frentes"]))


if __name__ == "__main__":
    unittest.main()
