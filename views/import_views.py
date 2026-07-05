import datetime

import pandas as pd
import streamlit as st
from google.genai import types

from finance_categories import CATEGORIAS_VALIDAS
from finance_constants import TIPOS_TRANSACAO
from finance_core import criar_lote_demonstrativo, lotes_sao_iguais
from repositories.finance_repository import buscar_lote_importado, substituir_lote_importado
from utils.ai_extraction import (
    carregar_resultado_extracao,
    montar_config_extracao_pdf,
    montar_prompt_extracao_pdf,
    normalizar_resultado_extracao,
)
from utils.bot_fiscal import disparar_bot_fiscal_email
from utils.error_handling import mostrar_erro_seguro
from utils.formatting import formatar_brl
from utils.import_workflow import processar_importacao_homologada


def render_importacao(lista_total_banco, usuario_id, email_usuario, is_admin, gerar_conteudo_gemini):
    st.title("Importação")
    st.markdown("### Importar PDF com apoio da IA")
    arquivo_subido = st.file_uploader(
        "Selecione um extrato bancário, fatura ou comprovante em PDF",
        type=["pdf"],
    )
    consentimento_pdf_ia = st.checkbox(
        "Autorizo o processamento temporário deste PDF pela IA para extrair os dados.",
        help="O documento pode conter informações financeiras sensíveis. Envie somente se concordar com o processamento externo.",
    )

    if is_admin:
        with st.expander("Modo de teste sem Gemini"):
            st.caption("Cria uma fatura fictícia e usa exatamente o mesmo fluxo de salvamento da importação real.")
            mes_teste = st.text_input(
                "Mês do teste (MM/AAAA)",
                value=datetime.datetime.now().strftime("%m/%Y"),
                key="mes_importacao_teste",
            )
            if st.button("Gerar importação demonstrativa", key="gerar_importacao_demonstrativa"):
                try:
                    lote_teste = criar_lote_demonstrativo(mes_teste)
                    st.session_state.dados_pre_visualizacao = {
                        "instituicao": lote_teste["instituicao"],
                        "tipo_documento": lote_teste["tipo_documento"],
                        "mes_referencia": lote_teste["mes_referencia"],
                        "total_documento": lote_teste["total_documento"],
                        "df_transacoes": pd.DataFrame(lote_teste["transacoes"]),
                    }
                    st.toast("Importação demonstrativa criada.", icon="🧪")
                    st.rerun()
                except ValueError as erro_teste:
                    st.warning(str(erro_teste))

    if arquivo_subido is not None and st.button("Extrair dados do PDF"):
        if not consentimento_pdf_ia:
            st.warning("Confirme a autorização de processamento externo antes de enviar o PDF.")
        else:
            with st.spinner("Lendo o PDF e organizando os lançamentos..."):
                try:
                    dados_pdf = arquivo_subido.read()
                    if len(dados_pdf) > 10 * 1024 * 1024:
                        raise ValueError("O PDF excede o limite de 10 MB.")

                    response = gerar_conteudo_gemini(
                        model="gemini-2.5-flash",
                        contents=[
                            types.Part.from_bytes(data=dados_pdf, mime_type="application/pdf"),
                            montar_prompt_extracao_pdf(),
                        ],
                        config=montar_config_extracao_pdf(types),
                    )
                    resultado_ia = carregar_resultado_extracao(response.text)
                    st.session_state.dados_pre_visualizacao = normalizar_resultado_extracao(
                        resultado_ia,
                        pd.DataFrame,
                    )
                    st.toast("Dados extraídos. Revise antes de salvar.", icon="🪄")
                except Exception as erro:
                    st.error(mostrar_erro_seguro(erro, email_usuario))

    if st.session_state.dados_pre_visualizacao is not None:
        _render_homologacao_importacao(usuario_id, email_usuario)
    elif lista_total_banco:
        st.caption("Nenhuma importação pendente de revisão.")


def _render_homologacao_importacao(usuario_id, email_usuario):
    st.markdown("---")
    st.subheader("Revisão antes de salvar")
    pre_vis = st.session_state.dados_pre_visualizacao
    mes_corrigido = st.text_input(
        "Mês de referência da importação (MM/AAAA)",
        value=str(pre_vis["mes_referencia"]),
        help="Confira este campo antes de salvar. Exemplo: 05/2026.",
    ).strip()
    pre_vis["mes_referencia"] = mes_corrigido

    c_meta1, c_meta2, c_meta3, c_meta4 = st.columns(4)
    with c_meta1:
        st.metric("Instituição Identificada", pre_vis["instituicao"])
    with c_meta2:
        st.metric("Tipo de Documento", pre_vis["tipo_documento"])
    with c_meta3:
        st.metric("Mês de Referência", pre_vis["mes_referencia"])
    with c_meta4:
        st.metric("Total identificado no documento", formatar_brl(pre_vis["total_documento"]))

    df_editavel = st.data_editor(
        pre_vis["df_transacoes"],
        column_config={
            "descricao": st.column_config.TextColumn(
                "Descrição da Transação",
                disabled=True,
                width="medium",
            ),
            "valor": st.column_config.NumberColumn("Valor (R$)", disabled=True, format="R$ %.2f"),
            "tipo": st.column_config.SelectboxColumn("Fluxo", options=TIPOS_TRANSACAO, required=True),
            "categoria": st.column_config.SelectboxColumn(
                "Classificação IA",
                options=CATEGORIAS_VALIDAS,
                required=True,
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="staging_data_editor",
    )

    col_btn1, col_btn2, _ = st.columns([15, 15, 70])
    with col_btn1:
        if st.button("Confirmar e salvar lançamentos", type="primary", use_container_width=True):
            with st.spinner("Salvando lançamentos revisados..."):
                try:
                    processar_importacao_homologada(
                        df_editavel=df_editavel,
                        pre_visualizacao=pre_vis,
                        usuario_id=usuario_id,
                        email_usuario=email_usuario,
                        secrets=st.secrets,
                        buscar_lote=buscar_lote_importado,
                        lotes_sao_iguais=lotes_sao_iguais,
                        substituir_lote=substituir_lote_importado,
                        disparar_alerta=disparar_bot_fiscal_email,
                    )
                    st.toast("Lançamentos salvos com sucesso!", icon="⚡")
                    st.session_state.dados_pre_visualizacao = None
                    st.rerun()
                except Exception as e_save:
                    st.error(mostrar_erro_seguro(e_save, email_usuario))

    with col_btn2:
        if st.button("Descartar revisão", use_container_width=True):
            st.session_state.dados_pre_visualizacao = None
            st.rerun()
