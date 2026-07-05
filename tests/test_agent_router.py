import unittest

from utils.agent_intents import (
    COSTO_ALTO,
    AgentRequest,
    INTENCAO_EDUCADOR,
    INTENCAO_FINANCEIRA,
    INTENCAO_FISCAL,
)
from utils.agent_router import AgentRouter


class AgentRouterTests(unittest.TestCase):
    def criar_request(self, **kwargs):
        dados = {
            "user_id": "user-1",
            "email_usuario": "cliente@example.com",
            "input_text": "Quero analisar meus gastos do mês.",
            "max_cost_tier": COSTO_ALTO,
        }
        dados.update(kwargs)
        return AgentRequest(**dados)

    def test_roteia_intencao_financeira_para_agente_financeiro(self):
        router = AgentRouter()

        decisao = router.route(
            self.criar_request(intent_hint="financeiro", input_text="Avalie meu orçamento.")
        )

        self.assertEqual(decisao.intent, INTENCAO_FINANCEIRA)
        self.assertEqual(decisao.agent_name, "Agente Financeiro")
        self.assertEqual(decisao.provider_name, "gemini")

    def test_roteia_explicacao_para_agente_educador(self):
        router = AgentRouter()

        decisao = router.route(
            self.criar_request(
                intent_hint=None,
                input_text="Explique o conceito de reserva de emergência.",
            )
        )

        self.assertEqual(decisao.intent, INTENCAO_EDUCADOR)
        self.assertEqual(decisao.agent_name, "Agente Educador")

    def test_roteia_alerta_divergencia_importacao_para_agente_fiscal(self):
        router = AgentRouter()

        decisao = router.route(
            self.criar_request(
                intent_hint=None,
                input_text="Houve divergência na importação do PDF da fatura.",
            )
        )

        self.assertEqual(decisao.intent, INTENCAO_FISCAL)
        self.assertEqual(decisao.agent_name, "Agente Fiscal")

    def test_aplica_anonimizacao_quando_dados_sensiveis(self):
        router = AgentRouter()

        decisao = router.route(
            self.criar_request(
                input_text="Gastei R$ 1.234,56 no cartão e recebi 9876,54.",
                dados_sensiveis=True,
            )
        )

        self.assertTrue(decisao.requires_anonymization)
        self.assertIn("[VALOR_OCULTO]", decisao.input_text_for_agent)
        self.assertNotIn("1.234,56", decisao.input_text_for_agent)
        self.assertNotIn("9876,54", decisao.input_text_for_agent)

    def test_audit_log_nao_expoe_valores_financeiros(self):
        router = AgentRouter()

        router.route(
            self.criar_request(
                input_text="Minha despesa foi R$ 9.999,99 e meu saldo é 1234,56.",
                dados_sensiveis=True,
            )
        )

        evento = router.audit_logger.last_event()
        texto_evento = str(evento)
        self.assertNotIn("9.999,99", texto_evento)
        self.assertNotIn("1234,56", texto_evento)
        self.assertNotIn("Minha despesa", texto_evento)
        self.assertEqual(evento["event"], "agent_router_decision")

    def test_trava_monitoramento_apenas_para_email_autorizado(self):
        router = AgentRouter()

        decisao_autorizada = router.route(
            self.criar_request(email_usuario="pedroaccorsi18@gmail.com")
        )
        decisao_cliente = router.route(
            self.criar_request(email_usuario="cliente@example.com")
        )

        self.assertTrue(decisao_autorizada.monitoramento_email_autorizado)
        self.assertFalse(decisao_cliente.monitoramento_email_autorizado)

    def test_retorna_fallback_seguro_para_intencao_desconhecida(self):
        router = AgentRouter()

        decisao = router.route(
            self.criar_request(
                intent_hint=None,
                input_text="Preciso falar sobre um assunto genérico.",
            )
        )

        self.assertEqual(decisao.intent, INTENCAO_EDUCADOR)
        self.assertEqual(decisao.agent_name, "Agente Educador")
        self.assertEqual(decisao.audit_reason, "fallback_intencao_desconhecida")


if __name__ == "__main__":
    unittest.main()
