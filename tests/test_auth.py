import base64
import json
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


streamlit_fake = ModuleType("streamlit")
streamlit_fake.session_state = {}
streamlit_fake.secrets = {}
streamlit_fake.error = lambda mensagem: None

supabase_fake = ModuleType("supabase")
supabase_fake.Client = object
supabase_fake.create_client = lambda url, chave: object()

sys.modules["streamlit"] = streamlit_fake
sys.modules["supabase"] = supabase_fake

import auth


APP_SOURCE = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
AUTH_VIEWS_SOURCE = (
    Path(__file__).parents[1] / "views" / "auth_views.py"
).read_text(encoding="utf-8")
SIDEBAR_VIEWS_SOURCE = (
    Path(__file__).parents[1] / "views" / "sidebar_views.py"
).read_text(encoding="utf-8")
AUTH_SOURCE = (Path(__file__).parents[1] / "auth.py").read_text(encoding="utf-8")
SESSION_STATE_SOURCE = (Path(__file__).parents[1] / "session_state.py").read_text(encoding="utf-8")
FINANCE_CATEGORIES_SOURCE = (Path(__file__).parents[1] / "finance_categories.py").read_text(encoding="utf-8")
FINANCE_CONSTANTS_SOURCE = (Path(__file__).parents[1] / "finance_constants.py").read_text(encoding="utf-8")
APP_CONFIG_SOURCE = (Path(__file__).parents[1] / "app_config.py").read_text(encoding="utf-8")
IMPORT_WORKFLOW_SOURCE = (
    Path(__file__).parents[1] / "utils" / "import_workflow.py"
).read_text(encoding="utf-8")
REQUIREMENTS = (Path(__file__).parents[1] / "requirements.txt").read_text(encoding="utf-8")


class SessionStateFake(dict):
    def __getattr__(self, nome):
        return self[nome]

    def __setattr__(self, nome, valor):
        self[nome] = valor


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.session_state = SessionStateFake()
        self.original_supabase = auth.supabase

    def tearDown(self):
        auth.supabase = self.original_supabase

    def test_login_retorna_identidade_do_supabase_auth(self):
        resposta = SimpleNamespace(
            user=SimpleNamespace(id="user-123", email="Pessoa@Exemplo.com")
        )
        auth.supabase = SimpleNamespace(
            auth=SimpleNamespace(sign_in_with_password=lambda credenciais: resposta)
        )

        with patch.object(auth.st, "session_state", self.session_state):
            usuario = auth.fazer_login("pessoa@exemplo.com", "senha-segura")

        self.assertEqual(
            usuario,
            {"id": "user-123", "email": "pessoa@exemplo.com"},
        )
        self.assertEqual(self.session_state["tentativas_login"], [])

    def test_cliente_supabase_e_reutilizado_apenas_na_mesma_sessao(self):
        clientes = [object(), object()]
        chamadas = []

        def criar_cliente(url, chave):
            chamadas.append((url, chave))
            return clientes[len(chamadas) - 1]

        sessao_um = SessionStateFake()
        sessao_dois = SessionStateFake()
        with (
            patch.object(
                auth.st,
                "secrets",
                {"SUPABASE_URL": "url", "SUPABASE_KEY": "sb_publishable_teste"},
            ),
            patch.object(auth, "create_client", criar_cliente),
        ):
            with patch.object(auth.st, "session_state", sessao_um):
                primeiro = auth.obter_conexao_supabase()
                repetido = auth.obter_conexao_supabase()
            with patch.object(auth.st, "session_state", sessao_dois):
                segundo = auth.obter_conexao_supabase()

        self.assertIs(primeiro, repetido)
        self.assertIsNot(primeiro, segundo)
        self.assertEqual(len(chamadas), 2)

    def test_cliente_supabase_e_recriado_quando_configuracao_muda(self):
        clientes = [object(), object()]
        chamadas = []

        def criar_cliente(url, chave):
            chamadas.append((url, chave))
            return clientes[len(chamadas) - 1]

        with (
            patch.object(auth.st, "session_state", SessionStateFake()),
            patch.object(auth, "create_client", criar_cliente),
        ):
            with patch.object(
                auth.st,
                "secrets",
                {"SUPABASE_URL": "url-antiga", "SUPABASE_KEY": "sb_publishable_antiga"},
            ):
                primeiro = auth.obter_conexao_supabase()
            with patch.object(
                auth.st,
                "secrets",
                {"SUPABASE_URL": "url-nova", "SUPABASE_KEY": "sb_publishable_nova"},
            ):
                segundo = auth.obter_conexao_supabase()

        self.assertIsNot(primeiro, segundo)
        self.assertEqual(
            chamadas,
            [
                ("url-antiga", "sb_publishable_antiga"),
                ("url-nova", "sb_publishable_nova"),
            ],
        )

    def test_bloqueia_jwt_service_role_antes_de_criar_cliente(self):
        payload = base64.urlsafe_b64encode(
            json.dumps({"role": "service_role"}).encode("utf-8")
        ).decode("ascii").rstrip("=")
        chave = f"cabecalho.{payload}.assinatura"

        with (
            patch.object(auth.st, "session_state", SessionStateFake()),
            patch.object(auth.st, "secrets", {"SUPABASE_URL": "url", "SUPABASE_KEY": chave}),
            patch.object(auth, "create_client") as criar_cliente,
        ):
            with self.assertRaises(RuntimeError):
                auth.obter_conexao_supabase()

        criar_cliente.assert_not_called()

    def test_bloqueia_chave_secreta_moderna(self):
        with self.assertRaises(RuntimeError):
            auth.validar_chave_publica_supabase("sb_secret_nao_permitida")

    def test_aceita_jwt_legado_com_role_anon(self):
        payload = base64.urlsafe_b64encode(
            json.dumps({"role": "anon"}).encode("utf-8")
        ).decode("ascii").rstrip("=")

        auth.validar_chave_publica_supabase(f"cabecalho.{payload}.assinatura")

    def test_revalida_identidade_com_supabase_auth(self):
        auth.supabase = SimpleNamespace(
            auth=SimpleNamespace(
                get_user=lambda: SimpleNamespace(
                    user=SimpleNamespace(id="user-456", email="Pessoa@Exemplo.com")
                )
            )
        )

        self.assertEqual(
            auth.validar_sessao_atual(),
            {"id": "user-456", "email": "pessoa@exemplo.com"},
        )

    def test_sessao_revogada_falha_na_revalidacao(self):
        def sessao_revogada():
            raise RuntimeError("token revogado")

        auth.supabase = SimpleNamespace(
            auth=SimpleNamespace(get_user=sessao_revogada)
        )

        self.assertFalse(auth.validar_sessao_atual())

    def test_envia_recuperacao_de_senha_normalizando_email(self):
        chamadas = []
        auth.supabase = SimpleNamespace(
            auth=SimpleNamespace(
                reset_password_for_email=lambda email: chamadas.append(email)
            )
        )

        self.assertTrue(auth.enviar_email_recuperacao_senha(" Pessoa@Exemplo.com "))
        self.assertEqual(chamadas, ["pessoa@exemplo.com"])

    def test_recuperacao_de_senha_retorna_falha_sem_lancar_erro(self):
        def falhar(_email):
            raise RuntimeError("servico indisponivel")

        auth.supabase = SimpleNamespace(
            auth=SimpleNamespace(reset_password_for_email=falhar)
        )

        self.assertFalse(auth.enviar_email_recuperacao_senha("pessoa@exemplo.com"))

    def test_logout_revoga_sessao_auth(self):
        chamadas = []
        auth.supabase = SimpleNamespace(
            auth=SimpleNamespace(sign_out=lambda: chamadas.append("sign_out"))
        )

        resultado = auth.encerrar_autenticacao_supabase()

        self.assertTrue(resultado)
        self.assertEqual(chamadas, ["sign_out"])

    def test_logout_retorna_falha_quando_supabase_nao_confirma(self):
        def falhar_logout():
            raise RuntimeError("indisponivel")

        auth.supabase = SimpleNamespace(
            auth=SimpleNamespace(sign_out=falhar_logout)
        )

        self.assertFalse(auth.encerrar_autenticacao_supabase())

    def test_app_limpa_sessao_local_quando_revalidacao_falha(self):
        self.assertIn("inicializar_estado_sessao()", APP_SOURCE)
        self.assertIn('if "autenticado" not in st.session_state:', SESSION_STATE_SOURCE)
        self.assertIn('st.session_state.tela_atual = "login"', SESSION_STATE_SOURCE)
        self.assertIn("st.session_state.dados_pre_visualizacao = None", SESSION_STATE_SOURCE)
        self.assertIn("identidade_revalidada = validar_sessao_atual()", APP_SOURCE)
        trecho = APP_SOURCE.split("if not identidade_revalidada:", 1)[-1]
        self.assertIn("limpar_sessao_usuario()", trecho)
        self.assertIn("st.session_state.autenticado = False", trecho)
        self.assertIn("st.rerun()", trecho)

    def test_app_preserva_config_do_cliente_supabase_apos_login(self):
        trecho = SESSION_STATE_SOURCE.split("def limpar_sessao_usuario", 1)[-1]
        trecho = trecho.split("def iniciar_sessao_autenticada", 1)[0]

        self.assertIn("from session_state import (", APP_SOURCE)
        self.assertIn('st.session_state.get("_supabase_client")', trecho)
        self.assertIn('st.session_state.get("_supabase_config")', trecho)
        self.assertIn('st.session_state["_supabase_client"] = cliente_supabase', trecho)
        self.assertIn('st.session_state["_supabase_config"] = config_supabase', trecho)

    def test_app_avisa_usuario_quando_logout_nao_e_confirmado(self):
        trecho = SESSION_STATE_SOURCE.split("def encerrar_sessao_usuario():", 1)[-1]
        self.assertIn("if not logout_confirmado:", trecho)
        self.assertIn("st.session_state.aviso_sessao", trecho)

    def test_app_inicializa_gemini_somente_quando_necessario(self):
        self.assertNotIn("client = inicializar_cliente_gemini()", APP_SOURCE)
        self.assertNotIn("from google import genai", APP_SOURCE)
        self.assertIn("def obter_cliente_gemini():", APP_SOURCE)
        self.assertIn("criar_cliente_gemini(chave)", APP_SOURCE)
        self.assertIn("obter_cliente_gemini(),", APP_SOURCE)

    def test_app_tem_fluxo_de_recuperacao_de_senha_sem_enumerar_usuario(self):
        self.assertIn('st.session_state.tela_atual = "recuperar_senha"', AUTH_VIEWS_SOURCE)
        self.assertIn("enviar_email_recuperacao_senha(email_recuperacao)", AUTH_VIEWS_SOURCE)
        self.assertIn("Se houver uma conta associada a este e-mail", AUTH_VIEWS_SOURCE)
        self.assertNotIn("e-mail nÃ£o encontrado", AUTH_VIEWS_SOURCE.lower())

    def test_app_orienta_confirmacao_de_email_apos_cadastro(self):
        self.assertIn('resultado == "confirmar_email"', AUTH_VIEWS_SOURCE)
        self.assertIn("st.session_state.aviso_sessao", AUTH_VIEWS_SOURCE)
        self.assertIn("confirme o e-mail de confirma", AUTH_VIEWS_SOURCE)
        self.assertIn("Verifique sua caixa de entrada ou spam", AUTH_VIEWS_SOURCE)
        self.assertIn("Se voc", AUTH_VIEWS_SOURCE)

    def test_app_usa_categorias_de_receita_no_lancamento_manual(self):
        trecho = SIDEBAR_VIEWS_SOURCE.split('with st.sidebar.form("form_transacao"', 1)[-1]
        trecho = trecho.split('ano_atual = datetime.datetime.now().year', 1)[0]
        trecho_antes_form = SIDEBAR_VIEWS_SOURCE.split('with st.sidebar.form("form_transacao"', 1)[0]

        self.assertIn("key=\"tipo_transacao_manual\"", trecho_antes_form)
        self.assertIn("CATEGORIAS_RECEITA if tipo_transacao == TIPO_RECEITA", trecho)
        self.assertIn("else CATEGORIAS_DESPESA", trecho)
        self.assertIn("key=f\"categoria_manual_{tipo_transacao.lower()}\"", trecho)
        self.assertIn("from finance_categories import CATEGORIAS_DESPESA, CATEGORIAS_RECEITA", SIDEBAR_VIEWS_SOURCE)
        self.assertIn("from finance_constants import (", APP_SOURCE)
        self.assertIn("TIPOS_TRANSACAO", trecho_antes_form)
        self.assertIn("TIPO_DESPESA = \"Despesa\"", FINANCE_CONSTANTS_SOURCE)
        self.assertIn("TIPO_RECEITA = \"Receita\"", FINANCE_CONSTANTS_SOURCE)
        self.assertIn("ORIGEM_MANUAL = \"Manual\"", FINANCE_CONSTANTS_SOURCE)
        self.assertIn("ORIGEM_AUTOMATICA = \"Automático\"", FINANCE_CONSTANTS_SOURCE)
        self.assertIn("TIPO_DOCUMENTO_MANUAL = \"Manual\"", FINANCE_CONSTANTS_SOURCE)
        self.assertIn("\"Salário\"", FINANCE_CATEGORIES_SOURCE)
        self.assertIn("\"Moradia\"", FINANCE_CATEGORIES_SOURCE)
        self.assertIn("\"Dívidas & Financiamentos\"", FINANCE_CATEGORIES_SOURCE)

    def test_app_nao_falha_quando_smtp_nao_esta_configurado(self):
        bot_fiscal_source = (Path(__file__).parents[1] / "utils" / "bot_fiscal.py").read_text(encoding="utf-8")
        self.assertIn("from utils.bot_fiscal import disparar_bot_fiscal_email", APP_SOURCE)
        self.assertIn("disparar_alerta(", IMPORT_WORKFLOW_SOURCE)
        self.assertIn("secrets,", IMPORT_WORKFLOW_SOURCE)
        self.assertIn("from app_config import SMTP_SECRET_KEYS", bot_fiscal_source)
        self.assertIn("SMTP_SECRET_KEYS", bot_fiscal_source)
        self.assertIn("\"SMTP_SERVER\"", APP_CONFIG_SOURCE)
        self.assertIn("\"EMAIL_DESTINATARIO_ALERTAS\"", APP_CONFIG_SOURCE)
        self.assertIn("if not all(configuracao.values()):", bot_fiscal_source)
        self.assertIn("return False", bot_fiscal_source)

    def test_autenticacao_nao_depende_de_bcrypt(self):
        self.assertNotIn("bcrypt", AUTH_SOURCE.lower())
        self.assertNotIn("bcrypt", REQUIREMENTS.lower())


if __name__ == "__main__":
    unittest.main()
