import re
import unittest
from pathlib import Path


MIGRACAO = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "202606100006_endurecer_user_id_not_null.sql"
)


class UserIdNotNullMigrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRACAO.read_text(encoding="utf-8").lower()
        cls.primeiro_alter = cls.sql.index("alter table")

    def test_bloqueia_tabelas_antes_de_validar_e_alterar(self):
        bloqueio = self.sql.index("lock table")
        validacao = self.sql.index("do $validar_user_id$")

        self.assertLess(bloqueio, validacao)
        self.assertLess(validacao, self.primeiro_alter)
        self.assertIn("in share row exclusive mode", self.sql)

    def test_define_timeouts_locais_antes_dos_locks(self):
        inicio = self.sql.index("begin;")
        lock_timeout = self.sql.index("set local lock_timeout = '5s';")
        statement_timeout = self.sql.index("set local statement_timeout = '60s';")
        bloqueio = self.sql.index("lock table")

        self.assertLess(inicio, lock_timeout)
        self.assertLess(lock_timeout, statement_timeout)
        self.assertLess(statement_timeout, bloqueio)
        self.assertEqual(self.sql.count("set local lock_timeout"), 1)
        self.assertEqual(self.sql.count("set local statement_timeout"), 1)
        self.assertIn("aplicar em janela controlada", self.sql)
        self.assertIn("auditoria de prontidao", self.sql)
        self.assertIn("se houver timeout", self.sql)

    def test_valida_nulos_e_orfaos_por_tabela_antes_de_qualquer_alter(self):
        for tabela in (
            "transacoes",
            "metas_financeiras",
            "feedbacks_oraculo",
        ):
            trecho_nulos = (
                f"from public.{tabela}\n"
                "        where user_id is null"
            )
            trecho_orfaos = (
                f"from public.{tabela} item\n"
                "        where not exists"
            )
            erro_nulos = (
                f"public.{tabela}.user_id: existem registros com user_id nulo"
            )
            erro_orfaos = (
                f"public.{tabela}.user_id: existem user_id sem correspondencia em auth.users"
            )

            for trecho in (trecho_nulos, trecho_orfaos, erro_nulos, erro_orfaos):
                self.assertIn(trecho, self.sql)
                self.assertLess(self.sql.index(trecho), self.primeiro_alter)

        self.assertEqual(self.sql.count("from auth.users autenticado"), 3)

    def test_endurece_somente_as_tres_colunas_user_id(self):
        alteracoes = re.findall(
            r"alter table\s+public\.([a-z_]+)\s+"
            r"alter column\s+user_id\s+set not null",
            self.sql,
        )

        self.assertEqual(
            alteracoes,
            ["transacoes", "metas_financeiras", "feedbacks_oraculo"],
        )
        self.assertEqual(self.sql.count("set not null"), 4)

    def test_nao_altera_dados_nem_objetos_fora_do_escopo(self):
        proibidos = (
            "update ",
            "delete ",
            "insert ",
            "drop ",
            "truncate ",
            "create policy",
            "alter policy",
            "enable row level security",
            "disable row level security",
            "grant ",
            "revoke ",
            "usuario_email",
            "public.usuarios",
            "trigger ",
            "drop function",
            "create function",
        )

        for proibido in proibidos:
            self.assertNotIn(proibido, self.sql)

    def test_migracao_e_transacional(self):
        self.assertTrue(self.sql.strip().startswith("--"))
        self.assertIn("begin;", self.sql)
        self.assertIn("end;\n$validar_user_id$;", self.sql)
        self.assertTrue(self.sql.strip().endswith("commit;"))


if __name__ == "__main__":
    unittest.main()
