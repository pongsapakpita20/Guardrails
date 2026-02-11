from typing import List, Dict, Any, Optional
import re
from .base import BaseGuardEngine, SwitchInfo, GuardResult
from guardrails import Guard # type: ignore
from guardrails.validators import ( # type: ignore
    Validator,
    register_validator,
    ValidationResult,
    PassResult,
    FailResult,
)
import requests
import os
import json

# ==========================================
# 🛡️ ZONE 1: Custom Validators (Input Rails)
# ==========================================


@register_validator(name="mock_jailbreak", data_type="string")
class MockJailbreak(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        # ดักจับความพยายามสั่ง AI ให้แหกกฎ
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
        # ดักจับเบอร์โทรศัพท์ 10 หลัก
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
        # ดักจับข้อความมั่วๆ (เช่น พิมพ์ตัวอักษรซ้ำๆ ยาวๆ)
        if len(value) > 10 and len(set(value.lower())) < 4:
            return FailResult(error_message="Gibberish input detected.", fix_value="")
        return PassResult()


# ==========================================
# 🛡️ ZONE 2: Custom Validators (Output Rails)
# ==========================================


@register_validator(name="mock_hallucination", data_type="string")
class MockHallucination(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        # สมมติว่าถ้า AI ตอบว่า "Earth is flat" คือมั่ว
        if "flat" in value.lower() and "earth" in value.lower():
            return FailResult(
                error_message="Hallucination detected (Fact Check).", fix_value=""
            )
        return PassResult()


@register_validator(name="mock_json_format", data_type="string")
class MockJSONFormat(Validator):
    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        # ตรวจแบบง่ายๆ ว่าเริ่มและจบด้วยปีกกาไหม
        v = value.strip()
        if not (v.startswith("{") and v.endswith("}")):
            return FailResult(error_message="Output is not valid JSON.", fix_value="{}")
        return PassResult()


# ==========================================
# 🧠 The Engine Logic
# ==========================================


class GuardrailsAIEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        return [
            # --- Input Switches ---
            SwitchInfo(key="jailbreak", label="🛡️ Anti-Jailbreak (Input)", default=True),
            SwitchInfo(
                key="profanity", label="🤬 Anti-Profanity (Input)", default=True
            ),
            SwitchInfo(key="pii", label="🕵️ PII Masking (Input)", default=True),
            SwitchInfo(
                key="off_topic", label="🚧 Topic Control (Input)", default=False
            ),
            SwitchInfo(
                key="gibberish", label="🤪 Gibberish Filter (Input)", default=True
            ),
            # --- Output Switches ---
            SwitchInfo(
                key="hallucination", label="🤥 Hallucination (Output)", default=False
            ),
            SwitchInfo(
                key="json_format", label="🧩 Force JSON (Output)", default=False
            ),
        ]

    async def process(self, message: str, config: Dict[str, bool]) -> GuardResult:
        """
        กระบวนการทำงาน: ตรวจ Input -> (จำลอง AI ตอบ) -> ตรวจ Output
        """

        # -------------------------------------------------
        # Step 1: Validate INPUT (User Request)
        # -------------------------------------------------
        input_validators = []
        if config.get("jailbreak"):
            input_validators.append(MockJailbreak(on_fail="exception"))
        if config.get("profanity"):
            input_validators.append(MockProfanity(on_fail="exception"))
        if config.get("pii"):
            input_validators.append(MockPII(on_fail="exception"))
        if config.get("off_topic"):
            input_validators.append(MockTopic(on_fail="exception"))
        if config.get("gibberish"):
            input_validators.append(MockGibberish(on_fail="exception"))

        if input_validators:
            try:
                guard = Guard.from_string(validators=input_validators)
                res = guard.parse(message)
                if not res.validation_passed:
                    return GuardResult(
                        safe=False,
                        violation="Input Guard",
                        reason="Blocked by Input Rails",
                    )
            except Exception as e:
                return GuardResult(
                    safe=False,
                    violation="Input Violation",
                    reason=str(e).split(":")[-1].strip(),
                )

        # -------------------------------------------------
        # Step 2: Simulate LLM Generation (จำลองคำตอบ AI)
        # -------------------------------------------------
        
        # ✅✅✅ แก้ไขตรงนี้ครับ ✅✅✅
        # ให้ Default เป็น http://ollama:11434 (ชื่อ Service ใน Docker)
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")

        # 2. เตรียม Payload
        system_prompt = "You are a helpful assistant."
        if config.get("json_format"):
            system_prompt += " You must answer in JSON format only."

        payload = {
            "model": "qwen3:8b",  # ตรวจสอบชื่อรุ่นโมเดลให้ตรงกับที่ pull มา
            "prompt": message,
            "system": system_prompt,
            "stream": False,
        }

        print(f"🚀 Sending request to Remote AI: {ollama_url}...")

        try:
            # 3. ยิง API จริงๆ!
            response = requests.post(
                f"{ollama_url}/api/generate", json=payload, timeout=200
            )

            if response.status_code == 200:
                ai_response = response.json().get("response", "")
            else:
                ai_response = f"Error from AI Server: {response.status_code}"

        except Exception as e:
            print(f"🔥 Connection Failed: {e}")
            ai_response = "Error: Could not connect to Remote AI Server."
        
        # -------------------------------------------------
        # Step 3: Validate OUTPUT (AI Response)
        # -------------------------------------------------
        output_validators = []
        if config.get("hallucination"):
            output_validators.append(MockHallucination(on_fail="exception"))
        if config.get("json_format"):
            output_validators.append(MockJSONFormat(on_fail="exception"))

        if output_validators:
            try:
                guard = Guard.from_string(validators=output_validators)
                res = guard.parse(ai_response)
                if not res.validation_passed:
                    return GuardResult(
                        safe=False,
                        violation="Output Guard",
                        reason="AI Response was blocked (Unsafe Output)",
                    )
            except Exception as e:
                return GuardResult(
                    safe=False,
                    violation="Output Violation",
                    reason=str(e).split(":")[-1].strip(),
                )

        # ถ้าผ่านหมดทั้ง Input และ Output
        # (Optional: ฝากคำตอบกลับไปใน reason เพื่อให้ main.py เห็น ถ้าต้องการ)
        return GuardResult(safe=True, reason=ai_response)