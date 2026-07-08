import unittest
from pathlib import Path


MIGRATION_SOURCE = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "202607070001_criar_perfis_cliente.sql"
).read_text(encoding="utf-8")
REPOSITORY_SOURCE = (
    Path(__file__).parents[1] / "repositories" / "finance_repository.py"
).read_text(encoding="utf-8")


class CustomerProfilePersistenceTests(unittest.TestCase):
    def test_migration_cria_perfis_cliente_com_rls(self):
        self.assertIn("create table if not exists public.perfis_cliente", MIGRATION_SOURCE)
        self.assertIn("user_id uuid primary key references auth.users(id)", MIGRATION_SOURCE)
        self.assertIn("alter table public.perfis_cliente enable row level security", MIGRATION_SOURCE)
        self.assertIn("auth.uid() = user_id", MIGRATION_SOURCE)
        self.assertIn("aceita_personalizacao boolean not null default true", MIGRATION_SOURCE)

    def test_repositorio_busca_e_salva_perfil_cliente(self):
        self.assertIn('supabase.table("perfis_cliente")', REPOSITORY_SOURCE)
        self.assertIn("def buscar_perfil_cliente", REPOSITORY_SOURCE)
        self.assertIn("def salvar_perfil_cliente", REPOSITORY_SOURCE)
        self.assertIn('on_conflict="user_id"', REPOSITORY_SOURCE)


if __name__ == "__main__":
    unittest.main()
