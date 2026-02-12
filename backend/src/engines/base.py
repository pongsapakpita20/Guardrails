from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

# กำหนดหน้าตาของ Switch ที่จะส่งไปให้ Frontend สร้างปุ่ม
class SwitchInfo(BaseModel):
    key: str           # ชื่อตัวแปร (เช่น violent_check)
    label: str         # ข้อความโชว์บนปุ่ม (เช่น "Block Violence")
    default: bool = True
    description: str = ""

# ผลลัพธ์การตรวจ
class GuardResult(BaseModel):
    safe: bool
    violation: str = None
    reason: str = None

# แม่แบบ (Abstract Base Class)
class BaseGuardEngine(ABC):
    
    @abstractmethod
    def get_switches(self) -> List[SwitchInfo]:
        pass

    # ✅ แก้บรรทัดนี้: เพิ่ม **kwargs เพื่อรับ model_name, provider_id
    @abstractmethod
    async def process(self, message: str, config: Dict[str, bool], **kwargs) -> GuardResult:
        """ประมวลผลข้อความตาม Config"""
        pass