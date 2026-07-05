from abc import ABC, abstractmethod
from dataclasses import dataclass

from utils.gemini_client import criar_cliente_gemini, gerar_conteudo_gemini


SCHEMA_EXTRACAO_PDF_FINANCEIRO = "extracao_pdf_financeiro"


@dataclass(frozen=True)
class LLMFilePart:
    data: bytes
    mime_type: str


@dataclass(frozen=True)
class LLMRequest:
    model: str
    contents: str
    temperature: float | None = None
    response_mime_type: str | None = None
    response_schema: str | None = None
    file_part: LLMFilePart | None = None


class LLMProvider(ABC):
    """Contrato comum para provedores de modelos generativos."""

    nome: str

    @abstractmethod
    def generate_content(self, *, tentativas: int = 3, **kwargs):
        """Gera conteudo preservando o contrato usado pela aplicacao."""


class GeminiProvider(LLMProvider):
    nome = "gemini"

    def __init__(self, *, api_key: str, client_factory=None, cliente=None, types_module=None):
        if cliente is not None:
            self._cliente = cliente
        else:
            self._cliente = criar_cliente_gemini(api_key, client_factory=client_factory)
        self._types_module = types_module

    def generate_content(self, *, tentativas: int = 3, request: LLMRequest | None = None, **kwargs):
        if request is not None:
            kwargs = self._kwargs_gemini(request)
        return gerar_conteudo_gemini(
            self._cliente,
            tentativas=tentativas,
            **kwargs,
        )

    def _kwargs_gemini(self, request: LLMRequest) -> dict:
        types = self._obter_types()
        kwargs = {
            "model": request.model,
            "contents": self._montar_contents(types, request),
        }
        config = self._montar_config(types, request)
        if config is not None:
            kwargs["config"] = config
        return kwargs

    def _obter_types(self):
        if self._types_module is not None:
            return self._types_module

        from google.genai import types

        return types

    def _montar_contents(self, types, request: LLMRequest):
        if request.file_part is None:
            return request.contents
        return [
            types.Part.from_bytes(
                data=request.file_part.data,
                mime_type=request.file_part.mime_type,
            ),
            request.contents,
        ]

    def _montar_config(self, types, request: LLMRequest):
        argumentos = {}
        if request.temperature is not None:
            argumentos["temperature"] = request.temperature
        if request.response_mime_type:
            argumentos["response_mime_type"] = request.response_mime_type
        if request.response_schema == SCHEMA_EXTRACAO_PDF_FINANCEIRO:
            from utils.ai_extraction import montar_schema_extracao_pdf

            argumentos.setdefault("response_mime_type", "application/json")
            argumentos["response_schema"] = montar_schema_extracao_pdf(types)
        elif request.response_schema:
            raise ValueError(f"Schema LLM desconhecido: {request.response_schema}")

        if not argumentos:
            return None
        return types.GenerateContentConfig(**argumentos)


class ProviderNaoImplementado(LLMProvider):
    nome = "nao_implementado"

    def generate_content(self, *, tentativas: int = 3, **kwargs):
        raise NotImplementedError(
            f"O provider {self.nome} ainda nao possui integracao ativa neste projeto."
        )


class OpenAIProvider(ProviderNaoImplementado):
    nome = "openai"


class ClaudeProvider(ProviderNaoImplementado):
    nome = "claude"


class DeepSeekProvider(ProviderNaoImplementado):
    nome = "deepseek"
