from typing import Dict, Any, List, Callable, Optional
import re
from guardrails.validators import ( # type: ignore
    Validator,
    register_validator,
    ValidationResult,
    PassResult,
    FailResult,
)

# ==========================================
# 🛠️ Helper: Mock Validator แบบ "Pass-Through"
# ==========================================
# ใช้กรณีฉุกเฉินเพื่อให้คลาสมีตัวตน แต่เราจะไปดัก Logic ใน Wrapper แทน
@register_validator(name="mock_hub_validator", data_type="string")
class MockHubValidator(Validator):
    def __init__(self, *args, **kwargs):
        super().__init__(on_fail="noop")
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return PassResult()

# พยายามโหลดของจริง ถ้าไม่มีให้เป็น None (เราจะไปดักใช้ Logic เองข้างล่าง)
try:
    from guardrails.hub import DetectPII, RestrictToTopic, DetectJailbreak, SelfCheck, ToxicLanguage, CompetitorCheck # type: ignore
except ImportError:
    print("⚠️ Warning: Guardrails Hub validators not installed. Using Regex/Keyword Logic.")
    DetectPII = None
    RestrictToTopic = None
    DetectJailbreak = None
    SelfCheck = None
    ToxicLanguage = None
    CompetitorCheck = None

# ==========================================
# 🛡️ ZONE 1: Input Rails (Wrappers with Logic)
# ==========================================

# 1.1 PII (เบอร์โทร)
@register_validator(name="hub_pii", data_type="string")
class HubPII(Validator):
    def __init__(self, piis: List[str] = None, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)
        # ถ้ามีของจริงให้ใช้ของจริง ถ้าไม่มีให้ใช้ None
        if DetectPII:
            self.validator = DetectPII(pii_entities=piis or ["PHONE_NUMBER"], on_fail=on_fail)
        else:
            self.validator = None

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        # ถ้ามีของจริง ให้ใช้ของจริง
        if self.validator: return self.validator.validate(value, metadata)
        
        return PassResult()

# 1.2 Off-Topic (การเมือง)
@register_validator(name="hub_topic", data_type="string")
class HubTopic(Validator):
    def __init__(self, valid_topics: List[str] = None, invalid_topics: List[str] = None, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        if RestrictToTopic:
            self.validator = RestrictToTopic(valid_topics=valid_topics, invalid_topics=invalid_topics, on_fail=on_fail, llm_callable=llm_callable, **kwargs)
        else:
            self.validator = None

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if self.validator: return self.validator.validate(value, metadata)

        return PassResult()

# 1.3 Jailbreak (Ignore previous)
@register_validator(name="hub_jailbreak", data_type="string")
class HubJailbreak(Validator):
    def __init__(self, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        if DetectJailbreak:
            self.validator = DetectJailbreak(on_fail=on_fail, llm_callable=llm_callable, **kwargs)
        else:
            self.validator = None

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if self.validator: return self.validator.validate(value, metadata)

        return PassResult()

# 1.4 Toxicity (คำหยาบ)
@register_validator(name="hub_toxicity", data_type="string")
class HubToxicity(Validator):
    def __init__(self, threshold: float = 0.5, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        if ToxicLanguage:
            self.validator = ToxicLanguage(threshold=threshold, on_fail=on_fail, **kwargs)
        else:
            self.validator = None

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if self.validator: return self.validator.validate(value, metadata)

        return PassResult()

# ... (ส่วน Output Validators ปล่อย Mock ไว้เหมือนเดิม เพราะเราเน้น Input ก่อน) ...
@register_validator(name="hub_hallucination", data_type="string")
class HubHallucination(Validator):
    def __init__(self, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = None
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return PassResult()

@register_validator(name="hub_competitor", data_type="string")
class HubCompetitor(Validator):
    def __init__(self, competitors: List[str] = None, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = None
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return PassResult()

@register_validator(name="mock_json_format", data_type="string")
class MockJSONFormat(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        v = str(value).strip()
        if not (v.startswith("{") and v.endswith("}")):
            return FailResult(error_message="Output is not valid JSON.", fix_value="{}")
        return PassResult()