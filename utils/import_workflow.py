"""Orquestracao da homologacao de importacoes financeiras."""

from utils.import_staging import preparar_transacoes_importadas


def processar_importacao_homologada(
    *,
    df_editavel,
    pre_visualizacao,
    usuario_id,
    email_usuario,
    secrets,
    buscar_lote,
    lotes_sao_iguais,
    substituir_lote,
    disparar_alerta,
):
    transacoes_para_inserir, gastos_reais, creditos_reais = preparar_transacoes_importadas(
        df_editavel,
        pre_visualizacao,
        usuario_id,
        email_usuario,
    )

    lote_substituido = False
    instituicao = pre_visualizacao["instituicao"].strip()
    mes_referencia = pre_visualizacao["mes_referencia"].strip()
    tipo_documento = pre_visualizacao["tipo_documento"]

    if transacoes_para_inserir:
        lote_existente = buscar_lote(
            usuario_id=usuario_id,
            mes_referencia=mes_referencia,
            instituicao_financeira=instituicao,
            tipo_documento=tipo_documento,
        )

        if not lotes_sao_iguais(transacoes_para_inserir, lote_existente):
            substituir_lote(
                usuario_id=usuario_id,
                mes_referencia=mes_referencia,
                instituicao_financeira=instituicao,
                tipo_documento=tipo_documento,
                transacoes=transacoes_para_inserir,
            )
            lote_substituido = True

    alerta_disparado = False
    total_documento = pre_visualizacao["total_documento"]
    if total_documento > 0:
        disparar_alerta(
            secrets,
            email_usuario,
            instituicao,
            tipo_documento,
            mes_referencia,
            gastos_reais,
            creditos_reais,
            total_documento,
        )
        alerta_disparado = True

    return {
        "transacoes": transacoes_para_inserir,
        "gastos_reais": gastos_reais,
        "creditos_reais": creditos_reais,
        "lote_substituido": lote_substituido,
        "alerta_disparado": alerta_disparado,
    }
