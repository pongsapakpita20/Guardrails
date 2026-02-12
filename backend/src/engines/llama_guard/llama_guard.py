from typing import List, Dict
import re
from ..base import BaseGuardEngine, SwitchInfo, GuardResult

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
        
        # --- 1. Violent Crimes ---
        if config.get("violent_check") and any(w in text for w in ["ระเบิด", "ฆ่า", "bomb", "kill"]):
            return GuardResult(safe=False, violation="S1: Violence", reason="ตรวจพบเนื้อหาความรุนแรง/การฆ่า")

        # --- 2. Non-Violent Crimes ---
        if config.get("crime_check") and any(w in text for w in ["ขโมย", "โกง", "steal", "fraud", "hack"]):
            return GuardResult(safe=False, violation="S2: Non-Violent Crimes", reason="ตรวจพบเนื้อหาอาชญากรรม/การโกง")

        # --- 3. Sex-Related ---
        if config.get("sex_check") and any(w in text for w in ["sex", "โป๊", "nude", "porn"]):
            return GuardResult(safe=False, violation="S3: Sex-Related", reason="ตรวจพบเนื้อหาทางเพศ")

        # --- 4. Child Exploitation ---
        if config.get("child_check") and any(w in text for w in ["child porn", "โลลิ", "loli"]):
            return GuardResult(safe=False, violation="S4: Child Exploitation", reason="ตรวจพบเนื้อหาละเมิดเด็ก")

        # --- 5. Self-Harm ---
        if config.get("self_harm_check") and any(w in text for w in ["ตาย", "die", "suicide", "ฆ่าตัวตาย"]):
            return GuardResult(safe=False, violation="S8: Self-Harm", reason="ตรวจพบเนื้อหาทำร้ายตัวเอง")

        # --- 6. Hate Speech ---
        if config.get("hate_check") and any(w in text for w in ["เกลียด", "hate", "stupid", "โง่", "เลว"]):
            return GuardResult(safe=False, violation="S7: Hate Speech", reason="ตรวจพบคำเหยียดหยาม/สร้างความเกลียดชัง")

        # --- 7. PII (Privacy) ---
        if config.get("pii_check"):
            # ตรวจเบอร์โทร 10 หลัก (แบบง่าย)
            if re.search(r"\d{10}", text):
                return GuardResult(safe=False, violation="Privacy", reason="ตรวจพบข้อมูลส่วนตัว (เบอร์โทรศัพท์)")

        # --- 8. Off-Topic ---
        if config.get("off_topic_check"):
            # ตัวอย่าง: ห้ามคุยเรื่องการเมือง
            if any(w in text for w in ["นายก", "government", "politics", "เลือกตั้ง"]):
                return GuardResult(safe=False, violation="Off-Topic", reason="ไม่อนุญาตให้คุยเรื่องการเมือง")

        # ผ่านทุกด่าน
        return GuardResult(safe=True)