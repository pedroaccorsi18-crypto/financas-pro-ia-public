import unittest

from app_config import feature_flag_ativa, montar_opcoes_navegacao


class AppConfigTests(unittest.TestCase):
    def test_navegacao_publica_esconde_modulos_avancados_por_padrao(self):
        opcoes = montar_opcoes_navegacao({}, is_admin=False)

        self.assertEqual(opcoes, ["Visão Geral", "Importação", "Transações"])

    def test_navegacao_permite_ligar_modulos_avancados_por_flag(self):
        opcoes = montar_opcoes_navegacao(
            {
                "ENABLE_PLANEJAMENTO_360": "true",
                "ENABLE_MARKET_RADAR": "sim",
                "ENABLE_ORACULO_IA": "1",
            },
            is_admin=False,
        )

        self.assertEqual(
            opcoes,
            [
                "Visão Geral",
                "Importação",
                "Transações",
                "Planejamento 360",
                "Radar de Mercado",
                "Oráculo IA",
            ],
        )

    def test_admin_continua_disponivel_para_usuario_autorizado(self):
        opcoes = montar_opcoes_navegacao({}, is_admin=True)

        self.assertEqual(opcoes, ["Visão Geral", "Importação", "Transações", "Admin"])

    def test_feature_flag_aceita_booleano_e_textos_comuns(self):
        self.assertTrue(feature_flag_ativa({"FLAG": True}, "FLAG"))
        self.assertTrue(feature_flag_ativa({"FLAG": "on"}, "FLAG"))
        self.assertFalse(feature_flag_ativa({"FLAG": "false"}, "FLAG"))


if __name__ == "__main__":
    unittest.main()
