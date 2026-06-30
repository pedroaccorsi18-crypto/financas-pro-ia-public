import unittest

from utils.financial_report import gerar_relatorio_consultivo_360


class FinancialReportTests(unittest.TestCase):
    def test_relatorio_consultivo_tem_secoes_360(self):
        relatorio = gerar_relatorio_consultivo_360(
            {
                "idade": 38,
                "dependentes": 2,
                "renda_mensal": 18000,
                "reserva_emergencia": 30000,
                "dividas": 90000,
                "patrimonio_investido": 120000,
                "perfil_risco": "Moderado",
                "objetivo_principal": "Expandir patrimônio",
                "horizonte": "6 a 10 anos",
                "idade_aposentadoria": 62,
                "renda_aposentadoria_desejada": 15000,
                "patrimonio_sucessorio": 500000,
                "possui_seguro": False,
            },
            {"despesas": 12000, "balanco": 2500},
        )

        self.assertIn("resumo_executivo", relatorio)
        self.assertIn("diagnostico_patrimonial", relatorio)
        self.assertIn("planejamento_financeiro", relatorio)
        self.assertIn("aposentadoria", relatorio)
        self.assertIn("expansao_patrimonial", relatorio)
        self.assertIn("sucessao", relatorio)
        self.assertIn("plano_30_60_90", relatorio)
        self.assertIn("maturidade financeira", relatorio["resumo_executivo"])
        self.assertTrue(
            any("dependentes" in item for item in relatorio["diagnostico_patrimonial"])
        )
        self.assertTrue(any("jurídico" in item for item in relatorio["sucessao"]))

    def test_relatorio_pede_dados_de_aposentadoria_quando_faltam(self):
        relatorio = gerar_relatorio_consultivo_360(
            {
                "renda_mensal": 10000,
                "reserva_emergencia": 60000,
                "dividas": 0,
                "patrimonio_investido": 150000,
            },
            {"despesas": 8000, "balanco": 2000},
        )

        self.assertTrue(
            any("Definir idade alvo" in item for item in relatorio["aposentadoria"])
        )
        self.assertIn("30_dias", relatorio["plano_30_60_90"])
        self.assertIn("60_dias", relatorio["plano_30_60_90"])
        self.assertIn("90_dias", relatorio["plano_30_60_90"])


if __name__ == "__main__":
    unittest.main()
