import base64
import json
import os
import unittest
import uuid
from urllib.parse import urlparse


OPT_IN = "SUPABASE_RLS_INTEGRATION_TESTS"
CONFIRMACAO = "SUPABASE_RLS_CONFIRMED_NON_PRODUCTION"
URL = "SUPABASE_RLS_TEST_URL"
URL_PERMITIDA = "SUPABASE_RLS_ALLOWED_URL"
CHAVE = "SUPABASE_RLS_TEST_ANON_KEY"
EMAIL_A = "SUPABASE_RLS_TEST_USER_A_EMAIL"
SENHA_A = "SUPABASE_RLS_TEST_USER_A_PASSWORD"
EMAIL_B = "SUPABASE_RLS_TEST_USER_B_EMAIL"
SENHA_B = "SUPABASE_RLS_TEST_USER_B_PASSWORD"


def _valor(nome):
    return os.environ.get(nome, "").strip()


def _validar_ambiente_opt_in():
    if _valor(OPT_IN) != "1":
        raise unittest.SkipTest(
            f"Testes de RLS ignorados; defina {OPT_IN}=1 para habilitar."
        )

    exigidas = (
        CONFIRMACAO,
        URL,
        URL_PERMITIDA,
        CHAVE,
        EMAIL_A,
        SENHA_A,
        EMAIL_B,
        SENHA_B,
    )
    ausentes = [nome for nome in exigidas if not _valor(nome)]
    if ausentes:
        raise RuntimeError(
            "Configuracao incompleta dos testes de RLS: "
            + ", ".join(sorted(ausentes))
        )

    if _valor(CONFIRMACAO) != "YES":
        raise RuntimeError(
            f"Execucao bloqueada: confirme ambiente nao produtivo com {CONFIRMACAO}=YES."
        )

    url = _valor(URL).rstrip("/")
    permitida = _valor(URL_PERMITIDA).rstrip("/")
    if url != permitida:
        raise RuntimeError(
            f"Execucao bloqueada: {URL} deve corresponder exatamente a {URL_PERMITIDA}."
        )

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        raise RuntimeError("Execucao bloqueada: URL de teste invalida.")
    if any(marcador in host for marcador in ("prod", "production", "live")):
        raise RuntimeError("Execucao bloqueada: a URL parece apontar para producao.")

    if _valor(EMAIL_A).lower() == _valor(EMAIL_B).lower():
        raise RuntimeError("Os dois usuarios de teste devem ser distintos.")

    _validar_chave_anon(_valor(CHAVE))


def _validar_chave_anon(chave):
    if chave.startswith("sb_publishable_"):
        return
    if chave.startswith("sb_secret_"):
        raise RuntimeError("Execucao bloqueada: chave secreta/service_role nao permitida.")

    partes = chave.split(".")
    if len(partes) != 3:
        raise RuntimeError("Configure uma chave anon/public valida para os testes.")

    try:
        payload = partes[1] + "=" * (-len(partes[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as erro:
        raise RuntimeError("Configure uma chave anon/public valida para os testes.") from erro

    if claims.get("role") != "anon":
        raise RuntimeError("Execucao bloqueada: somente chave anon/public e permitida.")


def _linhas(resposta):
    dados = resposta.data
    if dados is None:
        return []
    if isinstance(dados, list):
        return dados
    return [dados]


class SupabaseRlsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _validar_ambiente_opt_in()

        from supabase import create_client

        cls.marcador = f"rls-it-{uuid.uuid4().hex}"
        cls.mes_referencia = "12/2099"
        cls.instituicao_a = f"{cls.marcador}-instituicao-a"
        cls.instituicao_b = f"{cls.marcador}-instituicao-b"
        cls.tipo_documento = f"{cls.marcador}-documento"
        cls.cliente_a = create_client(_valor(URL), _valor(CHAVE))
        cls.cliente_b = create_client(_valor(URL), _valor(CHAVE))
        cls.cliente_anon = create_client(_valor(URL), _valor(CHAVE))
        cls.addClassCleanup(cls._cleanup)

        sessao_a = cls.cliente_a.auth.sign_in_with_password(
            {"email": _valor(EMAIL_A), "password": _valor(SENHA_A)}
        )
        sessao_b = cls.cliente_b.auth.sign_in_with_password(
            {"email": _valor(EMAIL_B), "password": _valor(SENHA_B)}
        )
        cls.user_a = str(sessao_a.user.id)
        cls.user_b = str(sessao_b.user.id)
        cls.email_a = (sessao_a.user.email or _valor(EMAIL_A)).strip().lower()
        cls.email_b = (sessao_b.user.email or _valor(EMAIL_B)).strip().lower()
        if cls.user_a == cls.user_b:
            raise RuntimeError("Supabase Auth retornou o mesmo auth.uid() para os dois usuarios.")

        cls.transacao_a = cls._inserir_transacao(
            cls.cliente_a, cls.user_a, f"{cls.marcador}-transacao-a"
        )
        cls.transacao_b = cls._inserir_transacao(
            cls.cliente_b, cls.user_b, f"{cls.marcador}-transacao-b"
        )
        cls.meta_a = cls._inserir_meta(
            cls.cliente_a, cls.user_a, cls.email_a, f"{cls.marcador}-meta-a"
        )
        cls.meta_b = cls._inserir_meta(
            cls.cliente_b, cls.user_b, cls.email_b, f"{cls.marcador}-meta-b"
        )
        cls.feedback_a = cls._inserir_feedback(
            cls.cliente_a, cls.user_a, cls.email_a, f"{cls.marcador}-feedback-a"
        )
        cls.feedback_b = cls._inserir_feedback(
            cls.cliente_b, cls.user_b, cls.email_b, f"{cls.marcador}-feedback-b"
        )

    @classmethod
    def _inserir_um(cls, cliente, tabela, payload):
        linhas = _linhas(cliente.table(tabela).insert(payload).execute())
        if len(linhas) != 1:
            raise AssertionError(f"INSERT proprio em {tabela} nao retornou um registro.")
        return linhas[0]

    @classmethod
    def _inserir_transacao(cls, cliente, user_id, descricao):
        return cls._inserir_um(
            cliente,
            "transacoes",
            {
                "user_id": user_id,
                "descricao": descricao,
                "valor": 10.0,
                "tipo": "Despesa",
                "categoria": "Outros",
                "mes_referencia": cls.mes_referencia,
                "meta_fatura": 0.0,
                "instituicao_financeira": f"{cls.marcador}-manual",
                "tipo_documento": "Manual",
                "origem_importacao": "Manual",
            },
        )

    @classmethod
    def _inserir_meta(cls, cliente, user_id, email, categoria):
        return cls._inserir_um(
            cliente,
            "metas_financeiras",
            {
                "user_id": user_id,
                "usuario_email": email,
                "categoria": categoria,
                "mes_referencia": cls.mes_referencia,
                "valor_meta": 10.0,
            },
        )

    @classmethod
    def _inserir_feedback(cls, cliente, user_id, email, status):
        return cls._inserir_um(
            cliente,
            "feedbacks_oraculo",
            {
                "user_id": user_id,
                "usuario_email": email,
                "status_resposta": status,
                "resposta_ia": f"{cls.marcador}-resposta",
                "dados_enviados": f"{cls.marcador}-dados",
            },
        )

    @classmethod
    def _filtro_marcador(cls, tabela):
        return {
            "transacoes": ("descricao", f"{cls.marcador}%"),
            "metas_financeiras": ("categoria", f"{cls.marcador}%"),
            "feedbacks_oraculo": ("status_resposta", f"{cls.marcador}%"),
        }[tabela]

    @classmethod
    def _registros_da_execucao(cls, cliente, tabela, colunas="id,user_id"):
        coluna, padrao = cls._filtro_marcador(tabela)
        return _linhas(
            cliente.table(tabela).select(colunas).like(coluna, padrao).execute()
        )

    @classmethod
    def _obter_do_proprietario(cls, cliente, tabela, registro_id, colunas):
        linhas = _linhas(
            cliente.table(tabela)
            .select(colunas)
            .eq("id", registro_id)
            .execute()
        )
        if len(linhas) != 1:
            raise AssertionError(
                f"Proprietario nao encontrou exatamente um registro em {tabela}: {registro_id}"
            )
        return linhas[0]

    @classmethod
    def _cleanup(cls):
        problemas = []
        tabelas = ("transacoes", "metas_financeiras", "feedbacks_oraculo")
        for nome, cliente in (
            ("usuario_a", getattr(cls, "cliente_a", None)),
            ("usuario_b", getattr(cls, "cliente_b", None)),
        ):
            if cliente is None or not hasattr(cls, "marcador"):
                continue
            for tabela in tabelas:
                coluna, padrao = cls._filtro_marcador(tabela)
                try:
                    cliente.table(tabela).delete().like(coluna, padrao).execute()
                    restantes = cls._registros_da_execucao(cliente, tabela)
                    if restantes:
                        ids = [str(item.get("id")) for item in restantes]
                        problemas.append(f"{nome}/{tabela}: ids restantes {ids}")
                except Exception as erro:
                    problemas.append(
                        f"{nome}/{tabela}: cleanup falhou ({type(erro).__name__})"
                    )
            try:
                cliente.auth.sign_out()
            except Exception:
                problemas.append(f"{nome}: logout de cleanup falhou")

        if problemas:
            raise AssertionError(
                f"Cleanup incompleto para marcador {cls.marcador}: " + "; ".join(problemas)
            )

    def _assert_insert_bloqueado(self, cliente, tabela, payload, proprietario, coluna):
        try:
            cliente.table(tabela).insert(payload).execute()
        except Exception:
            pass
        linhas = _linhas(
            proprietario.table(tabela)
            .select(f"id,{coluna},user_id")
            .eq(coluna, payload[coluna])
            .execute()
        )
        self.assertEqual(linhas, [], f"INSERT indevido persistiu em {tabela}.")

    def _assert_update_terceiro_bloqueado(
        self, atacante, proprietario, tabela, registro, coluna, valor_original, valor_forjado
    ):
        try:
            atacante.table(tabela).update({coluna: valor_forjado}).eq(
                "id", registro["id"]
            ).execute()
        except Exception:
            pass
        atual = self._obter_do_proprietario(
            proprietario, tabela, registro["id"], f"id,{coluna},user_id"
        )
        self.assertEqual(atual[coluna], valor_original)

    def _assert_delete_terceiro_bloqueado(self, atacante, proprietario, tabela, registro):
        try:
            atacante.table(tabela).delete().eq("id", registro["id"]).execute()
        except Exception:
            pass
        atual = self._obter_do_proprietario(
            proprietario, tabela, registro["id"], "id,user_id"
        )
        self.assertEqual(str(atual["id"]), str(registro["id"]))

    def test_transacoes_select_isolado(self):
        linhas_a = self._registros_da_execucao(
            self.cliente_a, "transacoes", "id,descricao,user_id"
        )
        linhas_b = self._registros_da_execucao(
            self.cliente_b, "transacoes", "id,descricao,user_id"
        )
        self.assertGreaterEqual(len(linhas_a), 1)
        self.assertGreaterEqual(len(linhas_b), 1)
        self.assertIn(self.transacao_a["id"], [item["id"] for item in linhas_a])
        self.assertNotIn(self.transacao_b["id"], [item["id"] for item in linhas_a])
        self.assertIn(self.transacao_b["id"], [item["id"] for item in linhas_b])
        self.assertNotIn(self.transacao_a["id"], [item["id"] for item in linhas_b])

    def test_transacoes_insert_user_id_forjado_e_nulo_bloqueados(self):
        base = {
            "descricao": f"{self.marcador}-transacao-forjada",
            "valor": 10.0,
            "tipo": "Despesa",
            "categoria": "Outros",
            "mes_referencia": self.mes_referencia,
            "meta_fatura": 0.0,
            "instituicao_financeira": f"{self.marcador}-forjada",
            "tipo_documento": "Manual",
            "origem_importacao": "Manual",
        }
        self._assert_insert_bloqueado(
            self.cliente_a,
            "transacoes",
            {**base, "user_id": self.user_b},
            self.cliente_b,
            "descricao",
        )
        descricao_nula = f"{self.marcador}-transacao-nula"
        with self.assertRaises(Exception):
            self.cliente_a.table("transacoes").insert(
                {**base, "descricao": descricao_nula, "user_id": None}
            ).execute()
        self.assertEqual(
            _linhas(
                self.cliente_a.table("transacoes")
                .select("id")
                .eq("descricao", descricao_nula)
                .execute()
            ),
            [],
        )

    def test_transacoes_update_nao_transfere_propriedade(self):
        try:
            self.cliente_a.table("transacoes").update({"user_id": self.user_b}).eq(
                "id", self.transacao_a["id"]
            ).execute()
        except Exception:
            pass
        atual = self._obter_do_proprietario(
            self.cliente_a, "transacoes", self.transacao_a["id"], "id,user_id"
        )
        self.assertEqual(str(atual["user_id"]), self.user_a)

    def test_transacoes_update_e_delete_de_terceiro_bloqueados(self):
        self._assert_update_terceiro_bloqueado(
            self.cliente_a,
            self.cliente_b,
            "transacoes",
            self.transacao_b,
            "descricao",
            self.transacao_b["descricao"],
            f"{self.marcador}-transacao-update-forjado",
        )
        self._assert_delete_terceiro_bloqueado(
            self.cliente_a, self.cliente_b, "transacoes", self.transacao_b
        )

    def test_metas_rls_completa(self):
        linhas_a = self._registros_da_execucao(
            self.cliente_a, "metas_financeiras", "id,categoria,user_id"
        )
        linhas_b = self._registros_da_execucao(
            self.cliente_b, "metas_financeiras", "id,categoria,user_id"
        )
        self.assertIn(self.meta_a["id"], [item["id"] for item in linhas_a])
        self.assertNotIn(self.meta_b["id"], [item["id"] for item in linhas_a])
        self.assertIn(self.meta_b["id"], [item["id"] for item in linhas_b])
        self.assertNotIn(self.meta_a["id"], [item["id"] for item in linhas_b])
        self._assert_insert_bloqueado(
            self.cliente_a,
            "metas_financeiras",
            {
                "user_id": self.user_b,
                "usuario_email": self.email_b,
                "categoria": f"{self.marcador}-meta-forjada",
                "mes_referencia": self.mes_referencia,
                "valor_meta": 10.0,
            },
            self.cliente_b,
            "categoria",
        )
        self._assert_update_terceiro_bloqueado(
            self.cliente_a,
            self.cliente_b,
            "metas_financeiras",
            self.meta_b,
            "valor_meta",
            self.meta_b["valor_meta"],
            999.0,
        )
        self._assert_delete_terceiro_bloqueado(
            self.cliente_a, self.cliente_b, "metas_financeiras", self.meta_b
        )

    def test_feedbacks_rls_completa(self):
        linhas_a = self._registros_da_execucao(
            self.cliente_a, "feedbacks_oraculo", "id,status_resposta,user_id"
        )
        linhas_b = self._registros_da_execucao(
            self.cliente_b, "feedbacks_oraculo", "id,status_resposta,user_id"
        )
        self.assertIn(self.feedback_a["id"], [item["id"] for item in linhas_a])
        self.assertNotIn(self.feedback_b["id"], [item["id"] for item in linhas_a])
        self.assertIn(self.feedback_b["id"], [item["id"] for item in linhas_b])
        self.assertNotIn(self.feedback_a["id"], [item["id"] for item in linhas_b])
        self._assert_insert_bloqueado(
            self.cliente_a,
            "feedbacks_oraculo",
            {
                "user_id": self.user_b,
                "usuario_email": self.email_b,
                "status_resposta": f"{self.marcador}-feedback-forjado",
                "resposta_ia": f"{self.marcador}-resposta",
                "dados_enviados": f"{self.marcador}-dados",
            },
            self.cliente_b,
            "status_resposta",
        )
        self._assert_update_terceiro_bloqueado(
            self.cliente_a,
            self.cliente_b,
            "feedbacks_oraculo",
            self.feedback_b,
            "resposta_ia",
            self.feedback_b["resposta_ia"],
            f"{self.marcador}-resposta-forjada",
        )
        self._assert_delete_terceiro_bloqueado(
            self.cliente_a, self.cliente_b, "feedbacks_oraculo", self.feedback_b
        )

    def test_rpc_ignora_user_id_forjado_e_isola_lotes(self):
        descricao_a = f"{self.marcador}-rpc-a"
        descricao_b = f"{self.marcador}-rpc-b"
        tentativa_a_no_lote_b = f"{self.marcador}-rpc-a-lote-b"
        self._chamar_rpc(self.cliente_a, self.instituicao_a, descricao_a, self.user_a, self.user_b)
        self._chamar_rpc(self.cliente_b, self.instituicao_b, descricao_b, self.user_b, self.user_a)
        self._chamar_rpc(
            self.cliente_a, self.instituicao_b, tentativa_a_no_lote_b, self.user_a, self.user_b
        )

        lote_a = self._buscar_lote(
            self.cliente_a, self.instituicao_a, descricao_a
        )
        lote_tentativa = self._buscar_lote(
            self.cliente_a, self.instituicao_b, tentativa_a_no_lote_b
        )
        lote_b = self._buscar_lote(
            self.cliente_b, self.instituicao_b, descricao_b
        )
        self.assertEqual(str(lote_a["user_id"]), self.user_a)
        self.assertEqual(str(lote_tentativa["user_id"]), self.user_a)
        self.assertEqual(str(lote_b["user_id"]), self.user_b)
        self.assertEqual(lote_b["descricao"], descricao_b)
        self.assertEqual(
            _linhas(
                self.cliente_a.table("transacoes")
                .select("id")
                .eq("descricao", descricao_b)
                .execute()
            ),
            [],
            )

    def test_rpc_rejeita_p_user_id_forjado(self):
        descricao = f"{self.marcador}-rpc-p-user-id-forjado"
        with self.assertRaises(Exception):
            self._chamar_rpc(
                self.cliente_a,
                f"{self.marcador}-rpc-p-user-id-forjado",
                descricao,
                self.user_b,
                self.user_a,
            )
        self.assertEqual(
            _linhas(
                self.cliente_a.table("transacoes")
                .select("id")
                .eq("descricao", descricao)
                .execute()
            ),
            [],
        )

    def test_cliente_anonimo_e_bloqueado(self):
        proprio = self._obter_do_proprietario(
            self.cliente_a, "transacoes", self.transacao_a["id"], "id,user_id"
        )
        self.assertEqual(str(proprio["user_id"]), self.user_a)

        try:
            anon_select = _linhas(
                self.cliente_anon.table("transacoes")
                .select("id")
                .eq("id", self.transacao_a["id"])
                .execute()
            )
        except Exception:
            anon_select = []
        self.assertEqual(anon_select, [])

        descricao = f"{self.marcador}-anon-insert"
        self._assert_insert_bloqueado(
            self.cliente_anon,
            "transacoes",
            {
                "user_id": self.user_a,
                "descricao": descricao,
                "valor": 10.0,
                "tipo": "Despesa",
                "categoria": "Outros",
                "mes_referencia": self.mes_referencia,
                "meta_fatura": 0.0,
                "instituicao_financeira": f"{self.marcador}-anon",
                "tipo_documento": "Manual",
                "origem_importacao": "Manual",
            },
            self.cliente_a,
            "descricao",
        )

        descricao_rpc = f"{self.marcador}-anon-rpc"
        with self.assertRaises(Exception):
            self._chamar_rpc(
                self.cliente_anon,
                f"{self.marcador}-anon-rpc-instituicao",
                descricao_rpc,
                self.user_a,
                self.user_a,
            )
        self.assertEqual(
            _linhas(
                self.cliente_a.table("transacoes")
                .select("id")
                .eq("descricao", descricao_rpc)
                .execute()
            ),
            [],
        )

    def _buscar_lote(self, cliente, instituicao, descricao):
        linhas = _linhas(
            cliente.table("transacoes")
            .select("id,descricao,user_id,instituicao_financeira")
            .eq("descricao", descricao)
            .eq("instituicao_financeira", instituicao)
            .execute()
        )
        self.assertEqual(len(linhas), 1)
        return linhas[0]

    def _chamar_rpc(self, cliente, instituicao, descricao, p_user_id, user_id_forjado):
        cliente.rpc(
            "substituir_lote_importado",
            {
                "p_user_id": p_user_id,
                "p_mes_referencia": self.mes_referencia,
                "p_instituicao_financeira": instituicao,
                "p_tipo_documento": self.tipo_documento,
                "p_transacoes": [
                    {
                        "user_id": user_id_forjado,
                        "descricao": descricao,
                        "valor": 10.0,
                        "tipo": "Despesa",
                        "categoria": "Outros",
                        "mes_referencia": self.mes_referencia,
                        "meta_fatura": 0.0,
                        "instituicao_financeira": instituicao,
                        "tipo_documento": self.tipo_documento,
                        "origem_importacao": "Automático",
                    }
                ],
            },
        ).execute()


if __name__ == "__main__":
    unittest.main()
