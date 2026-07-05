import unittest
from types import SimpleNamespace

from utils.llm_providers import (
    ClaudeProvider,
    DeepSeekProvider,
    GeminiProvider,
    LLMProvider,
    OpenAIProvider,
)
from utils.llm_service import gerar_conteudo_ia


class LLMProvidersTests(unittest.TestCase):
    def test_gemini_provider_reusa_contrato_atual_com_retry(self):
        chamadas = []
        pausas = []

        def gerar(**kwargs):
            chamadas.append(kwargs)
            if len(chamadas) == 1:
                raise RuntimeError("503 UNAVAILABLE: overloaded")
            return "ok"

        cliente = SimpleNamespace(models=SimpleNamespace(generate_content=gerar))
        provider = GeminiProvider(api_key="chave-teste", cliente=cliente)

        resultado = provider.generate_content(
            model="gemini-teste",
            contents="conteudo",
            tentativas=2,
            pausar=pausas.append,
        )

        self.assertEqual(resultado, "ok")
        self.assertEqual(len(chamadas), 2)
        self.assertEqual(pausas, [1])

    def test_servico_neutro_delega_para_provider_sem_logar_conteudo_ou_chave(self):
        class ProviderTeste(LLMProvider):
            nome = "teste"

            def __init__(self):
                self.kwargs_recebidos = None
                self.tentativas = None

            def generate_content(self, *, tentativas=3, **kwargs):
                self.tentativas = tentativas
                self.kwargs_recebidos = kwargs
                return "ok"

        provider = ProviderTeste()

        with self.assertLogs("utils.llm_service", level="INFO") as logs:
            resultado = gerar_conteudo_ia(
                provider,
                model="modelo-teste",
                contents="dado financeiro sensivel",
                api_key="segredo",
                tentativas=2,
            )

        saida = "\n".join(logs.output)
        self.assertEqual(resultado, "ok")
        self.assertEqual(provider.tentativas, 2)
        self.assertEqual(provider.kwargs_recebidos["contents"], "dado financeiro sensivel")
        self.assertIn("modelo-teste", saida)
        self.assertIn("teste", saida)
        self.assertNotIn("dado financeiro sensivel", saida)
        self.assertNotIn("segredo", saida)

    def test_providers_futuros_falham_de_forma_explicita(self):
        for provider in (OpenAIProvider(), ClaudeProvider(), DeepSeekProvider()):
            with self.subTest(provider=provider.nome):
                with self.assertRaises(NotImplementedError):
                    provider.generate_content(model="modelo", contents="conteudo")


if __name__ == "__main__":
    unittest.main()
