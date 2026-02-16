"""
NeMo Guardrails — PII Detection Guard (Input Guard)
ตรวจจับข้อมูลส่วนบุคคล: Direct Identifiers + Indirect Identifiers + ThaiNER
Falls back to prefix-only if pythainlp is not installed.
"""
import re
from typing import Tuple, List

# --- ThaiNER (optional, graceful fallback) ---
try:
    from pythainlp.tag import NER
    _ner = NER(engine="thainer-v2")
    _HAS_NER = True
except Exception:
    _HAS_NER = False


class PIIGuard:
    def __init__(self):
        self.patterns = {
            # ===== Direct Identifiers =====
            "PHONE": r"(?:0[689]\d[\s-]?\d{3}[\s-]?\d{4}|0[23457]\d[\s-]?\d{3}[\s-]?\d{4}|\+66[\s-]?\d[\s-]?\d{3}[\s-]?\d{4})",
            "THAI_ID": r"\b\d[\s-]?\d{4}[\s-]?\d{5}[\s-]?\d{2}[\s-]?\d\b",
            "PASSPORT": r"\b[A-Z]{1,2}\d{6,8}\b",
            "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "CREDIT_CARD": r"\b(?:\d[\s-]?){13,19}\b",
            "BANK_ACCOUNT": r"(?:(?:เลขบัญชี|บัญชี|account)[\s:]*\d[\s-]?\d{2,3}[\s-]?\d{3,5}[\s-]?\d{1,4})",
            "ADDRESS": r"(?:(?:บ้านเลขที่|ที่อยู่|เลขที่|ซอย|ถนน|แขวง|เขต|ตำบล|อำเภอ|จังหวัด|หมู่บ้าน|หมู่ที่)\s*[\wก-๙./\s-]+)",

            # ===== Indirect Identifiers =====
            "LINE_ID": r"(?:(?:LINE|ไลน์|line id|ไอดีไลน์)[\s:@]*[a-zA-Z0-9._-]{4,30})",
            "DOB": r"(?:(?:เกิด(?:วันที่)?|วันเกิด|date of birth|DOB)[\s:]*\d{1,2}[\s/.-]\d{1,2}[\s/.-]\d{2,4})",
            "THAI_NAME": r"(?:(?:นาย|นาง|นางสาว|ด\.ช\.|ด\.ญ\.|เด็กชาย|เด็กหญิง)\s+[ก-๙]{2,20}(?:\s+[ก-๙]{2,20})?)",
        }

        self.compiled = {k: re.compile(v, re.IGNORECASE) for k, v in self.patterns.items()}

    def check(self, text: str) -> Tuple[bool, str]:
        """Returns (is_safe, reason)."""
        found: List[str] = []

        # 1. Regex patterns
        for label, pattern in self.compiled.items():
            if pattern.search(text):
                found.append(label)

        # 2. ThaiNER for bare name detection (no prefix needed)
        if _HAS_NER:
            try:
                entities = _ner.tag(text)
                # BIO format: B-PERSON = begin, I-PERSON = inside
                names = []
                current_name = ""
                for word, tag in entities:
                    if "PERSON" in tag:
                        current_name += word
                    else:
                        if current_name.strip():
                            names.append(current_name.strip())
                        current_name = ""
                if current_name.strip():
                    names.append(current_name.strip())
                if names:
                    names_str = ", ".join(names[:3])
                    found.append(f"NAME(NER): {names_str}")
            except Exception:
                pass

        if found:
            return False, f"🔒 PII detected: {', '.join(found)}"
        return True, "No PII detected"

    def scan(self, text: str) -> Tuple[bool, str]:
        """Alias for check() to match guardrails_ai interface."""
        return self.check(text)

pii_guard = PIIGuard()
