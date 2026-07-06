import unittest

from utils.stripe_webhook import processar_webhook_stripe


class WebhookFake:
    evento = None
    chamada = None

    @classmethod
    def construct_event(cls, payload, assinatura, webhook_secret):
        cls.chamada = (payload, assinatura, webhook_secret)
        return cls.evento


class StripeFake:
    Webhook = WebhookFake


class StripeObjectFake:
    def __init__(self, evento):
        self.evento = evento

    def to_dict_recursive(self):
        return self.evento


class StripeWebhookTests(unittest.TestCase):
    def setUp(self):
        WebhookFake.evento = None
        WebhookFake.chamada = None
        self.secrets = {
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "STRIPE_PRICE_PRO": "price_pro",
            "STRIPE_PRICE_FAMILIA": "price_familia",
        }

    def test_processa_checkout_completed_e_sincroniza_assinatura(self):
        WebhookFake.evento = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": "user-1",
                    "customer": "cus_123",
                    "subscription": "sub_123",
                    "metadata": {"plano": "pro", "user_id": "user-1"},
                    "line_items": {"data": [{"price": {"id": "price_pro"}}]},
                }
            },
        }
        eventos_registrados = []
        assinaturas = []

        resultado = processar_webhook_stripe(
            payload=b"{}",
            assinatura_header="sig_test",
            secrets=self.secrets,
            stripe_module=StripeFake,
            registrar_evento=eventos_registrados.append,
            sincronizar_assinatura=lambda assinatura: assinaturas.append(assinatura) or {"plano": "pro"},
        )

        self.assertTrue(resultado["processado"])
        self.assertEqual(resultado["assinatura"], {"plano": "pro"})
        self.assertEqual(eventos_registrados[0]["id"], "evt_123")
        self.assertEqual(assinaturas[0]["owner_id"], "user-1")
        self.assertEqual(assinaturas[0]["plano"], "pro")
        self.assertEqual(assinaturas[0]["limite_membros"], 1)
        self.assertEqual(WebhookFake.chamada, (b"{}", "sig_test", "whsec_test"))

    def test_evento_sem_alteracao_de_assinatura_e_apenas_registrado(self):
        WebhookFake.evento = {
            "id": "evt_invoice",
            "type": "invoice.created",
            "data": {"object": {}},
        }
        eventos_registrados = []
        chamadas_sync = []

        resultado = processar_webhook_stripe(
            payload=b"{}",
            assinatura_header="sig_test",
            secrets=self.secrets,
            stripe_module=StripeFake,
            registrar_evento=eventos_registrados.append,
            sincronizar_assinatura=chamadas_sync.append,
        )

        self.assertFalse(resultado["processado"])
        self.assertEqual(resultado["motivo"], "evento_sem_alteracao_de_assinatura")
        self.assertEqual(eventos_registrados[0]["id"], "evt_invoice")
        self.assertEqual(chamadas_sync, [])

    def test_aceita_evento_stripe_object_convertido_para_dict(self):
        WebhookFake.evento = StripeObjectFake(
            {
                "id": "evt_deleted",
                "type": "customer.subscription.deleted",
                "data": {
                    "object": {
                        "id": "sub_123",
                        "customer": "cus_123",
                        "metadata": {"user_id": "user-1"},
                        "items": {"data": [{"price": {"id": "price_familia"}}]},
                    }
                },
            }
        )
        assinaturas = []

        resultado = processar_webhook_stripe(
            payload=b"{}",
            assinatura_header="sig_test",
            secrets=self.secrets,
            stripe_module=StripeFake,
            registrar_evento=lambda evento: None,
            sincronizar_assinatura=lambda assinatura: assinaturas.append(assinatura) or assinatura,
        )

        self.assertTrue(resultado["processado"])
        self.assertEqual(assinaturas[0]["status"], "cancelado")
        self.assertEqual(assinaturas[0]["limite_membros"], 4)

    def test_rejeita_evento_sem_id(self):
        WebhookFake.evento = {"type": "checkout.session.completed", "data": {"object": {}}}

        with self.assertRaisesRegex(ValueError, "sem id"):
            processar_webhook_stripe(
                payload=b"{}",
                assinatura_header="sig_test",
                secrets=self.secrets,
                stripe_module=StripeFake,
            )

    def test_exige_webhook_secret(self):
        WebhookFake.evento = {"id": "evt_123", "type": "invoice.created"}

        with self.assertRaisesRegex(ValueError, "STRIPE_WEBHOOK_SECRET"):
            processar_webhook_stripe(
                payload=b"{}",
                assinatura_header="sig_test",
                secrets={},
                stripe_module=StripeFake,
            )


if __name__ == "__main__":
    unittest.main()
