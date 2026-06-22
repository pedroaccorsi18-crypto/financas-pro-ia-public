from auth import supabase


ORIGEM_IMPORTACAO_AUTOMATICA = "Automático"


def listar_transacoes_usuario(usuario_id: str) -> list[dict]:
    resposta = (
        supabase.table("transacoes")
        .select("*")
        .eq("user_id", usuario_id)
        .order("created_at", desc=False)
        .execute()
    )
    return resposta.data or []


def inserir_transacao(transacao: dict) -> None:
    supabase.table("transacoes").insert(transacao).execute()


def atualizar_categoria_transacao(transacao_id, categoria: str) -> None:
    supabase.table("transacoes").update({"categoria": categoria}).eq("id", transacao_id).execute()


def buscar_lote_importado(
    *,
    usuario_id: str,
    mes_referencia: str,
    instituicao_financeira: str,
    tipo_documento: str,
) -> list[dict]:
    campos_comparacao = [
        "descricao",
        "valor",
        "tipo",
        "categoria",
        "mes_referencia",
        "meta_fatura",
        "instituicao_financeira",
        "tipo_documento",
        "origem_importacao",
    ]
    resposta = (
        supabase.table("transacoes")
        .select("id," + ",".join(campos_comparacao))
        .eq("user_id", usuario_id)
        .eq("mes_referencia", mes_referencia)
        .eq("instituicao_financeira", instituicao_financeira)
        .eq("tipo_documento", tipo_documento)
        .eq("origem_importacao", ORIGEM_IMPORTACAO_AUTOMATICA)
        .execute()
    )
    return resposta.data or []


def substituir_lote_importado(
    *,
    usuario_id: str,
    mes_referencia: str,
    instituicao_financeira: str,
    tipo_documento: str,
    transacoes: list[dict],
) -> None:
    supabase.rpc(
        "substituir_lote_importado",
        {
            "p_user_id": usuario_id,
            "p_mes_referencia": mes_referencia,
            "p_instituicao_financeira": instituicao_financeira,
            "p_tipo_documento": tipo_documento,
            "p_transacoes": transacoes,
        },
    ).execute()


def salvar_meta_financeira(meta: dict) -> None:
    supabase.table("metas_financeiras").upsert(
        meta,
        on_conflict="user_id,categoria,mes_referencia",
    ).execute()


def listar_metas_usuario_mes(usuario_id: str, mes_referencia: str) -> list[dict]:
    resposta = (
        supabase.table("metas_financeiras")
        .select("*")
        .eq("user_id", usuario_id)
        .eq("mes_referencia", mes_referencia)
        .execute()
    )
    return resposta.data or []


def salvar_feedback_oraculo(feedback: dict) -> None:
    supabase.table("feedbacks_oraculo").insert(feedback).execute()
