"""Regras de base para o futuro Plano Familia."""

LIMITE_MEMBROS_FAMILIA = 4
STATUS_MEMBRO_FAMILIA = ("pendente", "ativo", "removido")
PAPEIS_MEMBRO_FAMILIA = ("dono", "membro")


def normalizar_email_convite(email: str) -> str:
    return str(email or "").strip().lower()


def validar_nome_familia(nome: str) -> str:
    nome_limpo = str(nome or "").strip()
    if not nome_limpo:
        raise ValueError("Informe um nome para a familia.")
    if len(nome_limpo) > 80:
        raise ValueError("O nome da familia deve ter no maximo 80 caracteres.")
    return nome_limpo


def validar_email_convite(email: str) -> str:
    email_limpo = normalizar_email_convite(email)
    if not email_limpo or "@" not in email_limpo:
        raise ValueError("Informe um e-mail valido para o convite.")
    if len(email_limpo) > 254:
        raise ValueError("O e-mail do convite deve ter no maximo 254 caracteres.")
    return email_limpo


def validar_limite_membros(total_membros: int, limite: int = LIMITE_MEMBROS_FAMILIA) -> None:
    if total_membros >= limite:
        raise ValueError(f"O Plano Familia permite ate {limite} pessoas.")


def pode_adicionar_membro(total_membros: int, limite: int = LIMITE_MEMBROS_FAMILIA) -> bool:
    return total_membros < limite
