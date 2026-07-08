from dataclasses import dataclass


MOMENTOS_FINANCEIROS = (
    "Organizando a casa",
    "Saindo de dívidas",
    "Criando reserva",
    "Investindo melhor",
    "Planejando família",
    "Preparando aposentadoria",
)

OBJETIVOS_PRINCIPAIS = (
    "Entender para onde o dinheiro está indo",
    "Reduzir gastos recorrentes",
    "Montar reserva de emergência",
    "Quitar dívidas",
    "Investir com mais consistência",
    "Organizar finanças da família",
)

DORES_FINANCEIRAS = (
    "Falta de clareza sobre gastos",
    "Dificuldade para manter constância",
    "Gastos impulsivos",
    "Dívidas ou parcelas pesadas",
    "Falta de planejamento familiar",
    "Medo de investir errado",
)

NIVEIS_ORGANIZACAO = (
    "Estou começando agora",
    "Tenho algum controle, mas falho na constância",
    "Acompanho todo mês",
    "Tenho método e quero otimizar",
)

PERFIS_DECISAO = (
    "Quero recomendações simples e diretas",
    "Quero entender o motivo antes de agir",
    "Quero comparar cenários",
)

PREFERENCIAS_ACOMPANHAMENTO = (
    "Semanal",
    "Quinzenal",
    "Mensal",
)


@dataclass(frozen=True)
class DiagnosticoPerfilCliente:
    nivel: str
    mensagem: str
    proxima_acao: str


def perfil_cliente_padrao(usuario_id: str | None = None) -> dict:
    return {
        "user_id": usuario_id,
        "momento_financeiro": MOMENTOS_FINANCEIROS[0],
        "objetivo_principal": OBJETIVOS_PRINCIPAIS[0],
        "maior_dor": DORES_FINANCEIRAS[0],
        "nivel_organizacao": NIVEIS_ORGANIZACAO[0],
        "perfil_decisao": PERFIS_DECISAO[0],
        "preferencia_acompanhamento": PREFERENCIAS_ACOMPANHAMENTO[2],
        "aceita_personalizacao": True,
    }


def normalizar_perfil_cliente(perfil: dict | None, usuario_id: str | None = None) -> dict:
    normalizado = perfil_cliente_padrao(usuario_id)
    for chave in normalizado:
        if chave == "user_id":
            continue
        valor = (perfil or {}).get(chave)
        if valor not in (None, ""):
            normalizado[chave] = valor
    normalizado["user_id"] = (perfil or {}).get("user_id") or usuario_id
    normalizado["aceita_personalizacao"] = bool(normalizado["aceita_personalizacao"])
    return normalizado


def montar_payload_perfil_cliente(
    *,
    usuario_id: str,
    momento_financeiro: str,
    objetivo_principal: str,
    maior_dor: str,
    nivel_organizacao: str,
    perfil_decisao: str,
    preferencia_acompanhamento: str,
    aceita_personalizacao: bool,
) -> dict:
    return {
        "user_id": usuario_id,
        "momento_financeiro": _validar_opcao(momento_financeiro, MOMENTOS_FINANCEIROS),
        "objetivo_principal": _validar_opcao(objetivo_principal, OBJETIVOS_PRINCIPAIS),
        "maior_dor": _validar_opcao(maior_dor, DORES_FINANCEIRAS),
        "nivel_organizacao": _validar_opcao(nivel_organizacao, NIVEIS_ORGANIZACAO),
        "perfil_decisao": _validar_opcao(perfil_decisao, PERFIS_DECISAO),
        "preferencia_acompanhamento": _validar_opcao(
            preferencia_acompanhamento,
            PREFERENCIAS_ACOMPANHAMENTO,
        ),
        "aceita_personalizacao": bool(aceita_personalizacao),
    }


def diagnosticar_perfil_cliente(perfil: dict | None) -> DiagnosticoPerfilCliente:
    perfil_normalizado = normalizar_perfil_cliente(perfil)
    if not perfil or not perfil_normalizado.get("aceita_personalizacao"):
        return DiagnosticoPerfilCliente(
            nivel="Inicial",
            mensagem="Complete seu perfil para receber uma experiência mais alinhada ao seu momento.",
            proxima_acao="Responder às perguntas principais do perfil.",
        )

    if perfil_normalizado["nivel_organizacao"] in NIVEIS_ORGANIZACAO[:2]:
        return DiagnosticoPerfilCliente(
            nivel="Em organização",
            mensagem="O foco ideal agora é ganhar clareza, rotina e consistência.",
            proxima_acao="Conectar lançamentos, revisar categorias e escolher uma meta simples.",
        )

    return DiagnosticoPerfilCliente(
        nivel="Pronto para personalização",
        mensagem="Já existe contexto suficiente para orientar recomendações mais específicas.",
        proxima_acao="Usar seus objetivos e dores para priorizar insights, metas e alertas.",
    )


def _validar_opcao(valor: str, opcoes: tuple[str, ...]) -> str:
    if valor not in opcoes:
        raise ValueError("Opção inválida para o perfil do cliente.")
    return valor
