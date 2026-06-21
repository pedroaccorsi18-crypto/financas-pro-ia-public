# Financas Pro IA

Aplicacao Streamlit para organizacao financeira pessoal com autenticacao via Supabase, importacao assistida por IA e dashboards de acompanhamento mensal.

## Stack

- Python
- Streamlit
- Supabase Auth, Postgres e RLS
- Google Gemini
- Pandas
- Plotly

## Funcionalidades

- Cadastro, login, revalidacao de sessao e logout com Supabase Auth.
- Lancamentos manuais de receitas e despesas.
- Dashboard mensal com categorias, metas e visualizacoes.
- Importacao de documentos financeiros com revisao humana antes da gravacao.
- Persistencia multiusuario usando `user_id` e policies RLS no Supabase.
- RPC transacional para substituir lotes importados.
- Feedback de respostas de IA com anonimizacao parcial.
- Bot fiscal opcional via SMTP para alertas de divergencia.

## Requisitos

- Python 3.11 ou superior.
- Projeto Supabase configurado com as migracoes em `supabase/migrations`.
- Chave publica/publishable ou anon do Supabase. Nunca use `service_role` na aplicacao.
- Chave Gemini, caso recursos de IA sejam usados.

## Instalacao

1. Crie e ative um ambiente virtual.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Instale as dependencias.

```powershell
pip install -r requirements.txt
```

3. Configure os secrets.

Copie `.streamlit/secrets.example.toml` para `.streamlit/secrets.toml` e preencha com valores reais somente no seu ambiente local ou no provedor de deploy.

Tambem ha um `.env.example` para plataformas que usam variaveis de ambiente.

4. Aplique as migracoes no Supabase, em ambiente controlado, revisando cada arquivo em `supabase/migrations`.

5. Rode a aplicacao.

```powershell
streamlit run app.py
```

## Testes

Os testes unitarios e de contrato podem ser executados com:

```powershell
python -m unittest discover -s tests -v
```

A suite de integracao RLS e opt-in e exige um projeto Supabase nao produtivo com dois usuarios de teste. Veja `tests/integration/README.md`.

## Seguranca

- Nunca versione `.env`, `.streamlit/secrets.toml`, dumps, backups, uploads, PDFs, planilhas, logs ou credenciais reais.
- A aplicacao deve usar somente chave Supabase publica/publishable ou anon.
- Chaves `service_role`, `sb_secret_`, tokens privados e senhas devem existir apenas em ambientes seguros.
- Antes de publicar forks ou releases, rode uma busca de segredos e revise o historico Git.

## Estrutura

```text
app.py                  Interface e orquestracao Streamlit
auth.py                 Autenticacao Supabase e cliente por sessao
finance_core.py         Regras financeiras puras
utils/                  Utilitarios de privacidade, formatacao, IA e SMTP
supabase/migrations/    Migracoes operacionais do banco
tests/                  Testes unitarios, contratos e integracao opt-in
```
