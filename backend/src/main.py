from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# สร้างแอป
app = FastAPI(title="AI Guardrails Gateway")

# 1. Config CORS (เพื่อให้ Frontend React ยิงเข้ามาได้)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ใน Production ควรระบุเป็น ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Define Data Model (หน้าตาข้อมูลที่รับ-ส่ง)
class ConfigSwitches(BaseModel):
    violent_check: bool = True
    crime_check: bool = True
    sex_check: bool = True
    child_check: bool = True
    self_harm_check: bool = True
    hate_check: bool = True
    pii_check: bool = False
    off_topic_check: bool = False

class ChatRequest(BaseModel):
    message: str
    config: Optional[ConfigSwitches] = None

# 3. Routes (จุดเชื่อมต่อ)
@app.get("/")
async def health_check():
    return {"status": "online", "service": "Guardrails Gateway"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Phase 2: Mockup logic (ยังไม่ได้ต่อ AI จริง)
    print(f"Received message: {request.message}")
    print(f"Active Switches: {request.config}")
    
    return {
        "status": "success",
        "response": f"Echo from Gateway: {request.message}",
        "violation": None
    }