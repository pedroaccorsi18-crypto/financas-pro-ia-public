import json
import unittest
from pathlib import Path

import pandas as pd

from finance_categories import CATEGORIAS_VALIDAS
from finance_constants import TIPOS_TRANSACAO
from finance_core import mes_referencia_valido
from utils.import_staging import preparar_transacoes_importadas


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ia_extracao"
TERMOS_SENSIVEIS_BLOQUEADOS = (
    "@",
    "cpf",
    "rg ",
    "rg:",
    "rg-",
    "telefone",
    "celular",
    "endereco",
    "cartao final",
    "agencia",
    "conta corrente",
)


class IaExtractionCaseTests(unittest.TestCase):
    def carregar_casos(self):
        return [
            json.loads(caminho.read_text(encoding="utf-8"))
            for caminho in sorted(FIXTURES_DIR.glob("*.json"))
        ]

    def test_casos_anonimizados_seguem_contrato_do_extrator(self):
        casos = self.carregar_casos()

        self.assertGreaterEqual(len(casos), 3)
        for caso in casos:
            with self.subTest(caso=caso["case_id"]):
                saida = caso["expected_output"]

                self.assertTrue(saida["instituicao_financeira"].strip())
                self.assertIn(
                    saida["tipo_documento"],
                    ["Fatura de Cart\u00e3o", "Extrato Banc\u00e1rio", "Comprovante", "Outro"],
                )
                self.assertTrue(mes_referencia_valido(saida["mes_fatura"]))
                self.assertGreater(float(saida["total_documento"]), 0)
                self.assertGreater(len(saida["transacoes"]), 0)

                for transacao in saida["transacoes"]:
                    self.assertTrue(transacao["descricao"].strip())
                    self.assertGreater(float(transacao["valor"]), 0)
                    self.assertIn(transacao["tipo"], TIPOS_TRANSACAO)
                    self.assertIn(transacao["categoria"], CATEGORIAS_VALIDAS)

    def test_casos_anonimizados_passam_pela_homologacao(self):
        for caso in self.carregar_casos():
            with self.subTest(caso=caso["case_id"]):
                saida = caso["expected_output"]
                pre_visualizacao = {
                    "instituicao": saida["instituicao_financeira"],
                    "tipo_documento": saida["tipo_documento"],
                    "mes_referencia": saida["mes_fatura"],
                    "total_documento": saida["total_documento"],
                }

                transacoes, gastos, receitas = preparar_transacoes_importadas(
                    pd.DataFrame(saida["transacoes"]),
                    pre_visualizacao,
                    usuario_id="usuario-teste",
                    email_usuario="usuario@example.invalid",
                )

                self.assertEqual(len(transacoes), len(saida["transacoes"]))
                self.assertGreaterEqual(gastos + receitas, saida["total_documento"])
                self.assertTrue(
                    all(t["origem_importacao"] == "Autom\u00e1tico" for t in transacoes)
                )

    def test_casos_nao_contem_identificadores_pessoais_obvios(self):
        for caso in self.carregar_casos():
            texto = json.dumps(caso, ensure_ascii=False).lower()
            with self.subTest(caso=caso["case_id"]):
                for termo in TERMOS_SENSIVEIS_BLOQUEADOS:
                    self.assertNotIn(termo, texto)


if __name__ == "__main__":
    unittest.main()
