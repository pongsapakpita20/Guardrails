from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseLLMService(ABC):
    @abstractmethod
    def get_models(self) -> List[str]:
        """ดึงรายชื่อโมเดลที่มีในเครื่อง"""
        pass

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", model_name: str = "") -> str:
        """ส่งข้อความไปให้ AI ตอบกลับมา"""
        pass