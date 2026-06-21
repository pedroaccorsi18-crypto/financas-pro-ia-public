begin;

drop function if exists public.substituir_lote_importado(text, text, text, text, jsonb);

create or replace function public.substituir_lote_importado(
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
    v_user_id uuid := auth.uid();
    v_email text := lower(trim(coalesce(auth.jwt() ->> 'email', '')));
begin
    if v_user_id is null then
        raise exception 'Usuario nao autenticado';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_transacoes) item
        where item->>'mes_referencia' is distinct from p_mes_referencia
           or item->>'instituicao_financeira' is distinct from p_instituicao_financeira
           or item->>'tipo_documento' is distinct from p_tipo_documento
    ) then
        raise exception 'Payload inconsistente com a identidade do lote';
    end if;

    delete from public.transacoes
    where user_id = v_user_id
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
        v_user_id,
        v_email,
        item->>'descricao',
        (item->>'valor')::numeric,
        item->>'tipo',
        item->>'categoria',
        p_mes_referencia,
        (item->>'meta_fatura')::numeric,
        p_instituicao_financeira,
        p_tipo_documento,
        item->>'origem_importacao'
    from jsonb_array_elements(p_transacoes) item;
end;
$$;

revoke all on function public.substituir_lote_importado(text, text, text, jsonb)
    from public, anon;
grant execute on function public.substituir_lote_importado(text, text, text, jsonb)
    to authenticated;

commit;
