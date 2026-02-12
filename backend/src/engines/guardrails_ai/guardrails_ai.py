from typing import List, Dict, Callable
import requests
import os
from guardrails import Guard # type: ignore
from ..base import BaseGuardEngine, SwitchInfo, GuardResult
from ...llm.factory import LLMFactory

# Import Validators ทั้งหมด
from .validators import (
    HubPII,
    HubTopic,
    HubJailbreak,
    HubHallucination,
    HubToxicity,
    HubCompetitor,
    MockJSONFormat
)

class GuardrailsAIEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        return [
            SwitchInfo(key="jailbreak", label="🛡️ Anti-Jailbreak", default=True),
            SwitchInfo(key="profanity", label="🤬 Anti-Toxicity", default=True),
            SwitchInfo(key="pii", label="🕵️ PII Masking", default=True),
            SwitchInfo(key="off_topic", label="🚧 Topic Control", default=False),
            SwitchInfo(key="hallucination", label="🤥 Anti-Hallucination", default=False),
            SwitchInfo(key="json_format", label="🧩 Force JSON", default=False),
        ]

    async def process(self, message: str, config: Dict[str, bool], **kwargs) -> GuardResult:
        
        # 1. ดึงค่าจาก kwargs (ถ้าไม่มีให้ใช้ Default)
        current_provider = kwargs.get("provider_id", "ollama")
        current_model = kwargs.get("model_name", "scb10x/typhoon2.5-qwen3-4b") # ใช้ default จาก config คุณ

        # 🟢 สร้างฟังก์ชัน llm_callable แบบ Dynamic
        def my_llm_callable(prompt: str) -> str:
            # ใช้ URL ตาม Provider (ตอนนี้เน้น Ollama ไปก่อนเพื่อความง่ายของ Validator)
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
            try:
                res = requests.post(f"{ollama_url}/api/generate", json={
                    "model": current_model,  # <--- ✅ ใช้โมเดลที่เลือกมา
                    "prompt": prompt,
                    "stream": False
                }, timeout=30)
                if res.status_code == 200:
                    return res.json().get("response", "")
                else:
                    print(f"⚠️ LLM Error ({res.status_code}): {res.text}")
            except Exception as e:
                print(f"Validator LLM Connection Error: {e}")
            return ""

        # ... (Step 1: Input Validators เหมือนเดิม) ...
        input_validators = []
        if config.get("jailbreak"): 
            input_validators.append(HubJailbreak(on_fail="exception", llm_callable=my_llm_callable))
        # ... (ตัวอื่น ๆ เหมือนเดิม) ...

        if input_validators:
            try:
                guard = Guard.from_string(validators=input_validators)
                res = guard.parse(message)
                if not res.validation_passed:
                    return GuardResult(safe=False, violation="Input Guard", reason="Blocked by Input Rails")
            except Exception as e:
                print(f"Guard Error: {e}")
                # return GuardResult(safe=False, violation="System Error", reason=str(e))
                pass 

        # -------------------------------------------------
        # Step 2: Call Main LLM (ใช้ Factory)
        # -------------------------------------------------
        try:
            llm_service = LLMFactory.get_service(current_provider) # <--- ✅ ใช้ Provider ที่เลือก
            ai_response = await llm_service.generate(message, model_name=current_model) # <--- ✅ ใช้ Model ที่เลือก
        except Exception as e:
            return GuardResult(safe=False, violation="LLM Error", reason=f"Failed to generate response: {str(e)}")

        # -------------------------------------------------
        # Step 3: Validate OUTPUT
        # -------------------------------------------------
        output_validators = []
        
        if config.get("hallucination"):
            output_validators.append(HubHallucination(on_fail="exception", llm_callable=my_llm_callable))
            
        if config.get("json_format"):
            output_validators.append(MockJSONFormat(on_fail="exception"))

        if output_validators:
            try:
                guard = Guard.from_string(validators=output_validators)
                res = guard.parse(ai_response)
                if not res.validation_passed:
                    return GuardResult(safe=False, violation="Output Guard", reason="AI Response Blocked")
            except Exception as e:
                return GuardResult(safe=False, violation="Output Violation", reason=str(e).split(":")[-1].strip())

        return GuardResult(safe=True, reason=ai_response)