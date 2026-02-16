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
        
        # =========================================================
        # PART 1: ตรวจความปลอดภัยด้วย Llama Guard 3 (Local Ollama)
        # =========================================================
        
        # กฎความปลอดภัย (Safety Policy)
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
        
        # Prompt ตามมาตรฐาน Llama Guard 3
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
            # 🟢 บังคับใช้ Local Ollama สำหรับการตรวจ (Guard)
            guard_provider = "ollama"
            guard_model = "llama-guard3:8b" # ใช้รุ่น 8B ที่ดีที่สุดสำหรับ Local

            print(f"🛡️ Guard Checking with: {guard_model} on {guard_provider}...")
            
            guard_service = LLMFactory.get_service(guard_provider)
            guard_response = await guard_service.generate(prompt, model_name=guard_model)
            guard_response = guard_response.strip()

            # แปลผลลัพธ์
            if guard_response.startswith("unsafe"):
                parts = guard_response.split("\n")
                violation_codes = parts[1] if len(parts) > 1 else "Unknown"
                
                # เช็คว่า User ปิดสวิตช์กฎข้อนั้นไว้หรือเปล่า?
                violated_list = [v.strip() for v in violation_codes.split(",")]
                is_really_unsafe = False
                
                for code in violated_list:
                    if config.get(code, True): # ถ้าเปิดสวิตช์ไว้ ถือว่าผิดจริง
                        is_really_unsafe = True
                        break
                
                if is_really_unsafe:
                    print(f"🚫 BLOCKED by Llama Guard: {violation_codes}")
                    return GuardResult(
                        safe=False, 
                        violation=f"Llama Guard 3 ({violation_codes})", 
                        reason=f"AI ตรวจพบเนื้อหาไม่ปลอดภัยรหัส: {violation_codes}"
                    )
            
            print("✅ Input Safe. Forwarding to Chatbot...")

        except Exception as e:
            print(f"❌ Guard Error: {e}")
            # Fail Open (ปล่อยผ่านถ้า Guard พัง) หรือจะ Block ก็ได้
            # return GuardResult(safe=False, violation="System Error", reason="Guard System Failed")

        # =========================================================
        # PART 2: ส่งต่อให้ Chatbot บริษัท (GPUStack)
        # =========================================================
        try:
            # ดึง Provider/Model เป้าหมายจากที่ User เลือกหน้าเว็บ
            target_provider = kwargs.get("provider_id", "gpustack")
            target_model = kwargs.get("model_name", "scb10x/typhoon2.5-qwen3-4b")
            
            print(f"🚀 Sending to Chatbot: {target_model} on {target_provider}...")
            
            chat_service = LLMFactory.get_service(target_provider)
            
            # ส่งข้อความไปหา Chatbot (System Prompt จะไปถูกใส่ใน Service เอง)
            chat_response = await chat_service.generate(message, model_name=target_model)
            
            return GuardResult(safe=True, reason=chat_response)

        except Exception as e:
            return GuardResult(safe=False, violation="Chatbot Error", reason=f"ไม่สามารถติดต่อ Chatbot ได้: {str(e)}")