import unittest

from app_config import feature_flag_ativa, montar_opcoes_navegacao


class AppConfigTests(unittest.TestCase):
    def test_plano_gratuito_enxerga_apenas_recursos_basicos(self):
        opcoes = montar_opcoes_navegacao({}, is_admin=False, assinatura={"plano": "gratuito", "status": "ativo"})

        self.assertEqual(opcoes, ["Visão Geral", "Meu Perfil", "Transações", "Meu Plano"])

    def test_plano_pro_libera_importacao_e_modulos_avancados_por_flag(self):
        opcoes = montar_opcoes_navegacao(
            {
                "ENABLE_PLANEJAMENTO_360": "true",
                "ENABLE_MARKET_RADAR": "sim",
                "ENABLE_ORACULO_IA": "1",
            },
            is_admin=False,
            assinatura={"plano": "pro", "status": "ativo"},
        )

        self.assertEqual(
            opcoes,
            [
                "Visão Geral",
                "Meu Perfil",
                "Transações",
                "Meu Plano",
                "Importação",
                "Planejamento 360",
                "Radar de Mercado",
                "Oráculo IA",
            ],
        )

    def test_plano_familia_herda_recursos_pro(self):
        opcoes = montar_opcoes_navegacao(
            {"ENABLE_ORACULO_IA": "true"},
            is_admin=False,
            assinatura={"plano": "familia", "status": "trial"},
        )

        self.assertEqual(
            opcoes,
            ["Visão Geral", "Meu Perfil", "Transações", "Meu Plano", "Importação", "Oráculo IA"],
        )

    def test_assinatura_inadimplente_volta_para_recursos_gratuitos(self):
        opcoes = montar_opcoes_navegacao(
            {"ENABLE_ORACULO_IA": "true"},
            is_admin=False,
            assinatura={"plano": "pro", "status": "past_due"},
        )

        self.assertEqual(opcoes, ["Visão Geral", "Meu Perfil", "Transações", "Meu Plano"])

    def test_admin_continua_disponivel_para_usuario_autorizado(self):
        opcoes = montar_opcoes_navegacao({}, is_admin=True, assinatura={"plano": "gratuito", "status": "ativo"})

        self.assertEqual(opcoes, ["Visão Geral", "Meu Perfil", "Transações", "Meu Plano", "Admin"])

    def test_feature_flag_aceita_booleano_e_textos_comuns(self):
        self.assertTrue(feature_flag_ativa({"FLAG": True}, "FLAG"))
        self.assertTrue(feature_flag_ativa({"FLAG": "on"}, "FLAG"))
        self.assertFalse(feature_flag_ativa({"FLAG": "false"}, "FLAG"))

    def test_feature_flag_respeita_padrao_e_none_desliga_explicitamente(self):
        self.assertTrue(feature_flag_ativa({}, "FLAG", padrao=True))
        self.assertFalse(feature_flag_ativa({"FLAG": None}, "FLAG", padrao=True))


if __name__ == "__main__":
    unittest.main()
