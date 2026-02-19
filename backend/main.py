from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import time

from backend.logger import log_manager
from backend.ollama_service import ollama_service, gpustack_service, get_service
from backend.config.settings import SYSTEM_PROMPT, FRAMEWORK_INFO
from backend.metrics import get_resource_metrics

app = FastAPI(title="SRT Chatbot Guardrails")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class GuardToggle(BaseModel):
    pii: bool = False
    off_topic: bool = False
    jailbreak: bool = False
    competitor: bool = False
    toxicity: bool = False
    hallucination: bool = False

class LlamaGuardToggle(BaseModel):
    S1:  bool = True   # Violent Crimes
    S2:  bool = True   # Non-Violent Crimes
    S3:  bool = True   # Sex Crimes
    S4:  bool = True   # Child Exploitation
    S5:  bool = True   # Defamation
    S6:  bool = True   # Specialized Advice
    S7:  bool = True   # Privacy
    S8:  bool = True   # Intellectual Property
    S9:  bool = True   # Indiscriminate Weapons
    S10: bool = True   # Hate
    S11: bool = True   # Self-Harm
    S12: bool = True   # Sexual Content
    S13: bool = True   # Elections

class ChatRequest(BaseModel):
    message: str
    model: str
    framework: str = "none"
    backend: str = "ollama"  # "ollama" | "gpustack"
    guardrails_ai: GuardToggle = GuardToggle()
    nemo: GuardToggle = GuardToggle()
    llama_guard: LlamaGuardToggle = LlamaGuardToggle()

class ChatResponse(BaseModel):
    response: str
    blocked: bool = False
    violation_type: Optional[str] = None
    framework_used: Optional[str] = None

# FRAMEWORK_INFO is imported from backend.config.settings

def _load_guard(framework: str, guard_name: str):
    import importlib
    # Map framework → file suffix (e.g., pii → pii_guardai / pii_nemo)
    suffix_map = {
        "guardrails_ai": "_guardai",
        "nemo": "_nemo",
        "llama_guard": "_llamaguard",
    }
    suffix = suffix_map.get(framework, "")
    return importlib.import_module(f"backend.guards.{framework}.{guard_name}{suffix}")

# --- Endpoints ---

@app.get("/health")
async def health_check(backend: str = "ollama"):
    svc = get_service(backend)
    gpu_info = await svc.check_gpu()
    return {"status": "ok", "gpu": gpu_info, "backend": backend}

@app.get("/models")
async def get_models(backend: str = "ollama"):
    svc = get_service(backend)
    models = await svc.list_models()
    return {"models": models, "backend": backend}

@app.get("/frameworks")
async def get_frameworks():
    return {"frameworks": FRAMEWORK_INFO}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await log_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_manager.disconnect(websocket)


# --- Guard runners ---

async def run_input_guards(request: ChatRequest) -> Optional[ChatResponse]:
    fw = request.framework
    if fw == "none":
        return None

    # --- Llama Guard: unified S1-S14 check ---
    if fw == "llama_guard":
        toggles = request.llama_guard
        enabled = [k for k in ["S1","S2","S3","S4","S5","S6","S7","S8","S9","S10","S11","S12","S13"] if getattr(toggles, k)]
        if enabled:
            from backend.guards.llama_guard.checker_llamaguard import llama_guard_checker
            await log_manager.log("Input Guard", "processing", f"[Llama Guard 3] Checking {len(enabled)} categories...")
            is_safe, details = llama_guard_checker.check(request.message, enabled, role="User")
            if not is_safe:
                await log_manager.log("Input Guard", "error", f"[Llama Guard 3] Blocked: {details}")
                return ChatResponse(response="ข้อความละเมิดนโยบายความปลอดภัย",
                                    blocked=True, violation_type="Llama Guard", framework_used=fw)
        return None

    # --- Guardrails AI / NeMo: Input Guards (3) ---
    # 1. PII (regex), 2. Jailbreak (regex), 3. Off-Topic (LLM)
    toggles: GuardToggle = getattr(request, fw, GuardToggle())

    # Special handling for NeMo Pure Framework
    # Call NeMo ONCE and check all guards on the single response
    if fw == "nemo":
        from backend.guards.nemo.nemo_engine import check_all_guards

        # Build list of enabled input guards
        enabled_input = []
        if toggles.pii: enabled_input.append("pii")
        if toggles.jailbreak: enabled_input.append("jailbreak")
        if toggles.toxicity: enabled_input.append("toxicity")
        if toggles.off_topic: enabled_input.append("off_topic")

        if enabled_input:
            await log_manager.log("Input Guard", "processing", f"[NeMo] Checking {', '.join(g.upper() for g in enabled_input)}...")
            is_safe, details, violation = await check_all_guards(request.message, enabled_input)
            if not is_safe:
                if violation == "nemo_unavailable":
                    await log_manager.log("Input Guard", "error", f"[NeMo] Unavailable: {details}")
                    return ChatResponse(
                        response="ระบบ NeMo Guardrails ยังไม่พร้อมใช้งาน (โปรดติดตั้ง/activate environment ที่มี `nemoguardrails`)",
                        blocked=True,
                        violation_type="NeMoUnavailable",
                        framework_used=fw,
                    )
                if violation == "nemo_error":
                    await log_manager.log("Input Guard", "error", f"[NeMo] Error: {details}")
                    return ChatResponse(
                        response="ระบบ NeMo Guardrails ทำงานผิดพลาดชั่วคราว จึงระงับข้อความนี้เพื่อความปลอดภัยค่ะ",
                        blocked=True,
                        violation_type="NeMoError",
                        framework_used=fw,
                    )
                # Map violation type to user-facing response
                response_map = {
                    "pii": ("ข้อความมีข้อมูลส่วนบุคคล (PII) ไม่สามารถประมวลผลได้", "PII"),
                    "jailbreak": ("ข้อความละเมิดนโยบายความปลอดภัย", "Jailbreak"),
                    "toxicity": ("ข้อความมีเนื้อหาที่ไม่เหมาะสม", "Toxicity"),
                    "off_topic": ("ฉันสามารถตอบคำถามเกี่ยวกับการรถไฟแห่งประเทศไทยเท่านั้น", "Off-Topic"),
                }
                msg, vtype = response_map.get(violation, (details, violation))
                await log_manager.log("Input Guard", "error", f"[NeMo] {vtype} Blocked: {details}")
                return ChatResponse(response=msg, blocked=True, violation_type=vtype, framework_used=fw)
        return None


    # === GUARDRAILS AI HANDLING (Legacy/Hybrid) ===
    # === 1. PII Detection (regex — fast) ===
    if toggles.pii and "pii" in FRAMEWORK_INFO[fw]["supports"]:
        mod = _load_guard(fw, "pii")
        await log_manager.log("Input Guard", "processing", f"[{fw}] Checking PII...")
        is_safe, details = mod.pii_guard.scan(request.message)
        if not is_safe:
            await log_manager.log("Input Guard", "error", f"[{fw}] PII Blocked: {details}")
            return ChatResponse(response="ข้อความมีข้อมูลส่วนบุคคล (PII) ไม่สามารถประมวลผลได้",
                                blocked=True, violation_type="PII", framework_used=fw)

    # === 2. Jailbreak Attempt (regex — fast, specific) ===
    if toggles.jailbreak and "jailbreak" in FRAMEWORK_INFO[fw]["supports"]:
        mod = _load_guard(fw, "jailbreak")
        await log_manager.log("Input Guard", "processing", f"[{fw}] Checking Jailbreak...")
        is_safe, details = mod.jailbreak_guard.check(request.message)
        if not is_safe:
            await log_manager.log("Input Guard", "error", f"[{fw}] Jailbreak Blocked: {details}")
            return ChatResponse(response="ข้อความละเมิดนโยบายความปลอดภัย",
                                blocked=True, violation_type="Jailbreak", framework_used=fw)

    # === 3. Profanity & Toxicity (regex — fast) ===
    if toggles.toxicity and "toxicity" in FRAMEWORK_INFO[fw]["supports"]:
        mod = _load_guard(fw, "toxicity")
        await log_manager.log("Input Guard", "processing", f"[{fw}] Checking Toxicity...")
        is_safe, details = mod.toxicity_guard.check(request.message)
        if not is_safe:
            await log_manager.log("Input Guard", "error", f"[{fw}] Toxicity Blocked: {details}")
            return ChatResponse(response="ข้อความมีเนื้อหาที่ไม่เหมาะสม",
                                blocked=True, violation_type="Toxicity", framework_used=fw)

    # === 4. Off-Topic (LLM — slower, catch-all) ===
    if toggles.off_topic and "off_topic" in FRAMEWORK_INFO[fw]["supports"]:
        mod = _load_guard(fw, "off_topic")
        await log_manager.log("Input Guard", "processing", f"[{fw}] Checking Off-Topic...")
        is_safe, details = mod.off_topic_guard.check(request.message, request.model)
        if not is_safe:
            await log_manager.log("Input Guard", "error", f"[{fw}] Off-Topic Blocked: {details}")
            return ChatResponse(response="ฉันสามารถตอบคำถามเกี่ยวกับการรถไฟแห่งประเทศไทยเท่านั้น",
                                blocked=True, violation_type="Off-Topic", framework_used=fw)

    return None


async def run_output_guards(response_text: str, request: ChatRequest) -> Optional[ChatResponse]:
    fw = request.framework
    if fw == "none":
        return None

    # --- Llama Guard: same S1-S14 check on output ---
    if fw == "llama_guard":
        toggles = request.llama_guard
        enabled = [k for k in ["S1","S2","S3","S4","S5","S6","S7","S8","S9","S10","S11","S12","S13"] if getattr(toggles, k)]
        if enabled:
            from backend.guards.llama_guard.checker_llamaguard import llama_guard_checker
            await log_manager.log("Output Guard", "processing", f"[Llama Guard 3] Checking output ({len(enabled)} categories)...")
            is_safe, details = llama_guard_checker.check(response_text, enabled, role="Agent")
            if not is_safe:
                await log_manager.log("Output Guard", "error", f"[Llama Guard 3] Blocked: {details}")
                return ChatResponse(response="คำตอบถูกกรองเนื่องจากมีเนื้อหาไม่เหมาะสม",
                                    blocked=True, violation_type="Llama Guard", framework_used=fw)
        return None

    # --- Guardrails AI / NeMo: Output Guards (3) ---
    # 1. Hallucination, 2. Toxicity, 3. Competitor
    toggles: GuardToggle = getattr(request, fw, GuardToggle())

    # Special handling for NeMo Pure Framework
    # Call NeMo ONCE and check all output guards on the single response
    if fw == "nemo":
        from backend.guards.nemo.nemo_engine import check_all_guards

        # Build list of enabled output guards
        enabled_output = []
        if toggles.hallucination: enabled_output.append("hallucination")
        if toggles.toxicity: enabled_output.append("toxicity")
        if toggles.competitor: enabled_output.append("competitor")

        if enabled_output:
            await log_manager.log("Output Guard", "processing", f"[NeMo] Checking {', '.join(g.upper() for g in enabled_output)}...")
            is_safe, details, violation = await check_all_guards(response_text, enabled_output)
            if not is_safe:
                if violation == "nemo_unavailable":
                    await log_manager.log("Output Guard", "error", f"[NeMo] Unavailable: {details}")
                    return ChatResponse(
                        response="ระบบ NeMo Guardrails ยังไม่พร้อมใช้งาน (โปรดติดตั้ง/activate environment ที่มี `nemoguardrails`)",
                        blocked=True,
                        violation_type="NeMoUnavailable",
                        framework_used=fw,
                    )
                if violation == "nemo_error":
                    await log_manager.log("Output Guard", "error", f"[NeMo] Error: {details}")
                    return ChatResponse(
                        response="ระบบ NeMo Guardrails ทำงานผิดพลาดชั่วคราว จึงระงับคำตอบนี้เพื่อความปลอดภัยค่ะ",
                        blocked=True,
                        violation_type="NeMoError",
                        framework_used=fw,
                    )
                response_map = {
                    "hallucination": ("คำตอบถูกกรองเนื่องจากอาจมีข้อมูลที่ไม่ถูกต้อง", "Hallucination"),
                    "toxicity": ("คำตอบถูกกรองเนื่องจากมีเนื้อหาไม่เหมาะสม", "Toxicity"),
                    "competitor": ("คำตอบถูกกรองเนื่องจากมีการกล่าวถึงคู่แข่ง", "Competitor"),
                }
                msg, vtype = response_map.get(violation, (details, violation))
                await log_manager.log("Output Guard", "error", f"[NeMo] {vtype} Blocked: {details}")
                return ChatResponse(response=msg, blocked=True, violation_type=vtype, framework_used=fw)
        return None


    # === GUARDRAILS AI HANDLING (Legacy/Hybrid) ===
    # === 1. Hallucination ===
    if toggles.hallucination and "hallucination" in FRAMEWORK_INFO[fw]["supports"]:
        mod = _load_guard(fw, "hallucination")
        await log_manager.log("Output Guard", "processing", f"[{fw}] Checking Hallucination...")
        if fw == "guardrails_ai":
            is_safe, details = mod.hallucination_guard.check(response_text, request.model)
        else:
            is_safe, details = mod.hallucination_guard.check(response_text)
        if not is_safe:
            await log_manager.log("Output Guard", "error", f"[{fw}] Hallucination Blocked: {details}")
            return ChatResponse(response="คำตอบถูกกรองเนื่องจากอาจมีข้อมูลที่ไม่ถูกต้อง",
                                blocked=True, violation_type="Hallucination", framework_used=fw)

    # === 2. Profanity & Toxicity ===
    if toggles.toxicity and "toxicity" in FRAMEWORK_INFO[fw]["supports"]:
        mod = _load_guard(fw, "toxicity")
        await log_manager.log("Output Guard", "processing", f"[{fw}] Checking Toxicity...")
        is_safe, details = mod.toxicity_guard.check(response_text)
        if not is_safe:
            await log_manager.log("Output Guard", "error", f"[{fw}] Toxicity Blocked: {details}")
            return ChatResponse(response="คำตอบถูกกรองเนื่องจากมีเนื้อหาไม่เหมาะสม",
                                blocked=True, violation_type="Toxicity", framework_used=fw)

    # === 3. Competitor Mention ===
    if toggles.competitor and "competitor" in FRAMEWORK_INFO[fw]["supports"]:
        mod = _load_guard(fw, "competitor")
        await log_manager.log("Output Guard", "processing", f"[{fw}] Checking Competitor...")
        is_safe, details = mod.competitor_guard.check(response_text)
        if not is_safe:
            await log_manager.log("Output Guard", "error", f"[{fw}] Competitor Blocked: {details}")
            return ChatResponse(response="คำตอบถูกกรองเนื่องจากมีการกล่าวถึงคู่แข่ง",
                                blocked=True, violation_type="Competitor", framework_used=fw)

    return None


# --- Main Chat Endpoint ---

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    fw = request.framework

    await log_manager.log("Input Guard", "start", f"Framework: {fw} — Checking input...")
    input_guard_start = time.time()
    blocked = await run_input_guards(request)
    input_guard_sec = time.time() - input_guard_start
    if blocked:
        total_sec = time.time() - start_time
        metrics = get_resource_metrics()
        await log_manager.log(
            "Input Guard", "success",
            f"Blocked (input) — รวม {total_sec:.2f}s",
            input_guard_sec,
            metrics=metrics,
            blocked=True,
        )
        cpu_info = f"CPU {metrics.get('cpu_percent', '—')}%"
        
        ram_info = f"RAM: {metrics.get('ram_used_gb', '—')}GB"
        if metrics.get('ram_percent'): ram_info += f" ({metrics['ram_percent']}%)"

        process_info = f"App: {metrics.get('process_mem_mb', '—')}MB"

        # Show GB if > 1GB, else MB
        gpu_mem = metrics.get('gpu_mem_gb')
        if gpu_mem and gpu_mem > 1.0:
            gpu_info = f"GPU: {gpu_mem}GB"
        else:
            gpu_info = f"GPU: {metrics.get('gpu_mem_mb', '—')}MB"
            
        if metrics.get('gpu_percent'): gpu_info += f" ({metrics['gpu_percent']}%)"

        await log_manager.log(
            "System", "complete",
            f"Blocked (Input) {total_sec:.2f}s\n"
            f"CPU: {metrics.get('cpu_percent', '—')}%\n"
            f"{ram_info}\n"
            f"{process_info}\n"
            f"{gpu_info}",
            total_sec,
            metrics=metrics,
            blocked=True,
        )
        return blocked
    await log_manager.log("Input Guard", "success", f"Input ผ่านทุกด่านแล้ว ({input_guard_sec:.2f}s)", input_guard_sec)

    llm_start = time.time()
    svc = get_service(request.backend)
    await log_manager.log("LLM", "processing", f"กำลังสร้างคำตอบจาก {request.model} ({request.backend})...")

    system_prompt = SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message},
    ]

    full_response = ""
    try:
        for chunk in svc.chat_stream(request.model, messages):
            full_response += chunk
    except Exception as e:
        await log_manager.log("LLM", "error", f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    llm_sec = time.time() - llm_start
    await log_manager.log("LLM", "success", f"สร้างคำตอบเสร็จสิ้น ({llm_sec:.2f}s)", llm_sec)

    await log_manager.log("Output Guard", "start", f"Framework: {fw} — Checking output...")
    output_guard_start = time.time()
    blocked = await run_output_guards(full_response, request)
    output_guard_sec = time.time() - output_guard_start
    if blocked:
        total_sec = time.time() - start_time
        metrics = get_resource_metrics()
        await log_manager.log(
            "Output Guard", "success",
            f"Blocked (output) — รวม {total_sec:.2f}s",
            output_guard_sec,
            metrics=metrics,
            blocked=True,
        )
        cpu_info = f"CPU {metrics.get('cpu_percent', '—')}%"
        
        ram_info = f"RAM: {metrics.get('ram_used_gb', '—')}GB"
        if metrics.get('ram_percent'): ram_info += f" ({metrics['ram_percent']}%)"

        process_info = f"App: {metrics.get('process_mem_mb', '—')}MB"

        # Show GB if > 1GB, else MB
        gpu_mem = metrics.get('gpu_mem_gb')
        if gpu_mem and gpu_mem > 1.0:
            gpu_info = f"GPU: {gpu_mem}GB"
        else:
            gpu_info = f"GPU: {metrics.get('gpu_mem_mb', '—')}MB"
            
        if metrics.get('gpu_percent'): gpu_info += f" ({metrics['gpu_percent']}%)"

        await log_manager.log(
            "System", "complete",
            f"Blocked (Output) {total_sec:.2f}s\n"
            f"CPU: {metrics.get('cpu_percent', '—')}%\n"
            f"{ram_info}\n"
            f"{process_info}\n"
            f"{gpu_info}",
            total_sec,
            metrics=metrics,
            blocked=True,
        )
        return blocked
    await log_manager.log("Output Guard", "success", f"Output ผ่านทุกด่านแล้ว ({output_guard_sec:.2f}s)", output_guard_sec)

    total_sec = time.time() - start_time
    metrics = get_resource_metrics()
    cpu_info = f"CPU {metrics.get('cpu_percent', '—')}%"
    
    ram_info = f"RAM: {metrics.get('ram_used_gb', '—')}GB"
    if metrics.get('ram_percent'): ram_info += f" ({metrics['ram_percent']}%)"

    process_info = f"App: {metrics.get('process_mem_mb', '—')}MB"

    # Show GB if > 1GB, else MB
    gpu_mem = metrics.get('gpu_mem_gb')
    if gpu_mem and gpu_mem > 1.0:
        gpu_info = f"GPU: {gpu_mem}GB"
    else:
        gpu_info = f"GPU: {metrics.get('gpu_mem_mb', '—')}MB"
        
    if metrics.get('gpu_percent'): gpu_info += f" ({metrics['gpu_percent']}%)"

    await log_manager.log(
        "System", "complete",
        f"Complete {total_sec:.2f}s\n"
        f"CPU: {metrics.get('cpu_percent', '—')}%\n"
        f"{ram_info}\n"
        f"{process_info}\n"
        f"{gpu_info}",
        total_sec,
        metrics=metrics,
        blocked=False,
    )

    return ChatResponse(response=full_response, framework_used=fw)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
