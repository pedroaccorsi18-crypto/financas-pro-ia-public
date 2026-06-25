import streamlit as st
import datetime
import logging
from google.genai import types
from auth import (
    auditar_saude_plataforma,
    cadastrar_usuario,
    enviar_email_recuperacao_senha,
    fazer_login,
    validar_chave_publica_supabase,
    validar_sessao_atual,
)
from finance_core import (
    calcular_resumo_financeiro,
    criar_lote_demonstrativo,
    lotes_sao_iguais,
    mes_referencia_valido,
    ordenar_meses_cronologicamente,
    resumir_historico_para_ia,
)
from finance_categories import (
    CATEGORIAS_DESPESA,
    CATEGORIAS_RECEITA,
    CATEGORIAS_VALIDAS,
)
from finance_constants import (
    ORIGEM_MANUAL,
    TIPO_DESPESA,
    TIPO_RECEITA,
    TIPOS_TRANSACAO,
)
from repositories.finance_repository import (
    atualizar_categoria_transacao,
    buscar_lote_importado,
    inserir_transacao,
    listar_metas_usuario_mes,
    listar_transacoes_usuario,
    salvar_feedback_oraculo,
    salvar_meta_financeira,
    substituir_lote_importado,
)
from session_state import (
    encerrar_sessao_usuario,
    inicializar_estado_sessao,
    iniciar_sessao_autenticada,
    limpar_sessao_usuario,
)
from utils.authorization import eh_usuario_admin
from utils.audit import preparar_dataframe_auditoria_categoria
from utils.ai_extraction import (
    carregar_resultado_extracao,
    montar_config_extracao_pdf,
    montar_prompt_extracao_pdf,
    normalizar_resultado_extracao,
)
from utils.bot_fiscal import disparar_bot_fiscal_email
from utils.category_maintenance import (
    CATEGORIA_TRANSPORTE,
    carregar_mapa_reclassificacao,
    extrair_descricoes_para_reclassificar,
    montar_prompt_reclassificacao_categorias,
    preparar_atualizacoes_reclassificacao,
    selecionar_linhas_para_reclassificar,
    selecionar_transacoes_de_transporte,
)
from utils.category_analysis import preparar_dados_analise_categorias
from utils.error_handling import mostrar_erro_seguro
from utils.formatting import formatar_brl
from utils.gemini_client import (
    criar_cliente_gemini,
    gerar_conteudo_gemini as gerar_com_cliente_gemini,
)
from utils.history import formatar_linha_historico
from utils.import_workflow import processar_importacao_homologada
from utils.manual_entry import preparar_transacao_manual
from utils.goals import calcular_status_meta
from utils.oracle_analysis import (
    montar_payload_feedback_oraculo,
    montar_prompt_oraculo,
    reforcar_prompt_oraculo,
    resposta_oraculo_tem_secoes,
)
from utils.privacy import anonimizar_dados
from utils.trends import TENDENCIA_SEM_HISTORICO, calcular_textos_tendencia
import pandas as pd
import plotly.express as px

logger = logging.getLogger(__name__)


# Configuração da página em modo WIDE para melhor aproveitamento do espaço visual
st.set_page_config(page_title="Finanças Pro IA", page_icon="💰", layout="wide")

try:
    validar_chave_publica_supabase(st.secrets["SUPABASE_KEY"])
except Exception:
    logger.critical("Chave Supabase insegura ou invalida configurada", exc_info=True)
    st.error("A configuracao de acesso ao Supabase e insegura ou invalida.")
    st.stop()

# ==========================================
# ⚡ CAMADA DE CACHE INDUSTRIAL (PERFORMANCE)
# ==========================================
@st.cache_resource
def obter_cliente_gemini():
    """Cria o cliente Gemini somente quando um recurso de IA e acionado."""
    chave = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    if not chave:
        raise RuntimeError("GEMINI_API_KEY nao configurada")
    return criar_cliente_gemini(chave)


def gerar_conteudo_gemini(*, tentativas=3, **kwargs):
    return gerar_com_cliente_gemini(
        obter_cliente_gemini(),
        tentativas=tentativas,
        **kwargs,
    )

inicializar_estado_sessao()

if st.session_state.autenticado:
    identidade_revalidada = validar_sessao_atual()
    if not identidade_revalidada:
        limpar_sessao_usuario()
        st.session_state.autenticado = False
        st.session_state.tela_atual = "login"
        st.session_state.aviso_sessao = (
            "Sua sessao expirou ou foi revogada. Entre novamente para continuar."
        )
        st.rerun()
    else:
        st.session_state.usuario_id = identidade_revalidada["id"]
        st.session_state.usuario_email = identidade_revalidada["email"]

# ==========================================
# CONTROLADOR DE TELAS (LOGIN / CADASTRO)
# ==========================================
if aviso_sessao := st.session_state.pop("aviso_sessao", None):
    st.warning(aviso_sessao)

if not st.session_state.autenticado and st.session_state.tela_atual == "login":
    st.title("💰 Finanças Pro IA")
    st.subheader("Faça seu login para acessar o painel")
    with st.form("formulario_login"):
        email = st.text_input("E-mail").strip().lower()
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if email and senha:
                usuario_autenticado = fazer_login(email, senha)
                if usuario_autenticado:
                    iniciar_sessao_autenticada(
                        usuario_autenticado["email"],
                        usuario_autenticado["id"],
                    )
                    st.toast("Autenticação autorizada com sucesso!", icon="🔐")
                    st.rerun()
                else: 
                    st.error(
                        "E-mail ou senha incorretos. Se você acabou de criar a conta, "
                        "confirme o e-mail de confirmação antes de entrar."
                    )
            else: 
                st.warning("Por favor, preencha todos os campos.")
    if st.button("Não tem uma conta? Cadastre-se aqui"):
        st.session_state.tela_atual = "cadastro"
        st.rerun()
    if st.button("Esqueci minha senha"):
        st.session_state.tela_atual = "recuperar_senha"
        st.rerun()

elif not st.session_state.autenticado and st.session_state.tela_atual == "recuperar_senha":
    st.title("Recuperar senha")
    st.caption(
        "Informe o e-mail da sua conta. Se ele estiver cadastrado, enviaremos "
        "as instruções de redefinição."
    )
    with st.form("formulario_recuperacao_senha"):
        email_recuperacao = st.text_input("E-mail").strip().lower()
        if st.form_submit_button("Enviar instruções"):
            if email_recuperacao:
                if enviar_email_recuperacao_senha(email_recuperacao):
                    st.success(
                        "Se houver uma conta associada a este e-mail, você receberá "
                        "as instruções de recuperação em alguns minutos."
                    )
                else:
                    st.error(
                        "Não foi possível solicitar a recuperação agora. "
                        "Tente novamente em alguns minutos."
                    )
            else:
                st.warning("Informe seu e-mail para continuar.")
    if st.button("Voltar para o login"):
        st.session_state.tela_atual = "login"
        st.rerun()

elif not st.session_state.autenticado and st.session_state.tela_atual == "cadastro":
    st.title("📝 Criar Nova Conta")
    with st.form("formulario_cadastro"):
        novo_email = st.text_input("E-mail").strip().lower()
        nova_senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirme a Senha", type="password")
        if st.form_submit_button("Criar Conta"):
            if novo_email and nova_senha and confirmar_senha:
                if nova_senha == confirmar_senha:
                    if len(nova_senha) < 10:
                        st.error("A senha deve ter pelo menos 10 caracteres.")
                    else:
                        resultado = cadastrar_usuario(novo_email, nova_senha)
                        if resultado == "existe": 
                            st.error("Esse e-mail já está cadastrado!")
                        elif resultado == "confirmar_email":
                            st.session_state.aviso_sessao = (
                                "Conta criada! Verifique sua caixa de entrada ou spam, "
                                "confirme o e-mail de confirmação e depois entre com seu e-mail e senha."
                            )
                            st.session_state.tela_atual = "login"
                            st.rerun()
                        elif resultado is True:
                            st.success("Conta criada! Redirecionando...")
                            st.session_state.tela_atual = "login"
                            st.rerun()
                else: 
                    st.error("As senhas não coincidem.")
            else: 
                st.warning("Preencha todos os campos.")
    if st.button("Já tem uma conta? Voltar para o Login"):
        st.session_state.tela_atual = "login"
        st.rerun()

# ==========================================
# PAINEL CORE DO SAAS (AUTENTICADO)
# ==========================================
elif st.session_state.autenticado:
    email_usuario = st.session_state.usuario_email
    usuario_id = st.session_state.usuario_id

    try:
        lista_total_banco = listar_transacoes_usuario(usuario_id)
    except Exception as e_fetch:
        msg = mostrar_erro_seguro(e_fetch, email_usuario)
        st.error(msg)
        lista_total_banco = []

    st.sidebar.title("Navegação")
    st.sidebar.write(f"Usuário ativo: **{email_usuario}**")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("➕ Lançamento Manual")
    tipo_transacao = st.sidebar.selectbox(
        "Tipo",
        TIPOS_TRANSACAO,
        key="tipo_transacao_manual",
    )
    with st.sidebar.form("form_transacao", clear_on_submit=True):
        desc = st.text_input("Descrição (Ex: Uber)")
        val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        categorias_manuais = (
            CATEGORIAS_RECEITA if tipo_transacao == TIPO_RECEITA else CATEGORIAS_DESPESA
        )
        cat_manual = st.selectbox(
            "Categoria",
            categorias_manuais,
            key=f"categoria_manual_{tipo_transacao.lower()}",
        )
        
        ano_atual = datetime.datetime.now().year
        meses_ano = [f"{m:02d}/{ano_atual}" for m in range(1, 13)]
        mes_manual = st.selectbox("Mês de Referência", meses_ano, index=datetime.datetime.now().month - 1)
        banco_manual = st.text_input("Instituição (Opcional)", value=ORIGEM_MANUAL).strip()
        
        if st.form_submit_button("Salvar Lançamento"):
            if desc and val > 0:
                try:
                    if not mes_referencia_valido(mes_manual):
                        st.error("Formato do mês de referência inválido.")
                    else:
                        inserir_transacao(
                            preparar_transacao_manual(
                                descricao=desc,
                                valor=val,
                                tipo_transacao=tipo_transacao,
                                categoria=cat_manual,
                                categorias_validas=categorias_manuais,
                                mes_referencia=mes_manual,
                                instituicao=banco_manual,
                                usuario_id=usuario_id,
                                email_usuario=email_usuario,
                            )
                        )
                        st.toast("Lançamento computado com sucesso!", icon="✅")
                        st.rerun()
                except Exception as e_insert:
                    msg = mostrar_erro_seguro(e_insert, email_usuario)
                    st.error(msg)

    if eh_usuario_admin(email_usuario, st.secrets.get("ADMIN_EMAILS", [])):
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Painel do Desenvolvedor")
        
        if st.sidebar.button("🪄 Corrigir Histórico Retroativo"):
            if not lista_total_banco:
                st.sidebar.warning("Nenhum dado encontrado para higienização.")
            else:
                with st.spinner("Higienizando e processando lote via inteligência analítica..."):
                    try:
                        for item in selecionar_transacoes_de_transporte(lista_total_banco):
                            atualizar_categoria_transacao(item["id"], CATEGORIA_TRANSPORTE)

                        linhas_para_atualizar = selecionar_linhas_para_reclassificar(
                            lista_total_banco
                        )
                        
                        if lines_to_fix := extrair_descricoes_para_reclassificar(linhas_para_atualizar):
                            prompt_lote = montar_prompt_reclassificacao_categorias(lines_to_fix)
                            response_batch = gerar_conteudo_gemini(model='gemini-2.5-flash', contents=prompt_lote, config=types.GenerateContentConfig(response_mime_type="application/json"))
                            mapa_categorias = carregar_mapa_reclassificacao(response_batch.text)
                            
                            for item_id, categoria in preparar_atualizacoes_reclassificacao(
                                linhas_para_atualizar,
                                mapa_categorias,
                            ):
                                atualizar_categoria_transacao(item_id, categoria)
                            
                        st.sidebar.success("Histórico totalmente saneado!")
                        st.rerun()
                    except Exception as ex:
                        msg = mostrar_erro_seguro(ex, email_usuario)
                        st.sidebar.error(msg)

    st.sidebar.markdown("---")
    if st.sidebar.button("Sair / Logout"):
        encerrar_sessao_usuario()
        st.rerun()

    if eh_usuario_admin(email_usuario, st.secrets.get("ADMIN_EMAILS", [])):
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛡️ Status da Infraestrutura")
        with st.sidebar.container():
            status_infra = auditar_saude_plataforma()
            st.sidebar.markdown(f"● **Banco Supabase:** {status_infra['supabase']}")
            st.sidebar.markdown(f"● **Criptografia/SSL:** {status_infra['seguranca']}")

    st.title("📊 Painel de Controle Financeiro Inteligente")
    st.markdown("### 🤖 Importação Inteligente por IA (Premium)")
    arquivo_subido = st.file_uploader("Suba aqui o seu extrato bancário, fatura ou comprovante em formato PDF", type=["pdf"])
    consentimento_pdf_ia = st.checkbox(
        "Autorizo o envio temporário deste PDF ao Google Gemini para extração dos dados.",
        help="O documento pode conter informações financeiras sensíveis. Envie somente se concordar com o processamento externo.",
    )

    if eh_usuario_admin(email_usuario, st.secrets.get("ADMIN_EMAILS", [])):
        with st.expander("🧪 Modo de teste sem Gemini"):
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

    if arquivo_subido is not None:
        if st.button("🪄 Extrair Dados com Gemini IA"):
            if not consentimento_pdf_ia:
                st.warning("Confirme a autorização de processamento externo antes de enviar o PDF.")
            else:
                with st.spinner("O parser de visão computacional da IA está varrendo o PDF..."):
                    try:
                        dados_pdf = arquivo_subido.read()
                        if len(dados_pdf) > 10 * 1024 * 1024:
                            raise ValueError("O PDF excede o limite de 10 MB.")

                        prompt_mestre = montar_prompt_extracao_pdf()
                        config_ia = montar_config_extracao_pdf(types)
                        response = gerar_conteudo_gemini(
                            model='gemini-2.5-flash',
                            contents=[types.Part.from_bytes(data=dados_pdf, mime_type='application/pdf'), prompt_mestre],
                            config=config_ia
                        )

                        resultado_ia = carregar_resultado_extracao(response.text)
                        st.session_state.dados_pre_visualizacao = normalizar_resultado_extracao(
                            resultado_ia,
                            pd.DataFrame,
                        )
                        st.toast("Extração contábil finalizada!", icon="🪄")
                    except Exception as erro:
                        msg = mostrar_erro_seguro(erro, email_usuario)
                        st.error(msg)

    if st.session_state.dados_pre_visualizacao is not None:
        st.markdown("---")
        st.subheader("📋 Área de Homologação e Pré-visualização Contábil")
        pre_vis = st.session_state.dados_pre_visualizacao
        mes_corrigido = st.text_input(
            "Mês de referência da importação (MM/AAAA)",
            value=str(pre_vis["mes_referencia"]),
            help="Confira este campo antes de salvar. Exemplo: 05/2026.",
        ).strip()
        pre_vis["mes_referencia"] = mes_corrigido
        
        c_meta1, c_meta2, c_meta3, c_meta4 = st.columns(4)
        with c_meta1: st.metric("🏦 Instituição Identificada", pre_vis["instituicao"])
        with c_meta2: st.metric("📄 Tipo de Documento", pre_vis["tipo_documento"])
        with c_meta3: st.metric("📅 Mês de Referência", pre_vis["mes_referencia"])
        with c_meta4: st.metric("💰 Total Declarado Oficial", formatar_brl(pre_vis["total_documento"]))
            
        df_editavel = st.data_editor(
            pre_vis["df_transacoes"],
            column_config={
                "descricao": st.column_config.TextColumn("Descrição da Transação", disabled=True, width="medium"),
                "valor": st.column_config.NumberColumn("Valor (R$)", disabled=True, format="R$ %.2f"),
                "tipo": st.column_config.SelectboxColumn("Fluxo", options=TIPOS_TRANSACAO, required=True),
                "categoria": st.column_config.SelectboxColumn("Classificação IA", options=CATEGORIAS_VALIDAS, required=True)
            },
            hide_index=True,
            use_container_width=True,
            key="staging_data_editor"
        )
        
        col_btn1, col_btn2, _ = st.columns([15, 15, 70])
        with col_btn1:
            if st.button("💾 Confirmar e Salvar no Supabase", type="primary", use_container_width=True):
                with st.spinner("Consolidando dados no Supabase..."):
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
                            
                        st.toast("Registros integrados com sucesso!", icon="⚡")
                        st.session_state.dados_pre_visualizacao = None
                        st.rerun()
                    except Exception as e_save:
                        msg = mostrar_erro_seguro(e_save, email_usuario)
                        st.error(msg)
                        
        with col_btn2:
            if st.button("❌ Descartar Importação", use_container_width=True):
                st.session_state.dados_pre_visualizacao = None
                st.rerun()

    st.markdown("---")

    meses_disponiveis = ordenar_meses_cronologicamente(
        [t.get("mes_referencia") for t in lista_total_banco]
    )
    if lista_total_banco:
        if meses_disponiveis:
            st.markdown("### 📅 Escolha o Mês de Visualização")
            mes_selecionado = st.selectbox("Filtrar Painel por Mês:", meses_disponiveis)
            lista_transacoes = [t for t in lista_total_banco if t.get("mes_referencia") == mes_selecionado]
        else:
            lista_transacoes = lista_total_banco
            mes_selecionado = "Geral"
    else:
        lista_transacoes, mes_selecionado = [], None

    if lista_transacoes:
        df_mes = pd.DataFrame(lista_transacoes)
        resumo_mes = calcular_resumo_financeiro(lista_transacoes)
        total_compras = resumo_mes["despesas"]
        total_pagamentos = resumo_mes["receitas"]
        valor_balanco_final = resumo_mes["balanco"]

        txt_tendencia_gastos = txt_tendencia_pagamentos = txt_tendencia_balanco = TENDENCIA_SEM_HISTORICO

        if mes_selecionado and mes_selecionado in meses_disponiveis:
            idx_atual = meses_disponiveis.index(mes_selecionado)
            if idx_atual + 1 < len(meses_disponiveis):
                mes_anterior = meses_disponiveis[idx_atual + 1]
                lista_anterior = [t for t in lista_total_banco if t.get("mes_referencia") == mes_anterior]
                
                if lista_anterior:
                    try:
                        resumo_anterior = calcular_resumo_financeiro(lista_anterior)
                        txt_tendencia_gastos, txt_tendencia_pagamentos, txt_tendencia_balanco = calcular_textos_tendencia(
                            resumo_mes,
                            resumo_anterior,
                        )
                    except Exception as e_trend:
                        msg = mostrar_erro_seguro(e_trend, email_usuario)
                        st.error(msg)

        card_html_estrutura = f"""
        <div style="display: flex; gap: 24px; width: 100%; margin-bottom: 25px;">
            <div style="flex: 1; background: linear-gradient(145deg, #1e1e24, #141418); padding: 22px 24px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 125px;">
                <div>
                    <div style="color: #a1a1aa; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">💳 Total de Gastos</div>
                    <div style="color: #ffffff; font-size: 30px; font-weight: 800; margin-top: 6px;">{formatar_brl(total_compras)}</div>
                </div>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.03);">{txt_tendencia_gastos} <span style="color:#71717a; font-size:12px;">vs mês anterior</span></div>
            </div>
            <div style="flex: 1; background: linear-gradient(145deg, #1e1e24, #141418); padding: 22px 24px; border-radius: 16px; border: 1px solid rgba(163, 184, 153, 0.15); display: flex; flex-direction: column; justify-content: space-between; min-height: 125px;">
                <div>
                    <div style="color: #a3b899; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">💰 Pagamentos / Créditos</div>
                    <div style="color: #a3b899; font-size: 30px; font-weight: 800; margin-top: 6px;">{formatar_brl(total_pagamentos)}</div>
                </div>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(163, 184, 153, 0.03);">{txt_tendencia_pagamentos} <span style="color:#71717a; font-size:12px;">vs mês anterior</span></div>
            </div>
            <div style="flex: 1; background: linear-gradient(145deg, #1e1e24, #141418); padding: 22px 24px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 125px;">
                <div>
                    <div style="color: #a1a1aa; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">🧾 Balanço Real Consolidado</div>
                    <div style="color: #ffffff; font-size: 30px; font-weight: 800; margin-top: 6px;">{formatar_brl(valor_balanco_final)}</div>
                </div>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.03);">{txt_tendencia_balanco} <span style="color:#71717a; font-size:12px;">vs mês anterior</span></div>
            </div>
        </div>
        """
        st.markdown(card_html_estrutura, unsafe_allow_html=True)
        st.markdown("---")

        if mes_selecionado:
            st.subheader(f"🎯 Gestão de Metas de Limite Comportamental ({mes_selecionado})")
            try:
                with st.expander("⚙️ Definir ou Ajustar Teto de Gasto por Grupo"):
                    col_m1, col_m2, col_m3 = st.columns([40, 40, 20])
                    with col_m1: cat_meta_sel = st.selectbox("Escolha a Categoria:", CATEGORIAS_DESPESA, key="cat_meta")
                    with col_m2: valor_meta_sel = st.number_input("Teto Limite Desejado (R$):", min_value=0.0, format="%.2f", key="val_meta")
                    with col_m3:
                        st.write("<br>", unsafe_allow_html=True)
                        if st.button("Definir Meta", use_container_width=True):
                            try:
                                salvar_meta_financeira({
                                    "user_id": usuario_id, "usuario_email": email_usuario, "categoria": cat_meta_sel, "mes_referencia": mes_selecionado, "valor_meta": valor_meta_sel
                                })
                                st.toast(f"Meta de {cat_meta_sel} salva!", icon="🎯")
                                st.rerun()
                            except Exception as e_upsert:
                                msg = mostrar_erro_seguro(e_upsert, email_usuario)
                                st.error(msg)
                
                metas_usuario = listar_metas_usuario_mes(usuario_id, mes_selecionado)
                dict_metas = {m["categoria"]: float(m["valor_meta"]) for m in metas_usuario}
                df_despesas = df_mes[df_mes["tipo"] == TIPO_DESPESA]
                
                for cat in CATEGORIAS_DESPESA:
                    gasto_atual = df_despesas[df_despesas["categoria"] == cat]["valor"].sum() if not df_despesas.empty else 0.0
                    meta_cadastrada = dict_metas.get(cat, 0.0)
                    
                    if meta_cadastrada > 0:
                        pct, cor_barra, txt_status = calcular_status_meta(
                            gasto_atual,
                            meta_cadastrada,
                        )
                        
                        st.markdown(f"**{cat}** | Gasto: {formatar_brl(gasto_atual)} de Meta: {formatar_brl(meta_cadastrada)} ({pct*100:.1f}%)")
                        st.progress(min(pct, 1.0))
                        st.markdown(f"<small style='color:{cor_barra}; font-weight:600;'>{txt_status}</small><br><br>", unsafe_allow_html=True)
            except Exception as e_metas:
                msg_metas = mostrar_erro_seguro(e_metas, email_usuario)
                st.info(msg_metas)

            st.markdown("---")

        st.subheader(f"📊 Central de Análise de Grupos ({mes_selecionado})")
        df_despesas = df_mes[df_mes["tipo"] == TIPO_DESPESA]
        
        if not df_despesas.empty:
            try:
                col_grafico, col_subtotais = st.columns([50, 50])
                with col_grafico:
                    df_agrupado, subtotais_categorias = preparar_dados_analise_categorias(
                        df_mes,
                        df_despesas,
                        CATEGORIAS_DESPESA,
                    )
                    fig_barras = px.bar(df_agrupado, x="Total (R$)", y="Categoria", orientation="h", text="Total (R$)", color="Total (R$)", color_continuous_scale="Plotly3")
                    fig_barras.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside', cliponaxis=False, marker_line_width=0, hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
                    fig_barras.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=40), height=380, xaxis=dict(showgrid=False, title="", showticklabels=False, fixedrange=True), yaxis=dict(title="", tickfont=dict(size=12, color="#a1a1aa"), fixedrange=True), coloraxis_showscale=False, dragmode=False)
                    st.plotly_chart(fig_barras, use_container_width=True, config={'displayModeBar': False})
                
                with col_subtotais:
                    for cat, v_cat in subtotais_categorias:
                        st.markdown(f"""
                        <div style="background: linear-gradient(90deg, #16161a, #1a1a22); padding: 11px 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); margin-bottom: 7px; display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #a1a1aa; font-size: 13px; font-weight: 600; text-transform: uppercase;">{cat}</span>
                            <span style="color: #ffffff; font-size: 15px; font-weight: 700;">{formatar_brl(v_cat)}</span>
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e_plots:
                msg_plots = mostrar_erro_seguro(e_plots, email_usuario)
                st.error(msg_plots)
        else:
            st.info("Nenhuma despesa para plotagem de gráficos.")

        st.markdown("---")

        st.subheader("🕵️‍♂️ Central de Auditoria Contábil")
        for cat in CATEGORIAS_DESPESA:
            try:
                df_exibicao = preparar_dataframe_auditoria_categoria(df_mes, cat)
                if not df_exibicao.empty:
                    with st.expander(f"📁 Linhas Auditadas de '{cat}' ({len(df_exibicao)} itens)"):
                        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
                else:
                    with st.expander(f"📁 Linhas Auditadas de '{cat}' (Zerado)"):
                        st.info(f"Nenhum gasto classificado em {cat} para este período.")
            except Exception as e_audit:
                msg_audit = mostrar_erro_seguro(e_audit, email_usuario)
                st.error(msg_audit)

        st.markdown("---")
        st.subheader(f"📋 Histórico Geral de Movimentações de {mes_selecionado}")
        for t in reversed(lista_transacoes):
            st.markdown(formatar_linha_historico(t))
    else:
        st.info("Nenhum dado disponível. Adicione lançamentos manuais ou suba um PDF.")

    st.markdown("---")
    
    st.title("🔮 Oráculo IA - Análise Preditiva e Saúde Financeira")
    st.caption("A análise envia somente totais agregados por mês e categoria, sem descrições de transações.")
    col_gatilho, _ = st.columns([3, 7])
    with col_gatilho:
        ativar_oraculo = st.button("🧠 Ativar Inteligência Preditiva", use_container_width=True)

    if ativar_oraculo:
        if not lista_total_banco:
            st.warning("Histórico de transações necessário para análise preditiva.")
        else:
            with st.spinner("O Oráculo está consolidando o relatório comportamental..."):
                try:
                    st.session_state.feedback_enviado = False
                    historico_formatado = resumir_historico_para_ia(lista_total_banco)
                    
                    st.session_state.historico_oraculo_enviado = historico_formatado
                    prompt_oraculo = montar_prompt_oraculo(historico_formatado)
                    
                    resposta_oraculo = gerar_conteudo_gemini(model='gemini-2.5-flash', contents=prompt_oraculo, config=types.GenerateContentConfig(temperature=0.1))
                    texto_final = resposta_oraculo.text
                    
                    if not resposta_oraculo_tem_secoes(texto_final):
                        resposta_oraculo = gerar_conteudo_gemini(model='gemini-2.5-flash', contents=reforcar_prompt_oraculo(prompt_oraculo), config=types.GenerateContentConfig(temperature=0.0))
                        texto_final = resposta_oraculo.text
                    
                    st.session_state.resposta_oraculo_texto = texto_final
                except Exception as e:
                    msg_oraculo = mostrar_erro_seguro(e, email_usuario)
                    st.error(msg_oraculo)

    if st.session_state.resposta_oraculo_texto:
        st.markdown("---")
        st.success("✨ Relatório Preditivo Gerado com Sucesso!")
        st.markdown(st.session_state.resposta_oraculo_texto)
        
        st.markdown("##### 📢 Avalie essa resposta da IA para calibragem do sistema:")
        col_fb1, col_fb2, _ = st.columns([1.5, 2, 6.5])
        
        if not st.session_state.feedback_enviado:
            with col_fb1:
                if st.button("👍 Ficou Top", use_container_width=True):
                    try:
                        salvar_feedback_oraculo(
                            montar_payload_feedback_oraculo(
                                usuario_id=usuario_id,
                                email_usuario=email_usuario,
                                status_resposta="TOP",
                                resposta_ia=st.session_state.resposta_oraculo_texto,
                                dados_enviados=st.session_state.historico_oraculo_enviado,
                                anonimizar=anonimizar_dados,
                            )
                        )
                        st.session_state.feedback_enviado = True
                        st.rerun()
                    except Exception as err: 
                        msg_fb1 = mostrar_erro_seguro(err, email_usuario)
                        st.error(msg_fb1)
            with col_fb2:
                if st.button("👎 Resposta Ruim/Falsa", use_container_width=True):
                    try:
                        salvar_feedback_oraculo(
                            montar_payload_feedback_oraculo(
                                usuario_id=usuario_id,
                                email_usuario=email_usuario,
                                status_resposta="RUIM",
                                resposta_ia=st.session_state.resposta_oraculo_texto,
                                dados_enviados=st.session_state.historico_oraculo_enviado,
                                anonimizar=anonimizar_dados,
                            )
                        )
                        st.session_state.feedback_enviado = True
                        st.rerun()
                    except Exception as err: 
                        msg_fb2 = mostrar_erro_seguro(err, email_usuario)
                        st.error(msg_fb2)
        else:
            st.info("🎯 Obrigado pelo feedback! Dados salvos na tabela 'feedbacks_oraculo'.")
