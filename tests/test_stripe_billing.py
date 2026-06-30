import unittest
from types import SimpleNamespace

from utils.stripe_billing import (
    STRIPE_API_VERSION,
    construir_evento_webhook,
    criar_checkout_assinatura,
    extrair_assinatura_de_evento,
    plano_por_price_id,
    price_id_por_plano,
)


class CheckoutSessionFake:
    chamadas = []

    @classmethod
    def create(cls, **kwargs):
        cls.chamadas.append(kwargs)
        return {"id": "cs_test_123", **kwargs}


class WebhookFake:
    chamada = None

    @classmethod
    def construct_event(cls, payload, assinatura, webhook_secret):
        cls.chamada = (payload, assinatura, webhook_secret)
        return {"type": "checkout.session.completed"}


class StripeFake:
    api_key = None
    api_version = None
    checkout = SimpleNamespace(Session=CheckoutSessionFake)
    Webhook = WebhookFake


class StripeBillingTests(unittest.TestCase):
    def setUp(self):
        StripeFake.api_key = None
        StripeFake.api_version = None
        CheckoutSessionFake.chamadas = []
        WebhookFake.chamada = None
        self.secrets = {
            "STRIPE_PRICE_PRO": "price_pro",
            "STRIPE_PRICE_FAMILIA": "price_familia",
        }

    def test_cria_checkout_de_assinatura_com_metadados_do_usuario(self):
        sessao = criar_checkout_assinatura(
            stripe_module=StripeFake,
            stripe_secret_key="sk_test",
            price_id="price_pro",
            usuario_id="user-1",
            email_usuario="pedro@example.com",
            plano="pro",
            success_url="https://app.test/sucesso",
            cancel_url="https://app.test/cancelado",
        )

        self.assertEqual(StripeFake.api_key, "sk_test")
        self.assertEqual(StripeFake.api_version, STRIPE_API_VERSION)
        self.assertEqual(sessao["mode"], "subscription")
        self.assertEqual(sessao["customer_email"], "pedro@example.com")
        self.assertEqual(sessao["client_reference_id"], "user-1")
        self.assertEqual(sessao["line_items"], [{"price": "price_pro", "quantity": 1}])
        self.assertEqual(sessao["metadata"], {"user_id": "user-1", "plano": "pro"})
        self.assertEqual(sessao["subscription_data"]["metadata"]["user_id"], "user-1")

    def test_checkout_rejeita_plano_gratuito_ou_sem_configuracao(self):
        with self.assertRaisesRegex(ValueError, "planos pagos"):
            criar_checkout_assinatura(
                stripe_module=StripeFake,
                stripe_secret_key="sk_test",
                price_id="price_pro",
                usuario_id="user-1",
                email_usuario="pedro@example.com",
                plano="gratuito",
                success_url="https://app.test/sucesso",
                cancel_url="https://app.test/cancelado",
            )

        with self.assertRaisesRegex(ValueError, "STRIPE_SECRET_KEY"):
            criar_checkout_assinatura(
                stripe_module=StripeFake,
                stripe_secret_key="",
                price_id="price_pro",
                usuario_id="user-1",
                email_usuario="pedro@example.com",
                plano="pro",
                success_url="https://app.test/sucesso",
                cancel_url="https://app.test/cancelado",
            )

    def test_resolve_price_id_por_plano(self):
        self.assertEqual(price_id_por_plano("pro", self.secrets), "price_pro")
        self.assertEqual(price_id_por_plano("familia", self.secrets), "price_familia")
        self.assertEqual(price_id_por_plano("gratuito", self.secrets), "")
        self.assertEqual(plano_por_price_id("price_familia", self.secrets), "familia")
        self.assertEqual(plano_por_price_id("desconhecido", self.secrets), "gratuito")

    def test_constroi_evento_webhook_com_assinatura(self):
        evento = construir_evento_webhook(
            stripe_module=StripeFake,
            payload=b"{}",
            assinatura="assinatura",
            webhook_secret="whsec_test",
        )

        self.assertEqual(evento["type"], "checkout.session.completed")
        self.assertEqual(WebhookFake.chamada, (b"{}", "assinatura", "whsec_test"))

    def test_extrai_assinatura_de_checkout_completed(self):
        evento = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": "user-1",
                    "customer": "cus_123",
                    "subscription": "sub_123",
                    "metadata": {"plano": "familia"},
                    "line_items": {"data": [{"price": {"id": "price_familia"}}]},
                }
            },
        }

        assinatura = extrair_assinatura_de_evento(evento, self.secrets)

        self.assertEqual(assinatura["owner_id"], "user-1")
        self.assertEqual(assinatura["plano"], "familia")
        self.assertEqual(assinatura["status"], "ativo")
        self.assertEqual(assinatura["provider"], "stripe")
        self.assertEqual(assinatura["stripe_customer_id"], "cus_123")
        self.assertEqual(assinatura["stripe_subscription_id"], "sub_123")
        self.assertEqual(assinatura["stripe_price_id"], "price_familia")
        self.assertEqual(assinatura["limite_membros"], 4)

    def test_extrai_assinatura_de_subscription_updated(self):
        evento = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "past_due",
                    "current_period_end": 1782864000,
                    "metadata": {"user_id": "user-1"},
                    "items": {"data": [{"price": {"id": "price_pro"}}]},
                }
            },
        }

        assinatura = extrair_assinatura_de_evento(evento, self.secrets)

        self.assertEqual(assinatura["owner_id"], "user-1")
        self.assertEqual(assinatura["plano"], "pro")
        self.assertEqual(assinatura["status"], "past_due")
        self.assertEqual(assinatura["limite_membros"], 1)
        self.assertEqual(assinatura["current_period_end"], "2026-07-01T00:00:00+00:00")

    def test_evento_ignorado_ou_sem_usuario_nao_altera_assinatura(self):
        self.assertIsNone(extrair_assinatura_de_evento({"type": "invoice.created"}, self.secrets))
        self.assertIsNone(
            extrair_assinatura_de_evento(
                {"type": "customer.subscription.updated", "data": {"object": {}}},
                self.secrets,
            )
        )


if __name__ == "__main__":
    unittest.main()
