-- Endurece user_id somente depois de revalidar nulos e referencias orfas.
-- Nao corrige dados e nao altera RLS, policies, grants ou objetos legados.
-- Aplicar em janela controlada e executar a auditoria de prontidao
-- imediatamente antes. Se houver timeout, a transacao falha e nada e aplicado.

begin;

set local lock_timeout = '5s';
set local statement_timeout = '60s';

-- Impede gravacoes concorrentes entre a validacao e o SET NOT NULL.
lock table
    public.transacoes,
    public.metas_financeiras,
    public.feedbacks_oraculo
in share row exclusive mode;

do $validar_user_id$
begin
    if exists (
        select 1
        from public.transacoes
        where user_id is null
    ) then
        raise exception
            'Nao foi possivel endurecer public.transacoes.user_id: existem registros com user_id nulo';
    end if;

    if exists (
        select 1
        from public.transacoes item
        where not exists (
            select 1
            from auth.users autenticado
            where autenticado.id = item.user_id
        )
    ) then
        raise exception
            'Nao foi possivel endurecer public.transacoes.user_id: existem user_id sem correspondencia em auth.users';
    end if;

    if exists (
        select 1
        from public.metas_financeiras
        where user_id is null
    ) then
        raise exception
            'Nao foi possivel endurecer public.metas_financeiras.user_id: existem registros com user_id nulo';
    end if;

    if exists (
        select 1
        from public.metas_financeiras item
        where not exists (
            select 1
            from auth.users autenticado
            where autenticado.id = item.user_id
        )
    ) then
        raise exception
            'Nao foi possivel endurecer public.metas_financeiras.user_id: existem user_id sem correspondencia em auth.users';
    end if;

    if exists (
        select 1
        from public.feedbacks_oraculo
        where user_id is null
    ) then
        raise exception
            'Nao foi possivel endurecer public.feedbacks_oraculo.user_id: existem registros com user_id nulo';
    end if;

    if exists (
        select 1
        from public.feedbacks_oraculo item
        where not exists (
            select 1
            from auth.users autenticado
            where autenticado.id = item.user_id
        )
    ) then
        raise exception
            'Nao foi possivel endurecer public.feedbacks_oraculo.user_id: existem user_id sem correspondencia em auth.users';
    end if;
end;
$validar_user_id$;

alter table public.transacoes
    alter column user_id set not null;

alter table public.metas_financeiras
    alter column user_id set not null;

alter table public.feedbacks_oraculo
    alter column user_id set not null;

commit;
