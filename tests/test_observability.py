import logging
import unittest
from unittest.mock import Mock

from utils.observability import contexto_seguro, fingerprint, registrar_evento


class ObservabilityTests(unittest.TestCase):
    def test_contexto_seguro_redige_campos_sensiveis(self):
        contexto = contexto_seguro(
            usuario="pessoa@example.com",
            api_key="segredo",
            SMTP_SENHA_REMETENTE="senha",
            token="abc",
        )

        self.assertEqual(contexto["usuario"], "pessoa@example.com")
        self.assertEqual(contexto["api_key"], "[redigido]")
        self.assertEqual(contexto["SMTP_SENHA_REMETENTE"], "[redigido]")
        self.assertEqual(contexto["token"], "[redigido]")

    def test_fingerprint_nao_expoe_valor_original(self):
        valor = fingerprint("Pessoa@Example.com")

        self.assertEqual(len(valor), 12)
        self.assertNotIn("Pessoa", valor)
        self.assertEqual(valor, fingerprint(" pessoa@example.com "))

    def test_registrar_evento_inclui_contexto_redigido(self):
        logger = Mock()

        registrar_evento(
            logger,
            logging.WARNING,
            "evento teste",
            contexto={"senha": "123", "operacao": "login"},
        )

        logger.log.assert_called_once()
        args, kwargs = logger.log.call_args
        self.assertEqual(args[0], logging.WARNING)
        self.assertEqual(args[1], "%s | contexto=%s")
        self.assertEqual(args[2], "evento teste")
        self.assertEqual(args[3]["senha"], "[redigido]")
        self.assertEqual(args[3]["operacao"], "login")
        self.assertFalse(kwargs["exc_info"])


if __name__ == "__main__":
    unittest.main()
