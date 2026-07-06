import unittest
from unittest.mock import patch

from views import subscription_views


class ColunaFake:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def metric(self, label, value):
        return None


class StreamlitFake:
    def __init__(self, botoes_clicados=None):
        self.titles = []
        self.captions = []
        self.markdowns = []
        self.buttons = []
        self.link_buttons = []
        self.successes = []
        self.infos = []
        self.errors = []
        self.session_state = {}
        self.botoes_clicados = set(botoes_clicados or [])

    def title(self, texto):
        self.titles.append(texto)

    def caption(self, texto):
        self.captions.append(texto)

    def markdown(self, texto):
        self.markdowns.append(texto)

    def columns(self, quantidade):
        return [ColunaFake() for _ in range(quantidade)]

    def metric(self, label, value):
        return None

    def button(self, label, **kwargs):
        self.buttons.append((label, kwargs))
        return label in self.botoes_clicados

    def link_button(self, label, url, **kwargs):
        self.link_buttons.append((label, url, kwargs))

    def success(self, texto):
        self.successes.append(texto)

    def info(self, texto):
        self.infos.append(texto)

    def error(self, texto):
        self.errors.append(texto)


class SubscriptionViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(subscription_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_upgrade_fica_bloqueado_sem_stripe_configurado(self):
        fake = self.usar_streamlit(StreamlitFake())

        subscription_views.render_meu_plano(
            {"plano": "gratuito", "status": "ativo", "limite_membros": 1},
            {},
        )

        self.assertEqual(fake.titles, ["Meu Plano"])
        self.assertTrue(fake.infos)
        self.assertTrue(any("Upgrade em breve" in texto for texto in fake.captions))
        self.assertTrue(all(kwargs.get("disabled") for _, kwargs in fake.buttons))

    def test_indica_stripe_pronto_quando_chaves_estao_configuradas(self):
        fake = self.usar_streamlit(StreamlitFake())

        subscription_views.render_meu_plano(
            {"plano": "pro", "status": "ativo", "limite_membros": 1},
            {
                "STRIPE_SECRET_KEY": "sk_test",
                "STRIPE_PRICE_PRO": "price_pro",
                "STRIPE_PRICE_FAMILIA": "price_familia",
            },
        )

        self.assertTrue(fake.successes)
        self.assertTrue(any("Plano atual" in texto for texto in fake.successes))
        self.assertTrue(any("Fazer upgrade para Família" == label for label, _ in fake.buttons))
        self.assertTrue(any(not kwargs.get("disabled") for _, kwargs in fake.buttons))

    def test_clique_em_upgrade_cria_link_de_checkout(self):
        fake = self.usar_streamlit(StreamlitFake(botoes_clicados={"Fazer upgrade para Pro"}))

        with patch.object(subscription_views, "_criar_url_checkout", return_value="https://checkout.stripe.test/sessao"):
            subscription_views.render_meu_plano(
                {"plano": "gratuito", "status": "ativo", "limite_membros": 1},
                {
                    "STRIPE_SECRET_KEY": "sk_test",
                    "STRIPE_PRICE_PRO": "price_pro",
                    "STRIPE_PRICE_FAMILIA": "price_familia",
                },
                usuario_id="user-1",
                email_usuario="pedro@example.com",
            )

        self.assertEqual(fake.session_state["checkout_url_pro"], "https://checkout.stripe.test/sessao")
        self.assertTrue(fake.link_buttons)
        self.assertEqual(fake.link_buttons[0][1], "https://checkout.stripe.test/sessao")


if __name__ == "__main__":
    unittest.main()
