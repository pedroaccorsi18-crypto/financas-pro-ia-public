import base64
import json
import logging
import time

import streamlit as st
from supabase import Client, create_client
from utils.observability import fingerprint, registrar_evento


logger = logging.getLogger(__name__)
LIMITE_TENTATIVAS_LOGIN = 5
JANELA_TENTATIVAS_SEGUNDOS = 300
CHAVE_CLIENTE_SUPABASE_SESSAO = "_supabase_client"
CHAVE_CONFIG_SUPABASE_SESSAO = "_supabase_config"
CHAVE_TENTATIVAS_LOGIN = "tentativas_login_por_email"
CHAVE_LOGIN_BLOQUEADO = "login_bloqueado_por_tentativas"


def validar_chave_publica_supabase(chave: str) -> None:
    """Aceita somente publishable key moderna ou JWT legado com role anon."""
    chave_limpa = str(chave or "").strip()
    if chave_limpa.startswith("sb_publishable_"):
        return
    if chave_limpa.startswith("sb_secret_"):
        raise RuntimeError("A aplicacao nao pode usar uma chave secreta do Supabase.")

    partes = chave_limpa.split(".")
    if len(partes) != 3:
        raise RuntimeError("Configure uma chave publica/anon valida do Supabase.")

    try:
        payload_codificado = partes[1] + "=" * (-len(partes[1]) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(payload_codificado.encode("ascii")).decode("utf-8")
        )
    except (ValueError, UnicodeError, json.JSONDecodeError) as erro:
        raise RuntimeError("Configure uma chave publica/anon valida do Supabase.") from erro

    if payload.get("role") != "anon":
        raise RuntimeError("A aplicacao deve usar somente a chave anon/public do Supabase.")


def mostrar_erro_seguro(erro: Exception, email_usuario: str = None) -> str:
    logger.error(
        "Falha na aplicacao para usuario %s",
        email_usuario or "nao identificado",
        exc_info=True,
    )
    return "Ocorreu um problema interno ao processar sua requisicao. Tente novamente mais tarde."


def obter_conexao_supabase() -> Client:
    """Retorna um cliente exclusivo da sessao Streamlit atual."""
    url = st.secrets["SUPABASE_URL"]
    chave = st.secrets["SUPABASE_KEY"]
    config_atual = (url, chave)

    if (
        CHAVE_CLIENTE_SUPABASE_SESSAO not in st.session_state
        or st.session_state.get(CHAVE_CONFIG_SUPABASE_SESSAO) != config_atual
    ):
        validar_chave_publica_supabase(chave)
        st.session_state[CHAVE_CLIENTE_SUPABASE_SESSAO] = create_client(
            url,
            chave,
        )
        st.session_state[CHAVE_CONFIG_SUPABASE_SESSAO] = config_atual
    return st.session_state[CHAVE_CLIENTE_SUPABASE_SESSAO]


class ClienteSupabaseDaSessao:
    """Encaminha chamadas para o cliente autenticado da sessao atual."""

    def __getattr__(self, nome):
        return getattr(obter_conexao_supabase(), nome)


supabase = ClienteSupabaseDaSessao()


def cadastrar_usuario(email: str, senha: str) -> str | bool:
    """Cria uma identidade no Supabase Auth."""
    email_limpo = email.strip().lower()
    try:
        resposta = supabase.auth.sign_up({"email": email_limpo, "password": senha})
        if not resposta.user:
            return False
        if resposta.session:
            supabase.auth.sign_out()
            return True
        return "confirmar_email"
    except Exception as erro:
        texto_erro = str(erro).lower()
        if "already registered" in texto_erro or "already been registered" in texto_erro:
            return "existe"
        st.error(mostrar_erro_seguro(erro, email_limpo))
        return False


def fazer_login(email: str, senha: str) -> dict | bool:
    """Autentica no Supabase Auth e retorna a identidade confiavel."""
    email_limpo = email.strip().lower()
    usuario_fp = fingerprint(email_limpo)
    st.session_state[CHAVE_LOGIN_BLOQUEADO] = False
    agora = time.time()
    tentativas_por_email = st.session_state.get(CHAVE_TENTATIVAS_LOGIN, {})
    tentativas = [
        instante
        for instante in tentativas_por_email.get(usuario_fp, [])
        if agora - instante < JANELA_TENTATIVAS_SEGUNDOS
    ]
    if len(tentativas) >= LIMITE_TENTATIVAS_LOGIN:
        st.session_state[CHAVE_LOGIN_BLOQUEADO] = True
        tentativas_por_email[usuario_fp] = tentativas
        st.session_state[CHAVE_TENTATIVAS_LOGIN] = tentativas_por_email
        st.error("Muitas tentativas de login. Aguarde alguns minutos antes de tentar novamente.")
        return False

    try:
        resposta = supabase.auth.sign_in_with_password(
            {"email": email_limpo, "password": senha}
        )
        if resposta.user:
            registrar_evento(
                logger,
                logging.INFO,
                "Login Supabase Auth aprovado",
                contexto={"usuario_fp": usuario_fp},
            )
            st.session_state.tentativas_login = []
            tentativas_por_email[usuario_fp] = []
            st.session_state[CHAVE_TENTATIVAS_LOGIN] = tentativas_por_email
            return {
                "id": str(resposta.user.id),
                "email": (resposta.user.email or email_limpo).strip().lower(),
            }
    except Exception as erro:
        registrar_evento(
            logger,
            logging.INFO,
            "Tentativa de login recusada pelo Supabase Auth",
            contexto={
                "usuario_fp": usuario_fp,
                "tipo_erro": type(erro).__name__,
            },
        )

    tentativas.append(agora)
    tentativas_por_email[usuario_fp] = tentativas
    st.session_state[CHAVE_TENTATIVAS_LOGIN] = tentativas_por_email
    st.session_state.tentativas_login = []
    return False


def enviar_email_recuperacao_senha(email: str) -> bool:
    """Solicita ao Supabase Auth o envio do e-mail de recuperacao de senha."""
    email_limpo = email.strip().lower()
    try:
        redirect_to = st.secrets.get("SUPABASE_PASSWORD_RESET_REDIRECT_URL", None)
        options = {"redirect_to": redirect_to} if redirect_to else None
        supabase.auth.reset_password_for_email(email_limpo, options=options)
        registrar_evento(
            logger,
            logging.INFO,
            "Recuperacao de senha solicitada ao Supabase Auth",
            contexto={"usuario_fp": fingerprint(email_limpo)},
        )
        return True
    except Exception as erro:
        registrar_evento(
            logger,
            logging.WARNING,
            "Falha ao solicitar recuperacao de senha no Supabase Auth",
            contexto={
                "usuario_fp": fingerprint(email_limpo),
                "tipo_erro": type(erro).__name__,
            },
            exc_info=True,
        )
        return False


def redefinir_senha_com_tokens(
    access_token: str,
    refresh_token: str,
    nova_senha: str,
) -> bool:
    """Redefine a senha usando os tokens enviados pelo fluxo de recovery."""
    try:
        cliente = obter_conexao_supabase()
        cliente.auth.set_session(access_token, refresh_token)
        cliente.auth.update_user({"password": nova_senha})
        cliente.auth.sign_out()
        registrar_evento(
            logger,
            logging.INFO,
            "Senha redefinida pelo fluxo de recuperacao Supabase Auth",
        )
        return True
    except Exception as erro:
        registrar_evento(
            logger,
            logging.WARNING,
            "Falha ao redefinir senha pelo fluxo de recuperacao Supabase Auth",
            contexto={"tipo_erro": type(erro).__name__},
            exc_info=True,
        )
        return False


def validar_sessao_atual() -> dict | bool:
    """Revalida a identidade atual diretamente no Supabase Auth."""
    try:
        resposta = supabase.auth.get_user()
        if not resposta.user or not resposta.user.id or not resposta.user.email:
            return False
        return {
            "id": str(resposta.user.id),
            "email": resposta.user.email.strip().lower(),
        }
    except Exception as erro:
        registrar_evento(
            logger,
            logging.INFO,
            "Sessao Supabase Auth ausente, expirada ou revogada",
            contexto={"tipo_erro": type(erro).__name__},
        )
        return False


def encerrar_autenticacao_supabase() -> bool:
    """Revoga a sessao Auth atual antes de limpar o estado local."""
    try:
        supabase.auth.sign_out()
        return True
    except Exception as erro:
        registrar_evento(
            logger,
            logging.WARNING,
            "Falha ao encerrar sessao no Supabase Auth",
            contexto={"tipo_erro": type(erro).__name__},
            exc_info=True,
        )
        return False


def auditar_saude_plataforma() -> dict:
    """Executa uma leitura autenticada protegida por RLS."""
    status = {"supabase": "Offline", "seguranca": "Nao validado"}
    try:
        supabase.table("transacoes").select("id").limit(1).execute()
        status["supabase"] = "Conectado"
        status["seguranca"] = "Sessao Auth e RLS ativos"
    except Exception as erro:
        registrar_evento(
            logger,
            logging.WARNING,
            "Auditoria de saude Supabase falhou",
            contexto={"tipo_erro": type(erro).__name__},
            exc_info=True,
        )
        status["supabase"] = "Erro de acesso"
    return status
