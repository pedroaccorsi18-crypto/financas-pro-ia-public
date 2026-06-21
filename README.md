# Financas Pro IA

Aplicacao financeira multiusuario que combina Streamlit, Supabase e IA generativa para transformar lancamentos manuais e PDFs financeiros em uma experiencia de acompanhamento, auditoria e analise preditiva.

O projeto foi desenhado como um SaaS financeiro em beta: cada usuario autentica com Supabase Auth, os dados sao isolados por `user_id` e RLS, e lotes extraidos por IA passam por uma etapa humana de homologacao antes de serem persistidos.

## Visao do Produto

Financas Pro IA resolve um problema comum em financas pessoais: dados financeiros chegam fragmentados em faturas, extratos, comprovantes e lancamentos manuais. A aplicacao centraliza esse fluxo em um painel unico, com importacao assistida por IA, validacao humana, metas por categoria e relatorios preditivos baseados em dados agregados.

O foco nao e apenas visualizar gastos, mas criar um fluxo confiavel de ingestao, revisao, persistencia e analise em um ambiente multi-tenant.

## Funcionalidades

- Autenticacao com cadastro, login, revalidacao de sessao e logout via Supabase Auth.
- Persistencia multiusuario com `user_id`, foreign keys para `auth.users` e policies RLS.
- Lancamentos manuais de receitas e despesas.
- Importacao de PDFs com consentimento explicito para processamento externo.
- Extracao estruturada com Gemini usando schema JSON controlado.
- Area de homologacao para revisar e ajustar classificacoes antes da gravacao.
- Substituicao transacional de lotes importados via RPC no Postgres.
- Dashboard mensal com resumo financeiro, agrupamento por categoria e graficos Plotly.
- Gestao de metas por categoria e mes.
- Central de auditoria para rastrear linhas por categoria, origem e instituicao.
- Oraculo IA com analise preditiva usando apenas totais agregados por mes e categoria.
- Feedback de respostas da IA com anonimizacao parcial antes da persistencia.
- Bot Fiscal opcional via SMTP para alertar divergencias entre valores calculados e declarados.
- Suite de testes unitarios, contratos SQL e integracao RLS opt-in.

## Screenshots

Adicione screenshots reais em `docs/screenshots/` antes de divulgar o projeto em portfolio, LinkedIn ou entrevistas. Sugestao de capturas:

| Tela | Objetivo |
| --- | --- |
| `docs/screenshots/login.png` | Mostrar autenticaçao e entrada do produto. |
| `docs/screenshots/dashboard.png` | Mostrar resumo financeiro, graficos e metas. |
| `docs/screenshots/importacao-ia.png` | Mostrar upload, consentimento e homologacao do PDF. |
| `docs/screenshots/oraculo-ia.png` | Mostrar relatorio preditivo e feedback da IA. |

Exemplo de uso no README apos adicionar as imagens:

```md
![Dashboard financeiro](docs/screenshots/dashboard.png)
```

## Arquitetura

```mermaid
flowchart LR
    U["Usuario"] --> UI["Streamlit / app.py"]
    UI --> AUTH["auth.py / Supabase Auth"]
    UI --> CORE["finance_core.py"]
    UI --> AI["Google Gemini"]
    UI --> SMTP["SMTP opcional"]
    AUTH --> DB["Supabase Postgres"]
    UI --> DB
    DB --> RLS["RLS por auth.uid()"]
    DB --> RPC["RPC substituir_lote_importado"]
```

### Componentes Principais

| Area | Arquivos | Responsabilidade |
| --- | --- | --- |
| Interface e orquestracao | `app.py` | Fluxos Streamlit, upload, dashboard, IA, metas e feedback. |
| Autenticacao | `auth.py` | Cliente Supabase por sessao, validacao de chave publica/anon, login e revalidacao. |
| Dominio financeiro | `finance_core.py` | Calculos, validacoes, comparacao de lotes e resumo agregado para IA. |
| Utilitarios | `utils/` | Privacidade, formatacao, Gemini, erros e Bot Fiscal SMTP. |
| Banco | `supabase/migrations/` | RPC transacional e endurecimento de `user_id`. |
| Qualidade | `tests/` | Testes unitarios, contratos SQL e integracao RLS opt-in. |

## Decisoes Tecnicas Relevantes

- **Isolamento multi-tenant:** a aplicacao filtra por `user_id`, mas a barreira real fica no Supabase com RLS baseada em `auth.uid()`.
- **Cliente Supabase por sessao:** evita compartilhar estado autenticado entre usuarios no processo Streamlit.
- **Bloqueio de chaves privilegiadas:** a aplicacao rejeita `sb_secret_` e JWTs com papel diferente de `anon`.
- **RPC transacional:** a importacao por IA nao grava item a item sem controle; o lote e validado e substituido de forma atomica.
- **Validacao antes de mutacao:** a RPC valida parametros, payload vazio, tipos e consistencia do lote antes de qualquer `DELETE` ou `INSERT`.
- **Privacidade no Oraculo IA:** relatorios preditivos usam dados agregados, sem descricoes individuais de transacoes.
- **Homologacao humana:** a IA sugere a extracao, mas o usuario revisa antes de persistir.

## Stack

- Python 3.11+
- Streamlit
- Supabase Auth
- Supabase Postgres
- Row Level Security
- PL/pgSQL
- Google Gemini
- Pandas
- Plotly
- unittest

## Desafios Tecnicos

### Segurança em ambiente multiusuario

O principal desafio foi impedir que a identidade do usuario fosse inferida apenas pelo cliente. A solucao combina Supabase Auth, `auth.uid()`, `user_id` obrigatorio nas tabelas operacionais e testes de RLS para bloquear leitura, escrita, update, delete e RPC com identidade forjada.

### Importacao por IA sem perda de controle

Extrair dados de PDFs financeiros exige lidar com classificacoes incertas, totais declarados e formatos variados. O fluxo usa Gemini para estruturar dados, mas coloca uma area de homologacao entre a IA e o banco.

### Persistencia idempotente de lotes

Reimportar a mesma fatura nao deve duplicar transacoes. A RPC `substituir_lote_importado` substitui somente o lote do usuario autenticado, com validacoes antes da exclusao.

### Privacidade em recursos de IA

O Oraculo IA evita enviar descricoes individuais, usando um historico agregado por mes e categoria. Feedbacks passam por anonimização parcial antes de serem persistidos.

## Estrutura

```text
app.py                  Interface e orquestracao Streamlit
auth.py                 Autenticacao Supabase e cliente por sessao
finance_core.py         Regras financeiras puras
utils/                  Utilitarios de privacidade, formatacao, IA e SMTP
supabase/migrations/    Migracoes operacionais do banco
tests/                  Testes unitarios, contratos e integracao opt-in
```

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

Copie `.streamlit/secrets.example.toml` para `.streamlit/secrets.toml` e preencha com valores reais somente no ambiente local ou no provedor de deploy.

Tambem ha `.env.example` para plataformas que usam variaveis de ambiente.

4. Aplique as migracoes no Supabase.

Revise os arquivos em `supabase/migrations/` e aplique em ambiente controlado.

5. Rode a aplicacao.

```powershell
streamlit run app.py
```

## Variaveis de Configuracao

Obrigatorias:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GEMINI_API_KEY`

Opcionais:

- `ADMIN_EMAILS`
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_EMAIL_REMETENTE`
- `SMTP_SENHA_REMETENTE`
- `EMAIL_DESTINATARIO_ALERTAS`

## Testes

```powershell
python -m unittest discover -s tests -v
```

A suite real de integracao RLS e opt-in e exige um projeto Supabase nao produtivo com dois usuarios de teste:

```powershell
python -m unittest tests.integration.test_supabase_rls -v
```

Veja `tests/integration/README.md` antes de executar.

## Segurança

- Nunca versione `.env`, `.streamlit/secrets.toml`, dumps, backups, uploads, PDFs, planilhas, logs ou credenciais reais.
- A aplicacao deve usar somente chave Supabase publica/publishable ou anon.
- Chaves `service_role`, `sb_secret_`, tokens privados e senhas devem existir apenas em ambientes seguros.
- Antes de publicar forks ou releases, rode secret scanning e revise o historico Git.

## Roadmap

- Adicionar fluxo de recuperacao de senha.
- Mover autorizacao administrativa para claims ou tabela protegida por RLS.
- Extrair camada de repositorios Supabase para reduzir acoplamento em `app.py`.
- Criar testes end-to-end para os principais fluxos Streamlit.
- Adicionar observabilidade estruturada para erros de IA, SMTP e banco.
- Criar pipeline de CI com testes e secret scanning.
- Melhorar avaliacao automatica da qualidade das extracoes por IA.
- Adicionar screenshots reais e demonstracao em video.

## Status

Projeto em versao publicavel para portfolio tecnico. O foco atual e demonstrar arquitetura, seguranca multi-tenant, integracao com IA e boas praticas de publicacao sem credenciais reais.
