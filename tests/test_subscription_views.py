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
    def __init__(self, botoes_clicados=None, entradas=None):
        self.titles = []
        self.captions = []
        self.markdowns = []
        self.buttons = []
        self.link_buttons = []
        self.successes = []
        self.infos = []
        self.warnings = []
        self.errors = []
        self.text_inputs = []
        self.session_state = {}
        self.botoes_clicados = set(botoes_clicados or [])
        self.entradas = dict(entradas or {})

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

    def text_input(self, label, value="", **kwargs):
        self.text_inputs.append((label, value, kwargs))
        return self.entradas.get(label, value)

    def success(self, texto):
        self.successes.append(texto)

    def info(self, texto):
        self.infos.append(texto)

    def warning(self, texto):
        self.warnings.append(texto)

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
        self.assertTrue(any("plano gratuito" in texto for texto in fake.infos))
        self.assertTrue(all(kwargs.get("disabled") for _, kwargs in fake.buttons))
        texto_cliente = "\n".join(fake.markdowns + fake.captions + fake.infos + fake.successes)
        self.assertNotIn("monetização", texto_cliente.lower())
        self.assertNotIn("webhook", texto_cliente.lower())
        self.assertNotIn("modo teste", texto_cliente.lower())

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
        self.assertTrue(any("Seu plano está ativo" in texto for texto in fake.successes))
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

    def test_selecionar_upgrade_limpa_checkout_anterior(self):
        fake = self.usar_streamlit(StreamlitFake(botoes_clicados={"Fazer upgrade para Pro"}))
        fake.session_state["checkout_url_familia"] = "https://checkout.stripe.test/familia"

        with patch.object(subscription_views, "_criar_url_checkout", return_value="https://checkout.stripe.test/pro"):
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

        self.assertEqual(fake.session_state["checkout_url_pro"], "https://checkout.stripe.test/pro")
        self.assertNotIn("checkout_url_familia", fake.session_state)
        self.assertEqual(len(fake.link_buttons), 1)
        self.assertEqual(fake.link_buttons[0][1], "https://checkout.stripe.test/pro")

    def test_plano_nao_familia_nao_libera_gestao_de_membros(self):
        fake = self.usar_streamlit(StreamlitFake())

        subscription_views.render_meu_plano(
            {"plano": "pro", "status": "ativo", "limite_membros": 1},
            {},
        )

        self.assertTrue(any("conta própria" in texto for texto in fake.captions))
        self.assertTrue(any("Plano Família" in texto for texto in fake.infos))
        self.assertFalse(any(label == "Enviar convite" for label, _ in fake.buttons))

    def test_plano_familia_lista_membros_e_permite_convite(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                botoes_clicados={"Enviar convite"},
                entradas={"E-mail do novo membro": " Pessoa@Exemplo.com "},
            )
        )

        with patch.object(subscription_views, "listar_familias_financeiras", return_value=[{"id": "family-1", "nome": "Casa"}]):
            with patch.object(
                subscription_views,
                "listar_membros_familia_financeira",
                return_value=[
                    {"email_convite": "dono@example.com", "papel": "dono", "status": "ativo"},
                    {"email_convite": "filha@example.com", "papel": "membro", "status": "pendente"},
                ],
            ):
                with patch.object(subscription_views, "convidar_membro_familia_financeira") as convidar:
                    subscription_views.render_meu_plano(
                        {"plano": "familia", "status": "ativo", "limite_membros": 4},
                        {},
                    )

        convidar.assert_called_once_with("family-1", "pessoa@exemplo.com")
        self.assertTrue(any("Família ativa: Casa" in texto for texto in fake.successes))
        self.assertTrue(any("2 de 4 pessoas" in texto for texto in fake.captions))
        self.assertTrue(any("dono@example.com" in texto for texto in fake.markdowns))

    def test_plano_familia_orienta_criacao_quando_nao_existe_grupo(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                botoes_clicados={"Criar família"},
                entradas={"Nome da família": " Casa Silva "},
            )
        )

        with patch.object(subscription_views, "listar_familias_financeiras", return_value=[]):
            with patch.object(subscription_views, "criar_familia_financeira") as criar:
                subscription_views.render_meu_plano(
                    {"plano": "familia", "status": "ativo", "limite_membros": 4},
                    {},
                )

        criar.assert_called_once_with("Casa Silva")
        self.assertTrue(any("Família criada" in texto for texto in fake.successes))


if __name__ == "__main__":
    unittest.main()
