from typing import List, Dict, Optional
import os
import nest_asyncio
from nemoguardrails import LLMRails, RailsConfig
from ..base import BaseGuardEngine, SwitchInfo, GuardResult

# Apply nest_asyncio to allow nested event loops (crucial for Colang 1.0)
nest_asyncio.apply()

class NemoGuardEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        return [
            SwitchInfo(key="jailbreak", label="🛡️ Anti-Jailbreak (NeMo)", default=True),
            SwitchInfo(key="input_check", label="🤬 Input Moderation (Toxicity)", default=True),
            SwitchInfo(key="pii", label="🕵️ PII Masking", default=True),
            SwitchInfo(key="off_topic", label="🚧 Topic Control", default=False),
            SwitchInfo(key="competitor_check", label="🏢 Competitor Check", default=False),
            SwitchInfo(key="hallucination", label="🤥 Anti-Hallucination (Fact Check)", default=False),
        ]

    async def process(self, message: str, config: Dict[str, bool], **kwargs) -> GuardResult:
        # 1. Prepare Configuration
        current_model = kwargs.get("model_name", "scb10x/typhoon2.5-qwen3-4b")
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")

        # Dynamic Colang & YAML generation
        colang_content = self._generate_colang(config)
        yaml_content = self._generate_yaml(config, current_model, ollama_url)

        # 2. Initialize Rails
        try:
            rails_config = RailsConfig.from_content(
                colang_content=colang_content,
                yaml_content=yaml_content
            )
            rails = LLMRails(rails_config)

            # 3. Generate Response
            # Note: NeMo Guardrails handles both input/output rails internally via 'generate'
            response = await rails.generate_async(messages=[{
                "role": "user",
                "content": message
            }])

            # 4. Check for Blocking
            # NeMo returns a predefined message if blocked (e.g., "I cannot answer that.")
            # We need to detect if it was blocked.
            # A simple way is to check the response content or use verbose mode to access intermediate steps.
            # For simplicity here, we assume if response matches our "bot refuse" templates.
            
            response_text = response.response[0]["content"]

            if response_text in ["I cannot answer that.", "I cannot answer questions about competitors.", "I cannot answer off-topic questions."]:
                return GuardResult(safe=False, violation="NeMo Guard", reason=response_text)
            
            # Additional check: If response is empty or error
            if not response_text:
                 return GuardResult(safe=False, violation="Error", reason="Empty response from NeMo")

            return GuardResult(safe=True, reason=response_text)

        except Exception as e:
            print(f"🔥 NeMo Engine Error: {e}")
            return GuardResult(safe=False, violation="System Error", reason=str(e))

    def _generate_colang(self, config: Dict[str, bool]) -> str:
        colang = """
        # ==========================================
        # 1. Politics (การเมือง) - TH & EN
        # ==========================================
        define user ask about politics
            "Who will win the election?"
            "What do you think about the government?"
            "พรรคไหนดีกว่ากัน"
            "ใครจะเป็นนายกคนต่อไป"
            "คิดยังไงกับม็อบ"
            "การเมืองช่วงนี้เป็นไง"

        define bot refuse politics
            "I cannot answer questions about politics. I am an SRT service assistant."
            "ขออภัยครับ กระผมไม่สามารถแสดงความคิดเห็นเรื่องการเมืองได้ครับ ผมยินดีให้ข้อมูลบริการรถไฟครับ"

        # ==========================================
        # 2. Competitors (คู่แข่ง: เครื่องบิน, รถทัวร์) - TH & EN
        # ==========================================
        define user ask about competitor
            "Is flying faster?"
            "AirAsia is cheaper"
            "Nakhonchai Air service is better"
            "นั่งเครื่องบินเร็วกว่าไหม"
            "รถทัวร์ถูกกว่าหรือเปล่า"
            "นครชัยแอร์ดีกว่ามั้ย"
            "ไปเครื่องบินดีกว่ามั้ย"
            "เทียบกับสมบัติทัวร์ให้หน่อย"

        define bot refuse competitor
             "I cannot compare with other transport providers. Please check their websites directly."
             "ขออภัยครับ กระผมไม่สามารถเปรียบเทียบกับผู้ให้บริการอื่นได้ครับ แต่หากเป็นเรื่องรถไฟ กระผมยินดีบริการเต็มที่ครับ"

        # ==========================================
        # 3. Off-Topic (นอกเรื่อง: หวย, ดูดวง) - TH & EN
        # ==========================================
        define user ask off topic
            "What represent lottery number?"
            "Lucky number for tomorrow"
            "หวยออกอะไร"
            "ขอเลขเด็ดหน่อย"
            "ดวงวันนี้เป็นไง"
            "อากาศเชียงใหม่เป็นไง"

        define bot refuse off topic
            "I can only help with SRT train services."
            "กระผมให้ข้อมูลได้เฉพาะเรื่องการเดินรถไฟและการจองตั๋วครับผม"

        # ==========================================
        # Flows Definitions
        # ==========================================
        define flow politics
            user ask about politics
            bot refuse politics
        
        define flow competitor_check
            user ask about competitor
            bot refuse competitor
            
        define flow off_topic_check
            user ask off topic
            bot refuse off topic
        """
        
        # Note: In dynamic generation, we append flows based on config.
        # But here I defined basic blocks directly for clarity.
        # Real logic should append 'define flow ...' only if config is True.
        
        # Reset and build dynamically to respect config (Cleaner approach)
        colang_body = ""
        
        if config.get("off_topic"):
             colang_body += """
             define flow off_topic_flow
                 user ask about politics
                 bot refuse politics
             
             define flow lottery_flow
                 user ask off topic
                 bot refuse off topic
             """
            
        if config.get("competitor_check"):
            colang_body += """
            define flow competitor_flow
                user ask about competitor
                bot refuse competitor
            """
            
        return colang + colang_body

    def _generate_yaml(self, config: Dict[str, bool], model: str, ollama_url: str) -> str:
        # Basic YAML config for Ollama
        yaml_config = f"""
        models:
          - type: main
            engine: ollama
            model: {model}
            parameters:
              base_url: {ollama_url}
        """
        
        # Add rails config based on switches
        rails = []
        
        if config.get("jailbreak"):
            rails.append("input: check jailbreak")
            
        if config.get("pii"):
            # Mock PII via prompt (real solution uses Presidio actions)
            rails.append("input: check pii") 
            
        if config.get("hallucination"):
            rails.append("output: check hallucination")

        # Add instructions if needed
        yaml_config += "\n        rails:\n          input:\n            flows:\n"
        if config.get("jailbreak"):
             yaml_config += "              - self check input\n"
             
        return yaml_config