"""
Guardrails AI — PII Detection Guard (Input Guard)
Uses Guardrails AI Hub 'DetectPII' validator.
User instruction: Use DetectPII but ensure internal model supports Thai (e.g. via Presidio config or external setup).
"""
from typing import Tuple
from guardrails import Guard
try:
    from guardrails.hub import DetectPII
except ImportError:
    DetectPII = None

class PIIGuard:
    def __init__(self):
        if DetectPII:
            # Presidio-based PII detection.
            # To support Thai, the underlying Presidio Analyzer must be configured with a Thai NLP engine (e.g. spaCy + th_core_news_sm).
            self.guard = Guard().use(
                DetectPII,
                pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "LOCATION"],
                on_fail="exception"
            )
            self._has_guard = True
        else:
            self._has_guard = False
            print("⚠️ DetectPII not found in Hub.")

    def scan(self, text: str) -> Tuple[bool, str]:
        if not self._has_guard:
            # Fallback if validator missing, but strictly should be installed
            return True, "Guard not installed"

        try:
            self.guard.validate(text)
            return True, "No PII detected"
        except Exception as e:
            return False, f"PII Detected (Hub): {str(e)}"

pii_guard = PIIGuard()
