import unittest
from types import SimpleNamespace
from unittest.mock import patch

from views import oracle_views


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
        if isinstance(quantidade, int):
            total = quantidade
        else:
            total = len(quantidade)
        return [ColunaFake() for _ in range(total)]

    def button(self, label, **kwargs):
        self.buttons.append((label, kwargs))
        return label == self.botao_clicado

    def rerun(self):
        raise RerunAcionado()


class OracleViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(oracle_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_estado_sem_dados_orienta_historico_financeiro(self):
        fake = self.usar_streamlit(StreamlitFake())

        oracle_views._render_estado_sem_dados_oraculo()

        texto_renderizado = "\n".join(texto for texto, _ in fake.markdowns)
        botoes = "\n".join(label for label, _ in fake.buttons)
        self.assertIn("O Oráculo precisa de histórico financeiro", texto_renderizado)
        self.assertIn("Importar PDF", botoes)
        self.assertIn("Lançar manualmente", botoes)

    def test_botao_importar_pdf_atualiza_secao_principal(self):
        fake = self.usar_streamlit(StreamlitFake(botao_clicado="Importar PDF"))

        with self.assertRaises(RerunAcionado):
            oracle_views._render_estado_sem_dados_oraculo()

        self.assertEqual(fake.session_state.secao_principal, "Importação")

    def test_botao_lancar_manualmente_atualiza_secao_principal(self):
        fake = self.usar_streamlit(StreamlitFake(botao_clicado="Lançar manualmente"))

        with self.assertRaises(RerunAcionado):
            oracle_views._render_estado_sem_dados_oraculo()

        self.assertEqual(fake.session_state.secao_principal, "Transações")


if __name__ == "__main__":
    unittest.main()
