# ใช้ Python รุ่นเล็กแต่แรง
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*
    
# ลง Library ที่จำเป็น
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy โค้ดทั้งหมด
COPY . .

# สั่งรัน FastAPI
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# ✅ Install Guardrails Hub Validators (ถาวร)
# -----------------------------------------------------------------------------
ARG GUARDRAILS_TOKEN
RUN if [ -n "$GUARDRAILS_TOKEN" ]; then \
    pip install --force-reinstall "rich<14.0.0" && \
    guardrails configure --token $GUARDRAILS_TOKEN --disable-metrics --disable-remote-inferencing && \
    guardrails hub install hub://guardrails/detect_pii && \
    guardrails hub install hub://tryolabs/restricttotopic && \
    guardrails hub install hub://guardrails/detect_jailbreak && \
    guardrails hub install hub://bespokelabs/bespoke_minicheck && \
    guardrails hub install hub://guardrails/toxic_language && \
    guardrails hub install hub://guardrails/competitor_check; \
    else \
    echo "⚠️ GUARDRAILS_TOKEN not provided. Skipping Hub installation."; \
    fi