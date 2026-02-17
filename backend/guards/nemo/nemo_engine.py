"""
NeMo Guardrails — Shared NeMo Rails Engine
Loads Colang rules + config.yml once and provides a shared LLMRails instance.
All NeMo guards use this shared engine for semantic matching.

IMPORTANT: NeMo is called ONCE per message. The single response is then checked
against all refusal patterns to determine which (if any) guard was triggered.
This avoids non-deterministic false positives from multiple LLM calls.
"""
import os
from pathlib import Path

# --- Load NeMo Guardrails ---
try:
    from nemoguardrails import RailsConfig, LLMRails

    _config_path = str(Path(__file__).parent.parent.parent / "config" / "nemo")

    _config = RailsConfig.from_path(_config_path)
    _rails = LLMRails(_config)
    _HAS_NEMO = True
    print(f"[NeMo] ✅ NeMo Guardrails loaded from {_config_path}")
except Exception as e:
    _HAS_NEMO = False
    _rails = None
    print(f"[NeMo] ⚠️  NeMo Guardrails not available ({e})")


# Refusal patterns — EXACT messages from rails.co
REFUSAL_MAP = {
    "pii": "กรุณาอย่าส่งข้อมูลส่วนตัว",
    "off_topic": "ฉันสามารถตอบคำถามเกี่ยวกับการรถไฟแห่งประเทศไทยเท่านั้น",
    "jailbreak": "ไม่สามารถทำตามคำขอนี้ได้ เนื่องจากละเมิดนโยบายความปลอดภัย",
    "toxicity": "กรุณาใช้ภาษาที่สุภาพ",
    "competitor": "ฉันแนะนำได้เฉพาะบริการของการรถไฟแห่งประเทศไทย",
    "hallucination": "ไม่สามารถให้ข้อมูลดังกล่าวได้เนื่องจากอาจไม่ถูกต้อง",
}


def get_rails():
    """Return the shared LLMRails instance."""
    return _rails


def is_available() -> bool:
    """Check if NeMo Guardrails is available."""
    return _HAS_NEMO


async def check_all_guards(text: str, enabled_guards: list[str]) -> tuple[bool, str, str | None]:
    """
    Call NeMo ONCE and check ALL enabled guards against the single response.
    
    Returns: (is_safe, details, violation_type)
      - is_safe: True if no guard triggered
      - details: Description of what happened  
      - violation_type: Which guard triggered (e.g. "pii", "off_topic") or None
    """
    if not _HAS_NEMO:
        return True, "NeMo not available", None

    try:
        # Call NeMo ONCE
        response = await _rails.generate_async(messages=[{"role": "user", "content": text}])
        content = str(response.get("content", ""))

        print(f"[NeMo] Input: '{text[:60]}' → Response: '{content[:100]}'")

        # Check the SINGLE response against all enabled guard patterns
        for guard_type in enabled_guards:
            pattern = REFUSAL_MAP.get(guard_type)
            if pattern and pattern in content:
                print(f"[NeMo] ⛔ {guard_type.upper()} triggered!")
                return False, f"NeMo Rail: {guard_type.capitalize()} detected", guard_type

        return True, "Safe", None
    except Exception as e:
        return True, f"NeMo check failed (open): {e}", None


# Legacy single-guard check (kept for backward compatibility)
async def check_guard(text: str, guard_type: str) -> tuple[bool, str]:
    """Single guard check — calls check_all_guards internally."""
    is_safe, details, _ = await check_all_guards(text, [guard_type])
    return is_safe, details

