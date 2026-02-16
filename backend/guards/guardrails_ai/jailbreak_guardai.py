"""
Guardrails AI — Jailbreak Detection Guard (Input Guard)
ตรวจจับ Prompt Injection, DAN, Role-play Attack, Payload Splitting, Adversarial Suffix
"""
import re
from typing import Tuple, List


class JailbreakGuard:
    def __init__(self):
        # ----- Pattern-based detection -----
        self.patterns_th = [
            r"ลืมคำสั่งทั้งหมด",
            r"ลืม(?:ทุก|ทั้งหมด|ทุกอย่าง).*(?:กฎ|คำสั่ง|ข้อจำกัด|ข้อกำหนด)",
            r"ไม่ต้องสนใจ.*(?:กฎ|คำสั่ง|ข้อจำกัด|ข้อกำหนด|system prompt)",
            r"(?:เปิดเผย|บอก|แสดง).*(?:system prompt|คำสั่งระบบ|prompt ของคุณ)",
            r"คุณคือ.*(?:ไม่มีกฎ|ไม่มีข้อจำกัด|ทำอะไรก็ได้)",
            r"สมมติว่าคุณเป็น",
            r"(?:ทำตัว|แกล้งทำ|สวมบทบาท).*(?:เป็น|คือ)",
            r"(?:จาก|ตั้งแต่).*(?:นี้ไป|ตอนนี้).*(?:คุณคือ|คุณเป็น)",
            r"(?:เปลี่ยน|แก้ไข|ยกเลิก).*(?:บทบาท|หน้าที่|ตัวตน)",
            r"(?:ข้าม|หลีกเลี่ยง|ไม่ต้อง).*(?:ตรวจ|กรอง|filter|guard)",
            r"(?:บอก|เปิดเผย).*(?:รหัส|password|secret|api.?key)",
            r"พิมพ์.*(?:คำสั่ง|instruction|prompt).*(?:ทั้งหมด|เต็มๆ|ข้างบน)",
        ]

        self.patterns_en = [
            r"ignore (?:all |your |previous |the )?(?:instructions|rules|guidelines|constraints|restrictions)",
            r"forget (?:all |your |previous |the )?(?:instructions|rules|guidelines|constraints)",
            r"disregard (?:all |your |previous )?(?:instructions|rules|guidelines)",
            r"(?:reveal|show|display|print|repeat|tell me) (?:your |the )?(?:system prompt|instructions|initial prompt|hidden prompt)",
            r"you are (?:now |)(?:DAN|an? AI without|free from|unfiltered|uncensored)",
            r"(?:act|pretend|behave) (?:as if|like) (?:you are|you're|you have) (?:no |without )?(?:rules|restrictions|limits|guidelines|filters)",
            r"do anything now",
            r"jailbreak",
            r"(?:bypass|disable|turn off|deactivate|circumvent) (?:your |the |all )?(?:safety|filter|guardrail|restriction|moderation)",
            r"(?:enter|switch to|activate) (?:developer|debug|admin|unrestricted|god) mode",
            r"(?:override|overwrite) (?:your |the )?(?:system|safety|content) (?:prompt|policy|filter)",
            r"from now on.*(?:you (?:are|will)|ignore|forget)",
            r"(?:ignore|disregard) (?:the )?(?:above|everything (?:above|before|I said))",
            r"what (?:is|are) your (?:system |initial |hidden )?(?:prompt|instructions|rules)",
            r"repeat (?:your |the )?(?:system |initial )?(?:prompt|instructions) (?:verbatim|word for word|exactly)",
        ]

        # Compile all patterns
        self.compiled_th = [re.compile(p, re.IGNORECASE) for p in self.patterns_th]
        self.compiled_en = [re.compile(p, re.IGNORECASE) for p in self.patterns_en]

        # Suspicious keywords (lower threshold)
        self.suspicious_keywords = [
            "system prompt", "initial prompt", "hidden prompt",
            "DAN", "do anything now", "developer mode",
            "ignore instructions", "forget rules",
            "คำสั่งระบบ", "prompt ซ่อน", "โหมดนักพัฒนา",
        ]

    def check(self, text: str) -> Tuple[bool, str]:
        """
        Returns (is_safe, reason).
        """
        text_lower = text.lower()

        # 1) Pattern matching (Thai)
        for pattern in self.compiled_th:
            match = pattern.search(text)
            if match:
                return False, f"🛡️ Jailbreak detected (TH pattern): '{match.group()[:50]}'"

        # 2) Pattern matching (English)
        for pattern in self.compiled_en:
            match = pattern.search(text)
            if match:
                return False, f"🛡️ Jailbreak detected (EN pattern): '{match.group()[:50]}'"

        # 3) Keyword heuristic — count suspicious keywords
        keyword_hits = sum(1 for kw in self.suspicious_keywords if kw.lower() in text_lower)
        if keyword_hits >= 2:
            return False, f"🛡️ Jailbreak suspected: {keyword_hits} suspicious keywords found"

        return True, "No jailbreak detected"

jailbreak_guard = JailbreakGuard()
