import logging

import streamlit as st

from repositories.finance_repository import (
    convidar_membro_familia_financeira,
    criar_familia_financeira,
    listar_familias_financeiras,
    listar_membros_familia_financeira,
)
from utils.family_plan import validar_email_convite, validar_nome_familia
from utils.subscriptions import normalizar_plano, pode_usar_plano_familia, rotulo_plano
from utils.stripe_billing import criar_checkout_assinatura, price_id_por_plano


logger = logging.getLogger(__name__)


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


def _base_url_app(secrets):
    return str(
        secrets.get("APP_BASE_URL")
        or secrets.get("PUBLIC_APP_URL")
        or "http://localhost:8501"
    ).rstrip("/")


def _obter_url_checkout(sessao):
    if isinstance(sessao, dict):
        return sessao.get("url")
    return getattr(sessao, "url", None)


def _criar_url_checkout(plano, secrets, usuario_id, email_usuario):
    import stripe

    base_url = _base_url_app(secrets)
    sessao = criar_checkout_assinatura(
        stripe_module=stripe,
        stripe_secret_key=str(secrets.get("STRIPE_SECRET_KEY", "")).strip(),
        price_id=price_id_por_plano(plano, secrets),
        usuario_id=usuario_id,
        email_usuario=email_usuario,
        plano=plano,
        success_url=f"{base_url}?checkout=sucesso",
        cancel_url=f"{base_url}?checkout=cancelado",
    )
    url_checkout = _obter_url_checkout(sessao)
    if not url_checkout:
        raise RuntimeError("Stripe nao retornou URL de checkout.")
    return url_checkout


def _render_link_checkout(plano, url_checkout):
    st.success("Link de pagamento criado. Abra em uma nova aba para concluir com segurança.")
    st.link_button(
        f"Abrir checkout do plano {plano['titulo']}",
        url_checkout,
        use_container_width=True,
    )


def _render_card_plano(plano, plano_atual, secrets, usuario_id, email_usuario):
    eh_plano_atual = plano["plano"] == plano_atual
    chave_checkout = f"checkout_url_{plano['plano']}"
    st.markdown(f"### {plano['titulo']}")
    st.markdown(f"**{plano['preco']}**")
    st.caption(plano["descricao"])
    for beneficio in plano["beneficios"]:
        st.markdown(f"- {beneficio}")

    if eh_plano_atual:
        st.success("Plano atual")
    elif stripe_configurado_para_upgrade(secrets, plano["plano"]):
        if st.button(f"Fazer upgrade para {plano['titulo']}", use_container_width=True):
            try:
                st.session_state[chave_checkout] = _criar_url_checkout(
                    plano["plano"],
                    secrets,
                    usuario_id,
                    email_usuario,
                )
            except ImportError:
                st.error("Biblioteca Stripe não instalada neste ambiente.")
            except Exception as erro:
                logger.warning(
                    "Nao foi possivel criar checkout Stripe",
                    extra={"tipo_erro": type(erro).__name__, "plano": plano["plano"]},
                )
                st.error("Não foi possível iniciar o checkout agora. Tente novamente em alguns minutos.")

        url_checkout = st.session_state.get(chave_checkout)
        if url_checkout:
            _render_link_checkout(plano, url_checkout)
        else:
            st.caption("Pagamento seguro processado pelo Stripe.")
    else:
        st.button(f"Upgrade para {plano['titulo']}", use_container_width=True, disabled=True)
        st.caption("Upgrade em breve. Estamos finalizando a liberação deste plano.")


def _render_membros_familia(membros):
    membros_ativos = [membro for membro in membros if membro.get("status") != "removido"]
    if not membros_ativos:
        st.info("Nenhum membro ativo encontrado.")
        return

    for membro in membros_ativos:
        email = membro.get("email_convite") or "E-mail não informado"
        papel = membro.get("papel") or "membro"
        status = membro.get("status") or "pendente"
        st.markdown(f"- **{email}** · {papel} · {status}")


def _render_convite_familia(familia_id, total_membros, limite_membros):
    if total_membros >= limite_membros:
        st.warning(f"Limite de {limite_membros} pessoas atingido neste plano.")
        return

    email_convite = st.text_input("E-mail do novo membro", key="email_convite_familia")
    if st.button("Enviar convite", use_container_width=True):
        try:
            email_validado = validar_email_convite(email_convite)
            convidar_membro_familia_financeira(familia_id, email_validado)
            st.success("Convite registrado. O membro deve usar uma conta própria para acessar.")
        except ValueError as erro:
            st.error(str(erro))
        except Exception as erro:
            logger.warning(
                "Nao foi possivel convidar membro da familia financeira",
                extra={"tipo_erro": type(erro).__name__},
            )
            st.error("Não foi possível enviar o convite agora. Tente novamente em alguns minutos.")


def _render_criacao_familia():
    st.info("Crie uma família para convidar membros com contas próprias.")
    nome_familia = st.text_input("Nome da família", value="Minha família", key="nome_familia")
    if st.button("Criar família", use_container_width=True):
        try:
            criar_familia_financeira(validar_nome_familia(nome_familia))
            st.success("Família criada. Agora você pode convidar os membros.")
        except ValueError as erro:
            st.error(str(erro))
        except Exception as erro:
            logger.warning(
                "Nao foi possivel criar familia financeira",
                extra={"tipo_erro": type(erro).__name__},
            )
            st.error("Não foi possível criar a família agora. Tente novamente em alguns minutos.")


def _render_gestao_familia(assinatura):
    st.markdown("### Gestão do Plano Família")
    st.caption(
        "Para proteger sua assinatura, cada pessoa deve acessar com conta própria. "
        "Não recomendamos compartilhar e-mail e senha."
    )

    if not pode_usar_plano_familia(assinatura):
        st.info("A gestão de membros fica disponível para assinantes do Plano Família.")
        return

    limite_membros = int((assinatura or {}).get("limite_membros") or 4)
    try:
        familias = listar_familias_financeiras()
    except Exception as erro:
        logger.warning(
            "Nao foi possivel listar familias financeiras",
            extra={"tipo_erro": type(erro).__name__},
        )
        st.error("Não foi possível carregar a família agora. Tente novamente em alguns minutos.")
        return

    if not familias:
        _render_criacao_familia()
        return

    familia = familias[0]
    familia_id = familia.get("id")
    st.success(f"Família ativa: {familia.get('nome') or 'Família financeira'}")

    try:
        membros = listar_membros_familia_financeira(familia_id)
    except Exception as erro:
        logger.warning(
            "Nao foi possivel listar membros da familia financeira",
            extra={"tipo_erro": type(erro).__name__},
        )
        st.error("Não foi possível carregar os membros agora. Tente novamente em alguns minutos.")
        return

    membros_ativos = [membro for membro in membros if membro.get("status") != "removido"]
    st.caption(f"{len(membros_ativos)} de {limite_membros} pessoas em uso.")
    _render_membros_familia(membros)
    _render_convite_familia(familia_id, len(membros_ativos), limite_membros)


def render_meu_plano(assinatura, secrets, usuario_id=None, email_usuario=None):
    plano_atual = normalizar_plano((assinatura or {}).get("plano"))
    st.title("Meu Plano")
    st.caption("Acompanhe sua assinatura e veja quais recursos entram em cada etapa.")

    col_plano, col_status, col_limite = st.columns(3)
    col_plano.metric("Plano atual", rotulo_plano(plano_atual))
    col_status.metric("Status", _status_do_plano(assinatura))
    col_limite.metric("Pessoas", str((assinatura or {}).get("limite_membros") or 1))

    st.markdown("### Escolha como quer evoluir")
    if plano_atual == "gratuito":
        st.info(
            "Você está no plano gratuito. Continue organizando seu mês sem custo ou escolha um plano pago "
            "quando quiser ganhar velocidade com importação, histórico e organização familiar."
        )
    else:
        st.success("Seu plano está ativo. Você pode acompanhar abaixo os recursos disponíveis e as opções de evolução.")

    st.markdown("---")
    colunas = st.columns(len(PLANOS_APP))
    for coluna, plano in zip(colunas, PLANOS_APP):
        with coluna:
            _render_card_plano(plano, plano_atual, secrets, usuario_id, email_usuario)

    st.markdown("---")
    _render_gestao_familia(assinatura)
