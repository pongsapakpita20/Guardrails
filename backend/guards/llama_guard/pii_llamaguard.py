"""
Llama Guard 3 8B — PII Detection Guard
Comprehensive regex patterns for Thai PII.
"""
import re
from typing import Tuple, List

class PIIGuard:
    def __init__(self):
        self.patterns = {
            "PHONE":         r"(?:0[689]\d{1}[-.\s]?\d{3}[-.\s]?\d{4}|0[2-9]\d{1}[-.\s]?\d{3}[-.\s]?\d{4})",
            "ID_CARD":       r"\b\d{1}[-\s]?\d{4}[-\s]?\d{5}[-\s]?\d{2}[-\s]?\d{1}\b",
            "ID_CARD_RAW":   r"\b\d{13}\b",
            "EMAIL":         r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            "CREDIT_CARD":   r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "BANK_ACCOUNT":  r"(?:เลขบัญชี|บัญชี|account)\s*[:：]?\s*\d{3}[-\s]?\d{1}[-\s]?\d{5}[-\s]?\d{1}",
            "PASSPORT":      r"\b[A-Z]{1,2}\d{6,8}\b",
            "LINE_ID":       r"(?:line|ไลน์|ไอดี)\s*[:：]?\s*[@]?[a-zA-Z0-9._\-]{3,}",
            "DOB":           r"(?:เกิด|วันเกิด|born)\s*[:：]?\s*\d{1,2}[-/.\s]\d{1,2}[-/.\s]\d{2,4}",
            "ADDRESS":       r"(?:บ้านเลขที่|ที่อยู่|ซอย|ถนน|ตำบล|อำเภอ|จังหวัด)\s*[:：]?\s*\S+",
        }

        self.name_keywords = [
            "ชื่อ", "นามสกุล", "นาย", "นาง", "นางสาว", "ด.ช.", "ด.ญ.", "คุณ",
        ]

    def scan(self, text: str) -> Tuple[bool, str]:
        found: List[str] = []
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.append(f"{pii_type}: {len(matches)}")

        for keyword in self.name_keywords:
            if keyword in text:
                pattern = rf"{re.escape(keyword)}\s*[:：]?\s*([\u0E00-\u0E7Fa-zA-Z]+\s*[\u0E00-\u0E7Fa-zA-Z]*)"
                match = re.search(pattern, text)
                if match and len(match.group(1).strip()) > 2:
                    found.append(f"NAME(via '{keyword}')")
                    break

        if found:
            return False, ", ".join(found)
        return True, "No PII detected"

pii_guard = PIIGuard()
