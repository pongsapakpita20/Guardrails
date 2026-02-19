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
import re

# --- Load NeMo Guardrails ---
try:
    from nemoguardrails import RailsConfig, LLMRails

    _config_path = str(Path(__file__).parent.parent.parent / "config" / "nemo")

    _config = RailsConfig.from_path(_config_path)
    _rails = LLMRails(_config)
    _HAS_NEMO = True
    print(f"[NeMo] OK NeMo Guardrails loaded from {_config_path}")
except Exception as e:
    _HAS_NEMO = False
    _rails = None
    print(f"[NeMo] WARN NeMo Guardrails not available ({e})")


def _normalize(text: str) -> str:
    """Light normalization to make substring matching robust to markdown/whitespace."""
    s = str(text or "")
    s = s.replace("*", "")  # remove markdown emphasis
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Refusal patterns — derived from backend/config/nemo/rails.co
# We keep these as *substrings* to remain stable even if emojis/newlines vary.
REFUSAL_PATTERNS: dict[str, list[str]] = {
    # Input rails
    "pii": [
        "[RAIL:PII]",
        "ขออภัยค่ะ เพื่อความปลอดภัยของข้อมูลส่วนบุคคล",
    ],
    "jailbreak": [
        "[RAIL:JAILBREAK]",
        "เรื่องนี้ขัดกับนโยบายความปลอดภัย",
        "น้องทำตามไม่ได้จริงๆ",
    ],
    "off_topic": [
        "[RAIL:OFF_TOPIC]",
        "ขออภัยค่ะ น้องรางรถไฟรู้แค่เรื่อง รถไฟ (SRT)",
        "เรื่องอื่นน้องไม่ถนัดเลย",
        "ขออภัยค่ะ น้องรางรถไฟให้ข้อมูลได้เฉพาะเรื่องรถไฟ รฟท. และสายสีแดงเท่านั้นนะคะ",
    ],
    "toxicity": [
        "[RAIL:TOXICITY]",
        # Output toxicity rail
        "คำตอบถูกระงับเนื่องจากมีเนื้อหาไม่เหมาะสม",
        "Profanity/Toxicity Detected",
    ],
    # Output rails
    "hallucination": [
        "[RAIL:HALLUCINATION]",
        "ข้อมูลนี้อาจจะคลาดเคลื่อนนะคะ",
        "รบกวนตรวจสอบกับ Call Center 1690",
    ],
    "competitor": [
        "[RAIL:COMPETITOR]",
        "น้องรางรถไฟขอแนะนำบริการของ การรถไฟแห่งประเทศไทย (รฟท.)",
    ],
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
        # Fail-closed when NeMo is selected but unavailable.
        return False, "NeMo Guardrails not available (missing dependency or failed to load)", "nemo_unavailable"

    try:
        # Call NeMo ONCE
        from backend.logger import log_manager
        
        await log_manager.log("NeMo", "processing", f"Generating response for: '{text[:60]}'")
        response = await _rails.generate_async(messages=[{"role": "user", "content": text}])
        content = str(response.get("content", ""))
        norm_content = _normalize(content)

        await log_manager.log("NeMo", "info", f"Response: '{content[:100]}'")

        # Check the SINGLE response against all enabled guard patterns
        for guard_type in enabled_guards:
            patterns = REFUSAL_PATTERNS.get(guard_type, [])
            for pattern in patterns:
                if pattern and _normalize(pattern) in norm_content:
                    await log_manager.log("NeMo", "warning", f"⛔ {guard_type.upper()} triggered!")
                    return False, f"NeMo Rail: {guard_type.capitalize()} detected", guard_type

        return True, "Safe", None
    except Exception as e:
        await log_manager.log("NeMo", "error", f"NeMo check failed: {e}")
        # Fail-closed: if NeMo rails cannot run, treat as blocked so we don't bypass the framework.
        return False, f"NeMo check failed: {e}", "nemo_error"


# Legacy single-guard check (kept for backward compatibility)
async def check_guard(text: str, guard_type: str) -> tuple[bool, str]:
    """Single guard check — calls check_all_guards internally."""
    is_safe, details, _ = await check_all_guards(text, [guard_type])
    return is_safe, details

