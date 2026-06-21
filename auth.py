import base64
import json
import logging
import time

import streamlit as st
from supabase import Client, create_client


logger = logging.getLogger(__name__)
LIMITE_TENTATIVAS_LOGIN = 5
JANELA_TENTATIVAS_SEGUNDOS = 300
CHAVE_CLIENTE_SUPABASE_SESSAO = "_supabase_client"


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
    if CHAVE_CLIENTE_SUPABASE_SESSAO not in st.session_state:
        chave = st.secrets["SUPABASE_KEY"]
        validar_chave_publica_supabase(chave)
        st.session_state[CHAVE_CLIENTE_SUPABASE_SESSAO] = create_client(
            st.secrets["SUPABASE_URL"],
            chave,
        )
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
    agora = time.time()
    tentativas = [
        instante
        for instante in st.session_state.get("tentativas_login", [])
        if agora - instante < JANELA_TENTATIVAS_SEGUNDOS
    ]
    if len(tentativas) >= LIMITE_TENTATIVAS_LOGIN:
        st.error("Muitas tentativas de login. Aguarde alguns minutos antes de tentar novamente.")
        return False

    try:
        resposta = supabase.auth.sign_in_with_password(
            {"email": email_limpo, "password": senha}
        )
        if resposta.user:
            st.session_state.tentativas_login = []
            return {
                "id": str(resposta.user.id),
                "email": (resposta.user.email or email_limpo).strip().lower(),
            }
    except Exception:
        logger.info("Tentativa de login recusada para %s", email_limpo)

    tentativas.append(agora)
    st.session_state.tentativas_login = tentativas
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
    except Exception:
        logger.info("Sessao Supabase Auth ausente, expirada ou revogada")
        return False


def encerrar_autenticacao_supabase() -> bool:
    """Revoga a sessao Auth atual antes de limpar o estado local."""
    try:
        supabase.auth.sign_out()
        return True
    except Exception:
        logger.warning("Falha ao encerrar sessao no Supabase Auth", exc_info=True)
        return False


def auditar_saude_plataforma() -> dict:
    """Executa uma leitura autenticada protegida por RLS."""
    status = {"supabase": "Offline", "seguranca": "Nao validado"}
    try:
        supabase.table("transacoes").select("id").limit(1).execute()
        status["supabase"] = "Conectado"
        status["seguranca"] = "Sessao Auth e RLS ativos"
    except Exception:
        status["supabase"] = "Erro de acesso"
    return status
