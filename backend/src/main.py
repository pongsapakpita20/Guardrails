from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

# ✅ ใช้ Factory แทน active_engine ตัวเก่า
from .engines.factory import EngineFactory
from .engines.base import SwitchInfo
from .llm.factory import LLMFactory
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
    provider_id: str = "ollama"      # <--- เพิ่ม
    model_name: str = "scb10x/typhoon2.5-qwen3-4b"   # <--- เพิ่ม (Default)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"📥 Input: {request.message} | Engine: {request.framework_id}")
    
    try:
        active_engine = EngineFactory.get_engine(request.framework_id)
        
        # 2. ส่ง provider_id และ model_name ไปให้ Engine
        # (ต้องแก้ Base Engine ให้รับ kwargs ได้ก่อน ดูข้อ 2)
        result = await active_engine.process(
            request.message, 
            request.config, 
            provider_id=request.provider_id, 
            model_name=request.model_name
        )
        # กรณี: ไม่ปลอดภัย (Blocked)
        if not result.safe:
            return {
                "status": "blocked",
                "response": "🚫 " + (result.reason or "เนื้อหาไม่ปลอดภัย"),
                "violation": result.violation,
                "reason": result.reason
            }
            
        real_response = result.reason if result.reason else f"AI: รับทราบครับ (ปลอดภัย)"
        
        return {
            "status": "success",
            "response": real_response,
            "violation": None
        }

    except Exception as e:
        print(f"🔥 System Error: {e}")
        return {
            "status": "error",
            "response": "System Error: เกิดข้อผิดพลาดภายในระบบ",
            "violation": str(e)
        }
@app.get("/health")
async def health_check():
    """เอาไว้ให้ Frontend ยิงเช็คว่า Server พร้อมหรือยัง"""
    return {"status": "ok", "message": "Backend is ready"}    
# ==========================================
# 4. Endpoint ใหม่: ขอรายชื่อ LLM Providers (Ollama, GPUStack)
# ==========================================
@app.get("/providers")
async def get_providers():
    return LLMFactory.get_providers()    

# ==========================================
# 5. Endpoint ใหม่: ขอรายชื่อ Models ของ Provider นั้นๆ
# ==========================================
@app.get("/models/{provider_id}")
async def get_models(provider_id: str):
    try:
        service = LLMFactory.get_service(provider_id)
        models = service.get_models()
        return {"provider": provider_id, "models": models}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class ModelPullRequest(BaseModel):
    provider_id: str
    model_name: str

@app.post("/model/pull")
async def pull_new_model(req: ModelPullRequest):
    try:
        service = LLMFactory.get_service(req.provider_id)
        
        # เฉพาะ Ollama ที่เราเขียนฟังก์ชัน pull ไว้
        if hasattr(service, 'pull_model'):
            success = service.pull_model(req.model_name)
            if success:
                 return {"status": "started", "message": f"Downloading {req.model_name}... Check logs."}
            else:
                 raise HTTPException(status_code=500, detail="Failed to trigger download")
        else:
             return {"status": "skipped", "message": "This provider does not support direct download via API."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))