import unittest
from types import SimpleNamespace
from unittest.mock import patch

from views import dashboard_views


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
        self.infos = []

    def markdown(self, texto, **kwargs):
        self.markdowns.append((texto, kwargs))

    def caption(self, texto):
        self.captions.append(texto)

    def columns(self, quantidade):
        return [ColunaFake() for _ in range(quantidade)]

    def button(self, label, **kwargs):
        self.buttons.append((label, kwargs))
        return label == self.botao_clicado

    def info(self, texto):
        self.infos.append(texto)

    def rerun(self):
        raise RerunAcionado()


class DashboardViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(dashboard_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_estado_inicial_orienta_primeiros_passos(self):
        fake = self.usar_streamlit(StreamlitFake())

        dashboard_views._render_estado_inicial()

        texto_renderizado = "\n".join(texto for texto, _ in fake.markdowns)
        self.assertIn("Seu painel financeiro ainda está vazio", texto_renderizado)
        self.assertIn("Plano de ativação", texto_renderizado)
        self.assertIn("Importar PDF", "\n".join(label for label, _ in fake.buttons))
        self.assertIn("Lançar manualmente", "\n".join(label for label, _ in fake.buttons))
        self.assertIn("primeiro resumo mensal", "\n".join(fake.infos))

    def test_botao_importacao_atualiza_secao_principal(self):
        fake = self.usar_streamlit(StreamlitFake(botao_clicado="Importar PDF"))

        with self.assertRaises(RerunAcionado):
            dashboard_views._render_estado_inicial()

        self.assertEqual(fake.session_state.secao_principal, "Importação")

    def test_botao_transacoes_atualiza_secao_principal(self):
        fake = self.usar_streamlit(StreamlitFake(botao_clicado="Lançar manualmente"))

        with self.assertRaises(RerunAcionado):
            dashboard_views._render_estado_inicial()

        self.assertEqual(fake.session_state.secao_principal, "Transações")


if __name__ == "__main__":
    unittest.main()
