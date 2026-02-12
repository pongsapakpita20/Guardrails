from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

# ✅ ใช้ Factory แทน active_engine ตัวเก่า
from .engines.factory import EngineFactory
from .engines.base import SwitchInfo

app = FastAPI(title="AI Guardrails Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. Endpoint ใหม่: ขอรายชื่อ Framework ทั้งหมด
# ==========================================
@app.get("/frameworks")
async def get_frameworks():
    """ส่งรายชื่อ Engine ที่ระบบมีกลับไปทำ Dropdown"""
    return EngineFactory.get_available_engines()

# ==========================================
# 2. Endpoint แก้ไข: ขอสวิตช์ (ตาม Framework ที่เลือก)
# ==========================================
@app.get("/config/switches", response_model=List[SwitchInfo])
async def get_switches(framework_id: str = Query("guardrails_ai", description="ID ของ Framework ที่ต้องการ")):
    try:
        engine = EngineFactory.get_engine(framework_id)
        return engine.get_switches()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==========================================
# 3. Endpoint แก้ไข: Chat (ระบุ Framework ได้)
# ==========================================
class ChatRequest(BaseModel):
    message: str
    config: Dict[str, bool]
    framework_id: str = "guardrails_ai"  # <--- เพิ่มช่องนี้

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"📥 Input: {request.message} | Engine: {request.framework_id}")
    
    try:
        # 1. เรียก Engine ตามที่ User เลือกผ่าน Factory
        active_engine = EngineFactory.get_engine(request.framework_id)
        
        # 2. ประมวลผล
        result = await active_engine.process(request.message, request.config)
        
        # กรณี: ไม่ปลอดภัย (Blocked)
        if not result.safe:
            return {
                "status": "blocked",
                "response": "🚫 " + (result.reason or "เนื้อหาไม่ปลอดภัย"),
                "violation": result.violation,
                "reason": result.reason
            }
        
        # กรณี: ปลอดภัย (Success)
        real_response = result.reason if result.reason else f"AI ({request.framework_id}): รับทราบครับ '{request.message}' (ปลอดภัย)"
        
        return {
            "status": "success",
            "response": real_response,
            "violation": None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Engine Error: {str(e)}")
    except Exception as e:
        print(f"🔥 System Error: {e}")
        return {
            "status": "error",
            "response": "System Error: เกิดข้อผิดพลาดภายในระบบ",
            "violation": str(e)
        }