import sys
import unittest
from types import ModuleType
from unittest.mock import patch


class RerunAcionado(RuntimeError):
    pass


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


class QueryParamsFake(dict):
    def clear(self):
        super().clear()


class ComponentsFake:
    def __init__(self):
        self.html_calls = []

    def html(self, conteudo, **kwargs):
        self.html_calls.append((conteudo, kwargs))


class StreamlitFake(ModuleType):
    def __init__(self, *, textos=None, submit=False, botoes=None, tela_atual="apresentacao"):
        super().__init__("streamlit")
        self.session_state = SessionStateFake(autenticado=False, tela_atual=tela_atual)
        self.query_params = QueryParamsFake()
        self.textos = list(textos or [])
        self.submit = submit
        self.botoes = set(botoes or [])
        self.titles = []
        self.subheaders = []
        self.captions = []
        self.markdowns = []
        self.forms = []
        self.buttons = []
        self.errors = []
        self.warnings = []
        self.successes = []
        self.toasts = []

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
        if self.textos:
            return self.textos.pop(0)
        return ""

    def form_submit_button(self, *args, **kwargs):
        return self.submit

    def button(self, texto, **kwargs):
        self.buttons.append(texto)
        return texto in self.botoes

    def error(self, mensagem):
        self.errors.append(mensagem)

    def warning(self, mensagem):
        self.warnings.append(mensagem)

    def success(self, mensagem):
        self.successes.append(mensagem)

    def toast(self, mensagem, **kwargs):
        self.toasts.append((mensagem, kwargs))

    def rerun(self):
        raise RerunAcionado()


streamlit_fake = StreamlitFake()
sys.modules["streamlit"] = streamlit_fake
supabase_fake = ModuleType("supabase")
supabase_fake.Client = object
supabase_fake.create_client = lambda url, chave: object()
sys.modules["supabase"] = supabase_fake

from views import auth_views


class AuthViewsTests(unittest.TestCase):
    def usar_streamlit(self, fake):
        patcher = patch.object(auth_views, "st", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        components_fake = ComponentsFake()
        patcher_components = patch.object(auth_views, "components", components_fake)
        patcher_components.start()
        self.addCleanup(patcher_components.stop)
        return fake

    def test_fluxo_padrao_renderiza_apresentacao_publica(self):
        fake = self.usar_streamlit(StreamlitFake())

        auth_views.render_fluxo_autenticacao()

        self.assertTrue(any("Finanças Pro IA" in texto for texto in fake.markdowns))
        self.assertIn("Começar agora", fake.buttons)
        self.assertIn("Já tenho conta", fake.buttons)
        self.assertTrue(any("Escolha como quer começar" in texto for texto in fake.markdowns))

    def test_apresentacao_leva_para_cadastro(self):
        fake = self.usar_streamlit(StreamlitFake(botoes=["Começar agora"]))

        with self.assertRaises(RerunAcionado):
            auth_views.render_fluxo_autenticacao()

        self.assertEqual(fake.session_state.tela_atual, "cadastro")

    def test_login_continua_disponivel_quando_usuario_escolhe_entrar(self):
        fake = self.usar_streamlit(StreamlitFake(tela_atual="login"))

        auth_views.render_fluxo_autenticacao()

        self.assertIn("formulario_login", fake.forms)
        self.assertIn("Esqueci minha senha", fake.buttons)

    def test_login_autenticado_inicia_sessao_e_recarrega_app(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                textos=[" Pessoa@Exemplo.com ", "senha-segura"],
                submit=True,
                tela_atual="login",
            )
        )
        usuario = {"email": "pessoa@exemplo.com", "id": "user-1"}
        sessoes_iniciadas = []

        with (
            patch.object(auth_views, "fazer_login", return_value=usuario) as login,
            patch.object(
                auth_views,
                "iniciar_sessao_autenticada",
                lambda email, usuario_id: sessoes_iniciadas.append((email, usuario_id)),
            ),
            self.assertRaises(RerunAcionado),
        ):
            auth_views.render_tela_login()

        login.assert_called_once_with("pessoa@exemplo.com", "senha-segura")
        self.assertEqual(sessoes_iniciadas, [("pessoa@exemplo.com", "user-1")])
        self.assertTrue(fake.toasts)

    def test_login_recusado_mostra_mensagem_neutra(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                textos=[" Pessoa@Exemplo.com ", "senha-incorreta"],
                submit=True,
                tela_atual="login",
            )
        )

        with patch.object(auth_views, "fazer_login", return_value=False) as login:
            auth_views.render_tela_login()

        login.assert_called_once_with("pessoa@exemplo.com", "senha-incorreta")
        self.assertTrue(fake.errors)
        self.assertIn("Confira e-mail e senha", fake.errors[0])
        self.assertIn("confirmação pendente", fake.errors[0])
        self.assertNotIn("confirme o e-mail de confirmação antes de entrar", fake.errors[0])

    def test_login_bloqueado_nao_duplica_mensagem_generica(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                textos=[" Pessoa@Exemplo.com ", "senha-incorreta"],
                submit=True,
                tela_atual="login",
            )
        )
        fake.session_state.login_bloqueado_por_tentativas = True

        with patch.object(auth_views, "fazer_login", return_value=False) as login:
            auth_views.render_tela_login()

        login.assert_called_once_with("pessoa@exemplo.com", "senha-incorreta")
        self.assertFalse(fake.errors)

    def test_recuperacao_de_senha_mantem_mensagem_sem_enumerar_usuario(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                textos=[" Pessoa@Exemplo.com "],
                submit=True,
                tela_atual="recuperar_senha",
            )
        )

        with patch.object(auth_views, "enviar_email_recuperacao_senha", return_value=True) as enviar:
            auth_views.render_fluxo_autenticacao()

        enviar.assert_called_once_with("pessoa@exemplo.com")
        self.assertTrue(any("Se houver uma conta" in msg for msg in fake.successes))
        self.assertFalse(fake.errors)

    def test_link_de_recuperacao_abre_tela_de_redefinir_senha(self):
        fake = self.usar_streamlit(StreamlitFake())
        fake.query_params["auth_recovery"] = (
            "access_token%3Daccess-token%26refresh_token%3Drefresh-token%26type%3Drecovery"
        )

        auth_views.render_fluxo_autenticacao()

        self.assertEqual(fake.session_state.tela_atual, "redefinir_senha")
        self.assertEqual(fake.session_state.recovery_access_token, "access-token")
        self.assertEqual(fake.session_state.recovery_refresh_token, "refresh-token")
        self.assertIn("formulario_redefinir_senha", fake.forms)
        self.assertEqual(fake.query_params, {})

    def test_redefinicao_de_senha_chama_servico_e_volta_para_login(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                textos=["senha-nova-segura", "senha-nova-segura"],
                submit=True,
                tela_atual="redefinir_senha",
            )
        )
        fake.session_state.recovery_access_token = "access-token"
        fake.session_state.recovery_refresh_token = "refresh-token"

        with (
            patch.object(auth_views, "redefinir_senha_com_tokens", return_value=True) as redefinir,
            self.assertRaises(RerunAcionado),
        ):
            auth_views.render_tela_redefinir_senha()

        redefinir.assert_called_once_with(
            "access-token",
            "refresh-token",
            "senha-nova-segura",
        )
        self.assertEqual(fake.session_state.tela_atual, "login")
        self.assertNotIn("recovery_access_token", fake.session_state)

    def test_cadastro_com_senha_curta_mostra_erro_sem_chamar_servico(self):
        fake = self.usar_streamlit(
            StreamlitFake(
                textos=[" pessoa@exemplo.com ", "curta", "curta"],
                submit=True,
                tela_atual="cadastro",
            )
        )

        with patch.object(auth_views, "cadastrar_usuario") as cadastrar:
            auth_views.render_fluxo_autenticacao()

        cadastrar.assert_not_called()
        self.assertIn("A senha deve ter pelo menos 10 caracteres.", fake.errors)


if __name__ == "__main__":
    unittest.main()
