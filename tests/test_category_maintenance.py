import unittest

from utils.category_maintenance import (
    CATEGORIA_FALLBACK_RECLASSIFICACAO,
    CATEGORIA_TRANSPORTE,
    carregar_mapa_reclassificacao,
    extrair_descricoes_para_reclassificar,
    montar_prompt_reclassificacao_categorias,
    preparar_atualizacoes_reclassificacao,
    selecionar_linhas_para_reclassificar,
    selecionar_transacoes_de_transporte,
)


class CategoryMaintenanceTests(unittest.TestCase):
    def test_seleciona_apenas_transacoes_de_transporte_a_corrigir(self):
        transacoes = [
            {"id": 1, "descricao": "PMBMETRO Bilhete", "categoria": "Geral"},
            {"id": 2, "descricao": "Mercado", "categoria": "Geral"},
            {"id": 3, "descricao": "Metro recarga", "categoria": CATEGORIA_TRANSPORTE},
        ]

        resultado = selecionar_transacoes_de_transporte(transacoes)

        self.assertEqual(resultado, [transacoes[0]])

    def test_seleciona_linhas_reclassificaveis_com_descricao(self):
        transacoes = [
            {"id": 1, "descricao": "Compra A", "categoria": "Compras & Assinaturas"},
            {"id": 2, "descricao": "Compra B", "categoria": "Geral"},
            {"id": 3, "descricao": "Compra C", "categoria": None},
            {"id": 4, "descricao": "", "categoria": "Geral"},
            {"id": 5, "descricao": "Mercado", "categoria": "Mercado"},
        ]

        resultado = selecionar_linhas_para_reclassificar(transacoes)

        self.assertEqual(resultado, transacoes[:3])
        self.assertEqual(
            extrair_descricoes_para_reclassificar(resultado),
            ["Compra A", "Compra B", "Compra C"],
        )

    def test_monta_prompt_com_descricoes_e_categorias_permitidas(self):
        prompt = montar_prompt_reclassificacao_categorias(["Compra A"])

        self.assertIn("categorias permitidas", prompt)
        self.assertIn("Compra A", prompt)
        self.assertIn("Mercado", prompt)
        self.assertIn('{"item_descricao": "Categoria"}', prompt)

    def test_carrega_mapa_reclassificacao(self):
        mapa = carregar_mapa_reclassificacao(' {"Compra A": "Mercado"} ')

        self.assertEqual(mapa, {"Compra A": "Mercado"})

    def test_prepara_atualizacoes_com_fallback_para_categoria_invalida(self):
        transacoes = [
            {"id": 1, "descricao": "Compra A"},
            {"id": 2, "descricao": "Compra B"},
            {"id": 3, "descricao": "Compra C"},
        ]
        mapa = {
            "Compra A": "Mercado",
            "Compra B": "Categoria Invalida",
        }

        resultado = preparar_atualizacoes_reclassificacao(transacoes, mapa)

        self.assertEqual(
            resultado,
            [
                (1, "Mercado"),
                (2, CATEGORIA_FALLBACK_RECLASSIFICACAO),
                (3, CATEGORIA_FALLBACK_RECLASSIFICACAO),
            ],
        )


if __name__ == "__main__":
    unittest.main()
