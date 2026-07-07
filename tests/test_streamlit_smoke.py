import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


class SessionStateFake(dict):
    def __getattr__(self, nome):
        try:
            return self[nome]
        except KeyError as erro:
            raise AttributeError(nome) from erro

    def __setattr__(self, nome, valor):
        self[nome] = valor


class FormFake:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class ColumnFake:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class StreamlitFake(ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = SessionStateFake()
        self.secrets = {
            "SUPABASE_KEY": "sb_publishable_teste",
            "SUPABASE_URL": "https://projeto-exemplo.supabase.co",
            "GEMINI_API_KEY": "",
        }
        self.titles = []
        self.subheaders = []
        self.captions = []
        self.markdowns = []
        self.forms = []
        self.buttons = []
        self.errors = []
        self.warnings = []

    def set_page_config(self, **kwargs):
        self.page_config = kwargs

    def cache_resource(self, func=None, **kwargs):
        def decorator(recurso):
            return recurso

        if func is not None:
            return decorator(func)
        return decorator

    def title(self, texto):
        self.titles.append(texto)

    def subheader(self, texto):
        self.subheaders.append(texto)

    def caption(self, texto):
        self.captions.append(texto)

    def markdown(self, texto, **kwargs):
        self.markdowns.append(texto)

    def columns(self, quantidade):
        return [ColumnFake() for _ in range(quantidade)]

    def form(self, nome, **kwargs):
        self.forms.append(nome)
        return FormFake()

    def text_input(self, *args, **kwargs):
        return ""

    def form_submit_button(self, *args, **kwargs):
        return False

    def button(self, texto, **kwargs):
        self.buttons.append(texto)
        return False

    def warning(self, mensagem):
        self.warnings.append(mensagem)

    def error(self, mensagem):
        self.errors.append(mensagem)

    def stop(self):
        raise RuntimeError("streamlit stop acionado")

    def rerun(self):
        raise RuntimeError("streamlit rerun acionado")


class StreamlitSmokeTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).parents[1]
        self.modules_originais = {}

    def tearDown(self):
        for nome, modulo in self.modules_originais.items():
            if modulo is None:
                sys.modules.pop(nome, None)
            else:
                sys.modules[nome] = modulo

    def substituir_modulo(self, nome, modulo):
        if nome not in self.modules_originais:
            self.modules_originais[nome] = sys.modules.get(nome)
        if modulo is None:
            sys.modules.pop(nome, None)
        else:
            sys.modules[nome] = modulo

    def importar_app_com_streamlit_fake(self, streamlit_fake):
        supabase_fake = ModuleType("supabase")
        supabase_fake.Client = object
        supabase_fake.create_client = lambda url, chave: object()

        google_fake = ModuleType("google")
        genai_fake = ModuleType("google.genai")
        types_fake = ModuleType("google.genai.types")
        genai_fake.types = types_fake
        google_fake.genai = genai_fake

        plotly_fake = ModuleType("plotly")
        express_fake = ModuleType("plotly.express")
        plotly_fake.express = express_fake

        for nome in ("app_smoke", "auth", "session_state", "views.auth_views"):
            self.substituir_modulo(nome, None)
        self.substituir_modulo("streamlit", streamlit_fake)
        self.substituir_modulo("supabase", supabase_fake)
        self.substituir_modulo("google", google_fake)
        self.substituir_modulo("google.genai", genai_fake)
        self.substituir_modulo("google.genai.types", types_fake)
        self.substituir_modulo("plotly", plotly_fake)
        self.substituir_modulo("plotly.express", express_fake)

        spec = importlib.util.spec_from_file_location(
            "app_smoke",
            self.repo_root / "app.py",
        )
        modulo = importlib.util.module_from_spec(spec)
        self.substituir_modulo("app_smoke", modulo)
        spec.loader.exec_module(modulo)
        return modulo

    def test_app_abre_tela_publica_sem_servicos_externos(self):
        streamlit_fake = StreamlitFake()

        self.importar_app_com_streamlit_fake(streamlit_fake)

        self.assertFalse(streamlit_fake.session_state.autenticado)
        self.assertEqual(streamlit_fake.session_state.tela_atual, "apresentacao")
        self.assertTrue(
            any("Finanças Pro IA" in texto for texto in streamlit_fake.markdowns),
            streamlit_fake.markdowns,
        )
        self.assertIn("Começar grátis", streamlit_fake.buttons)
        self.assertIn("Já tenho conta", streamlit_fake.buttons)
        self.assertFalse(streamlit_fake.errors)


if __name__ == "__main__":
    unittest.main()
