from typing import Dict, Any, List, Callable, Optional
from guardrails.validators import ( # type: ignore
    Validator,
    register_validator,
    ValidationResult,
    PassResult,
    FailResult,
)

# ==========================================
# 🛠️ Helper: Dummy Validator (กัน Crash)
# ==========================================
# ✅ เพิ่มบรรทัดนี้ครับ: ลงทะเบียนให้ระบบรู้จัก
@register_validator(name="mock_hub_validator", data_type="string")
class MockHubValidator(Validator):
    def __init__(self, *args, **kwargs):
        # รับ arguments อะไรก็ได้ แล้วไม่ทำอะไร
        super().__init__(on_fail="noop")
    
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        # print(f"⚠️ Warning: Using Mock Validator because Guardrails Hub is not installed.")
        return PassResult()

# Import from Hub (พยายามโหลดของจริง ถ้าไม่มีให้ใช้ของปลอม)
try:
    from guardrails.hub import DetectPII # type: ignore
    from guardrails.hub import RestrictToTopic # type: ignore
    from guardrails.hub import DetectJailbreak # type: ignore
    from guardrails.hub import SelfCheck # type: ignore
    from guardrails.hub import ToxicLanguage # type: ignore
    from guardrails.hub import CompetitorCheck # type: ignore
except ImportError:
    print("⚠️ Warning: Guardrails Hub validators not installed. Using Mocks.")
    DetectPII = MockHubValidator
    RestrictToTopic = MockHubValidator
    DetectJailbreak = MockHubValidator
    SelfCheck = MockHubValidator
    ToxicLanguage = MockHubValidator
    CompetitorCheck = MockHubValidator

# ==========================================
# 🛡️ ZONE 1: Input Rails (Wrappers)
# ==========================================

# 1.1 PII
@register_validator(name="hub_pii", data_type="string")
class HubPII(Validator):
    def __init__(self, piis: List[str] = None, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)
        self.validator = DetectPII(pii_entities=piis or ["PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD"], on_fail=on_fail)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 1.2 Off-Topic
@register_validator(name="hub_topic", data_type="string")
class HubTopic(Validator):
    def __init__(self, valid_topics: List[str] = None, invalid_topics: List[str] = None, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = RestrictToTopic(
            valid_topics=valid_topics or ["General conversation"], 
            invalid_topics=invalid_topics or [], 
            on_fail=on_fail, 
            llm_callable=llm_callable, # รับฟังก์ชันมาจาก engine.py
            **kwargs
        )

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 1.3 Jailbreak
@register_validator(name="hub_jailbreak", data_type="string")
class HubJailbreak(Validator):
    def __init__(self, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = DetectJailbreak(on_fail=on_fail, llm_callable=llm_callable, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# ==========================================
# 🛡️ ZONE 2: Output Rails (Wrappers)
# ==========================================

# 2.1 Hallucination
@register_validator(name="hub_hallucination", data_type="string")
class HubHallucination(Validator):
    def __init__(self, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = SelfCheck(on_fail=on_fail, llm_callable=llm_callable, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 2.2 Toxicity
@register_validator(name="hub_toxicity", data_type="string")
class HubToxicity(Validator):
    def __init__(self, threshold: float = 0.5, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = ToxicLanguage(threshold=threshold, validation_method="sentence", on_fail=on_fail, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 2.3 Competitor
@register_validator(name="hub_competitor", data_type="string")
class HubCompetitor(Validator):
    def __init__(self, competitors: List[str] = None, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = CompetitorCheck(competitors=competitors or [], on_fail=on_fail, llm_callable=llm_callable, **kwargs)

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return self.validator.validate(value, metadata)

# 2.4 JSON Format
@register_validator(name="mock_json_format", data_type="string")
class MockJSONFormat(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        v = value.strip()
        if not (v.startswith("{") and v.endswith("}")):
            return FailResult(error_message="Output is not valid JSON.", fix_value="{}")
        return PassResult()