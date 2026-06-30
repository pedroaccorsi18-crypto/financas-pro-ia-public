import unittest

from utils.family_plan import (
    LIMITE_MEMBROS_FAMILIA,
    normalizar_email_convite,
    pode_adicionar_membro,
    validar_email_convite,
    validar_limite_membros,
    validar_nome_familia,
)


class FamilyPlanTests(unittest.TestCase):
    def test_limite_do_plano_familia_e_quatro_pessoas(self):
        self.assertEqual(LIMITE_MEMBROS_FAMILIA, 4)
        self.assertTrue(pode_adicionar_membro(3))
        self.assertFalse(pode_adicionar_membro(4))

    def test_valida_limite_de_membros(self):
        validar_limite_membros(3)

        with self.assertRaisesRegex(ValueError, "ate 4 pessoas"):
            validar_limite_membros(4)

    def test_normaliza_e_valida_email_de_convite(self):
        self.assertEqual(
            normalizar_email_convite(" Pessoa@Exemplo.com "),
            "pessoa@exemplo.com",
        )
        self.assertEqual(validar_email_convite(" Pessoa@Exemplo.com "), "pessoa@exemplo.com")

        with self.assertRaisesRegex(ValueError, "e-mail valido"):
            validar_email_convite("sem-arroba")

    def test_valida_nome_da_familia(self):
        self.assertEqual(validar_nome_familia(" Casa Silva "), "Casa Silva")

        with self.assertRaisesRegex(ValueError, "nome para a familia"):
            validar_nome_familia(" ")


if __name__ == "__main__":
    unittest.main()
