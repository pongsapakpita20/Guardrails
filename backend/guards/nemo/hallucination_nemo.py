"""
NeMo Guardrails — Hallucination Detection Guard (Output Guard)
ตรวจจับคำตอบที่โมเดลอาจแต่งขึ้นเอง (Hallucination)
ใช้ heuristic-based detection: keyword patterns + confidence phrases
"""
import re
from typing import Tuple


class HallucinationGuard:
    def __init__(self):
        # Phrases that indicate fabrication or uncertainty
        self.fabrication_indicators_th = [
            r"(?:จาก|ตาม|อ้างอิง).*(?:เว็บไซต์|ลิงก์|URL|แหล่ง).*(?:www\.|https?://|\.com|\.co\.th)",
            r"(?:หมายเลข|เบอร์)(?:โทร|ติดต่อ).*(?:1\d{3}|0\d{1,2}[\s-]?\d{3}[\s-]?\d{4})",
            r"(?:ราคา|ค่าโดยสาร|ค่าตั๋ว).*\d+(?:\.\d+)?.*(?:บาท|THB)",
            r"(?:เวลา|ออก|ถึง).*(?:\d{1,2}[:.]\d{2}|ตอน\d{1,2})",
        ]

        self.fabrication_indicators_en = [
            r"(?:according to|source:|reference:).*(?:www\.|https?://|\.com)",
            r"(?:I (?:think|believe|assume)|probably|might be|could be|I'm not sure but)",
            r"(?:as of (?:my|the) (?:last|latest) (?:update|training|knowledge))",
        ]

        self.uncertainty_phrases_th = [
            "ผมไม่แน่ใจแต่",
            "น่าจะเป็น",
            "คาดว่า",
            "ถ้าจำไม่ผิด",
            "เท่าที่ทราบ",
            "ไม่สามารถยืนยันได้",
            "อาจจะ",
        ]

        self.compiled_th = [re.compile(p, re.IGNORECASE) for p in self.fabrication_indicators_th]
        self.compiled_en = [re.compile(p, re.IGNORECASE) for p in self.fabrication_indicators_en]

    def check(self, text: str) -> Tuple[bool, str]:
        """
        Returns (is_safe, reason).
        Checks model output for signs of hallucination.
        """
        issues = []

        # 1. Fabrication patterns (URLs, phone numbers, prices that model may have made up)
        for pattern in self.compiled_th:
            match = pattern.search(text)
            if match:
                issues.append(f"Possible fabrication (TH): '{match.group()[:60]}'")

        for pattern in self.compiled_en:
            match = pattern.search(text)
            if match:
                issues.append(f"Possible fabrication (EN): '{match.group()[:60]}'")

        # 2. Uncertainty phrases
        text_lower = text.lower()
        uncertainty_count = sum(1 for phrase in self.uncertainty_phrases_th if phrase in text)
        if uncertainty_count >= 2:
            issues.append(f"High uncertainty language ({uncertainty_count} phrases)")

        if issues:
            return False, f"🌀 Hallucination risk: {'; '.join(issues)}"
        return True, "No hallucination detected"

hallucination_guard = HallucinationGuard()
