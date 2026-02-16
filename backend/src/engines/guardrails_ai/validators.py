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
    from guardrails.hub import DetectPII, RestrictToTopic, DetectJailbreak, ToxicLanguage, CompetitorCheck, BespokeMiniCheck # type: ignore
except ImportError:
    print("⚠️ Warning: Guardrails Hub validators not installed or import error.")
    DetectPII = None
    RestrictToTopic = None
    DetectJailbreak = None
    ToxicLanguage = None
    CompetitorCheck = None
    BespokeMiniCheck = None

# ... (omitted)



import json

# ==========================================
# 🛠️ Helper: Validator Caching (Singleton Pattern)
# ==========================================
_VALIDATOR_CACHE: Dict[str, Any] = {}

def get_cached_validator(name: str, constructor: Callable, **kwargs) -> Any:
    # สร้าง Cache Key ที่คงที่โดยใช้ JSON dumps และ sort_keys
    # เราจะใช้เฉพาะค่าคอนฟิกที่ไม่ใช่ callable มาทำเป็น key
    stable_kwargs = {k: v for k, v in kwargs.items() if not callable(v)}
    cache_key = f"{name}_{json.dumps(stable_kwargs, sort_keys=True)}"
    
    if cache_key not in _VALIDATOR_CACHE:
        print(f"📦 [Cache] First time loading weights for {name} (Key: {cache_key})...")
        _VALIDATOR_CACHE[cache_key] = constructor(**kwargs)
    return _VALIDATOR_CACHE[cache_key]

# ==========================================
# 🛡️ ZONE 1: Input Rails (Wrappers with Logic)
# ==========================================

# 1.1 PII (เบอร์โทร)
@register_validator(name="hub_pii", data_type="string")
class HubPII(Validator):
    def __init__(self, piis: List[str] = None, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)
        self.piis = piis or ["PHONE_NUMBER"]
        self.on_fail = on_fail

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if DetectPII:
            validator = get_cached_validator("DetectPII", DetectPII, pii_entities=self.piis, on_fail=self.on_fail)
            return validator.validate(value, metadata)
        return PassResult()

# 1.2 Off-Topic (การเมือง)
@register_validator(name="hub_topic", data_type="string")
class HubTopic(Validator):
    def __init__(self, valid_topics: List[str] = None, invalid_topics: List[str] = None, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.args = {
            "valid_topics": valid_topics,
            "invalid_topics": invalid_topics,
            "on_fail": on_fail,
            "llm_callable": llm_callable,
            **kwargs
        }

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if RestrictToTopic:
            validator = get_cached_validator("RestrictToTopic", RestrictToTopic, **self.args)
            return validator.validate(value, metadata)
        return PassResult()

# 1.3 Jailbreak (Ignore previous)
@register_validator(name="hub_jailbreak", data_type="string")
class HubJailbreak(Validator):
    def __init__(self, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.args = {"on_fail": on_fail, "llm_callable": llm_callable, **kwargs}

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if DetectJailbreak:
            validator = get_cached_validator("DetectJailbreak", DetectJailbreak, **self.args)
            return validator.validate(value, metadata)
        return PassResult()

# 1.4 Toxicity (คำหยาบ)
@register_validator(name="hub_toxicity", data_type="string")
class HubToxicity(Validator):
    def __init__(self, threshold: float = 0.5, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail)
        self.args = {"threshold": threshold, "on_fail": on_fail, **kwargs}

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        text = str(value)
        print(f"🔍 [Debug] Checking Toxicity for: '{text}'")
        
        if ToxicLanguage:
            validator = get_cached_validator("ToxicLanguage", ToxicLanguage, **self.args)
            return validator.validate(value, metadata)
        
        return PassResult()

# 1.5 Competitor Monitor
@register_validator(name="hub_competitor", data_type="string")
class HubCompetitor(Validator):
    def __init__(self, competitors: List[str] = None, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.args = {"competitors": competitors or [], "on_fail": on_fail, "llm_callable": llm_callable, **kwargs}

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if CompetitorCheck:
            validator = get_cached_validator("CompetitorCheck", CompetitorCheck, **self.args)
            return validator.validate(value, metadata)
        return PassResult()

# ==========================================
# 🛡️ ZONE 2: Output Rails
# ==========================================

@register_validator(name="hub_hallucination", data_type="string")
class HubHallucination(Validator):
    def __init__(self, on_fail: str = "exception", llm_callable: Optional[Callable] = None, **kwargs):
        super().__init__(on_fail=on_fail)
        self.validator = None
        if BespokeMiniCheck:
            try:
                self.validator = BespokeMiniCheck(on_fail=on_fail, **kwargs)
            except Exception as e:
                print(f"⚠️ Warning: Failed to initialize BespokeMiniCheck (Hallucination): {e}")
                self.validator = None
        
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if self.validator:
            try:
                return self.validator.validate(value, metadata)
            except Exception as e:
                print(f"⚠️ Warning: BespokeMiniCheck validation failed: {e}")
                return PassResult()
        return PassResult()

@register_validator(name="mock_json_format", data_type="string")
class MockJSONFormat(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        v = str(value).strip()
        if not (v.startswith("{") and v.endswith("}")):
            return FailResult(error_message="Output is not valid JSON.", fix_value="{}")
        return PassResult()