from html import escape

import streamlit as st

from auth import auditar_saude_plataforma, supabase
from repositories.finance_repository import atualizar_categoria_transacao
from utils.category_maintenance import (
    CATEGORIA_TRANSPORTE,
    carregar_mapa_reclassificacao,
    extrair_descricoes_para_reclassificar,
    montar_prompt_reclassificacao_categorias,
    preparar_atualizacoes_reclassificacao,
    selecionar_linhas_para_reclassificar,
    selecionar_transacoes_de_transporte,
)
from utils.error_handling import mostrar_erro_seguro
from utils.llm_service import gerar_texto_ia
from utils.platform_health import (
    gerar_decisao_lancamento,
    gerar_health_check_lancamento,
    resumir_health_check,
)


def _classe_status_health(status):
    if status == "OK":
        return "status-ok"
    if status == "Ação necessária":
        return "status-action"
    return "status-attention"


def _montar_tabela_health_check_html(resultados_health):
    linhas = []
    for item in resultados_health:
        status = str(item.get("status", ""))
        linhas.append(
            "<tr>"
            f"<td><strong>{escape(str(item.get('item', '')))}</strong></td>"
            f"<td><span class='health-status {_classe_status_health(status)}'>{escape(status)}</span></td>"
            f"<td>{escape(str(item.get('detalhe', '')))}</td>"
            f"<td>{escape(str(item.get('acao', '')))}</td>"
            "</tr>"
        )
    return (
        "<style>"
        ".health-table{width:100%;border-collapse:separate;border-spacing:0;border:1px solid #d9e2ec;border-radius:8px;overflow:hidden;}"
        ".health-table th{background:#f6f8fb;color:#334155;text-align:left;font-size:0.86rem;font-weight:700;padding:0.75rem;border-bottom:1px solid #d9e2ec;}"
        ".health-table td{padding:0.78rem;border-bottom:1px solid #e8eef5;vertical-align:top;font-size:0.92rem;}"
        ".health-table tr:last-child td{border-bottom:0;}"
        ".health-status{display:inline-block;border-radius:999px;padding:0.18rem 0.55rem;font-size:0.78rem;font-weight:700;white-space:nowrap;}"
        ".status-ok{background:#e8f7ef;color:#087443;}"
        ".status-action{background:#fff4d6;color:#8a5a00;}"
        ".status-attention{background:#eaf2ff;color:#1d4ed8;}"
        "</style>"
        "<table class='health-table'>"
        "<thead><tr><th>Item</th><th>Status</th><th>Detalhe</th><th>Ação</th></tr></thead>"
        f"<tbody>{''.join(linhas)}</tbody>"
        "</table>"
    )


def _render_resumo_lancamento(decisao):
    pronto = "Sim" if decisao["pronto"] else "Não"
    st.markdown("#### Decisão de lançamento")
    st.markdown(
        "<style>"
        ".launch-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin:0.75rem 0 1rem;}"
        ".launch-card{border:1px solid #d9e2ec;border-radius:8px;padding:0.9rem 1rem;background:#fff;}"
        ".launch-card span{display:block;color:#64748b;font-size:0.82rem;font-weight:700;margin-bottom:0.35rem;}"
        ".launch-card strong{display:block;color:#102033;font-size:1.35rem;line-height:1.2;}"
        "@media(max-width:760px){.launch-summary{grid-template-columns:1fr;}}"
        "</style>"
        "<div class='launch-summary'>"
        f"<div class='launch-card'><span>Pronto para validar</span><strong>{escape(pronto)}</strong></div>"
        f"<div class='launch-card'><span>Bloqueios</span><strong>{len(decisao['bloqueios'])}</strong></div>"
        f"<div class='launch-card'><span>Pendências</span><strong>{len(decisao['pendencias'])}</strong></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Status:** {decisao['status']}")
    st.markdown(f"**Leitura:** {decisao['mensagem']}")
    st.markdown(f"**Próxima ação:** {decisao['proxima_acao']}")


def render_admin(lista_total_banco, usuario_id, email_usuario, gerar_conteudo_ia):
    st.title("Admin")
    st.subheader("Manutenção operacional")
    if st.button("Revisar histórico antigo"):
        if not lista_total_banco:
            st.warning("Nenhum dado encontrado para revisar.")
        else:
            with st.spinner("Revisando histórico e atualizando categorias..."):
                try:
                    for item in selecionar_transacoes_de_transporte(lista_total_banco):
                        atualizar_categoria_transacao(item["id"], CATEGORIA_TRANSPORTE)

                    linhas_para_atualizar = selecionar_linhas_para_reclassificar(lista_total_banco)
                    if descricoes := extrair_descricoes_para_reclassificar(linhas_para_atualizar):
                        prompt_lote = montar_prompt_reclassificacao_categorias(descricoes)
                        response_batch = gerar_texto_ia(
                            gerar_conteudo_ia,
                            model="gemini-2.5-flash",
                            prompt=prompt_lote,
                            response_mime_type="application/json",
                        )
                        mapa_categorias = carregar_mapa_reclassificacao(response_batch.text)
                        for item_id, categoria in preparar_atualizacoes_reclassificacao(
                            linhas_para_atualizar,
                            mapa_categorias,
                        ):
                            atualizar_categoria_transacao(item_id, categoria)

                    st.success("Histórico antigo revisado com sucesso.")
                    st.rerun()
                except Exception as erro:
                    st.error(mostrar_erro_seguro(erro, email_usuario))

    st.markdown("---")
    st.subheader("Status operacional")
    status_infra = auditar_saude_plataforma()
    st.markdown(f"**Banco Supabase:** {status_infra['supabase']}")
    st.markdown(f"**Criptografia/SSL:** {status_infra['seguranca']}")

    st.markdown("### Health Check de Lançamento")
    with st.spinner("Verificando prontidão de lançamento..."):
        resultados_health = gerar_health_check_lancamento(
            st.secrets,
            supabase,
            usuario_id,
            status_infra,
        )
    resumo_health = resumir_health_check(resultados_health)
    if resumo_health == "OK":
        st.success("Produto básico pronto para validação com usuários.")
    elif resumo_health == "Ação necessária":
        st.warning("Há bloqueios antes de liberar o app para usuários.")
    else:
        st.info("Produto básico utilizável, mas ainda há pendências operacionais.")
    _render_resumo_lancamento(gerar_decisao_lancamento(resultados_health))
    st.markdown(_montar_tabela_health_check_html(resultados_health), unsafe_allow_html=True)
