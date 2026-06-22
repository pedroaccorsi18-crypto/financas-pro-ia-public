import unittest
from unittest.mock import patch

from utils.bot_fiscal import agendar_alerta_fiscal, enviar_alerta_fiscal


CONFIGURACAO = {
    "SMTP_SERVER": "smtp.exemplo.com",
    "SMTP_PORT": 587,
    "SMTP_EMAIL_REMETENTE": "remetente@exemplo.com",
    "SMTP_SENHA_REMETENTE": "senha",
    "EMAIL_DESTINATARIO_ALERTAS": "alertas@exemplo.com",
}

DADOS = {
    "usuario": "usuario@exemplo.com",
    "instituicao": "Banco Teste",
    "tipo_doc": "Fatura",
    "mes": "06/2026",
    "total_gastos": 100.0,
    "total_creditos": 0.0,
    "valor_declarado": 90.0,
}


class SmtpFake:
    def __init__(self, servidor, porta, timeout):
        self.inicializacao = (servidor, porta, timeout)
        self.chamadas = []

    def starttls(self):
        self.chamadas.append("starttls")

    def login(self, remetente, senha):
        self.chamadas.append(("login", remetente, senha))

    def sendmail(self, remetente, destinatarios, mensagem):
        self.chamadas.append(("sendmail", remetente, destinatarios, mensagem))

    def quit(self):
        self.chamadas.append("quit")


class BotFiscalTests(unittest.TestCase):
    def test_envia_alerta_com_timeout_quando_existe_divergencia(self):
        instancias = []

        def criar_smtp(*args, **kwargs):
            instancia = SmtpFake(*args, **kwargs)
            instancias.append(instancia)
            return instancia

        enviado = enviar_alerta_fiscal(
            CONFIGURACAO,
            smtp_factory=criar_smtp,
            timeout=7,
            **DADOS,
        )

        self.assertTrue(enviado)
        self.assertEqual(instancias[0].inicializacao, ("smtp.exemplo.com", 587, 7))
        self.assertIn("starttls", instancias[0].chamadas)
        self.assertIn("quit", instancias[0].chamadas)

    def test_nao_conecta_quando_nao_existe_divergencia(self):
        with patch("utils.bot_fiscal.smtplib.SMTP") as smtp:
            enviado = enviar_alerta_fiscal(
                CONFIGURACAO,
                **{**DADOS, "valor_declarado": 100.0},
            )

        self.assertFalse(enviado)
        smtp.assert_not_called()

    def test_log_smtp_nao_expoe_senha(self):
        instancias = []

        def criar_smtp(*args, **kwargs):
            instancia = SmtpFake(*args, **kwargs)
            instancias.append(instancia)
            return instancia

        with self.assertLogs("utils.bot_fiscal", level="INFO") as logs:
            enviar_alerta_fiscal(
                CONFIGURACAO,
                smtp_factory=criar_smtp,
                **DADOS,
            )

        saida = "\n".join(logs.output)
        self.assertIn("Alerta fiscal enviado por SMTP", saida)
        self.assertIn("smtp.exemplo.com", saida)
        self.assertNotIn("senha", saida)


    def test_agendamento_usa_thread_daemon(self):
        with patch("utils.bot_fiscal.threading.Thread") as thread:
            instancia = thread.return_value

            retornada = agendar_alerta_fiscal(CONFIGURACAO, **DADOS)

        self.assertIs(retornada, instancia)
        self.assertTrue(thread.call_args.kwargs["daemon"])
        instancia.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
