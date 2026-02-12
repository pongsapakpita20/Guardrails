from typing import List, Dict
import requests
import os
from guardrails import Guard # type: ignore
from ..base import BaseGuardEngine, SwitchInfo, GuardResult

from .validators import (
    MockJailbreak,
    MockProfanity,
    MockPII,
    MockTopic,
    MockGibberish,
    MockHallucination,
    MockJSONFormat
)

class GuardrailsAIEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        return [
            # --- Input Switches ---
            SwitchInfo(key="jailbreak", label="🛡️ Anti-Jailbreak (Input)", default=True),
            SwitchInfo(key="profanity", label="🤬 Anti-Profanity (Input)", default=True),
            SwitchInfo(key="pii", label="🕵️ PII Masking (Input)", default=True),
            SwitchInfo(key="off_topic", label="🚧 Topic Control (Input)", default=False),
            SwitchInfo(key="gibberish", label="🤪 Gibberish Filter (Input)", default=True),
            # --- Output Switches ---
            SwitchInfo(key="hallucination", label="🤥 Hallucination (Output)", default=False),
            SwitchInfo(key="json_format", label="🧩 Force JSON (Output)", default=False),
        ]

    async def process(self, message: str, config: Dict[str, bool]) -> GuardResult:
        # -------------------------------------------------
        # Step 1: Validate INPUT
        # -------------------------------------------------
        input_validators = []
        if config.get("jailbreak"): input_validators.append(MockJailbreak(on_fail="exception"))
        if config.get("profanity"): input_validators.append(MockProfanity(on_fail="exception"))
        if config.get("pii"):       input_validators.append(MockPII(on_fail="exception"))
        if config.get("off_topic"): input_validators.append(MockTopic(on_fail="exception"))
        if config.get("gibberish"): input_validators.append(MockGibberish(on_fail="exception"))

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
        # Step 2: Call LLM
        # -------------------------------------------------
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
        from ...config import MODEL_NAME, SYSTEM_PROMPT

        # ปรับ System Prompt ตาม Config และเงื่อนไข JSON
        current_system_prompt = SYSTEM_PROMPT
        if config.get("json_format"):
            current_system_prompt += " \n(IMPORTANT: You must answer in JSON format only.)"

        payload = {
            "model": MODEL_NAME, 
            "prompt": message,
            "system": current_system_prompt,
            "stream": False,
        }

        print(f"🚀 Sending request to Remote AI: {ollama_url}...")

        try:
            # เพิ่ม Timeout เป็น 200 วินาที ตามที่คุณต้องการ
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
        # Step 3: Validate OUTPUT
        # -------------------------------------------------
        output_validators = []
        if config.get("hallucination"): output_validators.append(MockHallucination(on_fail="exception"))
        if config.get("json_format"):   output_validators.append(MockJSONFormat(on_fail="exception"))

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

        return GuardResult(safe=True, reason=ai_response)