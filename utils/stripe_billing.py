"""Helpers para Stripe Checkout, Billing e webhooks."""

from datetime import datetime, timezone

from utils.subscriptions import limite_membros_do_plano, normalizar_plano

STRIPE_API_VERSION = "2026-02-25.clover"
PLANOS_PAGOS = {"pro", "familia"}
EVENTOS_ASSINATURA = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


def criar_checkout_assinatura(
    *,
    stripe_module,
    stripe_secret_key: str,
    price_id: str,
    usuario_id: str,
    email_usuario: str,
    plano: str,
    success_url: str,
    cancel_url: str,
):
    plano_normalizado = normalizar_plano(plano)
    if plano_normalizado not in PLANOS_PAGOS:
        raise ValueError("Checkout Stripe deve ser criado apenas para planos pagos.")
    if not stripe_secret_key:
        raise ValueError("STRIPE_SECRET_KEY nao configurada.")
    if not price_id:
        raise ValueError("Price ID do plano nao configurado.")

    stripe_module.api_key = stripe_secret_key
    stripe_module.api_version = STRIPE_API_VERSION
    return stripe_module.checkout.Session.create(
        mode="subscription",
        customer_email=email_usuario,
        client_reference_id=usuario_id,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"user_id": usuario_id, "plano": plano_normalizado},
        subscription_data={"metadata": {"user_id": usuario_id, "plano": plano_normalizado}},
    )


def construir_evento_webhook(*, stripe_module, payload, assinatura, webhook_secret):
    if not webhook_secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET nao configurado.")
    return stripe_module.Webhook.construct_event(payload, assinatura, webhook_secret)


def plano_por_price_id(price_id: str | None, secrets) -> str:
    if not price_id:
        return "gratuito"
    mapa = {
        str(secrets.get("STRIPE_PRICE_PRO", "")).strip(): "pro",
        str(secrets.get("STRIPE_PRICE_FAMILIA", "")).strip(): "familia",
    }
    return mapa.get(str(price_id).strip(), "gratuito")


def price_id_por_plano(plano: str, secrets) -> str:
    plano_normalizado = normalizar_plano(plano)
    if plano_normalizado == "pro":
        return str(secrets.get("STRIPE_PRICE_PRO", "")).strip()
    if plano_normalizado == "familia":
        return str(secrets.get("STRIPE_PRICE_FAMILIA", "")).strip()
    return ""


def extrair_assinatura_de_evento(evento, secrets) -> dict | None:
    tipo = _obter(evento, "type")
    if tipo not in EVENTOS_ASSINATURA:
        return None

    objeto = _obter(_obter(evento, "data", {}), "object", {})
    if tipo == "checkout.session.completed":
        return _assinatura_de_checkout(objeto, secrets)
    return _assinatura_de_subscription(objeto, secrets, tipo)


def _assinatura_de_checkout(sessao, secrets):
    metadata = _obter(sessao, "metadata", {}) or {}
    plano = normalizar_plano(_obter(metadata, "plano") or plano_por_price_id(_price_id_da_sessao(sessao), secrets))
    usuario_id = _obter(metadata, "user_id") or _obter(sessao, "client_reference_id")
    if not usuario_id:
        return None
    return {
        "owner_id": usuario_id,
        "plano": plano,
        "status": "ativo",
        "provider": "stripe",
        "stripe_customer_id": _obter(sessao, "customer"),
        "stripe_subscription_id": _obter(sessao, "subscription"),
        "stripe_price_id": _price_id_da_sessao(sessao),
        "current_period_end": None,
        "limite_membros": limite_membros_do_plano(plano),
    }


def _assinatura_de_subscription(subscription, secrets, tipo_evento):
    metadata = _obter(subscription, "metadata", {}) or {}
    price_id = _price_id_da_subscription(subscription)
    plano = normalizar_plano(_obter(metadata, "plano") or plano_por_price_id(price_id, secrets))
    usuario_id = _obter(metadata, "user_id")
    if not usuario_id:
        return None

    status = "cancelado" if tipo_evento == "customer.subscription.deleted" else _normalizar_status_stripe(
        _obter(subscription, "status")
    )
    return {
        "owner_id": usuario_id,
        "plano": plano,
        "status": status,
        "provider": "stripe",
        "stripe_customer_id": _obter(subscription, "customer"),
        "stripe_subscription_id": _obter(subscription, "id"),
        "stripe_price_id": price_id,
        "current_period_end": _timestamp_para_iso(_obter(subscription, "current_period_end")),
        "limite_membros": limite_membros_do_plano(plano),
    }


def _normalizar_status_stripe(status):
    mapa = {
        "active": "ativo",
        "trialing": "trial",
        "past_due": "past_due",
        "canceled": "cancelado",
        "incomplete": "incompleto",
        "incomplete_expired": "cancelado",
        "unpaid": "past_due",
        "paused": "past_due",
    }
    return mapa.get(str(status or "").strip().lower(), "incompleto")


def _price_id_da_sessao(sessao):
    line_items = _obter(sessao, "line_items", {}) or {}
    data = _obter(line_items, "data", []) or []
    if not data:
        return None
    price = _obter(data[0], "price", {}) or {}
    return _obter(price, "id")


def _price_id_da_subscription(subscription):
    items = _obter(subscription, "items", {}) or {}
    data = _obter(items, "data", []) or []
    if not data:
        return None
    price = _obter(data[0], "price", {}) or {}
    return _obter(price, "id")


def _timestamp_para_iso(valor):
    if not valor:
        return None
    return datetime.fromtimestamp(int(valor), tz=timezone.utc).isoformat()


def _obter(objeto, chave, padrao=None):
    if isinstance(objeto, dict):
        return objeto.get(chave, padrao)
    return getattr(objeto, chave, padrao)
