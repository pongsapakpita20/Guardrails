"""
Llama Guard 3 8B — Full 15-Category Safety Check (Customized for SRT)
Uses the actual llama-guard3 model with individually toggleable S1–S15 categories.
"""
from typing import Tuple, Dict, List
from backend.ollama_service import ollama_service
from backend.config.settings import LLAMA_GUARD_MODEL


CATEGORIES = {
    "S1": "Violent Crimes. Planning, encouraging, or asking for help with violent crimes (e.g., murder, assault, kidnapping). Includes Thai context: ฆ่า, ทำร้ายร่างกาย, ตบตี, จ้างวานฆ่า, อุ้มหาย.",
    
    "S2": "Non-Violent Crimes. Discussing or facilitating fraud, scams, drug trafficking, or selling illegal/regulated items. Includes Thai slang and evasion: ขายยา, บัญชีม้า, ขายลูกปืน/ลูกปูน (bullets/weapons), ยัดเงิน, ใต้โต๊ะ, โกงเงิน.",
    
    "S3": "Sex Crimes. Encouraging or discussing sexual assault, harassment, or non-consensual sexual content. Includes Thai context: ข่มขืน, ลวนลาม, แอบถ่าย, วางยาปลุกเซ็กส์.",
    
    "S4": "Child Exploitation. Any content exploiting minors, including child abuse or selling children. Includes Thai context: ค้ามนุษย์, ขายเด็ก, ซื้อบริการเด็ก, อนาจารเด็ก.",
    
    "S5": "Defamation. Spreading false, damaging information to ruin someone's reputation. Includes Thai context: ใส่ร้าย, ประจาน, แฉ, หมิ่นประมาท.",
    
    "S6": "Specialized Advice. Providing unqualified medical, legal, or financial advice. Includes Thai context: ขอคำแนะนำเรื่องยา, ปรึกษาคดีความ, แนะนำหุ้น, ใบ้หวย.",
    
    "S7": "Privacy. Doxing or sharing sensitive personally identifiable information (PII). Includes Thai context: ขอเบอร์โทรส่วนตัว, ขอที่อยู่บ้าน, ตามสืบประวัติ, ขอบัตรประชาชน.",
    
    "S8": "Intellectual Property. Facilitating copyright infringement or piracy. Includes Thai context: แจกวาร์ปหนังเถื่อน, โหลดเถื่อน, โปรแกรมเถื่อน, ก๊อปปี้ผลงาน.",
    
    "S9": "Indiscriminate Weapons. Instructions on building weapons of mass destruction, explosives, or homemade guns. Includes Thai context: ทำระเบิด, ปืนเถื่อน, อาวุธสงคราม.",
    
    "S10": "Hate. Hate speech, discrimination, or slurs based on race, religion, gender, or social class. Includes Thai context: เหยียดเชื้อชาติ, เหยียดเพศ, บูลลี่รูปร่าง, ด่าเหมารวม (e.g., พวกเจ๊ก, พวกบ้านนอก, ตุ๊ด).",
    
    "S11": "Self-Harm. Encouraging or providing instructions for suicide or self-injury. Includes Thai context: ฆ่าตัวตาย, กรีดข้อมือ, วิธีตายแบบไม่เจ็บ, ไม่อยากอยู่แล้ว.",
    
    "S12": "Sexual Content. Depicting explicit sexual acts, erotica, or pornography. Includes Thai context: หนังโป๊, ขอคลิปหลุด, นิยาย 18+, เสียว, รูปโป๊.",
    
    "S13": "Elections. Election interference, misinformation about voting, or vote buying. Includes Thai context: ซื้อเสียง, โกงเลือกตั้ง, ข่าวปลอมการเมือง.",
    
    "S14": "Competitor Mention. Discussing, comparing, or recommending SRT competitors (airlines, buses, ride-hailing). Catch sarcasm or implicit comparisons. Includes Thai context: นครชัยแอร์, แอร์เอเชีย, นกแอร์, รถทัวร์, นั่งเครื่องบินดีกว่ามั้ย, บริการรถไฟสู้รถทัวร์ไม่ได้เลย.",
    
    "S15": "Off-Topic. Discussing topics completely unrelated to train travel, ticket booking, or railway services. Includes Thai context: การเมือง, รัฐบาล, นายก, หวยออกอะไร, ดวงวันนี้, ศาสนา, สภาพอากาศ, ถามเรื่องทั่วไปที่ไม่เกี่ยวกับการรถไฟ.",
    
    "S16": "Profanity, Toxicity, and Sarcasm. Using offensive language, swear words, insults, highly disrespectful language, passive-aggressive sarcasm, or masked words (using symbols to bypass filters). Includes Thai context: คำหยาบ (ไอ้เหี้ย, สัส, ควย, แม่ง, หน้าโง่), คำเลี่ยง (ค_ย, สั*ส, อห.), คำประชดประชัน (บริการหมาไม่แดก, เจริญล่ะ, รถไฟหรือเต่า, บริการดีจังเลยนะเรื่องโง่ๆ). Block any verbal abuse.",
}

class LlamaGuardChecker:
    def check(self, text: str, enabled_categories: List[str] = None, role: str = "User") -> Tuple[bool, str]:
        if enabled_categories is None:
            enabled_categories = list(CATEGORIES.keys())
        print(f"🛠️ [DEBUG] Llama Guard is checking {len(enabled_categories)} categories: {enabled_categories}")
        if not enabled_categories:
            return True, "No categories enabled — skipped"

        cat_block = "\n".join(
            f"{k}: {CATEGORIES[k]}"
            for k in enabled_categories if k in CATEGORIES
        )

        # 👇 1. เอา [INST] ออก และปรับให้ตรงตาม Standard Llama Guard 3 เป๊ะๆ
        prompt = f"""Task: Check if there is unsafe, competitor-related, or off-topic content in '{role}' messages. 
You are a strict guard for the State Railway of Thailand (SRT). Any topic not about trains or SRT is UNSAFE (S15).

<BEGIN UNSAFE CONTENT CATEGORIES>
{cat_block}
<END UNSAFE CONTENT CATEGORIES>

<EXAMPLES OF UNSAFE CONTENT>
User: " หมูกะทะร้านไหนอร่อย"
Verdict: unsafe
S15

User: "หุ้นตัวไหนน่าซื้อ"
Verdict: unsafe
S15

User: "ไอ้ควาย บริการแย่มาก"
Verdict: unsafe
S16

User: "จองตั๋วเครื่องบินแอร์เอเชียให้หน่อย"
Verdict: unsafe
S14
</EXAMPLES OF UNSAFE CONTENT>

<BEGIN CONVERSATION>
{role}: {text}
<END CONVERSATION>

Provide your safety assessment for {role} in the above conversation:
- First line must read 'safe' or 'unsafe'.
- If unsafe, a second line must include a comma-separated list of violated categories."""
        messages = [{"role": "user", "content": prompt}]
        response_text = ""
        try:
            for chunk in ollama_service.chat_stream(LLAMA_GUARD_MODEL, messages):
                response_text += chunk
        except Exception as e:
            return True, f"Llama Guard check failed (skipped): {str(e)}"

        # 👇 2. เพิ่ม DEBUG Print จะได้เห็นว่า Llama Guard ตอบอะไรกลับมาจริงๆ!
        print(f"🧐 [DEBUG Llama Guard 3] Raw Output:\n{response_text.strip()}")

        first_line = response_text.strip().split("\n")[0].lower()
        if "unsafe" in first_line:
            return False, f"Llama Guard 3: {response_text.strip()}"
        return True, "Llama Guard 3: Safe"

llama_guard_checker = LlamaGuardChecker()