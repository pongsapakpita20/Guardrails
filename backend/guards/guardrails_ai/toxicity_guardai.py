"""
Guardrails AI — Toxicity / Profanity Detection Guard
Comprehensive Thai + English blocklist with slang, misspellings, and variations.
"""
import re
from typing import Tuple, List

class ToxicityGuard:
    def __init__(self):
        # === Thai Profanity ===
        self.thai_words = [
            # คำหยาบหลัก
            "เหี้ย", "สัตว์", "ควาย", "มึง", "กู", "สัด", "เย็ด", "ควย",
            "ห่า", "แม่ง", "อีดอก", "อีสัตว์", "ไอ้บ้า", "ไอ้เวร",
            "อีเวร", "ไอ้สัตว์", "อีควาย", "ไอ้ควาย", "เฮงซวย",
            "ชิบหาย", "อีหน้าหี", "หน้าหี", "อีดอกทอง",
            # คำด่าทั่วไป
            "โง่", "ทุเรศ", "ส้นตีน", "สันดาน", "ชาติชั่ว",
            "อีช้างเย็ด", "แดก", "ดัดจริต",
            # คำแสลง / สแลง
            "กาก", "ห่วย", "ขยะ", "เหม็น", "บ้าบอ",
            "งี่เง่า", "ปัญญาอ่อน", "หัวขี้เลื่อย",
            # สะกดเพี้ยน / เว้นวรรค
            "เ หี้ ย", "ค ว า ย", "มึ ง", "สั ด", "ค ว ย",
            "เหี้ยๆ", "ควายๆ", "บ้าๆ", "ควยๆ",
            # ทับศัพท์
            "ฟัค", "ชิท", "บิทช์", "แอสโฮล",
        ]

        # === English Profanity ===
        self.english_words = [
            "fuck", "shit", "bitch", "asshole", "idiot", "stupid",
            "damn", "crap", "bastard", "moron", "dumb", "retard",
            "whore", "slut", "dick", "cock", "pussy",
            # Misspellings
            "fck", "fuk", "fvck", "sh1t", "b1tch", "a$$hole",
            "stfu", "wtf", "lmao",
        ]

        # Combined for simple check
        self.all_words = self.thai_words + self.english_words

        # Regex patterns for l33t speak and obfuscation
        self.patterns = [
            r"f+[u\*@]+c+k+",      # f**k, fuuck, etc.
            r"s+h+[i1!]+t+",       # sh1t, shiit
            r"b+[i1!]+t+c+h+",     # b1tch
            r"a+s+s+h+o+l+e+",     # asshole variations
        ]

    def check(self, text: str) -> Tuple[bool, str]:
        lower_text = text.lower()
        found: List[str] = []

        # 1. Direct match
        for word in self.all_words:
            if word.lower() in lower_text:
                found.append(word)

        # 2. Regex patterns for obfuscated English
        for pattern in self.patterns:
            if re.search(pattern, lower_text, re.IGNORECASE):
                found.append(f"pattern:{pattern[:15]}")

        # 3. Remove spaces and check again (catches "เ หี้ ย")
        no_space = lower_text.replace(" ", "")
        for word in self.thai_words[:12]:  # Check main Thai words without spaces
            if word.replace(" ", "") in no_space and word not in found:
                found.append(f"{word}(no-space)")

        if found:
            unique = list(set(found))
            return False, f"Toxicity detected: {', '.join(unique[:5])}"
        return True, "Clean"

toxicity_guard = ToxicityGuard()
