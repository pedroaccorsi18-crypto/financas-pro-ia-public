import unittest

from utils.platform_health import (
    gerar_decisao_lancamento,
    gerar_health_check_lancamento,
    gerar_health_check_supabase,
    resumir_health_check,
)
from views.admin_views import _montar_tabela_health_check_html


class QueryFake:
    def __init__(self, erro=None):
        self.erro = erro

    def select(self, _campos):
        return self

    def limit(self, _limite):
        return self

    def execute(self):
        if self.erro:
            raise self.erro
        return object()


class SupabaseHealthFake:
    def __init__(self, table_errors=None, rpc_error=None, rpc_errors=None):
        self.table_errors = table_errors or {}
        self.rpc_error = rpc_error
        self.rpc_errors = rpc_errors or {}
        self.tables = []
        self.rpc_calls = []

    def table(self, nome):
        self.tables.append(nome)
        return QueryFake(self.table_errors.get(nome))

    def rpc(self, nome, payload):
        self.rpc_calls.append((nome, payload))
        erro = self.rpc_errors.get(nome)
        if erro is None and nome == "substituir_lote_importado":
            erro = self.rpc_error
        return QueryFake(erro)


class PlatformHealthTests(unittest.TestCase):
    def test_health_check_reconhece_objetos_prontos(self):
        supabase = SupabaseHealthFake(
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio")
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")

        self.assertEqual(resumir_health_check(resultados), "OK")
        self.assertTrue(all(item["status"] == "OK" for item in resultados))
        self.assertIn("perfis_financeiros_360", supabase.tables)
        self.assertIn("perfis_cliente", supabase.tables)
        self.assertEqual(supabase.rpc_calls[0][0], "substituir_lote_importado")
        self.assertEqual(supabase.rpc_calls[0][1]["p_transacoes"], [])
        self.assertEqual(supabase.rpc_calls[1][0], "obter_ou_criar_assinatura_usuario")

    def test_health_check_aponta_tabela_ausente(self):
        supabase = SupabaseHealthFake(
            table_errors={
                "perfis_financeiros_360": RuntimeError(
                    "Could not find public.perfis_financeiros_360 in schema cache"
                )
            },
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio"),
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")
        perfil = next(item for item in resultados if item["item"] == "Perfil Financeiro 360")

        self.assertIn("necess", resumir_health_check(resultados).lower())
        self.assertEqual(perfil["status"], "Ação necessária")
        self.assertIn("202606250001_criar_perfis_financeiros_360.sql", perfil["acao"])

    def test_health_check_aponta_perfil_cliente_ausente(self):
        supabase = SupabaseHealthFake(
            table_errors={
                "perfis_cliente": RuntimeError(
                    "Could not find public.perfis_cliente in schema cache"
                )
            },
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio"),
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")
        perfil = next(item for item in resultados if item["item"] == "Perfil do Cliente")

        self.assertIn("necess", resumir_health_check(resultados).lower())
        self.assertIn("necess", perfil["status"].lower())
        self.assertIn("202607070001_criar_perfis_cliente.sql", perfil["acao"])

    def test_health_check_aponta_permissao_bloqueada(self):
        supabase = SupabaseHealthFake(
            table_errors={"metas_financeiras": RuntimeError("permission denied for table")},
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio"),
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")
        metas = next(item for item in resultados if item["item"] == "Metas financeiras")

        self.assertEqual(resumir_health_check(resultados), "Atenção")
        self.assertEqual(metas["status"], "Atenção")
        self.assertIn("RLS", metas["acao"])

    def test_health_check_aponta_rpc_ausente(self):
        supabase = SupabaseHealthFake(
            rpc_errors={
                "substituir_lote_importado": RuntimeError(
                    "Could not find function substituir_lote_importado"
                )
            }
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")
        rpc = next(item for item in resultados if item["item"] == "RPC de reimportação")

        self.assertEqual(resumir_health_check(resultados), "Ação necessária")
        self.assertEqual(rpc["status"], "Ação necessária")
        self.assertIn("202606100001_endurecer_rpc_substituir_lote.sql", rpc["acao"])

    def test_health_check_aponta_rpc_de_assinatura_ausente(self):
        supabase = SupabaseHealthFake(
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio"),
            rpc_errors={
                "obter_ou_criar_assinatura_usuario": RuntimeError(
                    "Could not find function obter_ou_criar_assinatura_usuario"
                )
            },
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")
        assinatura = next(
            item for item in resultados if item["item"] == "RPC de assinatura gratuita"
        )

        self.assertEqual(resumir_health_check(resultados), "Ação necessária")
        self.assertEqual(assinatura["status"], "Ação necessária")
        self.assertIn("202606300002_criar_assinaturas_stripe.sql", assinatura["acao"])

    def test_health_check_lancamento_reune_configuracao_e_escopo(self):
        supabase = SupabaseHealthFake(
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio")
        )
        secrets = {
            "SUPABASE_URL": "https://exemplo.supabase.co",
            "SUPABASE_KEY": "sb_publishable_teste",
            "GEMINI_API_KEY": "configurada",
            "ENABLE_ORACULO_IA": "false",
            "ENABLE_PLANEJAMENTO_360": "false",
            "ENABLE_MARKET_RADAR": "false",
        }

        resultados = gerar_health_check_lancamento(
            secrets,
            supabase,
            "user-1",
            {"seguranca": "Sessao Auth e RLS ativos"},
        )

        itens = {item["item"]: item for item in resultados}
        self.assertEqual(itens["Configuração Supabase"]["status"], "OK")
        self.assertEqual(itens["Autenticação e RLS"]["status"], "OK")
        self.assertEqual(itens["Escopo de lançamento"]["status"], "OK")
        self.assertEqual(itens["Gemini"]["status"], "OK")
        self.assertEqual(itens["Stripe"]["status"], "Atenção")
        self.assertEqual(resumir_health_check(resultados), "Atenção")

    def test_health_check_stripe_ok_exige_webhook_secret(self):
        supabase = SupabaseHealthFake(
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio")
        )
        secrets = {
            "SUPABASE_URL": "https://exemplo.supabase.co",
            "SUPABASE_KEY": "sb_publishable_teste",
            "GEMINI_API_KEY": "configurada",
            "STRIPE_SECRET_KEY": "sk_test",
            "STRIPE_PRICE_PRO": "price_pro",
            "STRIPE_PRICE_FAMILIA": "price_familia",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "ENABLE_ORACULO_IA": "false",
            "ENABLE_PLANEJAMENTO_360": "false",
            "ENABLE_MARKET_RADAR": "false",
        }

        resultados = gerar_health_check_lancamento(
            secrets,
            supabase,
            "user-1",
            {"seguranca": "Sessao Auth e RLS ativos"},
        )

        itens = {item["item"]: item for item in resultados}
        self.assertEqual(itens["Stripe"]["status"], "OK")
        self.assertIn("webhook", itens["Stripe"]["detalhe"].lower())

    def test_health_check_lancamento_bloqueia_sem_secrets_supabase(self):
        resultados = gerar_health_check_lancamento(
            {},
            SupabaseHealthFake(),
            "user-1",
            {"seguranca": "Nao validado"},
        )

        configuracao = next(
            item for item in resultados if item["item"] == "Configuração Supabase"
        )

        self.assertEqual(configuracao["status"], "Ação necessária")
        self.assertEqual(resumir_health_check(resultados), "Ação necessária")

    def test_decisao_lancamento_bloqueia_quando_ha_acao_necessaria(self):
        resultados = gerar_health_check_lancamento(
            {},
            SupabaseHealthFake(),
            "user-1",
            {"seguranca": "Nao validado"},
        )

        decisao = gerar_decisao_lancamento(resultados)

        self.assertFalse(decisao["pronto"])
        self.assertEqual(decisao["status"], "Bloqueado")
        self.assertGreater(len(decisao["bloqueios"]), 0)
        self.assertIn("SUPABASE_URL", decisao["proxima_acao"])

    def test_decisao_lancamento_permite_validacao_com_pendencias(self):
        supabase = SupabaseHealthFake(
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio")
        )
        resultados = gerar_health_check_lancamento(
            {
                "SUPABASE_URL": "https://exemplo.supabase.co",
                "SUPABASE_KEY": "sb_publishable_teste",
                "GEMINI_API_KEY": "configurada",
            },
            supabase,
            "user-1",
            {"seguranca": "Sessao Auth e RLS ativos"},
        )

        decisao = gerar_decisao_lancamento(resultados)

        self.assertTrue(decisao["pronto"])
        self.assertEqual(decisao["status"], "Validável com atenção")
        self.assertEqual(decisao["bloqueios"], [])
        self.assertGreater(len(decisao["pendencias"]), 0)

    def test_decisao_lancamento_pronto_quando_tudo_esta_ok(self):
        resultados = [
            {
                "item": "Config",
                "status": "OK",
                "detalhe": "Validado.",
                "acao": "Nenhuma ação necessária.",
            }
        ]

        decisao = gerar_decisao_lancamento(resultados)

        self.assertTrue(decisao["pronto"])
        self.assertEqual(decisao["status"], "Pronto")
        self.assertEqual(decisao["bloqueios"], [])
        self.assertEqual(decisao["pendencias"], [])

    def test_tabela_visual_do_health_check_escapa_html(self):
        html = _montar_tabela_health_check_html(
            [
                {
                    "item": "<script>alert(1)</script>",
                    "status": "Ação necessária",
                    "detalhe": "Objeto <ausente>",
                    "acao": "Aplique <migração>",
                }
            ]
        )

        self.assertIn("status-action", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("Objeto &lt;ausente&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)


if __name__ == "__main__":
    unittest.main()
