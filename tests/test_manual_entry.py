import unittest

from finance_constants import ORIGEM_MANUAL, TIPO_DESPESA, TIPO_DOCUMENTO_MANUAL
from utils.manual_entry import preparar_transacao_manual


class ManualEntryTests(unittest.TestCase):
    def test_monta_payload_do_lancamento_manual(self):
        payload = preparar_transacao_manual(
            descricao=" Uber ",
            valor="42.50",
            tipo_transacao=TIPO_DESPESA,
            categoria="Transporte",
            categorias_validas=["Mercado", "Transporte", "Outros"],
            mes_referencia="06/2026",
            instituicao=" Nubank ",
            usuario_id="user-123",
            email_usuario="usuario@example.com",
        )

        self.assertEqual(
            payload,
            {
                "user_id": "user-123",
                "usuario_email": "usuario@example.com",
                "descricao": "Uber",
                "valor": 42.5,
                "tipo": TIPO_DESPESA,
                "categoria": "Transporte",
                "mes_referencia": "06/2026",
                "meta_fatura": 0.0,
                "instituicao_financeira": "Nubank",
                "tipo_documento": TIPO_DOCUMENTO_MANUAL,
                "origem_importacao": ORIGEM_MANUAL,
            },
        )

    def test_preserva_fallback_de_categoria_e_instituicao_manual(self):
        payload = preparar_transacao_manual(
            descricao="Compra",
            valor=10,
            tipo_transacao=TIPO_DESPESA,
            categoria="Categoria inexistente",
            categorias_validas=["Mercado", "Outros"],
            mes_referencia="06/2026",
            instituicao="",
            usuario_id="user-123",
            email_usuario="usuario@example.com",
        )

        self.assertEqual(payload["categoria"], "Outros")
        self.assertEqual(payload["instituicao_financeira"], ORIGEM_MANUAL)


if __name__ == "__main__":
    unittest.main()
