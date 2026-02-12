from typing import Dict, List, Type
from .base import BaseGuardEngine

# Import Engine ทั้งหมดมารอไว้
from .guardrails_ai import GuardrailsAIEngine
from .llama_guard import LlamaGuardEngine
from .nemo_guard import NemoGuardEngine

class EngineFactory:
    """
    โรงงานสำหรับสร้างและจัดการ Guardrails Engine
    """
    _engines: Dict[str, Type[BaseGuardEngine]] = {
        "guardrails_ai": GuardrailsAIEngine,
        "llama_guard": LlamaGuardEngine,
        "nemo": NemoGuardEngine,
    }
    
    _instances: Dict[str, BaseGuardEngine] = {}

    @classmethod
    def get_engine(cls, engine_id: str) -> BaseGuardEngine:
        """
        สร้างหรือดึง Instance ของ Engine ตาม ID
        """
        engine_id = engine_id.lower()
        
        # ถ้าเคยสร้างไว้แล้ว ให้เอาของเดิมมาใช้ (Singleton per engine)
        if engine_id in cls._instances:
            return cls._instances[engine_id]
        
        # ถ้ายังไม่เคยสร้าง ให้สร้างใหม่
        engine_class = cls._engines.get(engine_id)
        if not engine_class:
            raise ValueError(f"Unknown engine ID: {engine_id}. Available: {list(cls._engines.keys())}")
            
        print(f"🏭 Factory: Initializing Engine '{engine_id}'...")
        instance = engine_class()
        cls._instances[engine_id] = instance
        
        return instance

    @classmethod
    def get_available_engines(cls) -> List[Dict[str, str]]:
        """
        คืนค่ารายชื่อ Engine ทั้งหมด (สำหรับทำ Dropdown)
        """
        return [
            {"id": "guardrails_ai", "name": "Guardrails AI (Validators)"},
            {"id": "nemo", "name": "NVIDIA NeMo (Colang)"},
            {"id": "llama_guard", "name": "Llama Guard (Meta)"},
        ]