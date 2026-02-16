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
            SwitchInfo(key="competitor_check", label="🏢 Competitor Check", default=False),
            SwitchInfo(key="hallucination", label="🤥 Anti-Hallucination", default=False),
            SwitchInfo(key="json_format", label="🧩 Force JSON", default=False),
        ]

    async def process(self, message: str, config: Dict[str, bool], **kwargs) -> GuardResult:
        
        # 1. ดึงค่า Model/Provider
        current_provider = kwargs.get("provider_id", "ollama")
        current_model = kwargs.get("model_name", "scb10x/typhoon2.5-qwen3-4b")

        # 🟢 สร้างฟังก์ชัน llm_callable
        def my_llm_callable(prompt: str, *args, **kwargs) -> str:
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
            try:
                res = requests.post(f"{ollama_url}/api/generate", json={
                    "model": current_model,
                    "prompt": prompt,
                    "stream": False
                }, timeout=30)
                if res.status_code == 200:
                    return res.json().get("response", "")
            except Exception as e:
                print(f"Validator LLM Error: {e}")
            return ""

        # -------------------------------------------------
        # Step 1: Validate INPUT
        # -------------------------------------------------
        input_validators = []
        
        if config.get("jailbreak"): 
            input_validators.append(HubJailbreak(on_fail="exception", llm_callable=my_llm_callable))
            
        if config.get("profanity"):
            input_validators.append(HubToxicity(on_fail="exception"))
            
        if config.get("pii"):
            # 1.1 Enhanced PII Check used: EMAIL, PHONE, CREDIT_CARD, IP, URL
            input_validators.append(HubPII(
                piis=["EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS", "CREDIT_CARD", "URL"], 
                on_fail="exception"
            ))

        print(f"DEBUG: Guardrails AI FULL Config -> {config}")
        if config.get("off_topic"):
            input_validators.append(HubTopic(
                valid_topics=[
                    "SRT_SERVICE: Questions about Thai railway services, train schedules, buying tickets, station facilities (like luggage storage), and official SRT information."
                ], 
                invalid_topics=[
                    "OTHER: Any topic that is NOT about Thai railway services, including general knowledge (dates, weather), social chat, greetings, politics, or other transportation."
                ],
                on_fail="exception",
                llm_callable=my_llm_callable
            ))
        
        # -------------------------------------------------
        # Input Guard Execution
        # -------------------------------------------------
        print(f"🛡️ [Guardrails AI] Total Input Validators: {len(input_validators)}")
        print(f"🛡️ [Guardrails AI] Validator Names: {[type(v).__name__ for v in input_validators]}")
        if input_validators:
            try:
                print(f"🛡️ [Guardrails AI] Testing Input: '{message}'")
                guard = Guard.from_string(validators=input_validators)
                res = guard.parse(message)
                
                if not res.validation_passed:
                    print(f"🚫 [Guardrails AI] Input Blocked. Reason: {res.validation_summaries}")
                    return GuardResult(safe=False, violation="Input Guard", reason="Blocked by Input Rails")
                
                print(f"✅ [Guardrails AI] Input Passed.")
            except Exception as e:
                # ✅ แก้ไขตรงนี้: จับ Error ได้แล้วต้อง "บล็อก" ทันที ห้ามปล่อยผ่าน!
                error_msg = str(e)
                print(f"🚫 [Guardrails AI] Exception Blocked: {error_msg}")
                
                # ดึงข้อความแจ้งเตือนที่สวยๆ ออกมา (ตัดส่วน technical ทิ้ง)
                user_reason = error_msg.split(":")[-1].strip()
                if "Validation failed" in user_reason:
                     # พยายามหาข้อความที่เราเขียนไว้ใน validators.py
                     if "Jailbreak" in error_msg: user_reason = "Jailbreak attempt detected."
                     elif "PII" in error_msg: user_reason = "Privacy violation detected."
                     elif "Off-topic" in error_msg: user_reason = "Off-topic content detected."
                     elif "Toxic" in error_msg: user_reason = "Toxic language detected."

                return GuardResult(safe=False, violation="Security Violation", reason=user_reason)

        # -------------------------------------------------
        # Step 2: Call Main LLM
        # -------------------------------------------------
        try:
            llm_service = LLMFactory.get_service(current_provider)
            ai_response = await llm_service.generate(message, model_name=current_model)
        except Exception as e:
            return GuardResult(safe=False, violation="System Error", reason=f"LLM Error: {str(e)}")

        # -------------------------------------------------
        # Step 3: Validate OUTPUT
        # -------------------------------------------------
        output_validators = []
        if config.get("hallucination"):
            output_validators.append(HubHallucination(on_fail="exception", llm_callable=my_llm_callable))
        
        # 2.3 Competitor Check (Output Rail)
        if config.get("competitor_check"):
             output_validators.append(HubCompetitor(
                 competitors=["Nakhonchai Air", "AirAsia", "Nok Air", "Thai Lion Air", "Grab", "Uber", "Bolt", "Sombat Tour"], 
                 on_fail="exception",
                 llm_callable=my_llm_callable
             ))

        if config.get("json_format"):
            output_validators.append(MockJSONFormat(on_fail="exception"))

        if output_validators:
            try:
                guard = Guard.from_string(validators=output_validators)
                res = guard.parse(ai_response)
                if not res.validation_passed:
                    return GuardResult(safe=False, violation="Output Guard", reason="AI Response Blocked")
            except Exception as e:
                print(f"🛡️ Output Guard Blocked: {e}")
                return GuardResult(safe=False, violation="Output Violation", reason="AI Response unsafe")

        return GuardResult(safe=True, reason=ai_response)