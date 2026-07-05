from dataclasses import asdict

from utils.agent_intents import AgentDecision
from utils.observability import fingerprint


class AuditLogger:
    def __init__(self):
        self.events = []

    def record_decision(self, *, request, decision: AgentDecision):
        evento = {
            "event": "agent_router_decision",
            "user_fp": fingerprint(request.user_id),
            "email_fp": fingerprint(request.email_usuario),
            "intent": decision.intent,
            "agent_name": decision.agent_name,
            "provider_name": decision.provider_name,
            "model": decision.model,
            "cost_tier": decision.cost_tier,
            "requires_anonymization": decision.requires_anonymization,
            "fallback_models": list(decision.fallback_models),
            "audit_reason": decision.audit_reason,
            "monitoramento_email_autorizado": decision.monitoramento_email_autorizado,
        }
        self.events.append(evento)
        return evento

    def last_event(self):
        if not self.events:
            return None
        return self.events[-1]

    def decisions_as_dicts(self):
        return [asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event) for event in self.events]
