import unittest
from pathlib import Path


APP_SOURCE = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
THEME_SOURCE = (Path(__file__).parents[1] / "views" / "app_theme.py").read_text(
    encoding="utf-8"
)


class AppThemeTests(unittest.TestCase):
    def test_tema_interno_fica_centralizado_em_modulo_proprio(self):
        self.assertIn("def aplicar_tema_interno", THEME_SOURCE)
        self.assertIn("TEMA_INTERNO_PREMIUM_CSS", THEME_SOURCE)
        self.assertIn("fp-sidebar-brand", THEME_SOURCE)
        self.assertIn("fp-user-card", THEME_SOURCE)
        self.assertIn("fp-plan-pill", THEME_SOURCE)

    def test_app_aplica_tema_no_fluxo_autenticado(self):
        trecho = APP_SOURCE.split("def render_app_autenticado", 1)[-1]

        self.assertIn("from views.app_theme import aplicar_tema_interno", APP_SOURCE)
        self.assertIn("aplicar_tema_interno()", trecho)

    def test_sidebar_premium_escapa_dados_do_usuario(self):
        self.assertIn("from html import escape", APP_SOURCE)
        self.assertIn("email_usuario_seguro = escape(str(email_usuario))", APP_SOURCE)
        self.assertIn("plano_atual_seguro = escape(str(plano_atual))", APP_SOURCE)
        self.assertIn("unsafe_allow_html=True", APP_SOURCE)


if __name__ == "__main__":
    unittest.main()
