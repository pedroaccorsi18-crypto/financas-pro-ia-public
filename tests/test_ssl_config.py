import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from utils.ssl_config import configurar_certificados_ssl_do_sistema


class SslConfigTest(unittest.TestCase):
    def test_retorna_false_quando_truststore_nao_esta_instalado(self):
        modulos = dict(sys.modules)
        modulos["truststore"] = None

        with patch.dict(sys.modules, modulos, clear=True):
            self.assertFalse(configurar_certificados_ssl_do_sistema())

    def test_ativa_truststore_quando_disponivel(self):
        chamadas = []
        truststore_fake = SimpleNamespace(
            inject_into_ssl=lambda: chamadas.append("inject")
        )

        with patch.dict(sys.modules, {"truststore": truststore_fake}):
            self.assertTrue(configurar_certificados_ssl_do_sistema())

        self.assertEqual(chamadas, ["inject"])

    def test_falha_com_segurança_se_truststore_recusar_injecao(self):
        def falhar():
            raise RuntimeError("falha simulada")

        truststore_fake = SimpleNamespace(inject_into_ssl=falhar)

        with patch.dict(sys.modules, {"truststore": truststore_fake}):
            self.assertFalse(configurar_certificados_ssl_do_sistema())


if __name__ == "__main__":
    unittest.main()
