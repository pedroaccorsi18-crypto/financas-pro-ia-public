from collections.abc import Iterable


def eh_usuario_admin(email_usuario: str | None, emails_admin: object) -> bool:
    email_normalizado = str(email_usuario or "").strip().lower()
    if not email_normalizado:
        return False

    if isinstance(emails_admin, str):
        candidatos: Iterable[object] = (emails_admin,)
    elif isinstance(emails_admin, Iterable):
        candidatos = emails_admin
    else:
        return False

    return email_normalizado in {
        str(email or "").strip().lower()
        for email in candidatos
        if str(email or "").strip()
    }
