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

    _topic_guard = Guard().use(
        _RestrictToTopic,
        valid_topics=[
            "trains",
            "railway",
            "train tickets",
            "train schedules",
            "train stations",
            "travel by train",
            "State Railway of Thailand",
            "transportation",
            "greetings",
            "customer service",
        ],
        invalid_topics=[
            "politics",
            "sports",
            "cooking",
            "entertainment",
            "programming",
            "medical advice",
            "legal advice",
            "cryptocurrency",
            "gambling",
        ],
        llm_callable="ollama/scb10x/typhoon2.5-qwen3-4b",
        on_fail="exception",
    )
    _HAS_GUARD = True
    print("[Off-Topic Guard] ✅ Guardrails AI RestrictToTopic loaded")
except Exception as e:
    _HAS_GUARD = False
    print(f"[Off-Topic Guard] ⚠️  RestrictToTopic not available ({e}), using LLM fallback")

# --- LLM fallback ---
from backend.ollama_service import ollama_service


class OffTopicGuard:
    def check(self, text: str, model: str) -> Tuple[bool, str]:
        """
        Returns (is_safe, reason).
        Input guard: blocks queries unrelated to SRT/railway.
        """
        # 1. Guardrails AI Hub — RestrictToTopic
        if _HAS_GUARD:
            try:
                _topic_guard.validate(text)
                return True, "Topic relevant (RestrictToTopic)"
            except Exception as e:
                error_msg = str(e)
                if "Validation failed" in error_msg or "ValidationError" in type(e).__name__:
                    return False, "Off-topic detected (RestrictToTopic): Query is not related to SRT/Travel."
                # Other errors: fall through to LLM fallback

        # 2. LLM fallback — Ollama (Typhoon)
        prompt = f"""คุณเป็นตัวจำแนกหัวข้อสำหรับ Chatbot ของการรถไฟแห่งประเทศไทย (รฟท.)
ตรวจสอบว่าคำถามของผู้ใช้เกี่ยวข้องกับหัวข้อต่อไปนี้หรือไม่:
1. รถไฟ ตารางเวลา ตั๋ว สถานี
2. การเดินทางในประเทศไทยด้วยรถไฟ
3. คำทักทายทั่วไป
4. คำถามเกี่ยวกับบอทเอง

คำถามผู้ใช้: "{text}"

คำถามนี้เกี่ยวข้องกับ รฟท. หรือการช่วยเหลือทั่วไปหรือไม่? ตอบเฉพาะ YES หรือ NO:"""

        messages = [{"role": "user", "content": prompt}]
        response = ""
        try:
            for chunk in ollama_service.chat_stream(model, messages):
                response += chunk
        except Exception as e:
            return True, f"Off-topic check failed (skipped): {str(e)}"

        if "N" in response.upper() and "Y" not in response.upper():
            return False, "Off-topic detected (LLM): Query is not related to SRT/Travel."
        return True, "Topic relevant"


off_topic_guard = OffTopicGuard()
