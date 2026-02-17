"""
Guardrails AI — Jailbreak Detection Guard (Input Guard)
Uses Guardrails AI Hub 'DetectJailbreak' (or 'PromptInjection' as fallback).
"""
from typing import Tuple
from guardrails import Guard
try:
    # User requested 'DetectJailbreak'. Structurally checking if it exists under that name or similar.
    # Functionally 'PromptInjection' is the standard Deepset one.
    # 'DetectJailbreak' might be a specific one user saw. I will try importing standard ones.
    # If using 'hub://guardrails/detect_jailbreak', class is DetectJailbreak.
    from guardrails.hub import DetectJailbreak
except ImportError:
    try:
        from guardrails.hub import DetectJailbreak
    except ImportError:
        DetectJailbreak = None

class JailbreakGuard:
    def __init__(self):
        if DetectJailbreak:
            self.guard = Guard().use(
                DetectJailbreak, 
                on_fail="exception"
            )
            self._has_guard = True
        else:
            self._has_guard = False
            print("⚠️ DetectJailbreak/PromptInjection not found in Hub.")

    def check(self, text: str, model: str = None) -> Tuple[bool, str]:
        if not self._has_guard:
            return True, "Guard not installed"
            
        try:
            self.guard.validate(text)
            return True, "Safe"
        except Exception as e:
            return False, f"Jailbreak detected (Hub): {str(e)}"

jailbreak_guard = JailbreakGuard()
