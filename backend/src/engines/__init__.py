import os
from .base import BaseGuardEngine
from .llama_guard import LlamaGuardEngine
from .nemo import NemoGuardEngine
# from .guardrails_ai import GuardrailsAIEngine

def get_engine() -> BaseGuardEngine:
    engine_type = os.getenv("GUARD_ENGINE", "llama").lower()
    
    print(f"🔧 Initializing Guard Engine: {engine_type.upper()}")
    
    if engine_type == "nemo":
        return NemoGuardEngine()
    elif engine_type == "guardrails_ai":
        # return GuardrailsAIEngine()
        raise NotImplementedError("Guardrails AI not implemented yet")
    else:
        return LlamaGuardEngine()

# สร้าง Singleton Instance ไว้ใช้ทั่วแอป
active_engine = get_engine()