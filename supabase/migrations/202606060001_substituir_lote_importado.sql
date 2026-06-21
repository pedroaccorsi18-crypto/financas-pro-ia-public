create or replace function public.substituir_lote_importado(
    p_usuario_email text,
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
begin
    delete from public.transacoes
    where usuario_email = lower(trim(p_usuario_email))
      and mes_referencia = p_mes_referencia
      and instituicao_financeira = p_instituicao_financeira
      and tipo_documento = p_tipo_documento
      and origem_importacao = 'Automático';

    insert into public.transacoes (
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
        lower(trim(p_usuario_email)),
        item->>'descricao',
        (item->>'valor')::numeric,
        item->>'tipo',
        item->>'categoria',
        item->>'mes_referencia',
        (item->>'meta_fatura')::numeric,
        item->>'instituicao_financeira',
        item->>'tipo_documento',
        item->>'origem_importacao'
    from jsonb_array_elements(p_transacoes) item;
end;
$$;
