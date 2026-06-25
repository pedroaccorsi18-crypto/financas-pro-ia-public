-- Cria armazenamento do Perfil Financeiro 360 com isolamento por auth.uid().
-- Tabela nova, sem alteracao de dados legados.

begin;

create table if not exists public.perfis_financeiros_360 (
    user_id uuid primary key references auth.users(id) on delete cascade,
    idade integer not null default 0 check (idade between 0 and 120),
    dependentes integer not null default 0 check (dependentes between 0 and 20),
    renda_mensal numeric(14, 2) not null default 0 check (renda_mensal >= 0),
    reserva_emergencia numeric(14, 2) not null default 0 check (reserva_emergencia >= 0),
    patrimonio_investido numeric(14, 2) not null default 0 check (patrimonio_investido >= 0),
    dividas numeric(14, 2) not null default 0 check (dividas >= 0),
    idade_aposentadoria integer not null default 0 check (idade_aposentadoria between 0 and 120),
    renda_aposentadoria_desejada numeric(14, 2) not null default 0 check (renda_aposentadoria_desejada >= 0),
    patrimonio_sucessorio numeric(14, 2) not null default 0 check (patrimonio_sucessorio >= 0),
    objetivo_principal text not null default 'Organizar vida financeira',
    perfil_risco text not null default 'Moderado' check (perfil_risco in ('Conservador', 'Moderado', 'Arrojado')),
    horizonte text not null default '3 a 5 anos',
    possui_seguro boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.perfis_financeiros_360 enable row level security;

drop policy if exists perfis_financeiros_360_select_proprio
    on public.perfis_financeiros_360;
drop policy if exists perfis_financeiros_360_insert_proprio
    on public.perfis_financeiros_360;
drop policy if exists perfis_financeiros_360_update_proprio
    on public.perfis_financeiros_360;
drop policy if exists perfis_financeiros_360_delete_proprio
    on public.perfis_financeiros_360;

create policy perfis_financeiros_360_select_proprio
    on public.perfis_financeiros_360
    for select
    to authenticated
    using (auth.uid() = user_id);

create policy perfis_financeiros_360_insert_proprio
    on public.perfis_financeiros_360
    for insert
    to authenticated
    with check (auth.uid() = user_id);

create policy perfis_financeiros_360_update_proprio
    on public.perfis_financeiros_360
    for update
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy perfis_financeiros_360_delete_proprio
    on public.perfis_financeiros_360
    for delete
    to authenticated
    using (auth.uid() = user_id);

commit;
