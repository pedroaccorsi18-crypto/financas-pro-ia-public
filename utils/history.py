"""Formatacao das linhas do historico geral."""

from finance_constants import ORIGEM_MANUAL, TIPO_DESPESA, TIPO_RECEITA
from utils.formatting import formatar_brl


def formatar_linha_historico(transacao):
    cor = "🟢" if transacao["tipo"] == TIPO_RECEITA else "🔴"
    status_tipo = "Entrada" if transacao["tipo"] == TIPO_RECEITA else "Saída"
    banco_tag = transacao.get("instituicao_financeira", ORIGEM_MANUAL)
    origem_label = "✍️" if transacao.get("origem_importacao") == ORIGEM_MANUAL else "🤖"
    categoria_tag = (
        f" [{transacao.get('categoria', 'Geral')}]"
        if transacao["tipo"] == TIPO_DESPESA
        else ""
    )
    return (
        f"{cor} **{transacao['descricao']}**{categoria_tag} | "
        f"{formatar_brl(transacao['valor'])} ({status_tipo} | {origem_label} {banco_tag})"
    )
