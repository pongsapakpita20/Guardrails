from typing import List, Dict
from .base import BaseGuardEngine, SwitchInfo, GuardResult

class LlamaGuardEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        return [
            SwitchInfo(key="violent_check", label="S1: Violent Crimes", default=True),
            SwitchInfo(key="crime_check", label="S2: Non-Violent Crimes", default=True),
            SwitchInfo(key="sex_check", label="S3: Sex-Related Crimes", default=True),
            SwitchInfo(key="child_check", label="S4: Child Exploitation", default=True),
            SwitchInfo(key="self_harm_check", label="S8: Self-Harm", default=True),
            SwitchInfo(key="hate_check", label="S7: Hate Speech", default=True),
            SwitchInfo(key="pii_check", label="Privacy (PII)", default=False),
            SwitchInfo(key="off_topic_check", label="Off-Topic Control", default=False),
        ]

    async def process(self, message: str, config: Dict[str, bool]) -> GuardResult:
        text = message.lower()
        
        # --- Logic จำลอง (เดี๋ยวค่อยต่อ AI จริงทีหลัง) ---
        if config.get("violent_check") and any(w in text for w in ["ระเบิด", "kill", "bomb"]):
            return GuardResult(safe=False, violation="S1: Violence", reason="Found violent content")
            
        if config.get("pii_check"):
            import re
            if re.search(r"\d{10}", text):
                return GuardResult(safe=False, violation="Privacy", reason="Found phone number")
        
        # ... (Logic อื่นๆ เหมือนเดิม) ...

        return GuardResult(safe=True)