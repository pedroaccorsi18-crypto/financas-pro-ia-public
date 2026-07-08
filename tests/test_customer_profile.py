import unittest

from utils.customer_profile import (
    MOMENTOS_FINANCEIROS,
    diagnosticar_perfil_cliente,
    montar_payload_perfil_cliente,
    normalizar_perfil_cliente,
)


class CustomerProfileTests(unittest.TestCase):
    def test_normaliza_perfil_padrao_para_usuario(self):
        perfil = normalizar_perfil_cliente(None, "user-1")

        self.assertEqual(perfil["user_id"], "user-1")
        self.assertEqual(perfil["momento_financeiro"], "Organizando a casa")
        self.assertTrue(perfil["aceita_personalizacao"])

    def test_payload_rejeita_opcao_fora_do_catalogo(self):
        with self.assertRaises(ValueError):
            montar_payload_perfil_cliente(
                usuario_id="user-1",
                momento_financeiro="Outro momento",
                objetivo_principal="Entender para onde o dinheiro está indo",
                maior_dor="Falta de clareza sobre gastos",
                nivel_organizacao="Estou começando agora",
                perfil_decisao="Quero recomendações simples e diretas",
                preferencia_acompanhamento="Mensal",
                aceita_personalizacao=True,
            )

    def test_diagnostico_fica_pronto_quando_ha_contexto(self):
        perfil = montar_payload_perfil_cliente(
            usuario_id="user-1",
            momento_financeiro=MOMENTOS_FINANCEIROS[3],
            objetivo_principal="Investir com mais consistência",
            maior_dor="Medo de investir errado",
            nivel_organizacao="Tenho método e quero otimizar",
            perfil_decisao="Quero comparar cenários",
            preferencia_acompanhamento="Semanal",
            aceita_personalizacao=True,
        )

        diagnostico = diagnosticar_perfil_cliente(perfil)

        self.assertEqual(diagnostico.nivel, "Pronto para personalização")
        self.assertIn("contexto suficiente", diagnostico.mensagem)


if __name__ == "__main__":
    unittest.main()
