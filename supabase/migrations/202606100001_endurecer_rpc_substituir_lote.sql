begin;

create or replace function public.substituir_lote_importado(
    p_user_id uuid,
    p_mes_referencia text,
    p_instituicao_financeira text,
    p_tipo_documento text,
    p_transacoes jsonb
)
returns void
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_auth_user_id uuid := auth.uid();
    v_email text := lower(trim(coalesce(auth.jwt() ->> 'email', '')));
begin
    if v_auth_user_id is null then
        raise exception 'Usuario nao autenticado';
    end if;

    if p_user_id is null or p_user_id is distinct from v_auth_user_id then
        raise exception 'Usuario do lote invalido';
    end if;

    if p_mes_referencia is null
       or p_mes_referencia !~ '^(0[1-9]|1[0-2])/[0-9]{4}$'
       or nullif(trim(p_instituicao_financeira), '') is null
       or nullif(trim(p_tipo_documento), '') is null then
        raise exception 'Identidade do lote invalida';
    end if;

    if p_transacoes is null
       or jsonb_typeof(p_transacoes) is distinct from 'array' then
        raise exception 'Payload de transacoes deve ser um array';
    end if;

    if jsonb_array_length(p_transacoes) = 0 then
        raise exception 'Payload de transacoes nao pode ser vazio';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_transacoes) item
        where jsonb_typeof(item) is distinct from 'object'
           or jsonb_typeof(item->'descricao') is distinct from 'string'
           or nullif(trim(item->>'descricao'), '') is null
           or jsonb_typeof(item->'valor') is distinct from 'number'
           or jsonb_typeof(item->'tipo') is distinct from 'string'
           or jsonb_typeof(item->'categoria') is distinct from 'string'
           or nullif(trim(item->>'categoria'), '') is null
           or jsonb_typeof(item->'mes_referencia') is distinct from 'string'
           or jsonb_typeof(item->'meta_fatura') is distinct from 'number'
           or jsonb_typeof(item->'instituicao_financeira') is distinct from 'string'
           or nullif(trim(item->>'instituicao_financeira'), '') is null
           or jsonb_typeof(item->'tipo_documento') is distinct from 'string'
           or nullif(trim(item->>'tipo_documento'), '') is null
           or jsonb_typeof(item->'origem_importacao') is distinct from 'string'
           or nullif(trim(item->>'origem_importacao'), '') is null
    ) then
        raise exception 'Payload de transacoes possui campos ausentes ou tipos invalidos';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_transacoes) item
        where (item->>'valor')::numeric <= 0
           or item->>'tipo' not in ('Despesa', 'Receita')
           or item->>'mes_referencia' is distinct from p_mes_referencia
           or (item->>'meta_fatura')::numeric < 0
           or item->>'instituicao_financeira' is distinct from p_instituicao_financeira
           or item->>'tipo_documento' is distinct from p_tipo_documento
           or item->>'origem_importacao' is distinct from 'Automático'
    ) then
        raise exception 'Payload de transacoes invalido ou inconsistente com o lote';
    end if;

    delete from public.transacoes
    where user_id = p_user_id
      and mes_referencia = p_mes_referencia
      and instituicao_financeira = p_instituicao_financeira
      and tipo_documento = p_tipo_documento
      and origem_importacao = 'Automático';

    insert into public.transacoes (
        user_id,
        usuario_email,
        descricao,
        valor,
        tipo,
        categoria,
        mes_referencia,
        meta_fatura,
        instituicao_financeira,
        tipo_documento,
        origem_importacao
    )
    select
        p_user_id,
        coalesce(nullif(lower(trim(item->>'usuario_email')), ''), v_email),
        trim(item->>'descricao'),
        (item->>'valor')::numeric,
        item->>'tipo',
        trim(item->>'categoria'),
        p_mes_referencia,
        (item->>'meta_fatura')::numeric,
        p_instituicao_financeira,
        p_tipo_documento,
        'Automático'
    from jsonb_array_elements(p_transacoes) item;
end;
$$;

revoke all on function public.substituir_lote_importado(text, text, text, jsonb)
    from public, anon, authenticated;
revoke all on function public.substituir_lote_importado(uuid, text, text, text, jsonb)
    from public, anon;
grant execute on function public.substituir_lote_importado(uuid, text, text, text, jsonb)
    to authenticated;

commit;
