import unittest

from utils.subscriptions import (
    assinatura_ativa,
    limite_membros_do_plano,
    normalizar_plano,
    pode_usar_plano_familia,
    pode_usar_plano_pro,
    rotulo_plano,
)


class SubscriptionsTests(unittest.TestCase):
    def test_normaliza_planos_conhecidos_e_desconhecidos(self):
        self.assertEqual(normalizar_plano(" Pro "), "pro")
        self.assertEqual(normalizar_plano("FAMILIA"), "familia")
        self.assertEqual(normalizar_plano("enterprise"), "gratuito")
        self.assertEqual(normalizar_plano(None), "gratuito")

    def test_limites_por_plano(self):
        self.assertEqual(limite_membros_do_plano("gratuito"), 1)
        self.assertEqual(limite_membros_do_plano("pro"), 1)
        self.assertEqual(limite_membros_do_plano("familia"), 4)

    def test_rotulo_do_plano_e_pronto_para_interface(self):
        self.assertEqual(rotulo_plano("gratuito"), "Gratuito")
        self.assertEqual(rotulo_plano("pro"), "Pro")
        self.assertEqual(rotulo_plano("familia"), "Família")
        self.assertEqual(rotulo_plano("desconhecido"), "Gratuito")

    def test_status_ativo_ou_trial_liberam_recursos(self):
        self.assertTrue(assinatura_ativa({"status": "ativo"}))
        self.assertTrue(assinatura_ativa({"status": "trial"}))
        self.assertFalse(assinatura_ativa({"status": "past_due"}))
        self.assertFalse(assinatura_ativa(None))

    def test_plano_pro_inclui_familia_com_assinatura_ativa(self):
        self.assertTrue(pode_usar_plano_pro({"plano": "pro", "status": "ativo"}))
        self.assertTrue(pode_usar_plano_pro({"plano": "familia", "status": "trial"}))
        self.assertFalse(pode_usar_plano_pro({"plano": "gratuito", "status": "ativo"}))
        self.assertFalse(pode_usar_plano_pro({"plano": "pro", "status": "cancelado"}))

    def test_plano_familia_exige_assinatura_familia_ativa(self):
        self.assertTrue(pode_usar_plano_familia({"plano": "familia", "status": "ativo"}))
        self.assertFalse(pode_usar_plano_familia({"plano": "pro", "status": "ativo"}))
        self.assertFalse(pode_usar_plano_familia({"plano": "familia", "status": "past_due"}))


if __name__ == "__main__":
    unittest.main()
