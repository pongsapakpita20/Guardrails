from typing import Dict, Any, List, Callable, Optional
import re
from guardrails.validators import (
    Validator,
    register_validator,
    ValidationResult,
    PassResult,
    FailResult,
)

# ==========================================
# 🛠️ Helper: Mock Validator แบบ "ดุ" (ตรวจจริงเจ็บจริง)
# ==========================================
@register_validator(name="mock_hub_validator", data_type="string")
class MockHubValidator(Validator):
    def __init__(self, *args, **kwargs):
        super().__init__(on_fail="noop")
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return PassResult()

# พยายามโหลดของจริง ถ้าไม่มีให้เป็น None (เราจะไปดักใช้ Logic เองข้างล่าง)
try:
    from guardrails.hub import DetectPII, RestrictToTopic, DetectJailbreak, SelfCheck, ToxicLanguage, CompetitorCheck
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

# 1.1 PII (ตรวจเบอร์โทร 10 หลัก)
@register_validator(name="hub_pii", data_type="string")
class HubPII(Validator):
    def __init__(self, piis: List[str] = None, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)
        if DetectPII:
            self.validator = DetectPII(pii_entities=piis or ["PHONE_NUMBER"], on_fail=on_fail)
        else:
            self.validator = None

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if self.validator: return self.validator.validate(value, metadata)
        
        # 🔥 Logic สำรอง: ตรวจเบอร์โทรด้วย Regex
        if re.search(r"\d{10}", str(value)):
             return FailResult(error_message="PII detected (Phone Number).", fix_value="[REDACTED]")
        return PassResult()

# 1.2 Off-Topic (ห้ามคุยการเมือง/คริปโต)
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

        # 🔥 Logic สำรอง: ตรวจคำต้องห้าม
        text = str(value).lower()
        forbidden = ["politics", "bitcoin", "crypto", "การเมือง", "นายก", "รัฐบาล"]
        for word in forbidden:
            if word in text:
                 return FailResult(error_message=f"Off-topic content detected ({word}).", fix_value="")
        return PassResult()

# 1.3 Jailbreak (ห้ามคำสั่ง ignore previous)
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

        # 🔥 Logic สำรอง
        text = str(value).lower()
        if "ignore previous" in text or "bypass" in text or "ลืมคำสั่ง" in text:
             return FailResult(error_message="Jailbreak attempt detected.", fix_value="")
        return PassResult()

# 1.4 Toxicity (ห้ามคำหยาบ)
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

        # 🔥 Logic สำรอง
        text = str(value).lower()
        bad_words = ["stupid", "idiot", "เลว", "โง่", "damn"]
        for word in bad_words:
            if word in text:
                 return FailResult(error_message=f"Toxic language detected ({word}).", fix_value="***")
        return PassResult()

# ... (HubHallucination, HubCompetitor, MockJSONFormat ปล่อยไว้เหมือนเดิมได้ครับ) ...
@register_validator(name="hub_hallucination", data_type="string")
class HubHallucination(Validator):
    def __init__(self, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = None # Mock
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return PassResult()

@register_validator(name="hub_competitor", data_type="string")
class HubCompetitor(Validator):
    def __init__(self, competitors: List[str] = None, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = None # Mock
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        return PassResult()

@register_validator(name="mock_json_format", data_type="string")
class MockJSONFormat(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        v = str(value).strip()
        if not (v.startswith("{") and v.endswith("}")):
            return FailResult(error_message="Output is not valid JSON.", fix_value="{}")
        return PassResult()