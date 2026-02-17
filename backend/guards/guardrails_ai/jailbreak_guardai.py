"""
Guardrails AI — Jailbreak Detection Guard (Input Guard)
Uses Guardrails AI Hub 'PromptInjection' validator (Deepset).
"""
from typing import Tuple
from guardrails import Guard
try:
    # User requested to remove SelfCheckInput.
    # Switching to standard Hub PromptInjection (e.g. deepset/deberta-v3-base-injection)
    from guardrails.hub import PromptInjection
except ImportError:
    PromptInjection = None

class JailbreakGuard:
    def __init__(self):
        if PromptInjection:
            self.guard = Guard().use(
                PromptInjection, 
                on_fail="exception"
            )
            self._has_guard = True
        else:
            self._has_guard = False
            print("⚠️ PromptInjection not found in Hub, please install: guardrails hub install hub://guardrails/prompt_injection")

    def check(self, text: str, model: str = None) -> Tuple[bool, str]:
        if not self._has_guard:
            return True, "Guard not installed"
            
        try:
            self.guard.validate(text)
            return True, "Safe"
        except Exception as e:
            return False, f"Jailbreak detected (Hub): {str(e)}"

jailbreak_guard = JailbreakGuard()
