from typing import List, Dict
import os
from ..base import BaseGuardEngine, SwitchInfo, GuardResult
from ...llm.factory import LLMFactory

class LlamaGuardEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        return [
            SwitchInfo(key="S1", label="S1: Violent Crimes", default=True),
            SwitchInfo(key="S2", label="S2: Non-Violent Crimes", default=True),
            SwitchInfo(key="S3", label="S3: Sex-Related Crimes", default=True),
            SwitchInfo(key="S4", label="S4: Child Exploitation", default=True),
            SwitchInfo(key="S5", label="S5: Defamation", default=True),
            SwitchInfo(key="S6", label="S6: Specialized Advice", default=True),
            SwitchInfo(key="S7", label="S7: Privacy", default=True),
            SwitchInfo(key="S8", label="S8: Intellectual Property", default=True),
            SwitchInfo(key="S9", label="S9: Indiscriminate Weapons", default=True),
            SwitchInfo(key="S10", label="S10: Hate Speech", default=True),
            SwitchInfo(key="S11", label="S11: Suicide & Self-Harm", default=True),
            SwitchInfo(key="S12", label="S12: Sexual Content", default=True),
            SwitchInfo(key="S13", label="S13: Elections", default=True),
        ]

    async def process(self, message: str, config: Dict[str, bool], **kwargs) -> GuardResult:
        
        # 1. เตรียม Policy (กฎ) สำหรับ Llama Guard 3
        # เราจะส่งกฎพวกนี้ไปบอก AI ว่า "ช่วยตรวจข้อความตามกฎพวกนี้หน่อย"
        # (ตัดมาเฉพาะส่วนสำคัญเพื่อประหยัด Token)
        policy = """
<BEGIN UNSAFE CONTENT CATEGORIES>
S1: Violent Crimes. 
S2: Non-Violent Crimes.
S3: Sex-Related Crimes.
S4: Child Sexual Exploitation.
S5: Defamation.
S6: Specialized Advice.
S7: Privacy.
S8: Intellectual Property.
S9: Indiscriminate Weapons.
S10: Hate Speech.
S11: Suicide & Self-Harm.
S12: Sexual Content.
S13: Elections.
<END UNSAFE CONTENT CATEGORIES>
"""
        
        # 2. สร้าง Prompt ตามมาตรฐาน Llama Guard 3
        # มันต้องการ Format แบบนี้:
        prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
Task: Check if there is unsafe content in 'User' messages in conversations according to our safety policy with the below categories.

{policy}

<BEGIN CONVERSATION>

User: {message}

<END CONVERSATION>

Provide your safety assessment for User in the above conversation:
- First line must read 'safe' or 'unsafe'.
- If unsafe, a second line must include a comma-separated list of violated categories.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

        try:
            # 3. เลือก Provider (Ollama หรือ GPUStack)
            # เราจะพยายามใช้ provider เดียวกับที่ User เลือกมา แต่ถ้าไม่มีก็ default ไปที่ gpustack
            provider_id = kwargs.get("provider_id", "gpustack")
            
            # ⚠️ สำคัญ: ต้องระบุชื่อโมเดล Llama Guard ที่เราจะใช้
            # ถ้าใน GPUStack ชื่อโมเดลอาจจะเป็น "meta-llama/Llama-Guard-3-1B" 
            # หรือถ้าใช้ Ollama อาจจะเป็น "llama-guard3"
            # เพื่อความยืดหยุ่น เราจะลองหาโมเดลที่มีคำว่า 'guard' ในชื่อก่อน
            llm_service = LLMFactory.get_service(provider_id)
            
            # (Logic เสริม: หาชื่อโมเดล Llama Guard อัตโนมัติ)
            available_models = llm_service.get_models()
            target_model = ""
            for m in available_models:
                if "guard" in m.lower():
                    target_model = m
                    break
            
            if not target_model:
                # ถ้าหาไม่เจอ ให้ใช้ชื่อ default (เผื่อไว้)
                target_model = "meta-llama/Llama-Guard-3-1B" 

            print(f"🛡️ LlamaGuard Checking using model: {target_model}")

            # 4. ยิงไปถาม AI
            response = await llm_service.generate(prompt, model_name=target_model)
            response = response.strip()

            # 5. แปลผลลัพธ์
            # Llama Guard จะตอบว่า "safe" หรือ "unsafe\nS1"
            if response.startswith("unsafe"):
                parts = response.split("\n")
                violation_codes = parts[1] if len(parts) > 1 else "Unknown"
                
                # เช็คว่า User ปิดสวิตช์กฎข้อนั้นไว้หรือเปล่า?
                # เช่น ถ้าเขาปิด S1 (Violent) แล้ว AI ตอบ S1 มา เราต้องปล่อยผ่าน
                violated_list = [v.strip() for v in violation_codes.split(",")]
                is_really_unsafe = False
                
                for code in violated_list:
                    # ถ้า config เปิดไว้ (True) ถือว่าผิดจริง
                    if config.get(code, True): 
                        is_really_unsafe = True
                        break
                
                if is_really_unsafe:
                    return GuardResult(
                        safe=False, 
                        violation=f"Llama Guard 3 ({violation_codes})", 
                        reason=f"AI ตรวจพบเนื้อหาไม่ปลอดภัยรหัส: {violation_codes}"
                    )

            # ถ้าตอบ safe หรือ รหัสที่เจอไม่ได้เปิดใช้งานสวิตช์
            return GuardResult(safe=True)

        except Exception as e:
            print(f"❌ Llama Guard Error: {e}")
            # ถ้าเอ๋อ ให้ปล่อยผ่านไปก่อน (Fail Open) หรือจะบล็อกก็ได้แล้วแต่นโยบาย
            return GuardResult(safe=True, reason=f"Llama Guard Error: {e}")