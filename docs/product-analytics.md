# Product Analytics

Este documento define a primeira arquitetura de Product Analytics do Financas Pro IA. O objetivo e entender o comportamento de uso da plataforma sem coletar dados financeiros sensiveis, prompts brutos, descricoes de transacoes ou valores exatos.

Product Analytics aqui nao substitui observabilidade tecnica. Logs tecnicos explicam falhas de sistema; eventos de produto explicam comportamento, adocao, friccao e lacunas percebidas pelo usuario.

## Objetivos

- Medir quais fluxos sao usados com mais frequencia.
- Identificar pontos de abandono em fluxos importantes.
- Entender se os usuarios preferem lancamento manual, importacao por PDF ou recursos de IA.
- Medir confianca na classificacao da IA por meio de revisoes e correcoes.
- Apoiar decisoes de produto com dados agregados e auditaveis.

## Principios de privacidade

- Nao armazenar descricao de transacao.
- Nao armazenar valores financeiros exatos.
- Nao armazenar texto enviado ao Oraculo IA.
- Nao armazenar prompts, respostas completas da IA ou conteudo de PDF.
- Nao armazenar credenciais, chaves, tokens ou dados de configuracao.
- Preferir metadados, contagens, flags booleanas e classificacoes de alto nivel.
- Manter `user_id` apenas para isolamento, auditoria e analises agregadas por usuario autenticado.

## Eventos iniciais

| Evento | Quando registrar | Contexto permitido |
| --- | --- | --- |
| `manual_transaction_created` | Apos um lancamento manual ser salvo com sucesso. | `tipo`, `categoria`, `mes_referencia`. |
| `pdf_import_reviewed` | Apos o usuario homologar e salvar uma importacao de PDF. | `instituicao_financeira`, `tipo_documento`, `mes_referencia`, `qtd_itens`, `qtd_categorias_corrigidas`. |
| `oracle_question_sent` | Apos o usuario enviar uma pergunta ao Oraculo IA. | `mes_referencia`, `qtd_meses_contexto`, `tem_historico_disponivel`. |

Esses tres eventos cobrem o nucleo do produto: entrada manual de dados, ingestao assistida por IA e analise conversacional.

## Eventos futuros

- `goal_created`: meta financeira cadastrada.
- `goal_updated`: meta financeira alterada.
- `ai_classification_corrected`: categoria sugerida pela IA corrigida pelo usuario.
- `oracle_feedback_submitted`: feedback positivo ou negativo sobre resposta do Oraculo.
- `audit_filter_used`: uso da central de auditoria por categoria, origem ou instituicao.
- `admin_panel_opened`: acesso ao painel administrativo por usuario autorizado.

## Modelo de dados proposto

Tabela futura: `public.product_events`

```sql
create table public.product_events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    event_name text not null,
    event_context jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);
```

Campos:

| Campo | Responsabilidade |
| --- | --- |
| `id` | Identificador tecnico do evento. |
| `user_id` | Dono do evento, sempre associado ao usuario autenticado. |
| `event_name` | Nome canonico do evento de produto. |
| `event_context` | Metadados permitidos, sem dados financeiros sensiveis. |
| `created_at` | Momento do registro. |

## RLS proposta

Diretriz inicial:

- Usuarios autenticados podem inserir eventos apenas para o proprio `auth.uid()`.
- Usuarios autenticados podem ler apenas os proprios eventos, se essa leitura for necessaria.
- Painel administrativo deve usar uma politica separada ou uma camada segura de agregacao.
- Nenhuma policy deve permitir escrita com `user_id` diferente de `auth.uid()`.

Exemplo conceitual:

```sql
create policy "product_events_insert_own"
on public.product_events
for insert
to authenticated
with check (user_id = auth.uid());
```

## Camada de aplicacao proposta

Arquivos futuros:

```text
product_analytics.py                         Validacao e padronizacao de eventos
repositories/product_events_repository.py    Persistencia dos eventos no Supabase
```

Uso esperado no `app.py`:

```python
registrar_evento_produto(
    usuario_id=usuario_id,
    event_name="manual_transaction_created",
    event_context={
        "tipo": tipo_transacao,
        "categoria": categoria_manual,
        "mes_referencia": mes_ref_manual,
    },
)
```

O `app.py` deve apenas indicar o evento e o contexto permitido. Regras de validacao, allowlist de eventos e persistencia devem ficar fora do arquivo principal.

## Metricas iniciais

- Total de usuarios ativos por semana.
- Distribuicao entre lancamento manual e importacao por PDF.
- Taxa de uso do Oraculo IA.
- Quantidade media de itens por importacao.
- Percentual de importacoes com categorias corrigidas.
- Uso de metas financeiras por usuario ativo.

## Fora do escopo da primeira versao

- Pipeline de Big Data.
- Data warehouse externo.
- Modelos preditivos.
- Segmentacao automatica de usuarios.
- Coleta de eventos em tempo real fora do Supabase.
- Tracking de cliques de baixa relevancia.

## Sequencia recomendada

1. Criar migration da tabela `product_events`.
2. Criar repository dedicado para insercao de eventos.
3. Criar modulo de Product Analytics com allowlist de eventos e contexto permitido.
4. Instrumentar apenas `manual_transaction_created`.
5. Validar RLS e testes de contrato.
6. Instrumentar `pdf_import_reviewed`.
7. Instrumentar `oracle_question_sent`.
8. Criar primeira visao agregada no painel administrativo.
