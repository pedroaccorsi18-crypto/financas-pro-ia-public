# Frontend Next.js

Primeira camada premium do Finanças Pro IA em React/Next.js.

Esta pasta ainda não substitui o app Streamlit. Ela nasce como casca pública do produto:

- landing page;
- comunicação para consumidor final;
- planos;
- entrada para cadastro/login.

## Rodar localmente

```powershell
cd frontend
npm install
npm run dev
```

Depois acesse `http://localhost:3000`.

## Próximos passos

- Conectar login/cadastro ao Supabase Auth.
- Integrar os botões de planos ao Stripe Checkout.
- Migrar dashboards internos gradualmente, sem quebrar o app Streamlit.
