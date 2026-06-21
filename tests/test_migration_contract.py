import re
import unittest
from pathlib import Path


MIGRACAO = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "202606100001_endurecer_rpc_substituir_lote.sql"
)
APP_SOURCE = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8").lower()


class MigrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRACAO.read_text(encoding="utf-8").lower()

    def test_rpc_deriva_identidade_do_auth_uid(self):
        trecho_nova_rpc = cls_trecho_nova_rpc(self.sql)
        self.assertNotIn("p_usuario_email", trecho_nova_rpc)
        self.assertIn("p_user_id uuid", trecho_nova_rpc)
        self.assertIn("v_auth_user_id uuid := auth.uid()", trecho_nova_rpc)
        self.assertIn("p_user_id is distinct from v_auth_user_id", trecho_nova_rpc)
        self.assertIn("where user_id = p_user_id", trecho_nova_rpc)

    def test_rpc_preserva_email_apenas_para_compatibilidade(self):
        trecho_nova_rpc = cls_trecho_nova_rpc(self.sql)
        self.assertIn("auth.jwt()", trecho_nova_rpc)
        self.assertIn("user_id", trecho_nova_rpc)
        self.assertIn("usuario_email", trecho_nova_rpc)

    def test_rpc_valida_identidade_do_lote_antes_do_delete(self):
        trecho_nova_rpc = cls_trecho_nova_rpc(self.sql)
        exclusao = "delete from public.transacoes"
        insercao = "insert into public.transacoes"

        for campo, parametro in (
            ("mes_referencia", "p_mes_referencia"),
            ("instituicao_financeira", "p_instituicao_financeira"),
            ("tipo_documento", "p_tipo_documento"),
        ):
            validacao = f"item->>'{campo}' is distinct from {parametro}"
            self.assertIn(validacao, trecho_nova_rpc)
            self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(exclusao))
            self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(insercao))

    def test_rpc_rejeita_payload_vazio_antes_do_delete(self):
        trecho_nova_rpc = cls_trecho_nova_rpc(self.sql)
        validacao_tipo = "jsonb_typeof(p_transacoes) is distinct from 'array'"
        validacao = "jsonb_array_length(p_transacoes) = 0"
        erro = "raise exception 'payload de transacoes nao pode ser vazio'"
        exclusao = "delete from public.transacoes"
        insercao = "insert into public.transacoes"

        self.assertLess(trecho_nova_rpc.index(validacao_tipo), trecho_nova_rpc.index(validacao))
        self.assertIn(validacao, trecho_nova_rpc)
        self.assertIn(erro, trecho_nova_rpc)
        self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(exclusao))
        self.assertLess(trecho_nova_rpc.index(erro), trecho_nova_rpc.index(exclusao))
        self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(insercao))
        self.assertLess(trecho_nova_rpc.index(erro), trecho_nova_rpc.index(insercao))

    def test_rpc_rejeita_parametros_invalidos_antes_do_delete(self):
        trecho_nova_rpc = cls_trecho_nova_rpc(self.sql)
        exclusao = "delete from public.transacoes"
        insercao = "insert into public.transacoes"
        validacoes = (
            "p_mes_referencia !~ '^(0[1-9]|1[0-2])/[0-9]{4}$'",
            "nullif(trim(p_instituicao_financeira), '') is null",
            "nullif(trim(p_tipo_documento), '') is null",
            "raise exception 'identidade do lote invalida'",
        )

        for validacao in validacoes:
            self.assertIn(validacao, trecho_nova_rpc)
            self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(exclusao))
            self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(insercao))

    def test_rpc_valida_todo_payload_antes_do_delete(self):
        trecho_nova_rpc = cls_trecho_nova_rpc(self.sql)
        exclusao = "delete from public.transacoes"
        insercao = "insert into public.transacoes"
        validacoes = (
            "jsonb_typeof(p_transacoes) is distinct from 'array'",
            "jsonb_typeof(item) is distinct from 'object'",
            "nullif(trim(item->>'descricao'), '') is null",
            "jsonb_typeof(item->'valor') is distinct from 'number'",
            "(item->>'valor')::numeric <= 0",
            "item->>'tipo' not in ('despesa', 'receita')",
            "nullif(trim(item->>'categoria'), '') is null",
            "(item->>'meta_fatura')::numeric < 0",
            "item->>'origem_importacao' is distinct from 'automático'",
            "raise exception 'payload de transacoes possui campos ausentes ou tipos invalidos'",
            "raise exception 'payload de transacoes invalido ou inconsistente com o lote'",
        )

        for validacao in validacoes:
            self.assertIn(validacao, trecho_nova_rpc)
            self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(exclusao))
            self.assertLess(trecho_nova_rpc.index(validacao), trecho_nova_rpc.index(insercao))

    def test_rpc_insere_identidade_do_lote_a_partir_dos_parametros_validados(self):
        trecho_nova_rpc = cls_trecho_nova_rpc(self.sql)
        self.assertIn("p_user_id,", trecho_nova_rpc)
        self.assertIn("p_mes_referencia,", trecho_nova_rpc)
        self.assertIn("p_instituicao_financeira,", trecho_nova_rpc)
        self.assertIn("p_tipo_documento,", trecho_nova_rpc)

    def test_migration_nao_faz_alteracoes_destrutivas(self):
        for operacao in (
            "drop table",
            "truncate ",
            "alter column user_id set not null",
            "delete from public.usuarios",
            "drop function",
        ):
            self.assertNotIn(operacao, self.sql)
        self.assertEqual(self.sql.count("delete from public.transacoes"), 1)

    def test_rpc_preserva_assinatura_e_permissoes_atuais(self):
        assinatura = "public.substituir_lote_importado(uuid, text, text, text, jsonb)"
        cabecalho = self.sql.split(
            "create or replace function public.substituir_lote_importado(",
            1,
        )[1].split(")", 1)[0]
        parametros = re.sub(r"\s+", " ", cabecalho).strip()

        self.assertIn("create or replace function public.substituir_lote_importado(", self.sql)
        self.assertEqual(
            parametros,
            (
                "p_user_id uuid, "
                "p_mes_referencia text, "
                "p_instituicao_financeira text, "
                "p_tipo_documento text, "
                "p_transacoes jsonb"
            ),
        )
        self.assertIn(f"revoke all on function {assinatura}", self.sql)
        self.assertIn(f"grant execute on function {assinatura}", self.sql)
        self.assertIn("to authenticated", self.sql)
        self.assertIn(
            "security invoker",
            cls_trecho_nova_rpc(self.sql),
        )
        self.assertNotIn("p_usuario_email text", self.sql)

    def test_app_grava_todo_lote_importado_pela_rpc(self):
        trecho_importacao = APP_SOURCE.split(
            "if transacoes_para_inserir:",
            1,
        )[1].split(
            "if pre_vis[\"total_documento\"] > 0:",
            1,
        )[0]

        self.assertIn('supabase.rpc("substituir_lote_importado"', trecho_importacao)
        self.assertIn('"p_user_id": usuario_id', trecho_importacao)
        self.assertNotIn(
            'supabase.table("transacoes").insert(transacoes_para_inserir)',
            APP_SOURCE,
        )
        self.assertNotIn("if lote_existente:", trecho_importacao)


def cls_trecho_nova_rpc(sql):
    return sql.split(
        "create or replace function public.substituir_lote_importado(",
    )[-1]


if __name__ == "__main__":
    unittest.main()
