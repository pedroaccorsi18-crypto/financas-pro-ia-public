-- Cria a base de perfil do cliente para personalizacao data driven.
-- Tabela nova, sem alteracao de dados legados.

begin;

create table if not exists public.perfis_cliente (
    user_id uuid primary key references auth.users(id) on delete cascade,
    momento_financeiro text not null default 'Organizando a casa' check (
        momento_financeiro in (
            'Organizando a casa',
            'Saindo de dívidas',
            'Criando reserva',
            'Investindo melhor',
            'Planejando família',
            'Preparando aposentadoria'
        )
    ),
    objetivo_principal text not null default 'Entender para onde o dinheiro está indo' check (
        objetivo_principal in (
            'Entender para onde o dinheiro está indo',
            'Reduzir gastos recorrentes',
            'Montar reserva de emergência',
            'Quitar dívidas',
            'Investir com mais consistência',
            'Organizar finanças da família'
        )
    ),
    maior_dor text not null default 'Falta de clareza sobre gastos' check (
        maior_dor in (
            'Falta de clareza sobre gastos',
            'Dificuldade para manter constância',
            'Gastos impulsivos',
            'Dívidas ou parcelas pesadas',
            'Falta de planejamento familiar',
            'Medo de investir errado'
        )
    ),
    nivel_organizacao text not null default 'Estou começando agora' check (
        nivel_organizacao in (
            'Estou começando agora',
            'Tenho algum controle, mas falho na constância',
            'Acompanho todo mês',
            'Tenho método e quero otimizar'
        )
    ),
    perfil_decisao text not null default 'Quero recomendações simples e diretas' check (
        perfil_decisao in (
            'Quero recomendações simples e diretas',
            'Quero entender o motivo antes de agir',
            'Quero comparar cenários'
        )
    ),
    preferencia_acompanhamento text not null default 'Mensal' check (
        preferencia_acompanhamento in ('Semanal', 'Quinzenal', 'Mensal')
    ),
    aceita_personalizacao boolean not null default true,
    feedback_preferencias jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.perfis_cliente enable row level security;

drop policy if exists perfis_cliente_select_proprio
    on public.perfis_cliente;
drop policy if exists perfis_cliente_insert_proprio
    on public.perfis_cliente;
drop policy if exists perfis_cliente_update_proprio
    on public.perfis_cliente;
drop policy if exists perfis_cliente_delete_proprio
    on public.perfis_cliente;

create policy perfis_cliente_select_proprio
    on public.perfis_cliente
    for select
    to authenticated
    using (auth.uid() = user_id);

create policy perfis_cliente_insert_proprio
    on public.perfis_cliente
    for insert
    to authenticated
    with check (auth.uid() = user_id);

create policy perfis_cliente_update_proprio
    on public.perfis_cliente
    for update
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy perfis_cliente_delete_proprio
    on public.perfis_cliente
    for delete
    to authenticated
    using (auth.uid() = user_id);

commit;
