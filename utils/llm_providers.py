from abc import ABC, abstractmethod

from utils.gemini_client import criar_cliente_gemini, gerar_conteudo_gemini


class LLMProvider(ABC):
    """Contrato comum para provedores de modelos generativos."""

    nome: str

    @abstractmethod
    def generate_content(self, *, tentativas: int = 3, **kwargs):
        """Gera conteudo preservando o contrato usado pela aplicacao."""


class GeminiProvider(LLMProvider):
    nome = "gemini"

    def __init__(self, *, api_key: str, client_factory=None, cliente=None):
        if cliente is not None:
            self._cliente = cliente
        else:
            self._cliente = criar_cliente_gemini(api_key, client_factory=client_factory)

    def generate_content(self, *, tentativas: int = 3, **kwargs):
        return gerar_conteudo_gemini(
            self._cliente,
            tentativas=tentativas,
            **kwargs,
        )


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
