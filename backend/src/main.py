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
    
    # เรียกใช้ Engine
    result = await active_engine.process(request.message, request.config)
    
    # กรณี: ไม่ปลอดภัย (Blocked)
    if not result.safe:
        return {
            "status": "blocked",
            "response": "🚫 " + (result.reason or "เนื้อหาไม่ปลอดภัย"),
            "violation": result.violation,
            "reason": result.reason
        }
    
    # กรณี: ปลอดภัย (Success) -> ✅ แก้ตรงนี้ครับ!
    # ถ้ามีคำตอบจาก AI (ฝากมาใน reason) ให้ใช้เลย
    # ถ้าไม่มี (เช่น LlamaGuardEngine ตัวเก่า) ให้ใช้ Default text
    real_response = result.reason if result.reason else f"AI: รับทราบครับ '{request.message}' (ปลอดภัย)"
    
    return {
        "status": "success",
        "response": real_response,
        "violation": None
    }