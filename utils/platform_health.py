TABELAS_OBRIGATORIAS = [
    {
        "nome": "Transações",
        "tabela": "transacoes",
        "select": "id",
        "acao": "Aplique as migrações iniciais das transações no Supabase.",
    },
    {
        "nome": "Metas financeiras",
        "tabela": "metas_financeiras",
        "select": "id",
        "acao": "Aplique as migrações de metas financeiras no Supabase.",
    },
    {
        "nome": "Feedback do Oráculo",
        "tabela": "feedbacks_oraculo",
        "select": "id",
        "acao": "Aplique as migrações de feedbacks_oraculo no Supabase.",
    },
    {
        "nome": "Perfil Financeiro 360",
        "tabela": "perfis_financeiros_360",
        "select": "user_id",
        "acao": "Aplique a migração 202606250001_criar_perfis_financeiros_360.sql.",
    },
]


def gerar_health_check_supabase(supabase, usuario_id):
    resultados = [_verificar_tabela(supabase, item) for item in TABELAS_OBRIGATORIAS]
    resultados.append(_verificar_rpc_reimportacao(supabase, usuario_id))
    return resultados


def resumir_health_check(resultados):
    if any(item["status"] == "Ação necessária" for item in resultados):
        return "Ação necessária"
    if any(item["status"] == "Atenção" for item in resultados):
        return "Atenção"
    return "OK"


def _verificar_tabela(supabase, item):
    try:
        (
            supabase.table(item["tabela"])
            .select(item["select"])
            .limit(1)
            .execute()
        )
        return _resultado(item["nome"], "OK", "Tabela acessível.", "Nenhuma ação necessária.")
    except Exception as erro:
        return _resultado_de_erro(
            item["nome"],
            erro,
            acao_padrao=item["acao"],
        )


def _verificar_rpc_reimportacao(supabase, usuario_id):
    try:
        supabase.rpc(
            "substituir_lote_importado",
            {
                "p_user_id": usuario_id,
                "p_mes_referencia": "01/1900",
                "p_instituicao_financeira": "__healthcheck__",
                "p_tipo_documento": "__healthcheck__",
                "p_transacoes": [],
            },
        ).execute()
        return _resultado(
            "RPC de reimportação",
            "OK",
            "Função disponível.",
            "Nenhuma ação necessária.",
        )
    except Exception as erro:
        texto = str(erro).lower()
        if (
            "payload de transacoes nao pode ser vazio" in texto
            or "payload de transações não pode ser vazio" in texto
        ):
            return _resultado(
                "RPC de reimportação",
                "OK",
                "Função disponível e valida payload antes de alterar dados.",
                "Nenhuma ação necessária.",
            )
        return _resultado_de_erro(
            "RPC de reimportação",
            erro,
            acao_padrao="Aplique a migração 202606100001_endurecer_rpc_substituir_lote.sql.",
        )


def _resultado_de_erro(nome, erro, *, acao_padrao):
    texto = str(erro).lower()
    if _parece_objeto_ausente(texto):
        return _resultado(nome, "Ação necessária", "Objeto ausente no Supabase.", acao_padrao)
    if _parece_permissao_negada(texto):
        return _resultado(
            nome,
            "Atenção",
            "Supabase bloqueou o acesso por permissão/RLS.",
            "Revise policies RLS e permissões para usuários autenticados.",
        )
    return _resultado(
        nome,
        "Atenção",
        "Não foi possível validar este item.",
        "Confira logs do app e conectividade com o Supabase.",
    )


def _parece_objeto_ausente(texto):
    marcadores = (
        "schema cache",
        "could not find",
        "does not exist",
        "pgrst202",
        "pgrst205",
        "42p01",
        "relation",
        "function",
    )
    return any(marcador in texto for marcador in marcadores)


def _parece_permissao_negada(texto):
    return "permission denied" in texto or "42501" in texto or "rls" in texto


def _resultado(nome, status, detalhe, acao):
    return {
        "item": nome,
        "status": status,
        "detalhe": detalhe,
        "acao": acao,
    }
