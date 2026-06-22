import logging
import time

from utils.gemini_errors import classificar_erro_gemini
from utils.observability import registrar_evento


logger = logging.getLogger(__name__)


def gerar_conteudo_gemini(
    cliente,
    *,
    tentativas: int = 3,
    pausar=time.sleep,
    **kwargs,
):
    if tentativas < 1:
        raise ValueError("tentativas deve ser maior que zero")

    for tentativa in range(tentativas):
        try:
            resposta = cliente.models.generate_content(**kwargs)
            registrar_evento(
                logger,
                logging.INFO,
                "Chamada Gemini concluida",
                contexto={
                    "modelo": kwargs.get("model"),
                    "tentativa": tentativa + 1,
                },
            )
            return resposta
        except Exception as erro:
            ultima_tentativa = tentativa == tentativas - 1
            classificacao = classificar_erro_gemini(erro)
            registrar_evento(
                logger,
                logging.WARNING if ultima_tentativa else logging.INFO,
                "Chamada Gemini falhou",
                contexto={
                    "modelo": kwargs.get("model"),
                    "tentativa": tentativa + 1,
                    "tentativas": tentativas,
                    "classificacao": classificacao or "desconhecida",
                    "tipo_erro": type(erro).__name__,
                },
                exc_info=ultima_tentativa,
            )
            if classificacao != "indisponibilidade" or ultima_tentativa:
                raise
            pausar(2 ** tentativa)
