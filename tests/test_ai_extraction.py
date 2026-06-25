import unittest

from finance_categories import CATEGORIAS_VALIDAS
from finance_constants import TIPOS_TRANSACAO
from utils.ai_extraction import (
    TIPOS_DOCUMENTO_EXTRACAO,
    carregar_resultado_extracao,
    montar_config_extracao_pdf,
    montar_prompt_extracao_pdf,
    montar_schema_extracao_pdf,
    normalizar_resultado_extracao,
)


class SchemaFake:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class GenerateContentConfigFake:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class TypeFake:
    OBJECT = "OBJECT"
    STRING = "STRING"
    NUMBER = "NUMBER"
    ARRAY = "ARRAY"


class TypesFake:
    Type = TypeFake
    Schema = SchemaFake
    GenerateContentConfig = GenerateContentConfigFake


class AiExtractionTests(unittest.TestCase):
    def test_monta_prompt_preserva_contrato_de_extracao(self):
        prompt = montar_prompt_extracao_pdf()

        self.assertIn("extrator de dados cont\u00e1beis", prompt)
        self.assertIn("mes_fatura", prompt)
        self.assertIn("MM/AAAA", prompt)
        self.assertIn("transacoes", prompt)

    def test_monta_schema_com_enums_do_app(self):
        schema = montar_schema_extracao_pdf(TypesFake)
        propriedades = schema.kwargs["properties"]

        self.assertEqual(schema.kwargs["type"], TypeFake.OBJECT)
        self.assertEqual(
            schema.kwargs["required"],
            [
                "instituicao_financeira",
                "tipo_documento",
                "total_documento",
                "mes_fatura",
                "transacoes",
            ],
        )
        self.assertEqual(
            propriedades["tipo_documento"].kwargs["enum"],
            TIPOS_DOCUMENTO_EXTRACAO,
        )

        item_transacao = propriedades["transacoes"].kwargs["items"]
        campos_transacao = item_transacao.kwargs["properties"]
        self.assertEqual(campos_transacao["tipo"].kwargs["enum"], TIPOS_TRANSACAO)
        self.assertEqual(
            campos_transacao["categoria"].kwargs["enum"],
            CATEGORIAS_VALIDAS,
        )

    def test_monta_config_json_com_temperatura_zero(self):
        config = montar_config_extracao_pdf(TypesFake)

        self.assertEqual(config.kwargs["response_mime_type"], "application/json")
        self.assertEqual(config.kwargs["temperature"], 0.0)
        self.assertIsInstance(config.kwargs["response_schema"], SchemaFake)

    def test_carrega_resultado_extracao_com_espacos(self):
        resultado = carregar_resultado_extracao(
            '  {"instituicao_financeira": "Banco Exemplo"}  '
        )

        self.assertEqual(resultado["instituicao_financeira"], "Banco Exemplo")

    def test_normaliza_resultado_para_pre_visualizacao(self):
        transacoes = [{"descricao": "Mercado", "valor": 10}]
        dataframes_criados = []

        def dataframe_factory(linhas):
            dataframes_criados.append(linhas)
            return {"linhas": linhas}

        resultado = normalizar_resultado_extracao(
            {
                "instituicao_financeira": "Banco Exemplo",
                "tipo_documento": "Fatura de Cart\u00e3o",
                "mes_fatura": "06/2026",
                "total_documento": "10.50",
                "transacoes": transacoes,
            },
            dataframe_factory,
        )

        self.assertEqual(resultado["instituicao"], "Banco Exemplo")
        self.assertEqual(resultado["tipo_documento"], "Fatura de Cart\u00e3o")
        self.assertEqual(resultado["mes_referencia"], "06/2026")
        self.assertEqual(resultado["total_documento"], 10.5)
        self.assertEqual(resultado["df_transacoes"], {"linhas": transacoes})
        self.assertEqual(dataframes_criados, [transacoes])

    def test_normaliza_total_vazio_como_zero(self):
        resultado = normalizar_resultado_extracao(
            {
                "instituicao_financeira": "Banco Exemplo",
                "tipo_documento": "Outro",
                "mes_fatura": "06/2026",
                "total_documento": None,
                "transacoes": [],
            },
            lambda linhas: linhas,
        )

        self.assertEqual(resultado["total_documento"], 0.0)


if __name__ == "__main__":
    unittest.main()
