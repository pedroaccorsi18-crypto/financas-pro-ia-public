import streamlit as st
import json
import datetime
import logging
from google import genai
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
    ORIGEM_AUTOMATICA,
    ORIGEM_MANUAL,
    TIPO_DESPESA,
    TIPO_DOCUMENTO_MANUAL,
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
from utils.bot_fiscal import disparar_bot_fiscal_email
from utils.error_handling import mostrar_erro_seguro
from utils.formatting import formatar_brl
from utils.gemini_client import gerar_conteudo_gemini as gerar_com_cliente_gemini
from utils.privacy import anonimizar_dados
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
    return genai.Client(
        api_key=chave,
        http_options={"headers": {"x-goog-api-key": chave}},
    )


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
                        inserir_transacao({
                            "user_id": usuario_id,
                            "usuario_email": email_usuario, 
                            "descricao": desc.strip(), 
                            "valor": float(val), 
                            "tipo": tipo_transacao,
                            "categoria": cat_manual if cat_manual in categorias_manuais else categorias_manuais[-1],
                            "mes_referencia": mes_manual,
                            "meta_fatura": 0.0,
                            "instituicao_financeira": banco_manual.strip() if banco_manual else ORIGEM_MANUAL,
                            "tipo_documento": TIPO_DOCUMENTO_MANUAL,
                            "origem_importacao": ORIGEM_MANUAL
                        })
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
                        for item in lista_total_banco:
                            desc_lower = item.get("descricao", "").lower()
                            if any(k in desc_lower for k in ["pmbmetro", "metro", "cptm", "autopass"]):
                                if item.get("categoria") != "Transporte":
                                    atualizar_categoria_transacao(item["id"], "Transporte")

                        linhas_para_atualizar = [t for t in lista_total_banco if t.get("categoria") in ["Compras & Assinaturas", "Geral", None] and t.get("descricao")]
                        
                        if lines_to_fix := [l["descricao"] for l in linhas_para_atualizar]:
                            prompt_lote = (
                                f"Classifique estritamente cada item da lista abaixo nas seguintes categorias permitidas:\n{str(CATEGORIAS_VALIDAS)}\n\n"
                                f"LISTA DE ITENS:\n{json.dumps(lines_to_fix)}\n\n"
                                "Retorne a resposta estritamente em um JSON plano no formato: {\"item_descricao\": \"Categoria\"}"
                            )
                            response_batch = gerar_conteudo_gemini(model='gemini-2.5-flash', contents=prompt_lote, config=types.GenerateContentConfig(response_mime_type="application/json"))
                            mapa_categorias = json.loads(response_batch.text.strip())
                            
                            for item in linhas_para_atualizar:
                                cat_inferida = mapa_categorias.get(item["descricao"], "Compras Gerais")
                                if cat_inferida not in CATEGORIAS_VALIDAS:
                                    cat_inferida = "Compras Gerais"
                                atualizar_categoria_transacao(item["id"], cat_inferida)
                            
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

                        prompt_mestre = (
                            "Você é um extrator de dados contábeis de altíssima precisão. Sua meta é extrair transações de faturas ou extratos com temperatura zero.\n"
                            "O campo 'mes_fatura' deve obrigatoriamente usar o formato MM/AAAA, por exemplo 05/2026.\n"
                            "Gere um JSON estrito contendo um único objeto com os campos: 'instituicao_financeira', 'tipo_documento', 'total_documento', 'mes_fatura' e a lista 'transacoes' (descricao, valor, tipo, categoria)."
                        )
                        esquema_json = types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "instituicao_financeira": types.Schema(type=types.Type.STRING),
                                "tipo_documento": types.Schema(type=types.Type.STRING, enum=["Fatura de Cartão", "Extrato Bancário", "Comprovante", "Outro"]),
                                "total_documento": types.Schema(type=types.Type.NUMBER),
                                "mes_fatura": types.Schema(type=types.Type.STRING, description="Mês no formato MM/AAAA"),
                                "transacoes": types.Schema(
                                    type=types.Type.ARRAY,
                                    items=types.Schema(
                                        type=types.Type.OBJECT,
                                        properties={
                                            "descricao": types.Schema(type=types.Type.STRING),
                                            "valor": types.Schema(type=types.Type.NUMBER),
                                            "tipo": types.Schema(type=types.Type.STRING, enum=TIPOS_TRANSACAO),
                                            "categoria": types.Schema(type=types.Type.STRING, enum=CATEGORIAS_VALIDAS),
                                        },
                                        required=["descricao", "valor", "tipo", "categoria"],
                                    ),
                                )
                            },
                            required=["instituicao_financeira", "tipo_documento", "total_documento", "mes_fatura", "transacoes"]
                        )
                        config_ia = types.GenerateContentConfig(response_mime_type="application/json", response_schema=esquema_json, temperature=0.0)
                        response = gerar_conteudo_gemini(
                            model='gemini-2.5-flash',
                            contents=[genai.types.Part.from_bytes(data=dados_pdf, mime_type='application/pdf'), prompt_mestre],
                            config=config_ia
                        )

                        resultado_ia = json.loads(response.text.strip())
                        st.session_state.dados_pre_visualizacao = {
                            "instituicao": resultado_ia["instituicao_financeira"],
                            "tipo_documento": resultado_ia["tipo_documento"],
                            "mes_referencia": resultado_ia["mes_fatura"],
                            "total_documento": float(resultado_ia["total_documento"]) if resultado_ia["total_documento"] else 0.0,
                            "df_transacoes": pd.DataFrame(resultado_ia["transacoes"])
                        }
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
                        if not pre_vis["instituicao"] or str(pre_vis["instituicao"]).strip() == "":
                            raise ValueError("A identificação da instituição financeira não pode estar vazia.")
                        
                        if not mes_referencia_valido(str(pre_vis["mes_referencia"])):
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
                                
                            if any(k in desc_original.lower() for k in ["pmbmetro", "metro", "cptm", "autopass"]):
                                categoria_final = "Transporte"
                                
                            if tipo_final == TIPO_DESPESA: gastos_reais += val_item
                            else: creditos_reais += val_item
                            
                            transacoes_para_inserir.append({
                                "user_id": usuario_id, "usuario_email": email_usuario, "descricao": desc_original, "valor": val_item, "tipo": tipo_final,
                                "categoria": categoria_final, "mes_referencia": pre_vis["mes_referencia"].strip(), "meta_fatura": pre_vis["total_documento"],
                                "instituicao_financeira": pre_vis["instituicao"].strip(), "tipo_documento": pre_vis["tipo_documento"], "origem_importacao": ORIGEM_AUTOMATICA
                            })
                            
                        if transacoes_para_inserir:
                            lote_existente = buscar_lote_importado(
                                usuario_id=usuario_id,
                                mes_referencia=pre_vis["mes_referencia"].strip(),
                                instituicao_financeira=pre_vis["instituicao"].strip(),
                                tipo_documento=pre_vis["tipo_documento"],
                            )

                            if not lotes_sao_iguais(transacoes_para_inserir, lote_existente):
                                substituir_lote_importado(
                                    usuario_id=usuario_id,
                                    mes_referencia=pre_vis["mes_referencia"].strip(),
                                    instituicao_financeira=pre_vis["instituicao"].strip(),
                                    tipo_documento=pre_vis["tipo_documento"],
                                    transacoes=transacoes_para_inserir,
                                )

                        if pre_vis["total_documento"] > 0:
                            disparar_bot_fiscal_email(st.secrets, email_usuario, pre_vis["instituicao"], pre_vis["tipo_documento"], pre_vis["mes_referencia"], gastos_reais, creditos_reais, pre_vis["total_documento"])
                            
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

        txt_tendencia_gastos = txt_tendencia_pagamentos = txt_tendencia_balanco = '<span style="color: #a1a1aa; font-size: 12px; font-weight: 500;">• Sem histórico base</span>'

        if mes_selecionado and mes_selecionado in meses_disponiveis:
            idx_atual = meses_disponiveis.index(mes_selecionado)
            if idx_atual + 1 < len(meses_disponiveis):
                mes_anterior = meses_disponiveis[idx_atual + 1]
                lista_anterior = [t for t in lista_total_banco if t.get("mes_referencia") == mes_anterior]
                
                if lista_anterior:
                    try:
                        resumo_anterior = calcular_resumo_financeiro(lista_anterior)
                        gastos_ant = resumo_anterior["despesas"]
                        pag_ant = resumo_anterior["receitas"]
                        bal_ant = resumo_anterior["balanco"]
                        
                        if gastos_ant > 0:
                            var_gastos = ((total_compras - gastos_ant) / gastos_ant) * 100
                            txt_tendencia_gastos = f'<span style="color: #a3b899; font-size: 12px; font-weight: 600;">▼ {abs(var_gastos):.1f}%</span>' if var_gastos < 0 else f'<span style="color: #ef4444; font-size: 12px; font-weight: 600;">▲ {var_gastos:.1f}%</span>'
                        if pag_ant > 0:
                            var_pag = ((total_pagamentos - pag_ant) / pag_ant) * 100
                            txt_tendencia_pagamentos = f'<span style="color: #a3b899; font-size: 12px; font-weight: 600;">▲ {var_pag:.1f}%</span>' if var_pag > 0 else f'<span style="color: #ef4444; font-size: 12px; font-weight: 600;">▼ {abs(var_pag):.1f}%</span>'
                        if bal_ant > 0:
                            var_bal = ((valor_balanco_final - bal_ant) / bal_ant) * 100
                            txt_tendencia_balanco = f'<span style="color: #a3b899; font-size: 12px; font-weight: 600;">▲ {var_bal:.1f}%</span>' if var_bal > 0 else f'<span style="color: #ef4444; font-size: 12px; font-weight: 600;">▼ {abs(var_bal):.1f}%</span>'
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
                        pct = (gasto_atual / meta_cadastrada)
                        restante = meta_cadastrada - gasto_atual
                        if pct >= 1.0:
                            cor_barra, txt_status = "red", f"🚨 Orçamento Estourado por {formatar_brl(abs(restante))}!"
                        elif pct >= 0.8:
                            cor_barra, txt_status = "orange", f"⚠️ Atenção! Você consumiu {pct*100:.1f}% do teto. Restam {formatar_brl(restante)}."
                        else:
                            cor_barra, txt_status = "green", f"✅ Sob Controle. Restam {formatar_brl(restante)} disponíveis."
                        
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
                    df_agrupado = df_despesas.groupby("categoria")["valor"].sum().reset_index().sort_values(by="valor", ascending=True)
                    df_agrupado = df_agrupado.rename(columns={"categoria": "Categoria", "valor": "Total (R$)"})
                    fig_barras = px.bar(df_agrupado, x="Total (R$)", y="Categoria", orientation="h", text="Total (R$)", color="Total (R$)", color_continuous_scale="Plotly3")
                    fig_barras.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside', cliponaxis=False, marker_line_width=0, hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
                    fig_barras.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=40), height=380, xaxis=dict(showgrid=False, title="", showticklabels=False, fixedrange=True), yaxis=dict(title="", tickfont=dict(size=12, color="#a1a1aa"), fixedrange=True), coloraxis_showscale=False, dragmode=False)
                    st.plotly_chart(fig_barras, use_container_width=True, config={'displayModeBar': False})
                
                with col_subtotais:
                    df_ordenado_lista = df_despesas.groupby("categoria")["valor"].sum().sort_values(ascending=False).reset_index()
                    todas_categorias_ordenadas = df_ordenado_lista["categoria"].tolist()
                    for c in CATEGORIAS_DESPESA:
                        if c not in todas_categorias_ordenadas: todas_categorias_ordenadas.append(c)
                    
                    for cat in todas_categorias_ordenadas:
                        v_cat = df_mes[(df_mes["categoria"] == cat) & (df_mes["tipo"] == TIPO_DESPESA)]["valor"].sum()
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
                df_filtrado_categoria = df_mes[(df_mes["categoria"] == cat) & (df_mes["tipo"] == TIPO_DESPESA)][["descricao", "valor", "instituicao_financeira", "origem_importacao"]]
                if not df_filtrado_categoria.empty:
                    df_exibicao = df_filtrado_categoria.rename(columns={"descricao": "Estabelecimento / Compra", "valor": "Valor (R$)", "instituicao_financeira": "Banco/Cartão", "origem_importacao": "Origem"})
                    with st.expander(f"📁 Linhas Auditadas de '{cat}' ({len(df_filtrado_categoria)} itens)"):
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
            cor = "🟢" if t["tipo"] == TIPO_RECEITA else "🔴"
            status_tipo = "Entrada" if t["tipo"] == TIPO_RECEITA else "Saída"
            banco_tag = t.get("instituicao_financeira", ORIGEM_MANUAL)
            origem_label = "✍️" if t.get("origem_importacao") == ORIGEM_MANUAL else "🤖"
            categoria_tag = f" [{t.get('categoria', 'Geral')}]" if t["tipo"] == TIPO_DESPESA else ""
            st.markdown(f"{cor} **{t['descricao']}**{categoria_tag} | {formatar_brl(t['valor'])} ({status_tipo} | {origem_label} {banco_tag})")
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
                    prompt_oraculo = (
                        "Você é um cientista de dados e mentor comportamental financeiro.\n"
                        f"Gere um relatório perspicaz baseado nas movimentações:\n{historico_formatado}\n\n"
                        "ESTRUTURA OBRIGATÓRIA RIGOROSA:\n### 📊 1. Raio-X Comportamental\n### 📉 2. Tendências Preditivas\n### 📈 3. Plano de Evolução"
                    )
                    
                    resposta_oraculo = gerar_conteudo_gemini(model='gemini-2.5-flash', contents=prompt_oraculo, config=types.GenerateContentConfig(temperature=0.1))
                    texto_final = resposta_oraculo.text
                    
                    if not all(tag in texto_final for tag in ["Raio-X Comportamental", "Tendências Preditivas", "Plano de Evolução"]):
                        resposta_oraculo = gerar_conteudo_gemini(model='gemini-2.5-flash', contents=prompt_oraculo + "\nUse rigorosamente os cabeçalhos em '### '.", config=types.GenerateContentConfig(temperature=0.0))
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
                        salvar_feedback_oraculo({
                            "user_id": usuario_id, "usuario_email": email_usuario, "status_resposta": "TOP",
                            "resposta_ia": anonimizar_dados(st.session_state.resposta_oraculo_texto),
                            "dados_enviados": anonimizar_dados(st.session_state.historico_oraculo_enviado)
                        })
                        st.session_state.feedback_enviado = True
                        st.rerun()
                    except Exception as err: 
                        msg_fb1 = mostrar_erro_seguro(err, email_usuario)
                        st.error(msg_fb1)
            with col_fb2:
                if st.button("👎 Resposta Ruim/Falsa", use_container_width=True):
                    try:
                        salvar_feedback_oraculo({
                            "user_id": usuario_id, "usuario_email": email_usuario, "status_resposta": "RUIM",
                            "resposta_ia": anonimizar_dados(st.session_state.resposta_oraculo_texto),
                            "dados_enviados": anonimizar_dados(st.session_state.historico_oraculo_enviado)
                        })
                        st.session_state.feedback_enviado = True
                        st.rerun()
                    except Exception as err: 
                        msg_fb2 = mostrar_erro_seguro(err, email_usuario)
                        st.error(msg_fb2)
        else:
            st.info("🎯 Obrigado pelo feedback! Dados salvos na tabela 'feedbacks_oraculo'.")
