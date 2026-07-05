from dataclasses import dataclass, field
from typing import Protocol


INTENCAO_FINANCEIRA = "financeiro"
INTENCAO_EDUCADOR = "educador"
INTENCAO_FISCAL = "fiscal"
INTENCAO_DESCONHECIDA = "desconhecida"

COSTO_BAIXO = "baixo"
COSTO_MEDIO = "medio"
COSTO_ALTO = "alto"
COSTO_BLOQUEADO = "bloqueado"

EMAIL_MONITORAMENTO_AUTORIZADO = "pedroaccorsi18@gmail.com"


@dataclass(frozen=True)
class AgentRequest:
    user_id: str
    email_usuario: str
    input_text: str
    intent_hint: str | None = None
    contexto: dict = field(default_factory=dict)
    dados_sensiveis: bool = True
    max_cost_tier: str = COSTO_BAIXO


@dataclass(frozen=True)
class AgentDecision:
    intent: str
    agent_name: str
    provider_name: str
    model: str
    cost_tier: str
    requires_anonymization: bool
    input_text_for_agent: str
    fallback_models: tuple[str, ...]
    audit_reason: str
    monitoramento_email_autorizado: bool


class BaseAgent(Protocol):
    name: str
    supported_intents: tuple[str, ...]
    default_model: str
    fallback_models: tuple[str, ...]

    def build_prompt(self, request: AgentRequest) -> str:
        ...

    def parse_response(self, response_text: str):
        ...
