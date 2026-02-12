import requests
import os
from typing import List
from .base import BaseLLMService

class GPUStackService(BaseLLMService):
    def __init__(self):
        # Default GPUStack port usually 80 or set via Env
        self.base_url = os.getenv("GPUSTACK_URL", "http://localhost:10101/v1")
        self.api_key = os.getenv("GPUSTACK_API_KEY", "sk-no-key-required")

    def get_models(self) -> List[str]:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            res = requests.get(f"{self.base_url}/models", headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return [model["id"] for model in data.get("data", [])]
            return []
        except Exception as e:
            print(f"⚠️ GPUStack Error: {e}")
            return []

    async def generate(self, prompt: str, system_prompt: str = "", model_name: str = "") -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        
        try:
            print(f"🚀 Sending to GPUStack ({model_name})...")
            res = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=120)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
            else:
                return f"Error: {res.status_code} - {res.text}"
        except Exception as e:
            return f"Connection Error: {str(e)}"
    
    # GPUStack มักจัดการโหลดโมเดลอัตโนมัติ เราแค่อาจจะ Ping เบาๆ
    def check_model_status(self, model_name: str) -> bool:
        return True