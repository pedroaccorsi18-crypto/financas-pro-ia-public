# Relatorio de Publicacao Segura

Pasta preparada:

```text
financas-pro-ia-github-public
```

## Resultado

A pasta limpa esta preparada e ja foi usada como base do repositorio publico no GitHub.

Ela nao contem:

- `.env` real;
- `.streamlit/secrets.toml` real;
- backups;
- dumps de banco;
- arquivos de upload;
- logs;
- `app_backup.py`;
- `estrutura.txt`;
- documentos internos de producao/homologacao;
- e-mails pessoais detectados;
- caminhos locais pessoais detectados.

## Arquivos mantidos

- Codigo da aplicacao: `app.py`, `auth.py`, `finance_core.py`.
- Utilitarios em `utils/`.
- Migracoes operacionais em `supabase/migrations/`.
- Testes unitarios, contratos e suite RLS opt-in em `tests/`.
- Workflow de CI com testes locais e secret scanning via Gitleaks.
- `README.md` revisado para uso publico.
- `.env.example` e `.streamlit/secrets.example.toml` com placeholders ficticios.
- `.gitignore` endurecido para bloquear segredos, backups, dumps, logs, uploads, caches e arquivos locais.
- `requirements.txt` com versoes fixadas.

## Varredura de segredos

Termos auditados:

```text
API_KEY
SECRET
TOKEN
PASSWORD
SUPABASE
GEMINI
JWT
PRIVATE_KEY
pedro
gmail
hotmail
```

Achados:

- Apenas nomes de variaveis, placeholders de exemplo, nomes de bibliotecas, mensagens de seguranca e testes.
- Nenhum valor real de chave Supabase, Gemini, JWT, e-mail pessoal ou dominio real de projeto Supabase foi detectado.

Tambem foram procurados padroes de segredo comuns:

```text
sb_secret_
sb_publishable_...
JWT completo iniciado por eyJ...
AIza...
postgres://
postgresql://
PRIVATE KEY
github_pat_
ghp_
```

Achados:

- Nenhum segredo real detectado.
- Ocorrencias de `sb_secret_` aparecem apenas como padrao bloqueado pelo codigo/testes.

## Testes

Comando executado nesta revisao:

```powershell
python -m unittest discover -s tests -v
```

Resultado local atual:

```text
Ran 110 tests
OK (skipped=1)
```

O teste pulado e a suite opt-in de integracao RLS, que exige um projeto Supabase
de teste com variaveis reais configuradas.

O workflow do GitHub Actions tambem executa Gitleaks, checagem de sintaxe e a
suite local de testes em pushes e pull requests.

## Recomendacao antes de publicar

1. Confirmar que o GitHub Actions esta verde apos cada push relevante.
2. Rodar `.\scripts\check.ps1` antes de preparar novas publicacoes.
3. Manter secrets reais somente no ambiente de deploy ou localmente, nunca no Git.
4. Rotacionar credenciais reais antigas caso alguma tenha existido no workspace original.
