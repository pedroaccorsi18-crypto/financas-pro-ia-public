import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


MIGRACAO = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "202606300002_criar_assinaturas_stripe.sql"
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

    def limit(self, limite):
        self.calls.append(("limit", limite))
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


class SubscriptionPersistenceTests(unittest.TestCase):
    def test_migration_cria_base_de_assinaturas_com_rls(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists public.assinaturas", sql)
        self.assertIn("create table if not exists public.eventos_pagamento", sql)
        self.assertIn("owner_id uuid primary key references auth.users(id)", sql)
        self.assertIn("plano text not null default 'gratuito'", sql)
        self.assertIn("limite_membros integer not null default 1", sql)
        self.assertIn("alter table public.assinaturas enable row level security", sql)
        self.assertIn("alter table public.eventos_pagamento enable row level security", sql)
        self.assertIn("owner_id = auth.uid()", sql)

    def test_migration_cria_rpc_para_assinatura_gratuita_automatica(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        self.assertIn("function public.obter_ou_criar_assinatura_usuario()", sql)
        self.assertIn("insert into public.assinaturas", sql)
        self.assertIn("'gratuito'", sql)
        self.assertIn("'manual'", sql)
        self.assertIn("grant execute on function public.obter_ou_criar_assinatura_usuario() to authenticated", sql)

    def test_migration_restringe_sincronizacao_stripe_ao_service_role(self):
        sql = MIGRACAO.read_text(encoding="utf-8").lower()

        self.assertIn("function public.sincronizar_assinatura_stripe", sql)
        self.assertIn("function public.registrar_evento_pagamento_stripe", sql)
        self.assertIn("on conflict (owner_id) do update", sql)
        self.assertIn("on conflict (event_id) do nothing", sql)
        self.assertIn("grant execute on function public.sincronizar_assinatura_stripe", sql)
        self.assertIn("to service_role", sql)
        self.assertNotIn("to authenticated;\n\ngrant execute on function public.sincronizar_assinatura_stripe", sql)

    def test_repositorio_obtem_ou_cria_assinatura_por_rpc(self):
        supabase = SupabaseFake(data={"owner_id": "user-1", "plano": "gratuito"})

        with patch.object(finance_repository, "supabase", supabase):
            assinatura = finance_repository.obter_ou_criar_assinatura_usuario()

        self.assertEqual(assinatura, {"owner_id": "user-1", "plano": "gratuito"})
        self.assertEqual(supabase.rpcs, [("obter_ou_criar_assinatura_usuario", {})])

    def test_repositorio_busca_assinatura_por_usuario(self):
        supabase = SupabaseFake(data=[{"owner_id": "user-1", "plano": "pro"}])

        with patch.object(finance_repository, "supabase", supabase):
            assinatura = finance_repository.buscar_assinatura_usuario("user-1")

        self.assertEqual(assinatura, {"owner_id": "user-1", "plano": "pro"})
        self.assertEqual(supabase.tables, ["assinaturas"])
        self.assertIn(("eq", "owner_id", "user-1"), supabase.query.calls)
        self.assertIn(("limit", 1), supabase.query.calls)

    def test_repositorio_sincroniza_assinatura_stripe_por_rpc(self):
        supabase = SupabaseFake(data={"owner_id": "user-1", "plano": "familia"})

        assinatura = {
            "owner_id": "user-1",
            "plano": "familia",
            "status": "ativo",
            "stripe_customer_id": "cus_123",
            "stripe_subscription_id": "sub_123",
            "stripe_price_id": "price_familia",
            "limite_membros": 4,
            "current_period_end": "2026-06-30T00:00:00+00:00",
        }
        with patch.object(finance_repository, "supabase", supabase):
            resultado = finance_repository.sincronizar_assinatura_stripe(assinatura)

        self.assertEqual(resultado, {"owner_id": "user-1", "plano": "familia"})
        self.assertEqual(supabase.rpcs[0][0], "sincronizar_assinatura_stripe")
        self.assertEqual(supabase.rpcs[0][1]["p_limite_membros"], 4)
        self.assertEqual(supabase.rpcs[0][1]["p_stripe_subscription_id"], "sub_123")

    def test_repositorio_registra_evento_pagamento_idempotente(self):
        supabase = SupabaseFake()
        evento = {"id": "evt_123", "type": "checkout.session.completed"}

        with patch.object(finance_repository, "supabase", supabase):
            finance_repository.registrar_evento_pagamento_stripe(evento)

        self.assertEqual(
            supabase.rpcs,
            [
                (
                    "registrar_evento_pagamento_stripe",
                    {
                        "p_event_id": "evt_123",
                        "p_tipo": "checkout.session.completed",
                        "p_payload": evento,
                    },
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
