import unittest

from utils.executive_summary import gerar_resumo_executivo_markdown


class ExecutiveSummaryTests(unittest.TestCase):
    def test_resumo_executivo_tem_estrutura_consultiva(self):
        resumo = gerar_resumo_executivo_markdown(
            {
                "idade": 41,
                "dependentes": 1,
                "renda_mensal": 22000,
                "reserva_emergencia": 90000,
                "patrimonio_investido": 450000,
                "dividas": 0,
                "perfil_risco": "Moderado",
                "horizonte": "6 a 10 anos",
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 16000,
                "patrimonio_sucessorio": 300000,
            },
            {"despesas": 14000, "balanco": 5000},
        )

        self.assertIn("# Resumo Executivo - Planejamento Financeiro 360", resumo)
        self.assertIn("## 1. Perfil do cliente", resumo)
        self.assertIn("## 4. Politica de planejamento", resumo)
        self.assertIn("## 7. Suitability e onboarding", resumo)
        self.assertIn("## 8. Roadmap de metas", resumo)
        self.assertIn("## 9. Stress test", resumo)
        self.assertIn("## 10. Preparacao da reuniao", resumo)
        self.assertIn("## 11. Estrategia patrimonial", resumo)
        self.assertIn("## 12. Proximos 90 dias", resumo)
        self.assertIn("Nao constitui recomendacao individualizada", resumo)

    def test_resumo_inclui_gap_de_aposentadoria_quando_dados_completos(self):
        resumo = gerar_resumo_executivo_markdown(
            {
                "idade": 40,
                "renda_mensal": 18000,
                "reserva_emergencia": 50000,
                "patrimonio_investido": 250000,
                "idade_aposentadoria": 65,
                "renda_aposentadoria_desejada": 12000,
            },
            {"despesas": 10000, "balanco": 3000},
        )

        self.assertIn("Anos ate aposentadoria: 25", resumo)
        self.assertIn("Gap estimado no cenario moderado", resumo)
        self.assertIn("Aporte mensal estimado", resumo)

    def test_resumo_lista_pendencias_de_aposentadoria_quando_faltam_dados(self):
        resumo = gerar_resumo_executivo_markdown(
            {"renda_mensal": 10000, "reserva_emergencia": 20000},
            {"despesas": 8000, "balanco": 1000},
        )

        self.assertIn("Informar idade atual", resumo)
        self.assertIn("Informar renda mensal desejada na aposentadoria", resumo)


if __name__ == "__main__":
    unittest.main()
