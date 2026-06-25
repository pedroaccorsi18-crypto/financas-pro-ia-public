# Decisao tecnica: autorizacao administrativa

## Contexto

Hoje o painel administrativo usa `ADMIN_EMAILS` nos secrets do Streamlit e a
funcao `eh_usuario_admin` em `utils/authorization.py`.

Esse desenho e simples, testado e suficiente para o projeto publico de
portfolio, mas ainda e uma limitacao assumida: a autorizacao fica configurada
na aplicacao, nao em uma regra centralizada no Supabase.

## Decisao atual

Manter `ADMIN_EMAILS` no curto prazo.

Motivos:

- evita migration e mudanca de RLS sem necessidade imediata;
- preserva o comportamento atual do app;
- segue adequado para um ambiente demonstrativo ou portfolio;
- ja existe cobertura de testes para normalizacao e rejeicao de configuracao invalida.

## Caminhos avaliados

| Opcao | Vantagem | Custo/Risco | Status |
| --- | --- | --- | --- |
| Manter `ADMIN_EMAILS` | Simples, reversivel e sem dependencia nova. | Exige alterar secrets para trocar admins. | Escolha atual. |
| Claims no Supabase Auth | Autorizacao acompanha a identidade autenticada. | Exige processo seguro para gerir claims. | Melhor opcao futura para producao. |
| Tabela `admin_users` protegida por RLS | Auditavel e alteravel via banco. | Exige migration, policies e tela/processo de gestao. | Alternativa futura. |
| Service role no app | Poder administrativo amplo. | Inseguro para Streamlit publico. | Rejeitado. |

## Recomendacao futura

Se o projeto evoluir para uso real, mover a autorizacao administrativa para
claims do Supabase Auth ou para uma tabela protegida por RLS. A escolha entre
as duas depende de como os administradores serao geridos:

- poucos admins estaveis: claims no Auth;
- admins alterados por operacao interna: tabela protegida por RLS.

## Criterios antes de migrar

- Ter um ambiente Supabase de teste.
- Escrever migration e testes de contrato.
- Garantir que usuarios comuns nao consigam ler dados agregados administrativos.
- Preservar a checagem atual como fallback temporario durante a migracao.

## Fora de escopo agora

- Criar migration de admins.
- Alterar RLS.
- Criar painel para gerir administradores.
- Usar service role dentro do app Streamlit.
