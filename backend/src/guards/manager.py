from ..models.schemas import ConfigSwitches

class GuardManager:
    """
    ผู้จัดการความปลอดภัย: รับ Input มาแล้ววิ่งเช็คทีละด่าน
    """
    
    async def process(self, message: str, config: ConfigSwitches):
        # แปลงข้อความให้เป็นตัวเล็กหมด จะได้เช็คง่ายๆ (เฉพาะช่วง Mockup)
        text = message.lower()
        
        # --- Group A: Safety (Llama Guard Simulation) ---
        
        # 1. Violent Crimes
        if config.violent_check:
            if any(word in text for word in ["ระเบิด", "ฆ่า", "bomb", "kill"]):
                return {"safe": False, "violation": "S1: Violent Crimes", "reason": "ตรวจพบคำว่า ฆ่า/ระเบิด"}

        # 2. Non-Violent Crimes
        if config.crime_check:
            if any(word in text for word in ["ขโมย", "โกง", "steal", "fraud"]):
                return {"safe": False, "violation": "S2: Non-Violent Crimes", "reason": "ตรวจพบเนื้อหาเกี่ยวกับอาชญากรรม"}

        # 3. Sex-Related
        if config.sex_check:
            if any(word in text for word in ["sex", "โป๊", "nude"]):
                return {"safe": False, "violation": "S3: Sex-Related", "reason": "ตรวจพบเนื้อหาทางเพศ"}

        # 4. Child Exploitation (ข้ามไปก่อนใน Mockup)
        
        # 5. Self-Harm
        if config.self_harm_check:
            if any(word in text for word in ["ตาย", "die", "suicide"]):
                return {"safe": False, "violation": "S8: Self-Harm", "reason": "ตรวจพบเนื้อหาทำร้ายตัวเอง"}
                
        # 6. Hate Speech
        if config.hate_check:
            if any(word in text for word in ["เกลียด", "hate", "stupid"]):
                return {"safe": False, "violation": "S7: Hate Speech", "reason": "ตรวจพบคำเหยียดหยาม"}

        # --- Group B: Custom Logic ---

        # 7. PII (ข้อมูลส่วนตัว)
        if config.pii_check:
            # จำลองการเจอเลข 10 หลัก (เบอร์โทร)
            import re
            if re.search(r"\d{10}", text):
                return {"safe": False, "violation": "Privacy", "reason": "ตรวจพบหมายเลขโทรศัพท์/บัตร"}

        # 8. Off-Topic
        if config.off_topic_check:
            # สมมติว่าห้ามคุยเรื่อง 'การเมือง'
            if "นายก" in text or "government" in text:
                return {"safe": False, "violation": "Off-Topic", "reason": "ไม่อนุญาตให้คุยเรื่องการเมือง"}

        # ถ้าผ่านทุกด่าน
        return {"safe": True, "violation": None, "reason": None}

# สร้าง Instance ไว้เรียกใช้
guard_manager = GuardManager()