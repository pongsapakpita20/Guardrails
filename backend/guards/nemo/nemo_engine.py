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


async def check_guard(text: str, guard_type: str) -> tuple[bool, str]:
    """
    Generic NeMo guard check.
    Uses rails.generate to check if the input/output triggers a refusal rail.
    """
    if not _HAS_NEMO:
        return True, "NeMo not available"

    try:
        import asyncio
        # Ensure we have a loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Generate response using NeMo Rails
        # NeMo will follow the flows defined in rails.co
        # If a rail triggers (e.g. off-topic), it generates a specific refusal message.
        response = await _rails.generate_async(messages=[{"role": "user", "content": text}])
        content = str(response.get("content", ""))

        # Check refusal patterns defined in rails.co
        refusal_map = {
            "pii": ["ข้อมูลส่วนบุคคล"],
            "off_topic": ["เกี่ยวกับการรถไฟ", "เฉพาะ"], 
            "jailbreak": ["นโยบายความปลอดภัย", "I cannot", "unethical"],
            "toxicity": ["สุภาพ", "toxic"],
            "competitor": ["แนะนำได้เฉพาะ", "คู่แข่ง"],
            "hallucination": ["ไม่ถูกต้อง", "ไม่เหมาะสม"] # Simulated for output
        }

        patterns = refusal_map.get(guard_type, [])
        for p in patterns:
            if p in content:
                return False, f"NeMo Rail: {guard_type.capitalize()} detected"

        return True, "Safe"
    except Exception as e:
        return True, f"NeMo check failed (open): {e}"
