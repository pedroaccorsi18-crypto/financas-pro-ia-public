"""Preparacao de lancamentos manuais antes da persistencia."""

from finance_constants import ORIGEM_MANUAL, TIPO_DOCUMENTO_MANUAL


def preparar_transacao_manual(
    *,
    descricao,
    valor,
    tipo_transacao,
    categoria,
    categorias_validas,
    mes_referencia,
    instituicao,
    usuario_id,
    email_usuario,
):
    return {
        "user_id": usuario_id,
        "usuario_email": email_usuario,
        "descricao": descricao.strip(),
        "valor": float(valor),
        "tipo": tipo_transacao,
        "categoria": categoria if categoria in categorias_validas else categorias_validas[-1],
        "mes_referencia": mes_referencia,
        "meta_fatura": 0.0,
        "instituicao_financeira": instituicao.strip() if instituicao else ORIGEM_MANUAL,
        "tipo_documento": TIPO_DOCUMENTO_MANUAL,
        "origem_importacao": ORIGEM_MANUAL,
    }
