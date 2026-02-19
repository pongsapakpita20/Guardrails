"""
Guardrails AI — Toxicity Detection Guard (Input + Output Guard)
Uses Guardrails AI Hub ToxicLanguage validator (Detoxify model).
Supplements with LLM-based Thai toxicity check via Ollama.
"""
from typing import Tuple
import re

# --- Guardrails AI Hub: ToxicLanguage ---
try:
    from guardrails import Guard
    from guardrails.hub import ToxicLanguage as _ToxicLanguage

    _toxic_guard = Guard().use(
        _ToxicLanguage,
        threshold=0.5,
        validation_method="sentence",
        on_fail="exception",
    )
    _HAS_GUARD = True
    print("[Toxicity Guard] OK Guardrails AI ToxicLanguage (Detoxify) loaded")
except Exception as e:
    _HAS_GUARD = False
    print(f"[Toxicity Guard] WARN ToxicLanguage not available ({e})")

# --- LLM-based Thai toxicity check ---
from backend.ollama_service import ollama_service


class ToxicityGuard:
    """Checks both input and output for toxic/profane content."""

    def __init__(self):
        self.default_model = "scb10x/typhoon2.5-qwen3-4b"

    def check(self, text: str, model: str = None) -> Tuple[bool, str]:
        """
        Returns (is_safe, reason).
        Used for both input guard and output guard.
        """
        # 1. Guardrails AI Hub — ToxicLanguage (Detoxify, EN-focused)
        if _HAS_GUARD:
            try:
                _toxic_guard.validate(text)
            except Exception as e:
                error_msg = str(e)
                if "Validation failed" in error_msg or "ValidationError" in type(e).__name__:
                    return False, f"Toxicity detected (Hub): {error_msg[:100]}"

        return True, "Clean"


toxicity_guard = ToxicityGuard()
