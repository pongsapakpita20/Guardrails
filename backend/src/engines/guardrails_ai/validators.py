from typing import Dict, Any, List
from guardrails.validators import ( # type: ignore
    Validator,
    register_validator,
    ValidationResult,
    PassResult,
    FailResult,
)

# Import from Hub (Assumes installation inside Docker)
try:
    from guardrails.hub import DetectPII
    from guardrails.hub import RestrictToTopic
    from guardrails.hub import DetectJailbreak
    from guardrails.hub import SelfCheck
    from guardrails.hub import ToxicLanguage
    from guardrails.hub import CompetitorCheck
except ImportError:
    print("⚠️ Warning: Guardrails Hub validators not installed. Please run 'guardrails hub install ...'")
    # Define dummy classes to prevent crash if not installed
    class DetectPII(Validator): pass
    class RestrictToTopic(Validator): pass
    class DetectJailbreak(Validator): pass
    class SelfCheck(Validator): pass
    class ToxicLanguage(Validator): pass
    class CompetitorCheck(Validator): pass

# ==========================================
# 🛡️ ZONE 1: Input Rails (Wrappers)
# ==========================================

# 1.1 PII
@register_validator(name="hub_pii", data_type="string")
class HubPII(Validator):
    def __init__(self, piis: List[str] = None, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)
        # Default entities commonly used
        self.validator = DetectPII(pii_entities=piis or ["PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD"], on_fail=on_fail)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 1.2 Off-Topic
@register_validator(name="hub_topic", data_type="string")
class HubTopic(Validator):
    def __init__(self, valid_topics: List[str] = None, invalid_topics: List[str] = None, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        # RestrictToTopic might need 'llm_callable'passed via kwargs or set globally
        self.validator = RestrictToTopic(valid_topics=valid_topics or [], invalid_topics=invalid_topics or [], on_fail=on_fail, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 1.3 Jailbreak
@register_validator(name="hub_jailbreak", data_type="string")
class HubJailbreak(Validator):
    def __init__(self, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = DetectJailbreak(on_fail=on_fail, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# ==========================================
# 🛡️ ZONE 2: Output Rails (Wrappers)
# ==========================================

# 2.1 Hallucination (SelfCheck)
@register_validator(name="hub_hallucination", data_type="string")
class HubHallucination(Validator):
    def __init__(self, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = SelfCheck(on_fail=on_fail, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 2.2 Profanity & Toxicity
@register_validator(name="hub_toxicity", data_type="string")
class HubToxicity(Validator):
    def __init__(self, threshold: float = 0.5, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = ToxicLanguage(threshold=threshold, validation_method="sentence", on_fail=on_fail, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 2.3 Competitor Check
@register_validator(name="hub_competitor", data_type="string")
class HubCompetitor(Validator):
    def __init__(self, competitors: List[str] = None, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = CompetitorCheck(competitors=competitors or [], on_fail=on_fail, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 2.4 JSON Format (Keep simple helper)
@register_validator(name="mock_json_format", data_type="string")
class MockJSONFormat(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        v = value.strip()
        if not (v.startswith("{") and v.endswith("}")):
            return FailResult(error_message="Output is not valid JSON.", fix_value="{}")
        return PassResult()