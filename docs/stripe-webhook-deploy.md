# Publicar o webhook Stripe em HTTPS

Este guia coloca o endpoint `POST /stripe/webhook` em uma URL publica com HTTPS para que o Stripe consiga confirmar pagamentos e assinaturas automaticamente.

## 1. Criar o servico web

Use um provedor que rode Python com HTTPS. O arquivo `render.yaml` ja deixa o deploy pronto para Render.

Configuracao esperada:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn api.stripe_webhook:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

## 2. Configurar variaveis de ambiente

Cadastre estas variaveis no provedor de deploy, sem colocar valores reais no Git:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_PRO`
- `STRIPE_PRICE_FAMILIA`

No primeiro deploy, `STRIPE_WEBHOOK_SECRET` ainda pode ficar temporariamente vazio. Depois de cadastrar a URL no Stripe, copie o segredo do endpoint e preencha essa variavel.

## 3. Validar a URL publica

Depois do deploy, abra:

```text
https://sua-url-publica/health
```

A resposta esperada e:

```json
{"status":"ok"}
```

## 4. Cadastrar no Stripe

No Stripe Dashboard, em modo de teste:

1. Abra Workbench ou Developers.
2. Entre em Webhooks.
3. Crie um novo endpoint.
4. Use a URL:

```text
https://sua-url-publica/stripe/webhook
```

5. Selecione eventos de assinatura e checkout, incluindo:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

6. Salve o endpoint.
7. Copie o signing secret do endpoint, no formato `whsec_...`.
8. Cole esse valor em `STRIPE_WEBHOOK_SECRET` no provedor de deploy.
9. Rode um novo deploy.

## 5. Confirmar no app

Quando o webhook estiver publicado e o segredo estiver configurado, o Health Check deve deixar de mostrar a pendencia de Stripe.
