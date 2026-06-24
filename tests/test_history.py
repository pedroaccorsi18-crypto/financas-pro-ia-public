import unittest

from finance_constants import ORIGEM_AUTOMATICA, ORIGEM_MANUAL, TIPO_DESPESA, TIPO_RECEITA
from utils.history import formatar_linha_historico


class HistoryTests(unittest.TestCase):
    def test_formata_linha_de_despesa_manual_com_categoria(self):
        linha = formatar_linha_historico(
            {
                "descricao": "Uber",
                "valor": 42.5,
                "tipo": TIPO_DESPESA,
                "categoria": "Transporte",
                "instituicao_financeira": "Nubank",
                "origem_importacao": ORIGEM_MANUAL,
            }
        )

        self.assertEqual(
            linha,
            "🔴 **Uber** [Transporte] | R$ 42,50 (Saída | ✍️ Nubank)",
        )

    def test_formata_linha_de_receita_importada_sem_categoria(self):
        linha = formatar_linha_historico(
            {
                "descricao": "Credito",
                "valor": 100,
                "tipo": TIPO_RECEITA,
                "categoria": "Compras Gerais",
                "instituicao_financeira": "Banco A",
                "origem_importacao": ORIGEM_AUTOMATICA,
            }
        )

        self.assertEqual(
            linha,
            "🟢 **Credito** | R$ 100,00 (Entrada | 🤖 Banco A)",
        )

    def test_usa_instituicao_manual_e_categoria_geral_como_fallback(self):
        linha = formatar_linha_historico(
            {
                "descricao": "Compra",
                "valor": 10,
                "tipo": TIPO_DESPESA,
            }
        )

        self.assertEqual(
            linha,
            "🔴 **Compra** [Geral] | R$ 10,00 (Saída | 🤖 Manual)",
        )


if __name__ == "__main__":
    unittest.main()
