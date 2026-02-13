# ใช้ Python รุ่นเล็กแต่แรง
FROM python:3.10-slim

WORKDIR /app

# 1. ลง System Dependencies ให้ครบก่อน
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy เฉพาะ requirements มาลงก่อน (เพื่อใช้ Docker Cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


ARG GUARDRAILS_TOKEN

# 3. เตรียม Environment (ลง Library หนักๆ รอไว้เลย จะได้ไม่ไปค้างตอน install hub)
# restricttotopic มักจะใช้ transformers, torch
RUN pip install --no-cache-dir transformers torch numpy scikit-learn

# 4. แยกการลง Validator ทีละตัว (ถ้าตัวไหนพัง จะได้ไม่พาเพื่อนซวย)
# และถ้าตัวไหนโหลดเสร็จแล้ว ครั้งหน้ามันจะไม่โหลดใหม่ครับ
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then \
    pip install --force-reinstall "rich<14.0.0" && \
    guardrails configure --token $GUARDRAILS_TOKEN --disable-metrics --disable-remote-inferencing; \
    fi

# ตัวเบาๆ ลงก่อน
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then guardrails hub install hub://guardrails/detect_pii; fi
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then guardrails hub install hub://guardrails/detect_jailbreak; fi
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then guardrails hub install hub://guardrails/toxic_language; fi
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then guardrails hub install hub://guardrails/competitor_check; fi

# ⚠️ ตัวปัญหา (restricttotopic) แยกมาเดี่ยวๆ
# ถ้ายังค้าง ให้ Comment บรรทัดนี้ทิ้งไปก่อนเพื่อทดสอบระบบ
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then \
    echo "Installing Heavy Validator..." && \
    guardrails hub install hub://tryolabs/restricttotopic || echo "Failed to install restricttotopic, skipping..."; \
    fi

# ตัว Bespoke (อาจจะหนักเหมือนกัน)
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then guardrails hub install hub://bespokelabs/bespoke_minicheck || echo "Skipping minicheck"; fi

# -----------------------------------------------------------------------------

# 5. Copy โค้ดทั้งหมด (ไว้หลังสุด! แก้โค้ดแล้วจะได้ไม่ต้องโหลด Model ใหม่)
COPY . .

# สั่งรัน FastAPI
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]