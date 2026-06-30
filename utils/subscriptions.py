"""Regras de assinatura e liberacao de recursos."""

PLANOS_ASSINATURA = ("gratuito", "pro", "familia")
STATUS_ASSINATURA = ("ativo", "trial", "past_due", "cancelado", "incompleto")

LIMITE_MEMBROS_POR_PLANO = {
    "gratuito": 1,
    "pro": 1,
    "familia": 4,
}

ROTULOS_PLANOS = {
    "gratuito": "Gratuito",
    "pro": "Pro",
    "familia": "Família",
}


def normalizar_plano(plano: str | None) -> str:
    plano_normalizado = str(plano or "gratuito").strip().lower()
    if plano_normalizado not in PLANOS_ASSINATURA:
        return "gratuito"
    return plano_normalizado


def limite_membros_do_plano(plano: str | None) -> int:
    return LIMITE_MEMBROS_POR_PLANO[normalizar_plano(plano)]


def rotulo_plano(plano: str | None) -> str:
    return ROTULOS_PLANOS[normalizar_plano(plano)]


def assinatura_ativa(assinatura: dict | None) -> bool:
    if not assinatura:
        return False
    return assinatura.get("status") in {"ativo", "trial"}


def pode_usar_plano_pro(assinatura: dict | None) -> bool:
    if not assinatura_ativa(assinatura):
        return False
    return normalizar_plano(assinatura.get("plano")) in {"pro", "familia"}


def pode_usar_plano_familia(assinatura: dict | None) -> bool:
    if not assinatura_ativa(assinatura):
        return False
    return normalizar_plano(assinatura.get("plano")) == "familia"
