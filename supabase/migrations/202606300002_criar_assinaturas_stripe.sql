-- Cria a base de assinaturas automatizadas para Gratuito, Pro e Familia.
-- Webhooks Stripe devem atualizar estas tabelas usando credencial server-side.

begin;

create table if not exists public.assinaturas (
    owner_id uuid primary key references auth.users(id) on delete cascade,
    plano text not null default 'gratuito' check (plano in ('gratuito', 'pro', 'familia')),
    status text not null default 'ativo' check (status in ('ativo', 'trial', 'past_due', 'cancelado', 'incompleto')),
    provider text not null default 'manual' check (provider in ('manual', 'stripe')),
    stripe_customer_id text unique,
    stripe_subscription_id text unique,
    stripe_price_id text,
    limite_membros integer not null default 1 check (limite_membros between 1 and 4),
    current_period_end timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.eventos_pagamento (
    event_id text primary key,
    provider text not null default 'stripe' check (provider in ('stripe')),
    tipo text not null,
    payload jsonb not null,
    processed_at timestamptz not null default now()
);

alter table public.assinaturas enable row level security;
alter table public.eventos_pagamento enable row level security;

drop policy if exists assinaturas_select_propria
    on public.assinaturas;

create policy assinaturas_select_propria
    on public.assinaturas
    for select
    to authenticated
    using (owner_id = auth.uid());

create or replace function public.obter_ou_criar_assinatura_usuario()
returns public.assinaturas
language plpgsql
security definer
set search_path = public
as $$
declare
    v_auth_user_id uuid := auth.uid();
    v_assinatura public.assinaturas;
begin
    if v_auth_user_id is null then
        raise exception 'Usuario autenticado obrigatorio para obter assinatura';
    end if;

    insert into public.assinaturas (
        owner_id,
        plano,
        status,
        provider,
        limite_membros
    )
    values (
        v_auth_user_id,
        'gratuito',
        'ativo',
        'manual',
        1
    )
    on conflict (owner_id) do nothing;

    select *
      into v_assinatura
      from public.assinaturas
     where owner_id = v_auth_user_id;

    return v_assinatura;
end;
$$;

create or replace function public.sincronizar_assinatura_stripe(
    p_owner_id uuid,
    p_plano text,
    p_status text,
    p_stripe_customer_id text,
    p_stripe_subscription_id text,
    p_stripe_price_id text,
    p_limite_membros integer,
    p_current_period_end timestamptz
)
returns public.assinaturas
language plpgsql
security definer
set search_path = public
as $$
declare
    v_assinatura public.assinaturas;
begin
    if p_owner_id is null then
        raise exception 'owner_id obrigatorio para sincronizar assinatura';
    end if;

    if p_plano not in ('gratuito', 'pro', 'familia') then
        raise exception 'Plano de assinatura invalido';
    end if;

    if p_status not in ('ativo', 'trial', 'past_due', 'cancelado', 'incompleto') then
        raise exception 'Status de assinatura invalido';
    end if;

    if p_limite_membros < 1 or p_limite_membros > 4 then
        raise exception 'Limite de membros invalido';
    end if;

    insert into public.assinaturas (
        owner_id,
        plano,
        status,
        provider,
        stripe_customer_id,
        stripe_subscription_id,
        stripe_price_id,
        limite_membros,
        current_period_end,
        updated_at
    )
    values (
        p_owner_id,
        p_plano,
        p_status,
        'stripe',
        p_stripe_customer_id,
        p_stripe_subscription_id,
        p_stripe_price_id,
        p_limite_membros,
        p_current_period_end,
        now()
    )
    on conflict (owner_id) do update set
        plano = excluded.plano,
        status = excluded.status,
        provider = excluded.provider,
        stripe_customer_id = excluded.stripe_customer_id,
        stripe_subscription_id = excluded.stripe_subscription_id,
        stripe_price_id = excluded.stripe_price_id,
        limite_membros = excluded.limite_membros,
        current_period_end = excluded.current_period_end,
        updated_at = now()
    returning * into v_assinatura;

    return v_assinatura;
end;
$$;

create or replace function public.registrar_evento_pagamento_stripe(
    p_event_id text,
    p_tipo text,
    p_payload jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    if p_event_id is null or char_length(trim(p_event_id)) = 0 then
        raise exception 'event_id obrigatorio';
    end if;

    insert into public.eventos_pagamento (
        event_id,
        provider,
        tipo,
        payload
    )
    values (
        p_event_id,
        'stripe',
        p_tipo,
        p_payload
    )
    on conflict (event_id) do nothing;
end;
$$;

revoke all on function public.sincronizar_assinatura_stripe(uuid, text, text, text, text, text, integer, timestamptz)
    from public;
revoke all on function public.registrar_evento_pagamento_stripe(text, text, jsonb)
    from public;

grant execute on function public.obter_ou_criar_assinatura_usuario() to authenticated;
grant execute on function public.sincronizar_assinatura_stripe(uuid, text, text, text, text, text, integer, timestamptz) to service_role;
grant execute on function public.registrar_evento_pagamento_stripe(text, text, jsonb) to service_role;

commit;
