"""
NeMo Guardrails — Shared NeMo Rails Engine
Loads Colang rules + config.yml once and provides a shared LLMRails instance.
All NeMo guards use this shared engine for semantic matching.
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


def get_rails():
    """Return the shared LLMRails instance."""
    return _rails


def is_available() -> bool:
    """Check if NeMo Guardrails is available."""
    return _HAS_NEMO


# Exact refusal messages from rails.co — used to detect which rail triggered
# Using EXACT messages prevents false positives where a normal LLM response
# about trains might contain words like "การรถไฟ"
_REFUSAL_MESSAGES = {
    "pii":           "กรุณาอย่าส่งข้อมูลส่วนตัว",
    "off_topic":     "ฉันสามารถตอบคำถามเกี่ยวกับการรถไฟแห่งประเทศไทยเท่านั้น",
    "jailbreak":     "ไม่สามารถทำตามคำขอนี้ได้",
    "toxicity":      "กรุณาใช้ภาษาที่สุภาพ",
    "hallucination": "ไม่สามารถให้ข้อมูลดังกล่าวได้",
    "competitor":    "แนะนำได้เฉพาะบริการของการรถไฟ",
}


async def check_all(text: str) -> dict:
    """
    Run NeMo Guardrails ONCE and detect which (if any) rail was triggered.
    Returns: {"safe": bool, "violation": str|None, "response": str}
    """
    if not _HAS_NEMO:
        return {"safe": True, "violation": None, "response": "NeMo not available"}

    try:
        response = await _rails.generate_async(
            messages=[{"role": "user", "content": text}]
        )
        content = str(response.get("content", ""))
        print(f"[NeMo] 📝 Raw response: {content[:120]}")

        # Check if the response IS a known refusal message (exact phrase match)
        for guard_type, refusal_phrase in _REFUSAL_MESSAGES.items():
            if refusal_phrase in content:
                return {
                    "safe": False,
                    "violation": guard_type,
                    "response": content,
                }

        return {"safe": True, "violation": None, "response": content}

    except Exception as e:
        print(f"[NeMo] ⚠️ check_all error: {e}")
        return {"safe": True, "violation": None, "response": f"NeMo error: {e}"}

