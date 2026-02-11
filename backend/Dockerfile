# ใช้ Python รุ่นเล็กแต่แรง
FROM python:3.10-slim

WORKDIR /app

# ลง Library ที่จำเป็น
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy โค้ดทั้งหมด
COPY . .

# สั่งรัน FastAPI
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]