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


def buscar_perfil_financeiro_360(usuario_id: str) -> dict | None:
    resposta = (
        supabase.table("perfis_financeiros_360")
        .select("*")
        .eq("user_id", usuario_id)
        .limit(1)
        .execute()
    )
    linhas = resposta.data or []
    return linhas[0] if linhas else None


def salvar_perfil_financeiro_360(perfil: dict) -> None:
    supabase.table("perfis_financeiros_360").upsert(
        perfil,
        on_conflict="user_id",
    ).execute()


def buscar_perfil_cliente(usuario_id: str) -> dict | None:
    resposta = (
        supabase.table("perfis_cliente")
        .select("*")
        .eq("user_id", usuario_id)
        .limit(1)
        .execute()
    )
    linhas = resposta.data or []
    return linhas[0] if linhas else None


def salvar_perfil_cliente(perfil: dict) -> None:
    supabase.table("perfis_cliente").upsert(
        perfil,
        on_conflict="user_id",
    ).execute()


def criar_familia_financeira(nome: str) -> dict | None:
    resposta = supabase.rpc(
        "criar_familia_financeira",
        {"p_nome": nome},
    ).execute()
    return resposta.data


def convidar_membro_familia_financeira(familia_id: str, email: str) -> dict | None:
    resposta = supabase.rpc(
        "convidar_membro_familia_financeira",
        {
            "p_familia_id": familia_id,
            "p_email": email,
        },
    ).execute()
    return resposta.data


def listar_familias_financeiras() -> list[dict]:
    resposta = (
        supabase.table("familias_financeiras")
        .select("*")
        .order("created_at", desc=False)
        .execute()
    )
    return resposta.data or []


def listar_membros_familia_financeira(familia_id: str) -> list[dict]:
    resposta = (
        supabase.table("membros_familia_financeira")
        .select("*")
        .eq("familia_id", familia_id)
        .order("created_at", desc=False)
        .execute()
    )
    return resposta.data or []


def obter_ou_criar_assinatura_usuario() -> dict | None:
    resposta = supabase.rpc("obter_ou_criar_assinatura_usuario", {}).execute()
    return resposta.data


def buscar_assinatura_usuario(usuario_id: str) -> dict | None:
    resposta = (
        supabase.table("assinaturas")
        .select("*")
        .eq("owner_id", usuario_id)
        .limit(1)
        .execute()
    )
    linhas = resposta.data or []
    return linhas[0] if linhas else None


def sincronizar_assinatura_stripe(assinatura: dict) -> dict | None:
    resposta = supabase.rpc(
        "sincronizar_assinatura_stripe",
        {
            "p_owner_id": assinatura["owner_id"],
            "p_plano": assinatura["plano"],
            "p_status": assinatura["status"],
            "p_stripe_customer_id": assinatura.get("stripe_customer_id"),
            "p_stripe_subscription_id": assinatura.get("stripe_subscription_id"),
            "p_stripe_price_id": assinatura.get("stripe_price_id"),
            "p_limite_membros": assinatura["limite_membros"],
            "p_current_period_end": assinatura.get("current_period_end"),
        },
    ).execute()
    return resposta.data


def registrar_evento_pagamento_stripe(evento: dict) -> None:
    supabase.rpc(
        "registrar_evento_pagamento_stripe",
        {
            "p_event_id": evento["id"],
            "p_tipo": evento["type"],
            "p_payload": evento,
        },
    ).execute()


def salvar_feedback_oraculo(feedback: dict) -> None:
    supabase.table("feedbacks_oraculo").insert(feedback).execute()
