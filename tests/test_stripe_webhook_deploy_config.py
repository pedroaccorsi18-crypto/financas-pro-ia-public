import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StripeWebhookDeployConfigTests(unittest.TestCase):
    def test_render_config_publica_endpoint_https(self):
        conteudo = (ROOT / "render.yaml").read_text(encoding="utf-8")

        self.assertIn("type: web", conteudo)
        self.assertIn("runtime: python", conteudo)
        self.assertIn("pip install -r requirements.txt", conteudo)
        self.assertIn("uvicorn api.stripe_webhook:app", conteudo)
        self.assertIn("--port $PORT", conteudo)
        self.assertIn("healthCheckPath: /health", conteudo)

    def test_render_config_nao_embute_segredos(self):
        conteudo = (ROOT / "render.yaml").read_text(encoding="utf-8")

        for chave in (
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "STRIPE_PRICE_PRO",
            "STRIPE_PRICE_FAMILIA",
        ):
            self.assertIn(f"key: {chave}", conteudo)

        self.assertNotIn("whsec_", conteudo)
        self.assertNotIn("sk_test_", conteudo)
        self.assertNotIn("sk_live_", conteudo)
        self.assertGreaterEqual(conteudo.count("sync: false"), 5)


if __name__ == "__main__":
    unittest.main()
