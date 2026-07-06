import streamlit as st

from utils.subscriptions import normalizar_plano, rotulo_plano
from utils.stripe_billing import price_id_por_plano


PLANOS_APP = (
    {
        "plano": "gratuito",
        "titulo": "Gratuito",
        "preco": "R$ 0",
        "descricao": "Para começar a organizar o mês e validar o método.",
        "beneficios": (
            "Lançamentos manuais",
            "Resumo mensal",
            "Metas por categoria",
        ),
    },
    {
        "plano": "pro",
        "titulo": "Pro",
        "preco": "R$ 19,90/mês",
        "descricao": "Para ganhar velocidade com importação e histórico financeiro.",
        "beneficios": (
            "Importação assistida",
            "Revisão por categoria",
            "Histórico e evolução mensal",
        ),
    },
    {
        "plano": "familia",
        "titulo": "Família",
        "preco": "R$ 29,90/mês",
        "descricao": "Para organizar a vida financeira da casa com até 4 pessoas.",
        "beneficios": (
            "Tudo do Pro",
            "Até 4 contas conectadas",
            "Objetivos familiares compartilhados",
        ),
    },
)


def stripe_configurado_para_upgrade(secrets, plano):
    return bool(
        secrets.get("STRIPE_SECRET_KEY")
        and price_id_por_plano(plano, secrets)
    )


def _status_do_plano(assinatura):
    status = str((assinatura or {}).get("status") or "ativo").strip().lower()
    mapa = {
        "ativo": "Ativo",
        "trial": "Teste ativo",
        "past_due": "Pagamento pendente",
        "cancelado": "Cancelado",
        "incompleto": "Incompleto",
    }
    return mapa.get(status, "Ativo")


def _render_card_plano(plano, plano_atual, secrets):
    eh_plano_atual = plano["plano"] == plano_atual
    st.markdown(f"### {plano['titulo']}")
    st.markdown(f"**{plano['preco']}**")
    st.caption(plano["descricao"])
    for beneficio in plano["beneficios"]:
        st.markdown(f"- {beneficio}")

    if eh_plano_atual:
        st.success("Plano atual")
    elif stripe_configurado_para_upgrade(secrets, plano["plano"]):
        st.button(f"Fazer upgrade para {plano['titulo']}", use_container_width=True, disabled=True)
        st.caption("Checkout Stripe preparado. Ativaremos a cobrança após a validação final.")
    else:
        st.button(f"Upgrade para {plano['titulo']}", use_container_width=True, disabled=True)
        st.caption("Upgrade em breve. Stripe ainda não está configurado para este plano.")


def render_meu_plano(assinatura, secrets):
    plano_atual = normalizar_plano((assinatura or {}).get("plano"))
    st.title("Meu Plano")
    st.caption("Acompanhe sua assinatura e veja quais recursos entram em cada etapa.")

    col_plano, col_status, col_limite = st.columns(3)
    col_plano.metric("Plano atual", rotulo_plano(plano_atual))
    col_status.metric("Status", _status_do_plano(assinatura))
    col_limite.metric("Pessoas", str((assinatura or {}).get("limite_membros") or 1))

    st.markdown("### Próximos passos para monetização")
    if stripe_configurado_para_upgrade(secrets, "pro") and stripe_configurado_para_upgrade(secrets, "familia"):
        st.success("Stripe configurado para planos pagos. Próximo passo: validar checkout e webhook em modo teste.")
    else:
        st.info(
            "Stripe ainda não está pronto para cobrança. A experiência de planos já está preparada, "
            "mas o upgrade permanece bloqueado para evitar cobrança quebrada."
        )

    st.markdown("---")
    colunas = st.columns(len(PLANOS_APP))
    for coluna, plano in zip(colunas, PLANOS_APP):
        with coluna:
            _render_card_plano(plano, plano_atual, secrets)
