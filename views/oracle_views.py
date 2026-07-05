import streamlit as st

from finance_core import resumir_historico_para_ia
from repositories.finance_repository import salvar_feedback_oraculo
from utils.error_handling import mostrar_erro_seguro
from utils.llm_service import gerar_texto_ia
from utils.oracle_analysis import (
    montar_payload_feedback_oraculo,
    montar_prompt_oraculo,
    reforcar_prompt_oraculo,
    resposta_oraculo_tem_secoes,
)
from utils.privacy import anonimizar_dados


def render_oraculo(lista_total_banco, usuario_id, email_usuario, gerar_conteudo_ia):
    st.title("Oráculo IA")
    st.caption(
        "A análise envia somente totais agregados por mês e categoria, sem descrições de transações."
    )
    col_gatilho, _ = st.columns([3, 7])
    with col_gatilho:
        ativar_oraculo = st.button("Gerar análise financeira", use_container_width=True)

    if ativar_oraculo:
        if not lista_total_banco:
            st.warning("Adicione transações antes de gerar a análise.")
        else:
            with st.spinner("Consolidando seu relatório financeiro..."):
                try:
                    st.session_state.feedback_enviado = False
                    historico_formatado = resumir_historico_para_ia(lista_total_banco)
                    st.session_state.historico_oraculo_enviado = historico_formatado
                    prompt_oraculo = montar_prompt_oraculo(historico_formatado)
                    resposta_oraculo = gerar_texto_ia(
                        gerar_conteudo_ia,
                        model="gemini-2.5-flash",
                        prompt=prompt_oraculo,
                        temperature=0.1,
                    )
                    texto_final = resposta_oraculo.text

                    if not resposta_oraculo_tem_secoes(texto_final):
                        resposta_oraculo = gerar_texto_ia(
                            gerar_conteudo_ia,
                            model="gemini-2.5-flash",
                            prompt=reforcar_prompt_oraculo(prompt_oraculo),
                            temperature=0.0,
                        )
                        texto_final = resposta_oraculo.text

                    st.session_state.resposta_oraculo_texto = texto_final
                except Exception as erro:
                    st.error(mostrar_erro_seguro(erro, email_usuario))

    if st.session_state.resposta_oraculo_texto:
        st.markdown("---")
        st.success("Relatório financeiro gerado com sucesso!")
        st.markdown(st.session_state.resposta_oraculo_texto)
        st.markdown("##### Avalie essa resposta para melhorar as próximas análises:")
        col_fb1, col_fb2, _ = st.columns([1.5, 2, 6.5])

        if not st.session_state.feedback_enviado:
            with col_fb1:
                if st.button("Foi útil", use_container_width=True):
                    _salvar_feedback_oraculo(usuario_id, email_usuario, "TOP")
            with col_fb2:
                if st.button("Precisa melhorar", use_container_width=True):
                    _salvar_feedback_oraculo(usuario_id, email_usuario, "RUIM")
        else:
            st.info("Obrigado pelo feedback! Ele será usado para melhorar as próximas análises.")


def _salvar_feedback_oraculo(usuario_id, email_usuario, status_resposta):
    try:
        salvar_feedback_oraculo(
            montar_payload_feedback_oraculo(
                usuario_id=usuario_id,
                email_usuario=email_usuario,
                status_resposta=status_resposta,
                resposta_ia=st.session_state.resposta_oraculo_texto,
                dados_enviados=st.session_state.historico_oraculo_enviado,
                anonimizar=anonimizar_dados,
            )
        )
        st.session_state.feedback_enviado = True
        st.rerun()
    except Exception as erro:
        st.error(mostrar_erro_seguro(erro, email_usuario))
