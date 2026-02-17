"""
Guardrails AI — Competitor Mention Guard (Output Guard)
Uses Guardrails AI Hub 'CompetitorCheck' validator.
"""
from typing import Tuple
from guardrails import Guard
try:
    from guardrails.hub import CompetitorCheck
except ImportError:
    CompetitorCheck = None

class CompetitorGuard:
    def __init__(self):
        if CompetitorCheck:
            self.guard = Guard().use(
                CompetitorCheck, 
                competitors=["AirAsia", "Nok Air", "Thai Lion Air", "Grab", "Bolt", "Uber", "Nakhonchai Air"],
                llm_callable="ollama/scb10x/typhoon2.5-qwen3-4b",
                on_fail="exception"
            )
            self._has_guard = True
        else:
            self._has_guard = False
            print("⚠️ CompetitorCheck not found in Hub, please install: guardrails hub install hub://guardrails/competitor_check")

    def check(self, text: str, model: str = None) -> Tuple[bool, str]:
        if not self._has_guard:
            return True, "Guard not installed"

        try:
            self.guard.validate(text)
            return True, "Clean"
        except Exception as e:
            return False, f"Competitor detected (Hub): {str(e)}"

competitor_guard = CompetitorGuard()
