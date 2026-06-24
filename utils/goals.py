"""Calculos de status para metas financeiras."""

from utils.formatting import formatar_brl


def calcular_status_meta(gasto_atual, meta_cadastrada):
    pct = gasto_atual / meta_cadastrada
    restante = meta_cadastrada - gasto_atual

    if pct >= 1.0:
        return pct, "red", f"🚨 Orçamento Estourado por {formatar_brl(abs(restante))}!"
    if pct >= 0.8:
        return (
            pct,
            "orange",
            f"⚠️ Atenção! Você consumiu {pct*100:.1f}% do teto. Restam {formatar_brl(restante)}.",
        )
    return (
        pct,
        "green",
        f"✅ Sob Controle. Restam {formatar_brl(restante)} disponíveis.",
    )
