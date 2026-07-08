import asyncio
import unittest
from http import HTTPStatus

from api.stripe_webhook import app, processar_requisicao_webhook


class RpcFake:
    def __init__(self, data=None):
        self.data = data

    def execute(self):
        return self


class SupabaseFake:
    def __init__(self):
        self.rpcs = []

    def rpc(self, nome, payload):
        self.rpcs.append((nome, payload))
        return RpcFake({"nome": nome})


class StripeWebhookEndpointTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "SUPABASE_URL": "https://projeto.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-test",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "STRIPE_PRICE_PRO": "price_pro",
            "STRIPE_PRICE_FAMILIA": "price_familia",
        }

    def test_processa_webhook_com_cliente_service_role(self):
        clientes = []
        chamadas = []

        def criar_cliente(url, chave):
            cliente = SupabaseFake()
            clientes.append((url, chave, cliente))
            return cliente

        def processar_webhook(**kwargs):
            chamadas.append(kwargs)
            kwargs["registrar_evento"]({"id": "evt_123", "type": "checkout.session.completed"})
            kwargs["sincronizar_assinatura"](
                {
                    "owner_id": "user-1",
                    "plano": "pro",
                    "status": "ativo",
                    "stripe_customer_id": "cus_123",
                    "stripe_subscription_id": "sub_123",
                    "stripe_price_id": "price_pro",
                    "limite_membros": 1,
                    "current_period_end": None,
                }
            )
            return {"processado": True, "tipo": "checkout.session.completed"}

        status, resposta = processar_requisicao_webhook(
            payload=b"{}",
            assinatura_header="sig_test",
            env=self.env,
            criar_cliente=criar_cliente,
            processar_webhook=processar_webhook,
        )

        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(resposta["ok"])
        self.assertTrue(resposta["processado"])
        self.assertEqual(clientes[0][0], "https://projeto.supabase.co")
        self.assertEqual(clientes[0][1], "service-role-test")
        self.assertEqual(chamadas[0]["assinatura_header"], "sig_test")
        self.assertEqual(clientes[0][2].rpcs[0][0], "registrar_evento_pagamento_stripe")
        self.assertEqual(clientes[0][2].rpcs[1][0], "sincronizar_assinatura_stripe")

    def test_recusa_secrets_obrigatorios_ausentes(self):
        status, resposta = processar_requisicao_webhook(
            payload=b"{}",
            assinatura_header="sig_test",
            env={},
            criar_cliente=lambda url, chave: SupabaseFake(),
            processar_webhook=lambda **kwargs: {"processado": False},
        )

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertFalse(resposta["ok"])

    def test_app_asgi_health(self):
        mensagens = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(mensagem):
            mensagens.append(mensagem)

        asyncio.run(
            app(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/health",
                    "headers": [],
                },
                receive,
                send,
            )
        )

        self.assertEqual(mensagens[0]["status"], 200)
        self.assertIn(b'"status": "ok"', mensagens[1]["body"])


if __name__ == "__main__":
    unittest.main()
