import unittest
from types import SimpleNamespace

from utils.gemini_client import gerar_conteudo_gemini
from utils.gemini_errors import classificar_erro_gemini, mensagem_erro_gemini


class GeminiErrorsTests(unittest.TestCase):
    def test_identifica_limite_do_plano_gratuito(self):
        erro = RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")

        self.assertEqual(classificar_erro_gemini(erro), "cota")
        self.assertIn("limite gratuito", mensagem_erro_gemini(erro))

    def test_identifica_indisponibilidade_temporaria(self):
        erro = RuntimeError("503 UNAVAILABLE: model overloaded")

        self.assertEqual(classificar_erro_gemini(erro), "indisponibilidade")
        self.assertIn("temporariamente congestionado", mensagem_erro_gemini(erro))

    def test_nao_classifica_erro_desconhecido(self):
        erro = RuntimeError("resposta invalida")

        self.assertIsNone(classificar_erro_gemini(erro))
        self.assertIsNone(mensagem_erro_gemini(erro))


class GeminiClientTests(unittest.TestCase):
    def test_repete_indisponibilidade_com_backoff(self):
        chamadas = []
        pausas = []

        def gerar(**kwargs):
            chamadas.append(kwargs)
            if len(chamadas) < 3:
                raise RuntimeError("503 UNAVAILABLE: overloaded")
            return "ok"

        cliente = SimpleNamespace(models=SimpleNamespace(generate_content=gerar))

        resultado = gerar_conteudo_gemini(
            cliente,
            model="gemini-teste",
            tentativas=3,
            pausar=pausas.append,
        )

        self.assertEqual(resultado, "ok")
        self.assertEqual(len(chamadas), 3)
        self.assertEqual(pausas, [1, 2])

    def test_nao_repete_erro_de_cota(self):
        chamadas = []

        def gerar(**kwargs):
            chamadas.append(kwargs)
            raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")

        cliente = SimpleNamespace(models=SimpleNamespace(generate_content=gerar))

        with self.assertRaises(RuntimeError):
            gerar_conteudo_gemini(cliente, tentativas=3, pausar=lambda _: None)

        self.assertEqual(len(chamadas), 1)

    def test_rejeita_numero_de_tentativas_invalido(self):
        cliente = SimpleNamespace(models=SimpleNamespace(generate_content=lambda: None))

        with self.assertRaises(ValueError):
            gerar_conteudo_gemini(cliente, tentativas=0)


if __name__ == "__main__":
    unittest.main()
