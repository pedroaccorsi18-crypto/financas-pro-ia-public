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
    {
        "nome": "Perfil do Cliente",
        "tabela": "perfis_cliente",
        "select": "user_id",
        "acao": "Aplique a migração 202607070001_criar_perfis_cliente.sql.",
    },
    {
        "nome": "Assinaturas",
        "tabela": "assinaturas",
        "select": "owner_id",
        "acao": "Aplique a migração 202606300002_criar_assinaturas_stripe.sql.",
    },
]


FLAGS_MODULOS_AVANCADOS = (
    "ENABLE_ORACULO_IA",
    "ENABLE_PLANEJAMENTO_360",
    "ENABLE_MARKET_RADAR",
)


def gerar_health_check_supabase(supabase, usuario_id):
    resultados = [_verificar_tabela(supabase, item) for item in TABELAS_OBRIGATORIAS]
    resultados.append(_verificar_rpc_reimportacao(supabase, usuario_id))
    resultados.append(_verificar_rpc_assinatura(supabase))
    return resultados


def gerar_health_check_lancamento(secrets, supabase, usuario_id, status_infra):
    resultados = []
    resultados.append(_verificar_secrets_supabase(secrets))
    resultados.append(_verificar_auth_operacional(status_infra))
    resultados.extend(gerar_health_check_supabase(supabase, usuario_id))
    resultados.append(_verificar_modulos_avancados_ocultos(secrets))
    resultados.append(_verificar_gemini_configurado(secrets))
    resultados.append(_verificar_stripe_configurado(secrets))
    return resultados


def resumir_health_check(resultados):
    if any(_eh_acao_necessaria(item["status"]) for item in resultados):
        return "Ação necessária"
    if any(_eh_atencao(item["status"]) for item in resultados):
        return "Atenção"
    return "OK"


def gerar_decisao_lancamento(resultados):
    bloqueios = [item for item in resultados if _eh_acao_necessaria(item["status"])]
    pendencias = [item for item in resultados if _eh_atencao(item["status"])]
    if bloqueios:
        return {
            "pronto": False,
            "status": "Bloqueado",
            "mensagem": "Ainda existem bloqueios antes de liberar o app para usuários.",
            "bloqueios": bloqueios,
            "pendencias": pendencias,
            "proxima_acao": bloqueios[0]["acao"],
        }
    if pendencias:
        return {
            "pronto": True,
            "status": "Validável com atenção",
            "mensagem": "O produto básico pode ser validado, mas há pendências operacionais.",
            "bloqueios": [],
            "pendencias": pendencias,
            "proxima_acao": pendencias[0]["acao"],
        }
    return {
        "pronto": True,
        "status": "Pronto",
        "mensagem": "Produto básico pronto para validação com usuários.",
        "bloqueios": [],
        "pendencias": [],
        "proxima_acao": "Liberar um grupo pequeno de usuários e acompanhar suporte, erros e conversão.",
    }


def _eh_acao_necessaria(status):
    return "necess" in str(status).lower()


def _eh_atencao(status):
    return str(status).lower().startswith("aten")


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


def _verificar_rpc_assinatura(supabase):
    try:
        supabase.rpc("obter_ou_criar_assinatura_usuario", {}).execute()
        return _resultado(
            "RPC de assinatura gratuita",
            "OK",
            "Função disponível para provisionar plano gratuito.",
            "Nenhuma ação necessária.",
        )
    except Exception as erro:
        return _resultado_de_erro(
            "RPC de assinatura gratuita",
            erro,
            acao_padrao="Aplique a migração 202606300002_criar_assinaturas_stripe.sql.",
        )


def _verificar_secrets_supabase(secrets):
    chaves_ausentes = [
        chave for chave in ("SUPABASE_URL", "SUPABASE_KEY") if not secrets.get(chave)
    ]
    if chaves_ausentes:
        return _resultado(
            "Configuração Supabase",
            "Ação necessária",
            "Secrets obrigatórios ausentes.",
            "Configure SUPABASE_URL e SUPABASE_KEY no secrets.toml ou no ambiente de deploy.",
        )
    return _resultado(
        "Configuração Supabase",
        "OK",
        "URL e chave pública carregadas.",
        "Nenhuma ação necessária.",
    )


def _verificar_auth_operacional(status_infra):
    seguranca = str(status_infra.get("seguranca", ""))
    if "RLS ativos" in seguranca:
        return _resultado(
            "Autenticação e RLS",
            "OK",
            "Sessão autenticada validada com leitura protegida.",
            "Nenhuma ação necessária.",
        )
    return _resultado(
        "Autenticação e RLS",
        "Atenção",
        "Não foi possível confirmar sessão autenticada e RLS.",
        "Faça login com usuário real e revise o Status operacional.",
    )


def _verificar_modulos_avancados_ocultos(secrets):
    flags_ativas = [
        flag for flag in FLAGS_MODULOS_AVANCADOS if _flag_ativa(secrets.get(flag))
    ]
    if flags_ativas:
        return _resultado(
            "Escopo de lançamento",
            "Atenção",
            "Há módulos avançados visíveis no app.",
            "Desative flags avançadas para lançar primeiro o app de finanças pessoais.",
        )
    return _resultado(
        "Escopo de lançamento",
        "OK",
        "Módulos avançados ocultos por feature flag.",
        "Nenhuma ação necessária.",
    )


def _verificar_gemini_configurado(secrets):
    if secrets.get("GEMINI_API_KEY"):
        return _resultado(
            "Gemini",
            "OK",
            "Chave de IA configurada.",
            "Nenhuma ação necessária.",
        )
    return _resultado(
        "Gemini",
        "Atenção",
        "IA não configurada para recursos assistidos.",
        "Configure GEMINI_API_KEY antes de liberar importação assistida em produção.",
    )


def _verificar_stripe_configurado(secrets):
    chaves = ("STRIPE_SECRET_KEY", "STRIPE_PRICE_PRO", "STRIPE_PRICE_FAMILIA")
    if all(secrets.get(chave) for chave in chaves) and secrets.get("STRIPE_WEBHOOK_SECRET"):
        return _resultado(
            "Stripe",
            "OK",
            "Checkout e webhook de assinaturas configurados.",
            "Faça uma compra de teste antes de cobrar usuários reais.",
        )
    if all(secrets.get(chave) for chave in chaves):
        return _resultado(
            "Stripe",
            "Atenção",
            "Checkout configurado, mas webhook ainda pendente.",
            "Configure STRIPE_WEBHOOK_SECRET e valide sincronização de assinaturas.",
        )
    return _resultado(
        "Stripe",
        "Atenção",
        "Cobrança ainda não configurada.",
        "Manter planos pagos ocultos ou configurar Stripe antes do lançamento comercial.",
    )


def _flag_ativa(valor):
    return str(valor or "").strip().lower() in {"1", "true", "yes", "y", "sim", "s", "on"}


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
