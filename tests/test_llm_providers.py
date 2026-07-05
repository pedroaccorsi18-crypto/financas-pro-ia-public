import unittest
from types import SimpleNamespace

from utils.llm_providers import (
    ClaudeProvider,
    DeepSeekProvider,
    GeminiProvider,
    LLMFilePart,
    LLMProvider,
    LLMRequest,
    OpenAIProvider,
    SCHEMA_EXTRACAO_PDF_FINANCEIRO,
)
from utils.llm_service import criar_provider_ia_padrao, gerar_conteudo_ia, gerar_pdf_ia, gerar_texto_ia


class LLMProvidersTests(unittest.TestCase):
    def _types_fake(self):
        class PartFake:
            @staticmethod
            def from_bytes(*, data, mime_type):
                return {"data": data, "mime_type": mime_type}

        class TypeFake:
            OBJECT = "object"
            STRING = "string"
            NUMBER = "number"
            ARRAY = "array"

        class SchemaFake:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class ConfigFake:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        return SimpleNamespace(
            GenerateContentConfig=ConfigFake,
            Part=PartFake,
            Schema=SchemaFake,
            Type=TypeFake,
        )

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

    def test_gemini_provider_converte_request_neutro_para_kwargs_gemini(self):
        chamadas = []
        cliente = SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **kwargs: chamadas.append(kwargs) or "ok")
        )
        provider = GeminiProvider(
            api_key="chave-teste",
            cliente=cliente,
            types_module=self._types_fake(),
        )

        resultado = provider.generate_content(
            request=LLMRequest(
                model="gemini-teste",
                contents="Extraia dados",
                file_part=LLMFilePart(data=b"%PDF", mime_type="application/pdf"),
                response_schema=SCHEMA_EXTRACAO_PDF_FINANCEIRO,
            )
        )

        self.assertEqual(resultado, "ok")
        self.assertEqual(chamadas[0]["model"], "gemini-teste")
        self.assertEqual(chamadas[0]["contents"][0]["mime_type"], "application/pdf")
        self.assertEqual(chamadas[0]["contents"][1], "Extraia dados")
        self.assertEqual(chamadas[0]["config"].kwargs["response_mime_type"], "application/json")
        self.assertIn("response_schema", chamadas[0]["config"].kwargs)

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

    def test_helpers_neutros_montam_request_sem_expor_sdk_gemini(self):
        requests = []

        def gerar_conteudo_fake(*, request, tentativas=3):
            requests.append((request, tentativas))
            return "ok"

        self.assertEqual(
            gerar_texto_ia(
                gerar_conteudo_fake,
                model="modelo",
                prompt="prompt",
                temperature=0.1,
                response_mime_type="application/json",
                tentativas=2,
            ),
            "ok",
        )
        self.assertEqual(
            gerar_pdf_ia(
                gerar_conteudo_fake,
                model="modelo",
                pdf_bytes=b"%PDF",
                prompt="prompt pdf",
                response_schema=SCHEMA_EXTRACAO_PDF_FINANCEIRO,
            ),
            "ok",
        )

        self.assertEqual(requests[0][0].temperature, 0.1)
        self.assertEqual(requests[0][0].response_mime_type, "application/json")
        self.assertEqual(requests[0][1], 2)
        self.assertEqual(requests[1][0].file_part.mime_type, "application/pdf")
        self.assertEqual(requests[1][0].response_schema, SCHEMA_EXTRACAO_PDF_FINANCEIRO)

    def test_providers_futuros_falham_de_forma_explicita(self):
        for provider in (OpenAIProvider(), ClaudeProvider(), DeepSeekProvider()):
            with self.subTest(provider=provider.nome):
                with self.assertRaises(NotImplementedError):
                    provider.generate_content(model="modelo", contents="conteudo")

    def test_provider_padrao_exige_gemini_api_key(self):
        with self.assertRaises(RuntimeError):
            criar_provider_ia_padrao({"GEMINI_API_KEY": ""})


if __name__ == "__main__":
    unittest.main()
