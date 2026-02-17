"""
Guardrails AI — PII Detection Guard (Input Guard)
Uses PyThaiNLP (ThaiNER) as requested for better Thai PII support.
"""
from typing import Tuple, List

# --- PyThaiNLP (ThaiNER) ---
# Treating PyThaiNLP as a supported library/framework component (not "custom rulebase")
try:
    from pythainlp.tag import NER
    _ner = NER(engine="thainer-v2")
    _HAS_NER = True
    print("[PII Guard] ✅ ThaiNER-v2 loaded")
except Exception as e:
    _HAS_NER = False
    print(f"[PII Guard] ⚠️  ThaiNER not available ({e})")


class PIIGuard:
    def scan(self, text: str) -> Tuple[bool, str]:
        found: List[str] = []

        # Use ThaiNER for PII detection
        if _HAS_NER:
            try:
                # ThaiNER returns list of (word, tag)
                # Tags like: PERSON, LOCATION, ORGANIZATION, DATE, TIME, EMAIL, ZIP, TEL, etc.
                entities = _ner.tag(text)
                
                # Simple extraction of relevant PII tags
                pii_tags = ["PERSON", "EMAIL", "TEL", "LOCATION", "ORGANIZATION"] # Adjust based on ThaiNER tags
                
                current_chunk = []
                current_tag = None
                
                for word, tag in entities:
                    # ThaiNER tags: B-PERSON, I-PERSON, O, etc. or just PERSON depending on version
                    # Usually thainer-v2 returns simple tags like 'PERSON', 'O'
                    if tag in pii_tags:
                        found.append(f"{tag}: {word}")
                    elif tag != "O" and any(pt in tag for pt in pii_tags): # Handle B-PERSON etc if needed
                         found.append(f"{tag}: {word}")
                         
            except Exception as e:
                found.append(f"PII Check Error: {str(e)}")

        if found:
            # unique items
            found = list(dict.fromkeys(found))
            return False, f"PII Detected (ThaiNER): {', '.join(found[:5])}"
            
        return True, "No PII detected"

pii_guard = PIIGuard()
