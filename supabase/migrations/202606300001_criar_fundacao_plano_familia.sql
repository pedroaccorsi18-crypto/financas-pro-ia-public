-- Cria a fundacao do Plano Familia sem alterar o isolamento atual das transacoes.
-- O compartilhamento de dados financeiros deve ser implementado em migracao futura.

begin;

create table if not exists public.familias_financeiras (
    id uuid primary key default gen_random_uuid(),
    nome text not null check (char_length(trim(nome)) between 1 and 80),
    owner_id uuid not null references auth.users(id) on delete cascade,
    limite_membros integer not null default 4 check (limite_membros between 1 and 4),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.membros_familia_financeira (
    id uuid primary key default gen_random_uuid(),
    familia_id uuid not null references public.familias_financeiras(id) on delete cascade,
    user_id uuid references auth.users(id) on delete cascade,
    email_convite text not null check (email_convite = lower(trim(email_convite)) and char_length(email_convite) between 3 and 254),
    papel text not null default 'membro' check (papel in ('dono', 'membro')),
    status text not null default 'pendente' check (status in ('pendente', 'ativo', 'removido')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (familia_id, email_convite)
);

create unique index if not exists membros_familia_financeira_usuario_ativo_idx
    on public.membros_familia_financeira (familia_id, user_id)
    where user_id is not null and status in ('pendente', 'ativo');

alter table public.familias_financeiras enable row level security;
alter table public.membros_familia_financeira enable row level security;

create or replace function public.usuario_e_dono_familia_financeira(p_familia_id uuid)
returns boolean
language sql
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.familias_financeiras familia
        where familia.id = p_familia_id
          and familia.owner_id = auth.uid()
    );
$$;

create or replace function public.usuario_pode_ver_familia_financeira(p_familia_id uuid)
returns boolean
language sql
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.familias_financeiras familia
        where familia.id = p_familia_id
          and familia.owner_id = auth.uid()
    )
    or exists (
        select 1
        from public.membros_familia_financeira membro
        where membro.familia_id = p_familia_id
          and membro.user_id = auth.uid()
          and membro.status = 'ativo'
    );
$$;

drop policy if exists familias_financeiras_select_participante
    on public.familias_financeiras;
drop policy if exists familias_financeiras_insert_dono
    on public.familias_financeiras;
drop policy if exists familias_financeiras_update_dono
    on public.familias_financeiras;
drop policy if exists familias_financeiras_delete_dono
    on public.familias_financeiras;

create policy familias_financeiras_select_participante
    on public.familias_financeiras
    for select
    to authenticated
    using (public.usuario_pode_ver_familia_financeira(id));

create policy familias_financeiras_insert_dono
    on public.familias_financeiras
    for insert
    to authenticated
    with check (owner_id = auth.uid());

create policy familias_financeiras_update_dono
    on public.familias_financeiras
    for update
    to authenticated
    using (public.usuario_e_dono_familia_financeira(id))
    with check (owner_id = auth.uid());

create policy familias_financeiras_delete_dono
    on public.familias_financeiras
    for delete
    to authenticated
    using (public.usuario_e_dono_familia_financeira(id));

drop policy if exists membros_familia_select_participante
    on public.membros_familia_financeira;
drop policy if exists membros_familia_insert_dono
    on public.membros_familia_financeira;
drop policy if exists membros_familia_update_dono
    on public.membros_familia_financeira;
drop policy if exists membros_familia_delete_dono
    on public.membros_familia_financeira;

create policy membros_familia_select_participante
    on public.membros_familia_financeira
    for select
    to authenticated
    using (
        user_id = auth.uid()
        or public.usuario_e_dono_familia_financeira(familia_id)
    );

create policy membros_familia_insert_dono
    on public.membros_familia_financeira
    for insert
    to authenticated
    with check (public.usuario_e_dono_familia_financeira(familia_id));

create policy membros_familia_update_dono
    on public.membros_familia_financeira
    for update
    to authenticated
    using (public.usuario_e_dono_familia_financeira(familia_id))
    with check (public.usuario_e_dono_familia_financeira(familia_id));

create policy membros_familia_delete_dono
    on public.membros_familia_financeira
    for delete
    to authenticated
    using (public.usuario_e_dono_familia_financeira(familia_id));

create or replace function public.criar_familia_financeira(p_nome text)
returns public.familias_financeiras
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_auth_user_id uuid := auth.uid();
    v_email text;
    v_familia public.familias_financeiras;
begin
    if v_auth_user_id is null then
        raise exception 'Usuario autenticado obrigatorio para criar familia financeira';
    end if;

    v_email := lower(coalesce(nullif(auth.jwt() ->> 'email', ''), v_auth_user_id::text));

    if p_nome is null or char_length(trim(p_nome)) = 0 or char_length(trim(p_nome)) > 80 then
        raise exception 'Nome da familia financeira invalido';
    end if;

    insert into public.familias_financeiras (nome, owner_id)
    values (trim(p_nome), v_auth_user_id)
    returning * into v_familia;

    insert into public.membros_familia_financeira (
        familia_id,
        user_id,
        email_convite,
        papel,
        status
    )
    values (
        v_familia.id,
        v_auth_user_id,
        v_email,
        'dono',
        'ativo'
    );

    return v_familia;
end;
$$;

create or replace function public.convidar_membro_familia_financeira(
    p_familia_id uuid,
    p_email text
)
returns public.membros_familia_financeira
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_auth_user_id uuid := auth.uid();
    v_email text := lower(trim(coalesce(p_email, '')));
    v_limite integer;
    v_total integer;
    v_membro public.membros_familia_financeira;
begin
    if v_auth_user_id is null then
        raise exception 'Usuario autenticado obrigatorio para convidar membro';
    end if;

    if v_email = '' or position('@' in v_email) = 0 or char_length(v_email) > 254 then
        raise exception 'E-mail de convite invalido';
    end if;

    select limite_membros
      into v_limite
      from public.familias_financeiras
     where id = p_familia_id
       and owner_id = v_auth_user_id;

    if v_limite is null then
        raise exception 'Familia financeira nao encontrada ou sem permissao';
    end if;

    select count(*)
      into v_total
      from public.membros_familia_financeira
     where familia_id = p_familia_id
       and status in ('pendente', 'ativo');

    if v_total >= v_limite then
        raise exception 'Limite de membros do Plano Familia atingido';
    end if;

    insert into public.membros_familia_financeira (
        familia_id,
        email_convite,
        papel,
        status
    )
    values (
        p_familia_id,
        v_email,
        'membro',
        'pendente'
    )
    returning * into v_membro;

    return v_membro;
end;
$$;

grant execute on function public.criar_familia_financeira(text) to authenticated;
grant execute on function public.convidar_membro_familia_financeira(uuid, text) to authenticated;
grant execute on function public.usuario_e_dono_familia_financeira(uuid) to authenticated;
grant execute on function public.usuario_pode_ver_familia_financeira(uuid) to authenticated;

commit;
