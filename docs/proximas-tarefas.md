# Proximas tarefas

Fila curta para manter o projeto evoluindo com pouco atrito e boa verificacao.

## Concluido

| Prioridade | Tarefa | Por que importa | Pronto quando |
| --- | --- | --- | --- |
| P0 | Validar o novo CI no GitHub | Garante que testes e secret scanning rodem fora da maquina local. | O primeiro push/PR executar `Gitleaks` e `Tests` com sucesso. |
| P1 | Criar um smoke test leve do fluxo Streamlit | Protege os caminhos principais da interface, que ainda ficam concentrados em `app.py`. | Um teste automatizado cobre abertura do app e um fluxo basico sem depender de Supabase real. |
| P1 | Revisar o fluxo de publicacao | Reduz risco de publicar arquivo local, segredo ou configuracao privada por acidente. | `PUBLICATION_AUDIT_REPORT.md`, `.gitignore`, exemplos de secrets e workflow estao coerentes. |
| P2 | Definir caminho para autorizacao administrativa | `ADMIN_EMAILS` funciona para portfolio, mas e uma limitacao tecnica assumida. | Decisao registrada em [`docs/autorizacao-admin.md`](autorizacao-admin.md). |
| P2 | Montar casos anonimizados para avaliar extracao por IA | Ajuda a medir qualidade da extracao antes de mexer em prompts ou schema. | Casos e validacao registrados em [`docs/ia-extracao-casos.md`](ia-extracao-casos.md). |

## Prioridade agora

| Prioridade | Tarefa | Por que importa | Pronto quando |
| --- | --- | --- | --- |
| P3 | Preparar demo curta do fluxo completo | Melhora o valor de portfolio e facilita explicar o projeto em entrevista. | Roteiro e capturas cobrem login, importacao, homologacao, dashboard, metas e IA. |

## Regra de trabalho

- Uma tarefa por vez.
- Mudanca pequena, testavel e reversivel.
- Rodar `.\scripts\check.ps1` antes de considerar pronto.
- Nao ativar testes RLS reais sem ambiente Supabase de teste configurado.

## Proxima acao sugerida

Preparar o roteiro da demo curta do fluxo completo.
