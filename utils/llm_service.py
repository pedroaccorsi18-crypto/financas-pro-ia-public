import logging

from utils.llm_providers import GeminiProvider, LLMFilePart, LLMProvider, LLMRequest
from utils.observability import registrar_evento


logger = logging.getLogger(__name__)


def criar_provider_ia_padrao(secrets) -> LLMProvider:
    chave = str(secrets.get("GEMINI_API_KEY", "")).strip()
    if not chave:
        raise RuntimeError("GEMINI_API_KEY nao configurada")
    return GeminiProvider(api_key=chave)


def gerar_conteudo_ia(
    provider: LLMProvider,
    *,
    tentativas: int = 3,
    request: LLMRequest | None = None,
    **kwargs,
):
    modelo = request.model if request is not None else kwargs.get("model")
    registrar_evento(
        logger,
        logging.INFO,
        "Chamada LLM iniciada",
        contexto={
            "provider": provider.nome,
            "modelo": modelo,
        },
    )
    return provider.generate_content(
        tentativas=tentativas,
        request=request,
        **kwargs,
    )


def gerar_texto_ia(
    gerar_conteudo,
    *,
    model: str,
    prompt: str,
    temperature: float | None = None,
    response_mime_type: str | None = None,
    tentativas: int = 3,
):
    return gerar_conteudo(
        request=LLMRequest(
            model=model,
            contents=prompt,
            temperature=temperature,
            response_mime_type=response_mime_type,
        ),
        tentativas=tentativas,
    )


def gerar_pdf_ia(
    gerar_conteudo,
    *,
    model: str,
    pdf_bytes: bytes,
    prompt: str,
    response_schema: str | None = None,
    tentativas: int = 3,
):
    return gerar_conteudo(
        request=LLMRequest(
            model=model,
            contents=prompt,
            file_part=LLMFilePart(data=pdf_bytes, mime_type="application/pdf"),
            response_schema=response_schema,
        ),
        tentativas=tentativas,
    )
