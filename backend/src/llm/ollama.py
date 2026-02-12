import requests
import os
from typing import List
from .base import BaseLLMService

class OllamaService(BaseLLMService):
    def __init__(self):
        # อ่าน URL จาก Environment (หรือใช้ default)
        self.base_url = os.getenv("OLLAMA_URL", "http://ollama:11434")

    def get_models(self) -> List[str]:
        """ยิงไปถาม Ollama ว่ามีโมเดลอะไรบ้าง"""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if res.status_code == 200:
                data = res.json()
                # ดึงเฉพาะชื่อโมเดลออกมา
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            print(f"⚠️ Ollama Error: {e}")
            return []
    def pull_model(self, model_name: str) -> bool:
        """สั่ง Ollama ให้ไปโหลดโมเดลจาก Registry"""
        print(f"⬇️ Pulling model: {model_name}...")
        payload = {"name": model_name, "stream": False} # Stream False เพื่อรอจนเสร็จ (หรือจะทำ Background Task ก็ได้)
        try:
            # หมายเหตุ: การ Pull โมเดลใหญ่อาจใช้เวลานานมาก จน Timeout ได้
            # ใน Production ควรทำเป็น Background Task แต่เบื้องต้นยิงไปก่อน
            requests.post(f"{self.base_url}/api/pull", json=payload, timeout=1) 
            # เราตั้ง timeout สั้นๆ เพื่อแค่ 'Trigger' ให้มันเริ่มโหลด แล้วปล่อยให้ Backend จัดการต่อ
            return True
        except requests.exceptions.ReadTimeout:
            # Timeout คือเรื่องปกติสำหรับการ Trigger pull
            return True 
        except Exception as e:
            print(f"❌ Pull failed: {e}")
            return False
    async def generate(self, prompt: str, system_prompt: str = "", model_name: str = "") -> str:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }
        
        print(f"🚀 Sending to Ollama ({model_name})...")
        try:
            res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
            if res.status_code == 200:
                return res.json().get("response", "")
            else:
                return f"Error: {res.status_code} - {res.text}"
        except Exception as e:
            return f"Connection Error: {str(e)}"