import unittest
from unittest.mock import patch

from views import import_views


class ColunaFake:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class StreamlitFake:
    def __init__(self):
        self.markdowns = []
        self.captions = []

    def markdown(self, texto, **kwargs):
        self.markdowns.append((texto, kwargs))

    def caption(self, texto):
        self.captions.append(texto)

    def columns(self, quantidade):
        return [ColunaFake() for _ in range(quantidade)]


class ImportViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(import_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_orientacao_importacao_explica_revisao_limite_e_consentimento(self):
        fake = self.usar_streamlit(StreamlitFake())

        import_views._render_orientacao_importacao()

        texto = "\n".join(texto for texto, _ in fake.markdowns)
        captions = "\n".join(fake.captions)
        self.assertIn("Transforme PDF em lançamentos revisáveis", texto)
        self.assertIn("nada é salvo antes da sua revisão", texto)
        self.assertIn("até 10 MB", captions)
        self.assertIn("consentimento", captions)


if __name__ == "__main__":
    unittest.main()
