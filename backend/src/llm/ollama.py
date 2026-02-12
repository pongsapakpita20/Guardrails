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