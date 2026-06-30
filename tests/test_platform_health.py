import unittest

from utils.platform_health import gerar_health_check_supabase, resumir_health_check


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
    def __init__(self, table_errors=None, rpc_error=None):
        self.table_errors = table_errors or {}
        self.rpc_error = rpc_error
        self.tables = []
        self.rpc_calls = []

    def table(self, nome):
        self.tables.append(nome)
        return QueryFake(self.table_errors.get(nome))

    def rpc(self, nome, payload):
        self.rpc_calls.append((nome, payload))
        return QueryFake(self.rpc_error)


class PlatformHealthTests(unittest.TestCase):
    def test_health_check_reconhece_objetos_prontos(self):
        supabase = SupabaseHealthFake(
            rpc_error=RuntimeError("Payload de transacoes nao pode ser vazio")
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")

        self.assertEqual(resumir_health_check(resultados), "OK")
        self.assertTrue(all(item["status"] == "OK" for item in resultados))
        self.assertIn("perfis_financeiros_360", supabase.tables)
        self.assertEqual(supabase.rpc_calls[0][0], "substituir_lote_importado")
        self.assertEqual(supabase.rpc_calls[0][1]["p_transacoes"], [])

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

        self.assertEqual(resumir_health_check(resultados), "Ação necessária")
        self.assertEqual(perfil["status"], "Ação necessária")
        self.assertIn("202606250001_criar_perfis_financeiros_360.sql", perfil["acao"])

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
            rpc_error=RuntimeError("Could not find function substituir_lote_importado")
        )

        resultados = gerar_health_check_supabase(supabase, "user-1")
        rpc = next(item for item in resultados if item["item"] == "RPC de reimportação")

        self.assertEqual(resumir_health_check(resultados), "Ação necessária")
        self.assertEqual(rpc["status"], "Ação necessária")
        self.assertIn("202606100001_endurecer_rpc_substituir_lote.sql", rpc["acao"])


if __name__ == "__main__":
    unittest.main()
