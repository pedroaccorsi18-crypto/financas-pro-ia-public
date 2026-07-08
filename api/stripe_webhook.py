"""Endpoint ASGI minimalista para webhooks do Stripe Billing."""

import json
import logging
import os
from http import HTTPStatus

from supabase import create_client

from utils.stripe_webhook import processar_webhook_stripe


logger = logging.getLogger(__name__)

CHAVES_OBRIGATORIAS = (
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRICE_PRO",
    "STRIPE_PRICE_FAMILIA",
)


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    caminho = scope.get("path", "")
    metodo = scope.get("method", "GET").upper()
    if caminho == "/health":
        await _enviar_json(send, HTTPStatus.OK, {"status": "ok"})
        return

    if caminho != "/stripe/webhook":
        await _enviar_json(send, HTTPStatus.NOT_FOUND, {"erro": "not_found"})
        return

    if metodo != "POST":
        await _enviar_json(send, HTTPStatus.METHOD_NOT_ALLOWED, {"erro": "method_not_allowed"})
        return

    payload = await _ler_body(receive)
    assinatura_header = _obter_header(scope, "stripe-signature")
    status, resposta = processar_requisicao_webhook(
        payload=payload,
        assinatura_header=assinatura_header,
    )
    await _enviar_json(send, status, resposta)


def processar_requisicao_webhook(
    *,
    payload,
    assinatura_header,
    env=None,
    criar_cliente=create_client,
    processar_webhook=processar_webhook_stripe,
):
    try:
        secrets = _carregar_secrets(env or os.environ)
        supabase = criar_cliente(
            secrets["SUPABASE_URL"],
            secrets["SUPABASE_SERVICE_ROLE_KEY"],
        )
        resultado = processar_webhook(
            payload=payload,
            assinatura_header=assinatura_header,
            secrets=secrets,
            registrar_evento=_registrar_evento(supabase),
            sincronizar_assinatura=_sincronizar_assinatura(supabase),
        )
        return HTTPStatus.OK, {
            "ok": True,
            "processado": bool(resultado.get("processado")),
            "tipo": resultado.get("tipo"),
        }
    except ValueError as erro:
        logger.warning(
            "Webhook Stripe recusado",
            extra={"tipo_erro": type(erro).__name__},
        )
        return HTTPStatus.BAD_REQUEST, {"ok": False, "erro": "webhook_invalido"}
    except Exception as erro:
        logger.error(
            "Falha ao processar webhook Stripe",
            extra={"tipo_erro": type(erro).__name__},
            exc_info=True,
        )
        return HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "erro": "erro_interno"}


def _carregar_secrets(env):
    secrets = {chave: str(env.get(chave, "")).strip() for chave in CHAVES_OBRIGATORIAS}
    ausentes = [chave for chave, valor in secrets.items() if not valor]
    if ausentes:
        raise ValueError("Secrets obrigatorios ausentes para webhook Stripe.")
    return secrets


def _registrar_evento(supabase):
    def registrar(evento):
        supabase.rpc(
            "registrar_evento_pagamento_stripe",
            {
                "p_event_id": evento["id"],
                "p_tipo": evento["type"],
                "p_payload": evento,
            },
        ).execute()

    return registrar


def _sincronizar_assinatura(supabase):
    def sincronizar(assinatura):
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

    return sincronizar


async def _ler_body(receive):
    partes = []
    more_body = True
    while more_body:
        mensagem = await receive()
        partes.append(mensagem.get("body", b""))
        more_body = mensagem.get("more_body", False)
    return b"".join(partes)


def _obter_header(scope, nome):
    nome_bytes = nome.lower().encode("latin1")
    for chave, valor in scope.get("headers", []):
        if chave.lower() == nome_bytes:
            return valor.decode("latin1")
    return ""


async def _enviar_json(send, status, payload):
    corpo = json.dumps(payload).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": int(status),
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(corpo)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": corpo})
