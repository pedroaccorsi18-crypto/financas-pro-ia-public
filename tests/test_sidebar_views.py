import sys
import unittest
from types import ModuleType
from unittest.mock import patch

from finance_categories import CATEGORIAS_RECEITA
from finance_constants import TIPO_DESPESA, TIPO_RECEITA


class RerunAcionado(RuntimeError):
    pass


class FormFake:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class SidebarFake:
    def __init__(self, streamlit_fake):
        self.streamlit_fake = streamlit_fake
        self.subheaders = []
        self.selectboxes = []
        self.forms = []

    def subheader(self, texto):
        self.subheaders.append(texto)

    def selectbox(self, label, options, **kwargs):
        self.selectboxes.append((label, list(options), kwargs))
        return self.streamlit_fake.tipo_transacao

    def form(self, nome, **kwargs):
        self.forms.append((nome, kwargs))
        return FormFake()


class StreamlitFake(ModuleType):
    def __init__(
        self,
        *,
        tipo_transacao=TIPO_DESPESA,
        textos=None,
        valor=0.0,
        categoria=None,
        mes="06/2026",
        submit=False,
    ):
        super().__init__("streamlit")
        self.tipo_transacao = tipo_transacao
        self.textos = list(textos or [])
        self.valor = valor
        self.categoria = categoria
        self.mes = mes
        self.submit = submit
        self.sidebar = SidebarFake(self)
        self.selectboxes = []
        self.errors = []
        self.toasts = []
        self.rerun_called = False

    def text_input(self, *args, **kwargs):
        if self.textos:
            return self.textos.pop(0)
        return kwargs.get("value", "")

    def number_input(self, *args, **kwargs):
        return self.valor

    def selectbox(self, label, options, **kwargs):
        opcoes = list(options)
        self.selectboxes.append((label, opcoes, kwargs))
        if label == "Categoria" and self.categoria is not None:
            return self.categoria
        if label.startswith("M"):
            return self.mes
        return opcoes[0]

    def form_submit_button(self, *args, **kwargs):
        return self.submit

    def error(self, mensagem):
        self.errors.append(mensagem)

    def toast(self, mensagem, **kwargs):
        self.toasts.append((mensagem, kwargs))

    def rerun(self):
        self.rerun_called = True


streamlit_fake = StreamlitFake()
sys.modules["streamlit"] = streamlit_fake

from views import sidebar_views


class SidebarViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(sidebar_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_receita_manual_usa_categorias_de_receita(self):
        fake = self.usar_streamlit(StreamlitFake(tipo_transacao=TIPO_RECEITA))

        sidebar_views.render_lancamento_manual(
            usuario_id="user-1",
            email_usuario="pessoa@example.com",
            inserir_transacao=lambda payload: None,
        )

        categoria = next(item for item in fake.selectboxes if item[0] == "Categoria")
        self.assertEqual(categoria[1], CATEGORIAS_RECEITA)

    def test_salva_lancamento_manual_com_payload_preparado(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                textos=[" Uber ", " Nubank "],
                valor=42.5,
                categoria="Transporte",
                submit=True,
            )
        )
        payloads = []

        sidebar_views.render_lancamento_manual(
            usuario_id="user-1",
            email_usuario="pessoa@example.com",
            inserir_transacao=payloads.append,
        )

        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["descricao"], "Uber")
        self.assertEqual(payloads[0]["valor"], 42.5)
        self.assertEqual(payloads[0]["tipo"], TIPO_DESPESA)
        self.assertEqual(payloads[0]["categoria"], "Transporte")
        self.assertEqual(payloads[0]["instituicao_financeira"], "Nubank")
        self.assertTrue(fake.toasts)
        self.assertTrue(fake.rerun_called)


if __name__ == "__main__":
    unittest.main()
