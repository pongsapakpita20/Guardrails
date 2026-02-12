from typing import List, Dict, Any
import requests
import os
from guardrails import Guard # type: ignore
from ..base import BaseGuardEngine, SwitchInfo, GuardResult
from ...config import MODEL_NAME, SYSTEM_PROMPT

from .validators import (
    HubJailbreak,
    HubToxicity,
    HubPII,
    HubTopic,     # Needs LLM
    HubHallucination, # Needs LLM (SelfCheck)
    HubCompetitor,
    MockJSONFormat # Helper
)

class GuardrailsAIEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        return [
            # --- Input Switches ---
            SwitchInfo(key="jailbreak", label="🛡️ Anti-Jailbreak (Hub)", default=True),
            SwitchInfo(key="profanity", label="🤬 Anti-Toxicity (Hub)", default=True),
            SwitchInfo(key="pii", label="🕵️ PII Masking (Hub)", default=True),
            SwitchInfo(key="off_topic", label="🚧 Topic Control (Hub)", default=True), # Default True for SRT
            SwitchInfo(key="competitor", label="🏢 Competitor Check (Hub)", default=True),
            
            # --- Output Switches ---
            SwitchInfo(key="hallucination", label="🤥 Hallucination (SelfCheck)", default=False),
            SwitchInfo(key="json_format", label="🧩 Force JSON (Output)", default=False),
        ]

    def _ollama_callable(self, prompt: str, **kwargs) -> str:
        """Helper to call Ollama from within Validators (if needed)"""
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        }
        try:
            res = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=60)
            if res.status_code == 200:
                return res.json().get("response", "")
        except Exception as e:
            print(f"Error in LLM Callable: {e}")
        return ""

    async def process(self, message: str, config: Dict[str, bool]) -> GuardResult:
        # -------------------------------------------------
        # Step 1: Validate INPUT
        # -------------------------------------------------
        input_validators = []
        
        # 1.1 Jailbreak
        if config.get("jailbreak"): 
            input_validators.append(HubJailbreak(on_fail="exception", llm_callable=self._ollama_callable))

        # 1.2 PII
        if config.get("pii"):       
            input_validators.append(HubPII(on_fail="exception"))

        # 1.3 Toxicity
        if config.get("profanity"): 
            input_validators.append(HubToxicity(on_fail="exception"))

        # 1.4 Topic Control (SRT Specific)
        if config.get("off_topic"):
            input_validators.append(HubTopic(
                valid_topics=["State Railway of Thailand", "Train Schedules", "Ticket Prices", "SRT Services", "Complaint", "Cargo"],
                invalid_topics=["Politics", "Religion", "Cryptocurrency", "competitors", "Airlines"],
                on_fail="exception",
                llm_callable=self._ollama_callable
            ))
            
        # 1.5 Competitor Check
        if config.get("competitor"):
            input_validators.append(HubCompetitor(
                competitors=["AirAsia", "Nok Air", "Thai Lion Air", "Bus Express", "Nakhonchai Air"],
                on_fail="exception",
                llm_callable=self._ollama_callable
            ))

        if input_validators:
            try:
                guard = Guard.from_string(validators=input_validators)
                # Note: Some validators might need prompt_params or direct LLM calls internally
                res = guard.parse(message)
                if not res.validation_passed:
                    return GuardResult(
                        safe=False,
                        violation="Input Policy Violation",
                        reason=f"Blocked by Guardrails: {res.validation_output or 'Unsafe Input'}",
                    )
            except Exception as e:
                # Handle ImportErrors or missing Hub installations gracefully
                err_msg = str(e)
                if "not installed" in err_msg or "module" in err_msg:
                    print(f"⚠️ Guardrails Hub Error: {err_msg} (Did you run 'guardrails hub install'?)")
                else:
                    return GuardResult(
                        safe=False,
                        violation="Guard Error",
                        reason=f"Input Guard Failed: {err_msg}",
                    )

        # -------------------------------------------------
        # Step 2: Call LLM (Business Logic)
        # -------------------------------------------------
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
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
            response = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=200)
            if response.status_code == 200:
                ai_response = response.json().get("response", "")
            else:
                ai_response = f"Error from AI Server: {response.status_code}"
                return GuardResult(safe=True, reason=ai_response) # Return error as response

        except Exception as e:
            print(f"🔥 Connection Failed: {e}")
            return GuardResult(safe=False, violation="Connection Error", reason="Could not connect to Remote AI Server.")

        # -------------------------------------------------
        # Step 3: Validate OUTPUT
        # -------------------------------------------------
        output_validators = []
        
        # 2.1 Hallucination (SelfCheck)
        if config.get("hallucination"): 
            output_validators.append(HubHallucination(on_fail="exception", llm_callable=self._ollama_callable))
            
        # 2.2 JSON Format
        if config.get("json_format"):   
            output_validators.append(MockJSONFormat(on_fail="exception"))

        if output_validators:
            try:
                guard = Guard.from_string(validators=output_validators)
                res = guard.parse(ai_response)
                if not res.validation_passed:
                    return GuardResult(
                        safe=False,
                        violation="Output Policy Violation",
                        reason="AI Response was blocked (Unsafe Output/Hallucination)",
                    )
            except Exception as e:
                return GuardResult(
                    safe=False,
                    violation="Output Guard Error",
                    reason=f"Output Guard Failed: {str(e)}",
                )

        return GuardResult(safe=True, reason=ai_response)