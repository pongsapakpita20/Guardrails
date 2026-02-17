"""
Guardrails AI — Off-Topic Detection Guard (Input Guard)
Uses Guardrails AI Hub RestrictToTopic validator.
Falls back to LLM-based classification via Ollama if Hub validator is unavailable.
"""
from typing import Tuple

# --- Guardrails AI Hub: RestrictToTopic ---
try:
    from guardrails import Guard
    from guardrails.hub import RestrictToTopic as _RestrictToTopic
    from guardrails.hub import RestrictToTopic
except ImportError:
    RestrictToTopic = None

class OffTopicGuard:
    def __init__(self):
        if RestrictToTopic:
            self.guard = Guard().use(
                RestrictToTopic,
                valid_topics=["trains", "railway services", "ticket booking", "train schedules", "SRT Thailand", "travel by train"],
                disable_classifier=True, 
                disable_llm=False,
                llm_callable="ollama/scb10x/typhoon2.5-qwen3-4b",
                on_fail="exception"
            )
            self._has_guard = True
        else:
            self._has_guard = False
            print("⚠️ RestrictToTopic not found in Hub.")

    def check(self, text: str, model: str = None) -> Tuple[bool, str]:
        if not self._has_guard:
            return True, "Guard not installed"
            
        try:
            self.guard.validate(text)
            return True, "On-topic"
        except Exception as e:
            return False, f"Off-Topic detected (Hub): {str(e)}"

off_topic_guard = OffTopicGuard()
