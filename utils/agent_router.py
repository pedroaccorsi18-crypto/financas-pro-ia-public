from utils.agent_audit import AuditLogger
from utils.agent_intents import (
    COSTO_ALTO,
    COSTO_BAIXO,
    COSTO_BLOQUEADO,
    COSTO_MEDIO,
    EMAIL_MONITORAMENTO_AUTORIZADO,
    AgentDecision,
    AgentRequest,
    INTENCAO_DESCONHECIDA,
    INTENCAO_EDUCADOR,
    INTENCAO_FINANCEIRA,
    INTENCAO_FISCAL,
)
from utils.agent_privacy import PrivacyGuard
from utils.agent_registry import AgentRegistry


class IntentClassifier:
    _ALIASES = {
        INTENCAO_FINANCEIRA: INTENCAO_FINANCEIRA,
        "financeira": INTENCAO_FINANCEIRA,
        "planejamento": INTENCAO_FINANCEIRA,
        "orcamento": INTENCAO_FINANCEIRA,
        "orçamento": INTENCAO_FINANCEIRA,
        INTENCAO_EDUCADOR: INTENCAO_EDUCADOR,
        "educacao": INTENCAO_EDUCADOR,
        "educação": INTENCAO_EDUCADOR,
        "explicacao": INTENCAO_EDUCADOR,
        "explicação": INTENCAO_EDUCADOR,
        INTENCAO_FISCAL: INTENCAO_FISCAL,
        "importacao": INTENCAO_FISCAL,
        "importação": INTENCAO_FISCAL,
        "alerta": INTENCAO_FISCAL,
    }
    _PALAVRAS_FINANCEIRAS = (
        "gasto",
        "despesa",
        "receita",
        "meta",
        "orcamento",
        "orçamento",
        "balanco",
        "balanço",
        "planejamento",
    )
    _PALAVRAS_EDUCADOR = (
        "explique",
        "explicar",
        "conceito",
        "o que significa",
        "como funciona",
        "me ensine",
    )
    _PALAVRAS_FISCAL = (
        "alerta",
        "divergencia",
        "divergência",
        "importacao",
        "importação",
        "extrato",
        "fatura",
        "pdf",
        "reimportacao",
        "reimportação",
    )

    def classify(self, request: AgentRequest) -> str:
        hint = str(request.intent_hint or "").strip().lower()
        if hint in self._ALIASES:
            return self._ALIASES[hint]

        texto = str(request.input_text or "").lower()
        if any(palavra in texto for palavra in self._PALAVRAS_FISCAL):
            return INTENCAO_FISCAL
        if any(palavra in texto for palavra in self._PALAVRAS_EDUCADOR):
            return INTENCAO_EDUCADOR
        if any(palavra in texto for palavra in self._PALAVRAS_FINANCEIRAS):
            return INTENCAO_FINANCEIRA
        return INTENCAO_DESCONHECIDA


class PolicyEngine:
    _COST_BY_INTENT = {
        INTENCAO_FINANCEIRA: COSTO_MEDIO,
        INTENCAO_EDUCADOR: COSTO_BAIXO,
        INTENCAO_FISCAL: COSTO_MEDIO,
        INTENCAO_DESCONHECIDA: COSTO_BAIXO,
    }
    _COST_ORDER = {
        COSTO_BAIXO: 1,
        COSTO_MEDIO: 2,
        COSTO_ALTO: 3,
        COSTO_BLOQUEADO: 0,
    }

    def cost_tier_for(self, intent: str) -> str:
        return self._COST_BY_INTENT.get(intent, COSTO_BAIXO)

    def enforce_cost_limit(self, *, requested_tier: str, max_cost_tier: str) -> str:
        max_tier = max_cost_tier if max_cost_tier in self._COST_ORDER else COSTO_BAIXO
        if max_tier == COSTO_BLOQUEADO:
            return COSTO_BLOQUEADO
        if self._COST_ORDER.get(requested_tier, 1) > self._COST_ORDER[max_tier]:
            return max_tier
        return requested_tier

    def provider_for(self, *, cost_tier: str) -> tuple[str, str]:
        if cost_tier == COSTO_BLOQUEADO:
            return ("none", "blocked")
        return ("gemini", "gemini-2.5-flash")


class AgentRouter:
    def __init__(
        self,
        *,
        registry: AgentRegistry | None = None,
        classifier: IntentClassifier | None = None,
        policy_engine: PolicyEngine | None = None,
        privacy_guard: PrivacyGuard | None = None,
        audit_logger: AuditLogger | None = None,
    ):
        self.registry = registry or AgentRegistry()
        self.classifier = classifier or IntentClassifier()
        self.policy_engine = policy_engine or PolicyEngine()
        self.privacy_guard = privacy_guard or PrivacyGuard()
        self.audit_logger = audit_logger or AuditLogger()

    def route(self, request: AgentRequest) -> AgentDecision:
        classified_intent = self.classifier.classify(request)
        if classified_intent == INTENCAO_DESCONHECIDA:
            intent = INTENCAO_EDUCADOR
            audit_reason = "fallback_intencao_desconhecida"
        else:
            intent = classified_intent
            audit_reason = "intent_hint" if request.intent_hint else "palavras_chave"

        agent = self.registry.get_agent_for_intent(intent)
        requested_cost = self.policy_engine.cost_tier_for(classified_intent)
        cost_tier = self.policy_engine.enforce_cost_limit(
            requested_tier=requested_cost,
            max_cost_tier=request.max_cost_tier,
        )
        provider_name, model = self.policy_engine.provider_for(cost_tier=cost_tier)
        input_text_for_agent = self.privacy_guard.sanitize(
            request.input_text,
            dados_sensiveis=request.dados_sensiveis,
        )
        decision = AgentDecision(
            intent=intent,
            agent_name=agent.name,
            provider_name=provider_name,
            model=model,
            cost_tier=cost_tier,
            requires_anonymization=request.dados_sensiveis,
            input_text_for_agent=input_text_for_agent,
            fallback_models=agent.fallback_models,
            audit_reason=audit_reason,
            monitoramento_email_autorizado=(
                str(request.email_usuario).strip().lower() == EMAIL_MONITORAMENTO_AUTORIZADO
            ),
        )
        self.audit_logger.record_decision(request=request, decision=decision)
        return decision
