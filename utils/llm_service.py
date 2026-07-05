import logging

from utils.llm_providers import LLMProvider
from utils.observability import registrar_evento


logger = logging.getLogger(__name__)


def gerar_conteudo_ia(
    provider: LLMProvider,
    *,
    tentativas: int = 3,
    **kwargs,
):
    registrar_evento(
        logger,
        logging.INFO,
        "Chamada LLM iniciada",
        contexto={
            "provider": provider.nome,
            "modelo": kwargs.get("model"),
        },
    )
    return provider.generate_content(
        tentativas=tentativas,
        **kwargs,
    )
