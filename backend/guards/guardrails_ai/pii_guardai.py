"""
Guardrails AI — PII Detection Guard
Regex patterns for Thai PII + ThaiNER for bare name detection.
Falls back to prefix-only if pythainlp is not installed.
"""
import re
from typing import Tuple, List

# --- ThaiNER (optional, graceful fallback) ---
try:
    from pythainlp.tag import NER
    _ner = NER(engine="thainer-v2")
    _HAS_NER = True
    print("[PII Guard] ✅ ThaiNER-v2 (WangchanBERTa) loaded")
except Exception as e:
    _HAS_NER = False
    print(f"[PII Guard] ⚠️  ThaiNER not available ({e}) — using prefix-only")


class PIIGuard:
    def __init__(self):
        self.patterns = {
            # --- Direct Identifiers ---
            "PHONE":         r"(?:0[689]\d{1}[-.\s]?\d{3}[-.\s]?\d{4}|0[2-9]\d{1}[-.\s]?\d{3}[-.\s]?\d{4})",
            "ID_CARD":       r"\b\d{1}[-\s]?\d{4}[-\s]?\d{5}[-\s]?\d{2}[-\s]?\d{1}\b",
            "ID_CARD_RAW":   r"\b\d{13}\b",
            "EMAIL":         r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            "CREDIT_CARD":   r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "BANK_ACCOUNT":  r"(?:เลขบัญชี|บัญชี|account)\s*[:：]?\s*\d{3}[-\s]?\d{1}[-\s]?\d{5}[-\s]?\d{1}",
            "PASSPORT":      r"\b[A-Z]{1,2}\d{6,8}\b",
            "LINE_ID":       r"(?:line|ไลน์|ไอดี)\s*[:：]?\s*[@]?[a-zA-Z0-9._\-]{3,}",

            # --- Indirect Identifiers ---
            "DOB":           r"(?:เกิด|วันเกิด|born)\s*[:：]?\s*\d{1,2}[-/.\s]\d{1,2}[-/.\s]\d{2,4}",
            "ADDRESS":       r"(?:บ้านเลขที่|ที่อยู่|ซอย|ถนน|ตำบล|อำเภอ|จังหวัด)\s*[:：]?\s*\S+",
            "ZIPCODE":       r"\b\d{5}\b(?=\s|$)",
        }

        # Formal Thai title prefixes for prefix-based name detection (fallback)
        self.name_keywords = [
            "ชื่อ", "นามสกุล", "นาย", "นาง", "นางสาว", "ด.ช.", "ด.ญ.", "name"
        ]

    def scan(self, text: str) -> Tuple[bool, str]:
        found: List[str] = []

        # 1. Regex patterns
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.append(f"{pii_type}: {len(matches)} instance(s)")

        # 2. Name detection — ThaiNER (preferred) or prefix-based (fallback)
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
                pass  # NER failed, skip
        else:
            # Fallback: prefix-based detection
            for keyword in self.name_keywords:
                if keyword in text:
                    pattern = rf"{re.escape(keyword)}\s*[:：]?\s*([\u0E00-\u0E7Fa-zA-Z]+\s*[\u0E00-\u0E7Fa-zA-Z]*)"
                    match = re.search(pattern, text)
                    if match and len(match.group(1).strip()) > 2:
                        found.append(f"NAME(via '{keyword}'): {match.group(1).strip()[:20]}")
                        break

        if found:
            return False, ", ".join(found)
        return True, "No PII detected"

    def redact(self, text: str) -> str:
        for pii_type, pattern in self.patterns.items():
            text = re.sub(pattern, f"[{pii_type}_REDACTED]", text, flags=re.IGNORECASE)
        return text

pii_guard = PIIGuard()
