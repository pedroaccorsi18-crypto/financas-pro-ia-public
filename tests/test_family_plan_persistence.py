import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


MIGRACAO = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "202606300001_criar_fundacao_plano_familia.sql"
)

streamlit_fake = ModuleType("streamlit")
streamlit_fake.session_state = {}
streamlit_fake.secrets = {}
streamlit_fake.error = lambda mensagem: None

supabase_module_fake = ModuleType("supabase")
supabase_module_fake.Client = object
supabase_module_fake.create_client = lambda url, chave: object()

sys.modules["streamlit"] = streamlit_fake
sys.modules["supabase"] = supabase_module_fake

from repositories import finance_repository


class QueryFake:
    def __init__(self, data=None):
        self.data = data
        self.calls = []

    def select(self, campos):
        self.calls.append(("select", campos))
        return self

    def eq(self, campo, valor):
        self.calls.append(("eq", campo, valor))
        return self

    def order(self, campo, **kwargs):
        self.calls.append(("order", campo, kwargs))
        return self

    def execute(self):
        self.calls.append(("execute",))
        return SimpleNamespace(data=self.data)


class RpcFake:
    def __init__(self, data=None):
        self.data = data
        self.calls = []

    def execute(self):
        self.calls.append(("execute",))
        return SimpleNamespace(data=self.data)


class SupabaseFake:
    def __init__(self, data=None):
        self.query = QueryFake(data)
        self.rpc_query = RpcFake(data)
        self.tables = []
        self.rpcs = []

    def table(self, nome):
        self.tables.append(nome)
        return self.query

    def rpc(self, nome, payload):
        self.rpcs.append((nome, payload))
        return self.rpc_query


class FamilyPlanPersistenceTests(unittest.TestCase):
    def test_migration_cria_tabelas_familiares_com_rls(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists public.familias_financeiras", sql)
        self.assertIn("create table if not exists public.membros_familia_financeira", sql)
        self.assertIn("owner_id uuid not null references auth.users(id)", sql)
        self.assertIn("limite_membros integer not null default 4", sql)
        self.assertIn("alter table public.familias_financeiras enable row level security", sql)
        self.assertIn("alter table public.membros_familia_financeira enable row level security", sql)
        self.assertNotIn("service_role", sql)

    def test_migration_limita_convites_e_preserva_isolamento_atual(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        self.assertIn("if v_total >= v_limite then", sql)
        self.assertIn("limite de membros do plano familia atingido", sql)
        self.assertIn("owner_id = auth.uid()", sql)
        self.assertIn("membro.user_id = auth.uid()", sql)
        self.assertIn("security definer", sql)
        self.assertIn("usuario_pode_ver_familia_financeira(id)", sql)
        self.assertIn("usuario_e_dono_familia_financeira(familia_id)", sql)
        self.assertNotIn("alter table public.transacoes", sql)
        self.assertNotIn("drop table", sql)

    def test_migration_cria_rpcs_para_familia_e_convite(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        self.assertIn("function public.criar_familia_financeira(p_nome text)", sql)
        self.assertIn("function public.convidar_membro_familia_financeira", sql)
        self.assertIn("grant execute on function public.criar_familia_financeira(text) to authenticated", sql)
        self.assertIn(
            "grant execute on function public.convidar_membro_familia_financeira(uuid, text) to authenticated",
            sql,
        )

    def test_repositorio_cria_familia_por_rpc(self):
        supabase = SupabaseFake(data={"id": "family-1"})

        with patch.object(finance_repository, "supabase", supabase):
            familia = finance_repository.criar_familia_financeira("Casa Silva")

        self.assertEqual(familia, {"id": "family-1"})
        self.assertEqual(
            supabase.rpcs,
            [("criar_familia_financeira", {"p_nome": "Casa Silva"})],
        )

    def test_repositorio_convida_membro_por_rpc(self):
        supabase = SupabaseFake(data={"id": "member-1"})

        with patch.object(finance_repository, "supabase", supabase):
            membro = finance_repository.convidar_membro_familia_financeira(
                "family-1",
                "pessoa@example.com",
            )

        self.assertEqual(membro, {"id": "member-1"})
        self.assertEqual(
            supabase.rpcs,
            [
                (
                    "convidar_membro_familia_financeira",
                    {"p_familia_id": "family-1", "p_email": "pessoa@example.com"},
                )
            ],
        )

    def test_repositorio_lista_familias_e_membros(self):
        supabase = SupabaseFake(data=[{"id": "family-1"}])

        with patch.object(finance_repository, "supabase", supabase):
            familias = finance_repository.listar_familias_financeiras()

        self.assertEqual(familias, [{"id": "family-1"}])
        self.assertEqual(supabase.tables, ["familias_financeiras"])
        self.assertIn(("order", "created_at", {"desc": False}), supabase.query.calls)

        supabase = SupabaseFake(data=[{"id": "member-1"}])
        with patch.object(finance_repository, "supabase", supabase):
            membros = finance_repository.listar_membros_familia_financeira("family-1")

        self.assertEqual(membros, [{"id": "member-1"}])
        self.assertEqual(supabase.tables, ["membros_familia_financeira"])
        self.assertIn(("eq", "familia_id", "family-1"), supabase.query.calls)


if __name__ == "__main__":
    unittest.main()
