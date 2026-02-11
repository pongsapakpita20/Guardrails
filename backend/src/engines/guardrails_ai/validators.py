from typing import Dict, Any
import re
from guardrails.validators import ( # type: ignore
    Validator,
    register_validator,
    ValidationResult,
    PassResult,
    FailResult,
)

# ==========================================
# 🛡️ ZONE 1: Custom Validators (Input Rails)
# ==========================================

@register_validator(name="mock_jailbreak", data_type="string")
class MockJailbreak(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        triggers = ["ignore previous", "bypass", "system prompt", "jailbreak"]
        if any(t in value.lower() for t in triggers):
            return FailResult(error_message="Jailbreak attempt detected.", fix_value="")
        return PassResult()

@register_validator(name="mock_profanity", data_type="string")
class MockProfanity(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        bad_words = ["เลว", "โง่", "stupid", "idiot", "damn"]
        if any(w in value.lower() for w in bad_words):
            return FailResult(
                error_message=f"Profanity found: {value}", fix_value="***"
            )
        return PassResult()

@register_validator(name="mock_pii", data_type="string")
class MockPII(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if re.search(r"\d{10}", value):
            return FailResult(
                error_message="PII detected (Phone Number).", fix_value="[REDACTED]"
            )
        return PassResult()

@register_validator(name="mock_topic", data_type="string")
class MockTopic(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        forbidden = ["การเมือง", "politics", "crypto", "bitcoin"]
        if any(f in value.lower() for f in forbidden):
            return FailResult(error_message="Off-topic content detected.", fix_value="")
        return PassResult()

@register_validator(name="mock_gibberish", data_type="string")
class MockGibberish(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if len(value) > 10 and len(set(value.lower())) < 4:
            return FailResult(error_message="Gibberish input detected.", fix_value="")
        return PassResult()

# ==========================================
# 🛡️ ZONE 2: Custom Validators (Output Rails)
# ==========================================

@register_validator(name="mock_hallucination", data_type="string")
class MockHallucination(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        if "flat" in value.lower() and "earth" in value.lower():
            return FailResult(
                error_message="Hallucination detected (Fact Check).", fix_value=""
            )
        return PassResult()

@register_validator(name="mock_json_format", data_type="string")
class MockJSONFormat(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        v = value.strip()
        if not (v.startswith("{") and v.endswith("}")):
            return FailResult(error_message="Output is not valid JSON.", fix_value="{}")
        return PassResult()