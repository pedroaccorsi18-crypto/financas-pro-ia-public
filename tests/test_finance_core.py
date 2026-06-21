import unittest

from finance_core import (
    calcular_resumo_financeiro,
    criar_lote_demonstrativo,
    lotes_sao_iguais,
    mes_referencia_valido,
    ordenar_meses_cronologicamente,
    resumir_historico_para_ia,
)


class FinanceCoreTests(unittest.TestCase):
    def test_soma_documentos_distintos_da_mesma_instituicao(self):
        transacoes = [
            {
                "tipo": "Despesa",
                "valor": 100,
                "meta_fatura": 100,
                "instituicao_financeira": "Banco A",
                "tipo_documento": "Fatura",
                "mes_referencia": "05/2026",
            },
            {
                "tipo": "Despesa",
                "valor": 250,
                "meta_fatura": 250,
                "instituicao_financeira": "Banco A",
                "tipo_documento": "Extrato",
                "mes_referencia": "05/2026",
            },
        ]
        self.assertEqual(calcular_resumo_financeiro(transacoes)["balanco"], -350.0)

    def test_nao_repete_total_do_mesmo_documento(self):
        base = {
            "tipo": "Despesa",
            "valor": 50,
            "meta_fatura": 100,
            "instituicao_financeira": "Banco A",
            "tipo_documento": "Fatura",
            "mes_referencia": "05/2026",
        }
        self.assertEqual(calcular_resumo_financeiro([base, base])["balanco"], -100.0)

    def test_inclui_movimentos_manuais_no_balanco(self):
        transacoes = [
            {"tipo": "Despesa", "valor": 100, "meta_fatura": 100, "instituicao_financeira": "A"},
            {"tipo": "Despesa", "valor": 20, "meta_fatura": 0},
            {"tipo": "Receita", "valor": 5, "meta_fatura": 0},
        ]
        self.assertEqual(calcular_resumo_financeiro(transacoes)["balanco"], -115.0)

    def test_receita_manual_sem_despesa_gera_balanco_positivo(self):
        transacoes = [
            {"tipo": "Receita", "valor": 6500, "meta_fatura": 0},
        ]
        self.assertEqual(calcular_resumo_financeiro(transacoes)["balanco"], 6500.0)

    def test_meses_invalidos_sao_descartados(self):
        self.assertTrue(mes_referencia_valido("12/2025"))
        self.assertFalse(mes_referencia_valido("13/2025"))
        self.assertEqual(
            ordenar_meses_cronologicamente(["01/2026", None, "13/2025", "12/2025"]),
            ["01/2026", "12/2025"],
        )

    def test_comparacao_de_lotes_independe_da_ordem(self):
        a = {"descricao": "A", "valor": 10, "tipo": "Despesa"}
        b = {"descricao": "B", "valor": 20, "tipo": "Receita"}
        self.assertTrue(lotes_sao_iguais([a, b], [b, a]))

    def test_resumo_para_ia_nao_inclui_descricao(self):
        texto = resumir_historico_para_ia(
            [{"mes_referencia": "05/2026", "categoria": "Mercado", "tipo": "Despesa", "valor": 42, "descricao": "Nome sensível"}]
        )
        self.assertNotIn("Nome sensível", texto)
        self.assertIn("Mercado", texto)

    def test_lote_demonstrativo_e_contabilmente_consistente(self):
        lote = criar_lote_demonstrativo("06/2026")
        despesas = sum(t["valor"] for t in lote["transacoes"] if t["tipo"] == "Despesa")
        receitas = sum(t["valor"] for t in lote["transacoes"] if t["tipo"] == "Receita")
        self.assertAlmostEqual(despesas - receitas, lote["total_documento"], places=2)
        self.assertEqual(lote["mes_referencia"], "06/2026")


if __name__ == "__main__":
    unittest.main()
