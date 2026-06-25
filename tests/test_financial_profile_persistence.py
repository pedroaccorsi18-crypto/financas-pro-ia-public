import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


MIGRACAO = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "202606250001_criar_perfis_financeiros_360.sql"
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

    def limit(self, valor):
        self.calls.append(("limit", valor))
        return self

    def upsert(self, payload, **kwargs):
        self.calls.append(("upsert", payload, kwargs))
        return self

    def execute(self):
        self.calls.append(("execute",))
        return SimpleNamespace(data=self.data)


class SupabaseFake:
    def __init__(self, data=None):
        self.query = QueryFake(data)
        self.tables = []

    def table(self, nome):
        self.tables.append(nome)
        return self.query


class FinancialProfilePersistenceTests(unittest.TestCase):
    def test_migration_cria_tabela_com_rls_por_auth_uid(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists public.perfis_financeiros_360", sql)
        self.assertIn("user_id uuid primary key references auth.users(id)", sql)
        self.assertIn("alter table public.perfis_financeiros_360 enable row level security", sql)
        self.assertEqual(sql.count("auth.uid() = user_id"), 5)
        self.assertIn("for select", sql)
        self.assertIn("for insert", sql)
        self.assertIn("for update", sql)
        self.assertIn("for delete", sql)
        self.assertNotIn("service_role", sql)

    def test_migration_valida_campos_do_perfil_360(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        for campo in (
            "idade",
            "dependentes",
            "renda_mensal",
            "reserva_emergencia",
            "patrimonio_investido",
            "dividas",
            "idade_aposentadoria",
            "renda_aposentadoria_desejada",
            "patrimonio_sucessorio",
            "objetivo_principal",
            "perfil_risco",
            "horizonte",
            "possui_seguro",
        ):
            self.assertIn(campo, sql)

        self.assertIn("check (idade between 0 and 120)", sql)
        self.assertIn("check (perfil_risco in ('conservador', 'moderado', 'arrojado'))", sql)

    def test_repositorio_busca_perfil_por_usuario(self):
        supabase = SupabaseFake(data=[{"user_id": "user-1", "idade": 40}])

        with patch.object(finance_repository, "supabase", supabase):
            perfil = finance_repository.buscar_perfil_financeiro_360("user-1")

        self.assertEqual(perfil["idade"], 40)
        self.assertEqual(supabase.tables, ["perfis_financeiros_360"])
        self.assertIn(("eq", "user_id", "user-1"), supabase.query.calls)
        self.assertIn(("limit", 1), supabase.query.calls)

    def test_repositorio_salva_perfil_por_upsert_user_id(self):
        supabase = SupabaseFake(data=[])
        payload = {"user_id": "user-1", "idade": 40}

        with patch.object(finance_repository, "supabase", supabase):
            finance_repository.salvar_perfil_financeiro_360(payload)

        self.assertEqual(supabase.tables, ["perfis_financeiros_360"])
        self.assertIn(("upsert", payload, {"on_conflict": "user_id"}), supabase.query.calls)


if __name__ == "__main__":
    unittest.main()
