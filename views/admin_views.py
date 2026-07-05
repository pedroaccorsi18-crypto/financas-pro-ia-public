import streamlit as st
from google.genai import types

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
from utils.platform_health import gerar_health_check_supabase, resumir_health_check


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
                        response_batch = gerar_conteudo_ia(
                            model="gemini-2.5-flash",
                            contents=prompt_lote,
                            config=types.GenerateContentConfig(response_mime_type="application/json"),
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

    st.markdown("### Verificação de banco e migrações")
    with st.spinner("Verificando estrutura operacional..."):
        resultados_health = gerar_health_check_supabase(supabase, usuario_id)
    resumo_health = resumir_health_check(resultados_health)
    if resumo_health == "OK":
        st.success("Banco e estruturas essenciais prontos.")
    elif resumo_health == "Ação necessária":
        st.warning("Há migrações ou objetos obrigatórios pendentes.")
    else:
        st.info("Há itens que exigem atenção operacional.")
    st.dataframe(resultados_health, use_container_width=True, hide_index=True)
