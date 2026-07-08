import unittest
from unittest.mock import patch

from views import customer_profile_views


class ColunaFake:
    def metric(self, label, value):
        return None


class FormFake:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class StreamlitFake:
    def __init__(self, *, submit=False):
        self.submit = submit
        self.titles = []
        self.captions = []
        self.infos = []
        self.successes = []
        self.errors = []
        self.warnings = []
        self.markdowns = []
        self.selectboxes = []
        self.checkboxes = []

    def title(self, texto):
        self.titles.append(texto)

    def caption(self, texto):
        self.captions.append(texto)

    def info(self, texto):
        self.infos.append(texto)

    def success(self, texto):
        self.successes.append(texto)

    def error(self, texto):
        self.errors.append(texto)

    def warning(self, texto):
        self.warnings.append(texto)

    def markdown(self, texto):
        self.markdowns.append(texto)

    def columns(self, quantidade):
        return [ColunaFake() for _ in range(quantidade)]

    def form(self, nome):
        return FormFake()

    def selectbox(self, label, options, index=0):
        self.selectboxes.append((label, options, index))
        return options[index]

    def checkbox(self, label, value=False):
        self.checkboxes.append((label, value))
        return value

    def form_submit_button(self, label):
        return self.submit


class CustomerProfileViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(customer_profile_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_renderiza_perfil_sem_supabase(self):
        fake = self.usar_streamlit(StreamlitFake())

        with patch.object(customer_profile_views, "buscar_perfil_cliente", return_value=None):
            customer_profile_views.render_meu_perfil("user-1", "pessoa@example.com")

        self.assertEqual(fake.titles, ["Meu Perfil"])
        self.assertTrue(fake.infos)
        self.assertTrue(any("Próxima orientação" in texto for texto in fake.markdowns))
        self.assertEqual(len(fake.selectboxes), 6)

    def test_salva_perfil_quando_formulario_e_enviado(self):
        fake = self.usar_streamlit(StreamlitFake(submit=True))

        with patch.object(customer_profile_views, "buscar_perfil_cliente", return_value=None):
            with patch.object(customer_profile_views, "salvar_perfil_cliente") as salvar:
                customer_profile_views.render_meu_perfil("user-1", "pessoa@example.com")

        salvar.assert_called_once()
        payload = salvar.call_args.args[0]
        self.assertEqual(payload["user_id"], "user-1")
        self.assertTrue(payload["aceita_personalizacao"])
        self.assertTrue(fake.successes)


if __name__ == "__main__":
    unittest.main()
