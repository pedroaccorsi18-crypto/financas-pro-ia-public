import logging

from utils.gemini_errors import mensagem_erro_gemini


logger = logging.getLogger(__name__)


def mostrar_erro_seguro(erro: Exception, email_usuario: str = None) -> str:
    logger.error(
        "Falha na aplicação para usuário %s",
        email_usuario or "não identificado",
        exc_info=True,
    )
    texto_erro = str(erro).lower()
    if mensagem_gemini := mensagem_erro_gemini(erro):
        return mensagem_gemini
    if "substituir_lote_importado" in texto_erro or "pgrst202" in texto_erro:
        return "A função de reimportação ainda não está disponível no Supabase. Aplique a migração SQL e tente novamente."
    if "permission denied" in texto_erro or "42501" in texto_erro:
        return "O Supabase bloqueou esta operação por falta de permissão. Verifique as políticas da tabela."
    return "Ocorreu um problema interno. Tente novamente mais tarde."
