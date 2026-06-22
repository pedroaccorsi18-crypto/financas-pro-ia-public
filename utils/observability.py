import hashlib
import logging
from collections.abc import Mapping


SENSITIVE_KEYWORDS = (
    "api_key",
    "authorization",
    "chave",
    "key",
    "password",
    "secret",
    "senha",
    "token",
)


def fingerprint(valor: object) -> str:
    texto = str(valor or "").strip().lower()
    if not texto:
        return "anonimo"
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def contexto_seguro(**contexto) -> dict:
    seguro = {}
    for chave, valor in contexto.items():
        chave_texto = str(chave)
        if any(palavra in chave_texto.lower() for palavra in SENSITIVE_KEYWORDS):
            seguro[chave_texto] = "[redigido]"
        else:
            seguro[chave_texto] = valor
    return seguro


def registrar_evento(
    logger: logging.Logger,
    nivel: int,
    evento: str,
    *,
    contexto: Mapping | None = None,
    exc_info=False,
) -> None:
    extra = contexto_seguro(**dict(contexto or {}))
    if extra:
        logger.log(nivel, "%s | contexto=%s", evento, extra, exc_info=exc_info)
    else:
        logger.log(nivel, evento, exc_info=exc_info)
