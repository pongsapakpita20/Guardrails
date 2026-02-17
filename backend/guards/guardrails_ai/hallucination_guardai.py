"""
Guardrails AI — Hallucination Detection Guard (Output Guard)
Uses Guardrails AI Hub 'MiniCheck' (as requested) or fallback.
"""
from typing import Tuple
from guardrails import Guard
try:
    # User requested BespokeMiniCheck
    # This is often 'hub://bespokelabs/minicheck' -> class MiniCheck or BespokeMiniCheck
    from guardrails.hub import BespokeMiniCheck
except ImportError:
    BespokeMiniCheck = None

class HallucinationGuard:
    def __init__(self):
        if BespokeMiniCheck:
            self.guard = Guard().use(
                BespokeMiniCheck,
                on_fail="exception"
            )
            self._has_guard = True
        else:
            self._has_guard = False
            print("⚠️ BespokeMiniCheck not found in Hub.")

    def check(self, response: str, model: str = None) -> Tuple[bool, str]:
        if not self._has_guard:
            return True, "Guard not installed"

        try:
            self.guard.validate(response) 
            return True, "Response appears grounded"
        except Exception as e:
            return False, f"Hallucination detected (Hub): {str(e)}"

hallucination_guard = HallucinationGuard()
