"""
NeMo Guardrails — Toxicity / Profanity Guard
Comprehensive Thai + English blocklist with slang, misspellings, and variations.
"""
import re
from typing import Tuple, List

class ToxicityGuard:
    def __init__(self):
        self.thai_words = [
            "เหี้ย", "สัตว์", "ควาย", "มึง", "กู", "สัด", "เย็ด", "ควย",
            "ห่า", "แม่ง", "อีดอก", "อีสัตว์", "ไอ้บ้า", "ไอ้เวร",
            "อีเวร", "ไอ้สัตว์", "อีควาย", "ไอ้ควาย", "เฮงซวย",
            "ชิบหาย", "อีหน้าหี", "หน้าหี", "อีดอกทอง",
            "โง่", "ทุเรศ", "ส้นตีน", "สันดาน", "ชาติชั่ว",
            "แดก", "ดัดจริต",
            "กาก", "ห่วย", "งี่เง่า", "ปัญญาอ่อน", "หัวขี้เลื่อย",
            "เ หี้ ย", "ค ว า ย", "มึ ง", "สั ด", "ค ว ย",
            "เหี้ยๆ", "ควายๆ", "บ้าๆ", "ควยๆ",
            "ฟัค", "ชิท", "บิทช์", "แอสโฮล",
        ]

        self.english_words = [
            "fuck", "shit", "bitch", "asshole", "idiot", "stupid",
            "damn", "crap", "bastard", "moron", "dumb", "retard",
            "whore", "slut", "dick", "cock", "pussy",
            "fck", "fuk", "fvck", "sh1t", "b1tch", "a$$hole",
            "stfu", "wtf",
        ]

        self.all_words = self.thai_words + self.english_words

        self.patterns = [
            r"f+[u\*@]+c+k+",
            r"s+h+[i1!]+t+",
            r"b+[i1!]+t+c+h+",
        ]

    def check(self, text: str) -> Tuple[bool, str]:
        lower_text = text.lower()
        found: List[str] = []

        for word in self.all_words:
            if word.lower() in lower_text:
                found.append(word)

        for pattern in self.patterns:
            if re.search(pattern, lower_text, re.IGNORECASE):
                found.append(f"pattern:{pattern[:15]}")

        no_space = lower_text.replace(" ", "")
        for word in self.thai_words[:12]:
            if word.replace(" ", "") in no_space and word not in found:
                found.append(f"{word}(no-space)")

        if found:
            unique = list(set(found))
            return False, f"NeMo Rail: Toxicity detected — {', '.join(unique[:5])}"
        return True, "NeMo Rail: Clean"

toxicity_guard = ToxicityGuard()
