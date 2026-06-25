import unittest

from utils.oracle_analysis import (
    INSTRUCAO_REFORCO_CABECALHOS,
    montar_payload_feedback_oraculo,
    montar_prompt_oraculo,
    reforcar_prompt_oraculo,
    resposta_oraculo_tem_secoes,
)


class OracleAnalysisTests(unittest.TestCase):
    def test_monta_prompt_com_historico_e_secoes_obrigatorias(self):
        prompt = montar_prompt_oraculo("- Mes: 06/2026 | Categoria: Mercado")

        self.assertIn("cientista de dados", prompt)
        self.assertIn("06/2026", prompt)
        self.assertIn("Raio-X Comportamental", prompt)
        self.assertIn("Tend\u00eancias Preditivas", prompt)
        self.assertIn("Plano de Evolu\u00e7\u00e3o", prompt)

    def test_valida_resposta_com_todas_as_secoes(self):
        resposta = (
            "### 1. Raio-X Comportamental\nTexto\n"
            "### 2. Tend\u00eancias Preditivas\nTexto\n"
            "### 3. Plano de Evolu\u00e7\u00e3o\nTexto"
        )

        self.assertTrue(resposta_oraculo_tem_secoes(resposta))
        self.assertFalse(resposta_oraculo_tem_secoes("Raio-X Comportamental apenas"))

    def test_reforca_prompt_com_instrucao_de_cabecalhos(self):
        prompt = "Prompt base"

        self.assertEqual(
            reforcar_prompt_oraculo(prompt),
            prompt + INSTRUCAO_REFORCO_CABECALHOS,
        )

    def test_monta_payload_feedback_anonimizado(self):
        chamadas = []

        def anonimizar(texto):
            chamadas.append(texto)
            return f"anon:{texto}"

        payload = montar_payload_feedback_oraculo(
            usuario_id="user-123",
            email_usuario="usuario@example.com",
            status_resposta="TOP",
            resposta_ia="Resposta R$ 100",
            dados_enviados="Historico R$ 200",
            anonimizar=anonimizar,
        )

        self.assertEqual(
            payload,
            {
                "user_id": "user-123",
                "usuario_email": "usuario@example.com",
                "status_resposta": "TOP",
                "resposta_ia": "anon:Resposta R$ 100",
                "dados_enviados": "anon:Historico R$ 200",
            },
        )
        self.assertEqual(chamadas, ["Resposta R$ 100", "Historico R$ 200"])


if __name__ == "__main__":
    unittest.main()
