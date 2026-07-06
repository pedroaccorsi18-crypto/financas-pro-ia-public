"""Processamento seguro de webhooks do Stripe Billing."""

import logging

from repositories.finance_repository import (
    registrar_evento_pagamento_stripe,
    sincronizar_assinatura_stripe,
)
from utils.stripe_billing import construir_evento_webhook, extrair_assinatura_de_evento


logger = logging.getLogger(__name__)


def processar_webhook_stripe(
    *,
    payload,
    assinatura_header,
    secrets,
    stripe_module=None,
    registrar_evento=registrar_evento_pagamento_stripe,
    sincronizar_assinatura=sincronizar_assinatura_stripe,
):
    if stripe_module is None:
        import stripe

        stripe_module = stripe

    evento = construir_evento_webhook(
        stripe_module=stripe_module,
        payload=payload,
        assinatura=assinatura_header,
        webhook_secret=str(secrets.get("STRIPE_WEBHOOK_SECRET", "")).strip(),
    )
    evento_dict = _evento_para_dict(evento)
    _validar_evento(evento_dict)

    registrar_evento(evento_dict)
    assinatura = extrair_assinatura_de_evento(evento_dict, secrets)
    if not assinatura:
        return {
            "processado": False,
            "tipo": evento_dict["type"],
            "motivo": "evento_sem_alteracao_de_assinatura",
        }

    assinatura_atualizada = sincronizar_assinatura(assinatura)
    logger.info(
        "Webhook Stripe processado",
        extra={
            "tipo_evento": evento_dict["type"],
            "plano": assinatura["plano"],
            "status": assinatura["status"],
        },
    )
    return {
        "processado": True,
        "tipo": evento_dict["type"],
        "assinatura": assinatura_atualizada or assinatura,
    }


def _evento_para_dict(evento):
    if hasattr(evento, "to_dict_recursive"):
        return evento.to_dict_recursive()
    if isinstance(evento, dict):
        return evento
    raise TypeError("Evento Stripe em formato inesperado.")


def _validar_evento(evento):
    if not isinstance(evento, dict):
        raise TypeError("Evento Stripe deve ser um dicionário.")
    if not str(evento.get("id") or "").strip():
        raise ValueError("Evento Stripe sem id.")
    if not str(evento.get("type") or "").strip():
        raise ValueError("Evento Stripe sem tipo.")
