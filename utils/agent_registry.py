from dataclasses import dataclass

from utils.agent_intents import (
    BaseAgent,
    INTENCAO_EDUCADOR,
    INTENCAO_FINANCEIRA,
    INTENCAO_FISCAL,
)


@dataclass(frozen=True)
class AgenteFinanceiro:
    name: str = "Agente Financeiro"
    supported_intents: tuple[str, ...] = (INTENCAO_FINANCEIRA,)
    default_model: str = "gemini-2.5-flash"
    fallback_models: tuple[str, ...] = ("gemini-2.5-flash",)

    def build_prompt(self, request):
        return request.input_text

    def parse_response(self, response_text):
        return response_text


@dataclass(frozen=True)
class AgenteEducador:
    name: str = "Agente Educador"
    supported_intents: tuple[str, ...] = (INTENCAO_EDUCADOR,)
    default_model: str = "gemini-2.5-flash"
    fallback_models: tuple[str, ...] = ("gemini-2.5-flash",)

    def build_prompt(self, request):
        return request.input_text

    def parse_response(self, response_text):
        return response_text


@dataclass(frozen=True)
class AgenteFiscal:
    name: str = "Agente Fiscal"
    supported_intents: tuple[str, ...] = (INTENCAO_FISCAL,)
    default_model: str = "gemini-2.5-flash"
    fallback_models: tuple[str, ...] = ("gemini-2.5-flash",)

    def build_prompt(self, request):
        return request.input_text

    def parse_response(self, response_text):
        return response_text


class AgentRegistry:
    def __init__(self, agents: tuple[BaseAgent, ...] | None = None):
        self._agents = agents or (
            AgenteFinanceiro(),
            AgenteEducador(),
            AgenteFiscal(),
        )
        self._by_intent = {}
        for agent in self._agents:
            for intent in agent.supported_intents:
                self._by_intent[intent] = agent

    def get_agent_for_intent(self, intent: str) -> BaseAgent:
        return self._by_intent.get(intent, self._by_intent[INTENCAO_EDUCADOR])

    def list_agents(self) -> tuple[BaseAgent, ...]:
        return self._agents
