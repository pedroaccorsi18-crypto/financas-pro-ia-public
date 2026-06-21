import unittest

from utils.authorization import eh_usuario_admin
from utils.formatting import formatar_brl
from utils.privacy import anonimizar_dados


class FormattingTests(unittest.TestCase):
    def test_formata_valor_positivo_em_brl(self):
        self.assertEqual(formatar_brl(1234.56), "R$ 1.234,56")

    def test_formata_valor_negativo_em_brl(self):
        self.assertEqual(formatar_brl(-1234.56), "R$ -1.234,56")

    def test_formata_zero_em_brl(self):
        self.assertEqual(formatar_brl(0), "R$ 0,00")

    def test_preserva_fallback_para_valor_invalido(self):
        self.assertEqual(formatar_brl(object()), "R$ 0,00")


class PrivacyTests(unittest.TestCase):
    def test_texto_vazio_retorna_vazio(self):
        self.assertEqual(anonimizar_dados(""), "")
        self.assertEqual(anonimizar_dados(None), "")

    def test_anonimiza_valores_financeiros(self):
        texto = "Total R$ 1.234,56 e parcela 78,90."
        self.assertEqual(
            anonimizar_dados(texto),
            "Total [VALOR_OCULTO] e parcela [NUMERO_OCULTO].",
        )

    def test_preserva_texto_sem_valores_financeiros(self):
        texto = "Relatorio aprovado sem valores numericos."
        self.assertEqual(anonimizar_dados(texto), texto)


class AuthorizationTests(unittest.TestCase):
    def test_reconhece_admin_configurado_sem_diferenciar_maiusculas(self):
        self.assertTrue(
            eh_usuario_admin(
                " Admin@Exemplo.com ",
                ["admin@exemplo.com", "outro@exemplo.com"],
            )
        )

    def test_rejeita_email_nao_configurado(self):
        self.assertFalse(
            eh_usuario_admin("usuario@exemplo.com", ["admin@exemplo.com"])
        )

    def test_aceita_um_unico_email_configurado_como_texto(self):
        self.assertTrue(
            eh_usuario_admin("admin@exemplo.com", "admin@exemplo.com")
        )

    def test_rejeita_configuracao_ausente_ou_invalida(self):
        self.assertFalse(eh_usuario_admin("admin@exemplo.com", None))
        self.assertFalse(eh_usuario_admin(None, ["admin@exemplo.com"]))


if __name__ == "__main__":
    unittest.main()
