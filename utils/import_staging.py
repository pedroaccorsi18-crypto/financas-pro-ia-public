"""Preparacao de transacoes homologadas antes da persistencia."""

from finance_categories import CATEGORIAS_VALIDAS
from finance_constants import ORIGEM_AUTOMATICA, TIPO_DESPESA, TIPOS_TRANSACAO
from finance_core import mes_referencia_valido


TERMOS_TRANSPORTE = ["pmbmetro", "metro", "cptm", "autopass"]


def preparar_transacoes_importadas(df_editavel, pre_visualizacao, usuario_id, email_usuario):
    if not pre_visualizacao["instituicao"] or str(pre_visualizacao["instituicao"]).strip() == "":
        raise ValueError("A identificação da instituição financeira não pode estar vazia.")

    if not mes_referencia_valido(str(pre_visualizacao["mes_referencia"])):
        raise ValueError("O mês de referência extraído do PDF deve seguir estritamente o formato MM/AAAA.")

    gastos_reais, creditos_reais = 0.0, 0.0
    transacoes_para_inserir = []

    for _, row in df_editavel.iterrows():
        val_item = float(row["valor"])
        desc_original = str(row["descricao"]).strip()
        categoria_final = str(row["categoria"]).strip()
        tipo_final = str(row["tipo"]).strip()

        if not desc_original or desc_original == "":
            raise ValueError("Nenhum lançamento pode conter uma descrição vazia.")
        if val_item <= 0:
            raise ValueError(f"O lançamento '{desc_original}' possui valor nulo ou negativo inválido.")
        if tipo_final not in TIPOS_TRANSACAO:
            raise ValueError(f"O tipo do lançamento '{desc_original}' deve ser estritamente 'Despesa' ou 'Receita'.")
        if categoria_final not in CATEGORIAS_VALIDAS:
            raise ValueError(f"A categoria '{categoria_final}' no item '{desc_original}' não faz parte do catálogo permitido.")

        if any(k in desc_original.lower() for k in TERMOS_TRANSPORTE):
            categoria_final = "Transporte"

        if tipo_final == TIPO_DESPESA:
            gastos_reais += val_item
        else:
            creditos_reais += val_item

        transacoes_para_inserir.append({
            "user_id": usuario_id,
            "usuario_email": email_usuario,
            "descricao": desc_original,
            "valor": val_item,
            "tipo": tipo_final,
            "categoria": categoria_final,
            "mes_referencia": pre_visualizacao["mes_referencia"].strip(),
            "meta_fatura": pre_visualizacao["total_documento"],
            "instituicao_financeira": pre_visualizacao["instituicao"].strip(),
            "tipo_documento": pre_visualizacao["tipo_documento"],
            "origem_importacao": ORIGEM_AUTOMATICA,
        })

    return transacoes_para_inserir, gastos_reais, creditos_reais
