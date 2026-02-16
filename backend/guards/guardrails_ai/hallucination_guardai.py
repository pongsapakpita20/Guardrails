"""
Guardrails AI — Hallucination Detection Guard (Output)
Uses the model to verify if the response is grounded.
"""
from typing import Tuple
from backend.ollama_service import ollama_service

class HallucinationGuard:
    def check(self, response: str, model: str = "scb10x/typhoon2.5-qwen3-4b") -> Tuple[bool, str]:
        prompt = f"""You are a fact-checker for the State Railway of Thailand (SRT).
Analyze the following chatbot response and determine if it contains
fabricated information, made-up schedules, or fictional station names.

Response to check:
"{response}"

Does this response contain hallucinated or fabricated information?
Answer only YES or NO."""

        messages = [{"role": "user", "content": prompt}]
        result = ""
        try:
            for chunk in ollama_service.chat_stream(model, messages):
                result += chunk
        except Exception:
            return True, "Hallucination check failed (skipped)"

        if "YES" in result.upper() and "NO" not in result.upper():
            return False, "Possible hallucination detected in response"
        return True, "Response appears grounded"

hallucination_guard = HallucinationGuard()
