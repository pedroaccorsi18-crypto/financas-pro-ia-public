import unittest
from types import SimpleNamespace
from unittest.mock import patch

from views import transactions_views


class RerunAcionado(RuntimeError):
    pass


class ColunaFake:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class StreamlitFake:
    def __init__(self, botao_clicado=None):
        self.botao_clicado = botao_clicado
        self.session_state = SimpleNamespace()
        self.markdowns = []
        self.captions = []
        self.buttons = []

    def markdown(self, texto, **kwargs):
        self.markdowns.append((texto, kwargs))

    def caption(self, texto):
        self.captions.append(texto)

    def columns(self, quantidade):
        return [ColunaFake() for _ in range(quantidade)]

    def button(self, label, **kwargs):
        self.buttons.append((label, kwargs))
        return label == self.botao_clicado

    def rerun(self):
        raise RerunAcionado()


class TransactionsViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(transactions_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_estado_vazio_orienta_lancamento_e_importacao(self):
        fake = self.usar_streamlit(StreamlitFake())

        transactions_views._render_estado_vazio_transacoes()

        texto_renderizado = "\n".join(texto for texto, _ in fake.markdowns)
        self.assertIn("Escolha como quer começar", texto_renderizado)
        self.assertIn("Lançamento manual", texto_renderizado)
        self.assertIn("Importar PDF", "\n".join(label for label, _ in fake.buttons))

    def test_botao_importar_pdf_atualiza_secao_principal(self):
        fake = self.usar_streamlit(StreamlitFake(botao_clicado="Importar PDF"))

        with self.assertRaises(RerunAcionado):
            transactions_views._render_estado_vazio_transacoes()

        self.assertEqual(fake.session_state.secao_principal, "Importação")


if __name__ == "__main__":
    unittest.main()
