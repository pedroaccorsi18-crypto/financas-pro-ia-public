import unittest

from utils.market_radar import (
    calcular_score_radar,
    classificar_score_radar,
    filtrar_radar_mercado,
    gerar_radar_mercado,
    resumir_radar_mercado,
)


class MarketRadarTests(unittest.TestCase):
    def test_score_penaliza_risco_e_limita_entre_zero_e_cem(self):
        score = calcular_score_radar(
            {
                "momentum": 100,
                "qualidade": 100,
                "valuation": 100,
                "liquidez": 100,
                "risco": 100,
            }
        )

        self.assertEqual(score, 80)

    def test_classificacao_do_radar_por_score(self):
        self.assertEqual(classificar_score_radar(80), "Radar forte")
        self.assertEqual(classificar_score_radar(60), "Monitorar")
        self.assertEqual(classificar_score_radar(59), "Acompanhar com cautela")

    def test_radar_demo_retorna_lista_ordenada_com_status(self):
        radar = gerar_radar_mercado()

        self.assertGreaterEqual(len(radar), 5)
        self.assertGreaterEqual(radar[0]["score"], radar[-1]["score"])
        self.assertIn("status", radar[0])
        self.assertIn("alerta", radar[0])

    def test_filtra_por_classe_e_perfil(self):
        radar = gerar_radar_mercado()
        filtrado = filtrar_radar_mercado(radar, classe="ETF", perfil="Moderado")

        self.assertTrue(filtrado)
        self.assertTrue(all(item["classe"] == "ETF" for item in filtrado))
        self.assertTrue(all(item["perfil"] == "Moderado" for item in filtrado))

    def test_resumo_do_radar_agrega_indicadores(self):
        radar = gerar_radar_mercado()
        resumo = resumir_radar_mercado(radar)

        self.assertEqual(resumo["total"], len(radar))
        self.assertIsNotNone(resumo["maior_score"])
        self.assertGreaterEqual(resumo["risco_medio"], 0)


if __name__ == "__main__":
    unittest.main()
