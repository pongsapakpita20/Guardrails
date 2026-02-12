from .base import BaseGuardEngine
from .factory import EngineFactory

# ฟังก์ชันช่วยเรียกใช้ (Optional Helper)
def get_engine_by_id(engine_id: str) -> BaseGuardEngine:
    return EngineFactory.get_engine(engine_id)

# ดึงรายการ Engine ทั้งหมด
def get_engine_list():
    return EngineFactory.get_available_engines()