"""
Llama Guard 3 8B — Full 13-Category Safety Check
Uses the actual llama-guard3 model with individually toggleable S1–S13 categories.
"""
from typing import Tuple, Dict, List
from backend.ollama_service import ollama_service
from backend.config.settings import LLAMA_GUARD_MODEL

# All 13 Llama Guard 3 categories
CATEGORIES = {
    "S1":  "Violent Crimes",
    "S2":  "Non-Violent Crimes",
    "S3":  "Sex Crimes",
    "S4":  "Child Exploitation",
    "S5":  "Defamation",
    "S6":  "Specialized Advice",
    "S7":  "Privacy",
    "S8":  "Intellectual Property",
    "S9":  "Indiscriminate Weapons",
    "S10": "Hate",
    "S11": "Self-Harm",
    "S12": "Sexual Content",
    "S13": "Elections",
}


class LlamaGuardChecker:
    def check(self, text: str, enabled_categories: List[str] = None, role: str = "User") -> Tuple[bool, str]:
        if enabled_categories is None:
            enabled_categories = list(CATEGORIES.keys())

        if not enabled_categories:
            return True, "No categories enabled — skipped"

        cat_block = "\n".join(
            f"{k}: {CATEGORIES[k]}."
            for k in enabled_categories if k in CATEGORIES
        )

        prompt = f"""[INST] Task: Check if there is unsafe content in '{role}' messages in conversations according to our safety policy with the below categories.

<BEGIN UNSAFE CONTENT CATEGORIES>
{cat_block}
<END UNSAFE CONTENT CATEGORIES>

<BEGIN CONVERSATION>
{role}: {text}
<END CONVERSATION>

Provide your safety assessment for {role} in the above conversation:
- First line must read 'safe' or 'unsafe'.
- If unsafe, a second line must include a comma-separated list of violated categories. [/INST]"""

        messages = [{"role": "user", "content": prompt}]
        response_text = ""
        try:
            for chunk in ollama_service.chat_stream(LLAMA_GUARD_MODEL, messages):
                response_text += chunk
        except Exception as e:
            return True, f"Llama Guard check failed (skipped): {str(e)}"

        first_line = response_text.strip().split("\n")[0].lower()
        if "unsafe" in first_line:
            return False, f"Llama Guard 3: {response_text.strip()}"
        return True, "Llama Guard 3: Safe"


llama_guard_checker = LlamaGuardChecker()
