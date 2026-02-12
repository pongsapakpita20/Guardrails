import os
from .base import BaseGuardEngine
from .base import BaseGuardEngine
from .llama_guard.llama_guard import LlamaGuardEngine
from .nemo.nemo_guard import NemoGuardEngine 
from .guardrails_ai.guardrails_ai import GuardrailsAIEngine # <--- Import เข้ามา

def get_engine() -> BaseGuardEngine:
    engine_type = os.getenv("GUARD_ENGINE", "llama").lower()
    
    print(f"🔧 Initializing Guard Engine: {engine_type.upper()}")
    
    if engine_type == "nemo":
        return NemoGuardEngine()
    elif engine_type == "guardrails_ai":
        return GuardrailsAIEngine()  # <-- เปิดใช้งาน
    else:
        return LlamaGuardEngine()

active_engine = get_engine()