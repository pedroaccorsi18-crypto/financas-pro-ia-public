import unittest

import pandas as pd

from finance_constants import TIPO_DESPESA, TIPO_RECEITA
from utils.import_workflow import processar_importacao_homologada


class ImportWorkflowTests(unittest.TestCase):
    def pre_visualizacao_base(self, total_documento=150.0):
        return {
            "instituicao": " Banco Teste ",
            "tipo_documento": "Fatura de Cartao",
            "mes_referencia": " 06/2026 ",
            "total_documento": total_documento,
        }

    def df_base(self):
        return pd.DataFrame(
            [
                {
                    "descricao": "Mercado",
                    "valor": 100,
                    "tipo": TIPO_DESPESA,
                    "categoria": "Mercado",
                },
                {
                    "descricao": "Credito",
                    "valor": 50,
                    "tipo": TIPO_RECEITA,
                    "categoria": "Reembolso",
                },
            ]
        )

    def test_substitui_lote_quando_conteudo_mudou_e_dispara_alerta(self):
        chamadas = []

        def buscar_lote(**kwargs):
            chamadas.append(("buscar", kwargs))
            return [{"descricao": "Antigo"}]

        def lotes_sao_iguais(novo, antigo):
            chamadas.append(("comparar", len(novo), antigo))
            return False

        def substituir_lote(**kwargs):
            chamadas.append(("substituir", kwargs))

        def disparar_alerta(*args):
            chamadas.append(("alerta", args))

        resultado = processar_importacao_homologada(
            df_editavel=self.df_base(),
            pre_visualizacao=self.pre_visualizacao_base(),
            usuario_id="user-123",
            email_usuario="usuario@example.com",
            secrets={"SMTP_SERVER": "smtp"},
            buscar_lote=buscar_lote,
            lotes_sao_iguais=lotes_sao_iguais,
            substituir_lote=substituir_lote,
            disparar_alerta=disparar_alerta,
        )

        self.assertTrue(resultado["lote_substituido"])
        self.assertTrue(resultado["alerta_disparado"])
        self.assertEqual(resultado["gastos_reais"], 100.0)
        self.assertEqual(resultado["creditos_reais"], 50.0)
        self.assertEqual(chamadas[0][0], "buscar")
        self.assertEqual(chamadas[0][1]["instituicao_financeira"], "Banco Teste")
        self.assertEqual(chamadas[0][1]["mes_referencia"], "06/2026")
        self.assertEqual(chamadas[2][0], "substituir")
        self.assertEqual(chamadas[3][0], "alerta")

    def test_nao_substitui_lote_igual(self):
        substituicoes = []

        resultado = processar_importacao_homologada(
            df_editavel=self.df_base(),
            pre_visualizacao=self.pre_visualizacao_base(),
            usuario_id="user-123",
            email_usuario="usuario@example.com",
            secrets={},
            buscar_lote=lambda **kwargs: [{"descricao": "Mercado"}],
            lotes_sao_iguais=lambda novo, antigo: True,
            substituir_lote=lambda **kwargs: substituicoes.append(kwargs),
            disparar_alerta=lambda *args: None,
        )

        self.assertFalse(resultado["lote_substituido"])
        self.assertEqual(substituicoes, [])

    def test_nao_dispara_alerta_quando_total_documento_zero(self):
        alertas = []

        resultado = processar_importacao_homologada(
            df_editavel=self.df_base(),
            pre_visualizacao=self.pre_visualizacao_base(total_documento=0.0),
            usuario_id="user-123",
            email_usuario="usuario@example.com",
            secrets={},
            buscar_lote=lambda **kwargs: [],
            lotes_sao_iguais=lambda novo, antigo: False,
            substituir_lote=lambda **kwargs: None,
            disparar_alerta=lambda *args: alertas.append(args),
        )

        self.assertFalse(resultado["alerta_disparado"])
        self.assertEqual(alertas, [])


if __name__ == "__main__":
    unittest.main()
