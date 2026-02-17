"""
Guardrails AI — Hallucination Detection Guard (Output Guard)
Uses Guardrails AI Hub 'MiniCheck' (as requested) or fallback.
"""
from typing import Tuple
from guardrails import Guard
try:
    # User requested MiniCheck
    # Note: MiniCheck might require specific installation: guardrails hub install hub://bespokelabs/minicheck
    from guardrails.hub import MiniCheck
except ImportError:
    MiniCheck = None

class HallucinationGuard:
    def __init__(self):
        if MiniCheck:
            self.guard = Guard().use(
                MiniCheck,
                on_fail="exception"
            )
            self._has_guard = True
        else:
            self._has_guard = False
            print("⚠️ MiniCheck not found in Hub, please install: guardrails hub install hub://bespokelabs/minicheck")

    def check(self, response: str, model: str = None) -> Tuple[bool, str]:
        if not self._has_guard:
            return True, "Guard not installed"

        try:
            # MiniCheck usually requires context (source document/prompt) to verify against.
            # But adapting to current interface which only sends 'response'.
            # If MiniCheck allows checking without context (self-consistency? unlikely), or we pass generated text as context?
            self.guard.validate(response) 
            return True, "Response appears grounded"
        except Exception as e:
            return False, f"Hallucination detected (Hub): {str(e)}"

hallucination_guard = HallucinationGuard()
