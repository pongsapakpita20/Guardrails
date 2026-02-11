from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any

# Import Engine ที่เราเพิ่งทำ
from .engines import active_engine 
from .engines.base import SwitchInfo

app = FastAPI(title="AI Guardrails Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. Endpoint ใหม่: ขอรายการสวิตช์ ---
@app.get("/config/switches", response_model=List[SwitchInfo])
async def get_switches():
    """Frontend จะเรียกอันนี้เพื่อไปวาดปุ่ม"""
    return active_engine.get_switches()

# --- 2. Endpoint เดิม: แต่ใช้ Engine ใหม่ ---
class ChatRequest(BaseModel):
    message: str
    config: Dict[str, bool] # รับเป็น Dict ยืดหยุ่น ไม่ Fix Field แล้ว

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"📥 Input: {request.message}")
    
    # เรียกใช้ Engine ปัจจุบัน
    result = await active_engine.process(request.message, request.config)
    
    if not result.safe:
        return {
            "status": "blocked",
            "response": "[BLOCKED] เนื้อหาไม่ปลอดภัย",
            "violation": result.violation,
            "reason": result.reason
        }
    
    return {
        "status": "success",
        "response": f"AI: รับทราบครับ '{request.message}' (ปลอดภัย)",
        "violation": None
    }