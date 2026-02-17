# 🚂 SRT Chatbot Guardrails

> ระบบ Guardrails สำหรับ Chatbot Call Center ของการรถไฟแห่งประเทศไทย (รฟท.)
> ตรวจจับและป้องกันข้อความที่ไม่เหมาะสมทั้ง Input และ Output ด้วย 3 Framework

---

## 📋 สารบัญ

- [สถาปัตยกรรมระบบ](#-สถาปัตยกรรมระบบ)
- [โมเดลที่ใช้](#-โมเดลที่ใช้)
- [Guardrail Frameworks](#-guardrail-frameworks)
- [ความต้องการของระบบ](#-ความต้องการของระบบ)
- [การติดตั้ง](#-การติดตั้ง)
- [การรันระบบ](#-การรันระบบ)
- [การประเมินผล (Evaluation)](#-การประเมินผล-evaluation)
- [โครงสร้างโปรเจกต์](#-โครงสร้างโปรเจกต์)

---

## 🏗 สถาปัตยกรรมระบบ

```
┌──────────────┐     ┌──────────────────────────────────────┐     ┌────────────────┐
│              │     │           Backend (FastAPI)           │     │                │
│   Frontend   │────▶│                                      │────▶│  Ollama /      │
│  React+Vite  │◀────│  Input Guards ─▶ LLM ─▶ Output Guards│◀────│  GPUStack      │
│              │     │                                      │     │                │
└──────────────┘     └──────────────────────────────────────┘     └────────────────┘
     :5173                     :8000                              :11434 / :80
```

- **Frontend** — React 19 + Vite พร้อม UI สำหรับ Chat, Settings, และ Log Panel (WebSocket)
- **Backend** — FastAPI พร้อมระบบ Guard แบบ Modular รองรับ 3 Framework
- **LLM Backend** — Ollama (local) หรือ GPUStack (remote/cluster)

---

## 🤖 โมเดลที่ใช้

### โมเดลหลัก (Chat Generation)

| โมเดล | รายละเอียด | ขนาด |
|---|---|---|
| **scb10x/typhoon2.5-qwen3-4b** | โมเดลภาษาไทย โดย SCB 10X, ค่าเริ่มต้นของระบบ | ~4B parameters |

> 💡 สามารถเลือกโมเดลอื่นได้จาก UI หรือตั้งค่าผ่าน Environment Variable `DEFAULT_MODEL`
> ระบบจะแสดงรายชื่อโมเดลที่มีอยู่ใน Ollama/GPUStack ของคุณ

### โมเดล Safety (Llama Guard)

| โมเดล | รายละเอียด |
|---|---|
| **llama-guard3** | Meta Llama Guard 3 8B สำหรับตรวจจับเนื้อหาอันตราย 13 หมวดหมู่ |

### การดาวน์โหลดโมเดลผ่าน Ollama

```bash
# โมเดลหลัก — Typhoon 2.5 (ภาษาไทย)
ollama pull scb10x/typhoon2.5-qwen3-4b

# โมเดล Safety — Llama Guard 3
ollama pull llama-guard3
```

> ⚠️ **หมายเหตุ**: โมเดลทั้งสองต้องการ **GPU ที่มี VRAM อย่างน้อย 8 GB** เพื่อประสิทธิภาพที่ดี

---

## 🛡 Guardrail Frameworks

ระบบรองรับ 3 Framework ที่เลือกใช้ได้จาก UI:

### 1. Guardrails AI

| Guard | ประเภท | หน้าที่ |
|---|---|---|
| PII | Input | ตรวจจับข้อมูลส่วนบุคคล (บัตรประชาชน, เบอร์โทร, อีเมล ฯลฯ) |
| Jailbreak | Input | ตรวจจับการพยายาม Bypass ระบบรักษาความปลอดภัย |
| Toxicity | Input/Output | ตรวจจับคำหยาบ/เนื้อหาไม่เหมาะสม |
| Off-Topic | Input | ตรวจจับคำถามที่ไม่เกี่ยวกับการรถไฟ (ใช้ LLM) |
| Hallucination | Output | ตรวจจับคำตอบที่อาจเป็นข้อมูลเท็จ (ใช้ LLM) |
| Competitor | Output | ตรวจจับการกล่าวถึงคู่แข่ง (สายการบิน, รถทัวร์ ฯลฯ) |

### 2. NeMo Guardrails

รองรับ Guard เดียวกัน 6 ประเภท แต่ใช้ NVIDIA NeMo Guardrails Framework

### 3. Llama Guard 3 8B

ใช้โมเดล Llama Guard 3 ตรวจสอบ 13 หมวดหมู่ความปลอดภัย:

| Code | หมวดหมู่ |
|---|---|
| S1 | Violent Crimes |
| S2 | Non-Violent Crimes |
| S3 | Sex Crimes |
| S4 | Child Exploitation |
| S5 | Defamation |
| S6 | Specialized Advice |
| S7 | Privacy |
| S8 | Intellectual Property |
| S9 | Indiscriminate Weapons |
| S10 | Hate |
| S11 | Self-Harm |
| S12 | Sexual Content |
| S13 | Elections |

---

## 💻 ความต้องการของระบบ

### ซอฟต์แวร์ที่จำเป็น

| ซอฟต์แวร์ | เวอร์ชัน | หมายเหตุ |
|---|---|---|
| Python | 3.10 | แนะนำผ่าน Conda |
| Node.js | 18+ | สำหรับ Frontend |
| Conda / Miniconda | Latest | จัดการ Environment |
| Ollama | Latest | สำหรับรัน LLM ในเครื่อง |
| Git | Latest | สำหรับ Clone โปรเจกต์ |

### ฮาร์ดแวร์ที่แนะนำ

| ส่วนประกอบ | ขั้นต่ำ | แนะนำ |
|---|---|---|
| GPU | NVIDIA (CUDA) VRAM 8 GB | VRAM 16 GB+ |
| RAM | 16 GB | 32 GB |
| พื้นที่ดิสก์ | 20 GB | 40 GB+ |

---

## 🔧 การติดตั้ง

### ขั้นตอนที่ 1 — Clone โปรเจกต์

```bash
git clone https://github.com/<your-org>/Guardrails.git
cd Guardrails
```

### ขั้นตอนที่ 2 — ติดตั้ง Ollama และดาวน์โหลดโมเดล

#### Windows

1. ดาวน์โหลด Ollama จาก [https://ollama.com/download](https://ollama.com/download) แล้วติดตั้ง
2. เปิด Terminal แล้วรัน:

```bash
ollama pull scb10x/typhoon2.5-qwen3-4b
ollama pull llama-guard3
```

#### macOS

```bash
# ติดตั้งผ่าน Homebrew
brew install ollama

# หรือดาวน์โหลดจาก https://ollama.com/download

# ดาวน์โหลดโมเดล
ollama pull scb10x/typhoon2.5-qwen3-4b
ollama pull llama-guard3
```

#### Linux

```bash
# ติดตั้ง Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# ดาวน์โหลดโมเดล
ollama pull scb10x/typhoon2.5-qwen3-4b
ollama pull llama-guard3
```

> ✅ ตรวจสอบว่า Ollama ทำงานอยู่: `ollama list` จะแสดงรายชื่อโมเดลที่ดาวน์โหลดแล้ว

### ขั้นตอนที่ 3 — ติดตั้ง Backend (Python)

```bash
# สร้าง Conda Environment จากไฟล์ environment.yml
conda env create -f environment.yml

# เปิดใช้งาน Environment
conda activate Guardrail
```

#### ติดตั้ง spaCy Model (จำเป็นสำหรับ PII Detection)

```bash
python -m spacy download en_core_web_lg
```

### ขั้นตอนที่ 4 — ติดตั้ง Frontend (Node.js)

```bash
cd frontend
npm install
cd ..
```

### ขั้นตอนที่ 5 — ตั้งค่า Environment Variables (ถ้าต้องการ)

สร้างไฟล์ `.env` ที่ Root ของโปรเจกต์ (ไม่จำเป็นถ้าใช้ค่าเริ่มต้น):

```env
# Ollama
OLLAMA_HOST=http://localhost:11434

# GPUStack (ถ้าใช้)
GPUSTACK_HOST=http://localhost:80
GPUSTACK_API_KEY=your-api-key

# โมเดลเริ่มต้น
DEFAULT_MODEL=scb10x/typhoon2.5-qwen3-4b

# Llama Guard Model
LLAMA_GUARD_MODEL=llama-guard3

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🚀 การรันระบบ

### 1. เริ่ม Ollama Server

```bash
ollama serve
```

> Ollama จะรันที่ `http://localhost:11434`

### 2. เริ่ม Backend

```bash
# ที่ Root ของโปรเจกต์
conda activate Guardrail
python -m backend.main
```

> Backend จะรันที่ `http://localhost:8000`
> API Docs จะอยู่ที่ `http://localhost:8000/docs`

### 3. เริ่ม Frontend

```bash
cd frontend
npm run dev
```

> Frontend จะรันที่ `http://localhost:5173`

### 4. เปิดใช้งาน

เปิดเบราว์เซอร์ไปที่ **http://localhost:5173** แล้วเริ่มใช้งาน:

1. เลือก **Backend** (Ollama หรือ GPUStack)
2. เลือก **Model** ที่ต้องการ
3. เลือก **Guardrail Framework** (None / Guardrails AI / NeMo / Llama Guard 3)
4. เปิด/ปิด Guard แต่ละตัวตามต้องการ
5. พิมพ์ข้อความใน Chat แล้วส่ง

---

## 📊 การประเมินผล (Evaluation)

ระบบมีชุดทดสอบ (`evaluation/dataset.json`) สำหรับวัดประสิทธิภาพ Guard แต่ละ Framework:

```bash
# ประเมิน Guardrails AI
python -m evaluation.evaluate --framework guardrails_ai --model typhoon2.5

# ประเมิน NeMo Guardrails
python -m evaluation.evaluate --framework nemo --model typhoon2.5

# ประเมิน Llama Guard 3
python -m evaluation.evaluate --framework llama_guard --model typhoon2.5
```

ผลลัพธ์จะแสดง Precision, Recall, F1-Score ของแต่ละ Guard และบันทึกเป็นไฟล์ `evaluation/results_<framework>.json`

---

## 📁 โครงสร้างโปรเจกต์

```
Guardrails/
├── backend/
│   ├── main.py                  # FastAPI — Endpoints & Guard Pipeline
│   ├── ollama_service.py        # Ollama & GPUStack Clients
│   ├── logger.py                # WebSocket Log Manager
│   ├── config/
│   │   └── settings.py          # System Prompt, Framework Config, ENV
│   └── guards/
│       ├── guardrails_ai/       # Guardrails AI Guards (6 ไฟล์)
│       │   ├── pii_guardai.py
│       │   ├── jailbreak_guardai.py
│       │   ├── toxicity_guardai.py
│       │   ├── off_topic_guardai.py
│       │   ├── hallucination_guardai.py
│       │   └── competitor_guardai.py
│       ├── nemo/                # NeMo Guardrails Guards (6 ไฟล์)
│       │   ├── pii_nemo.py
│       │   ├── jailbreak_nemo.py
│       │   ├── toxicity_nemo.py
│       │   ├── off_topic_nemo.py
│       │   ├── hallucination_nemo.py
│       │   └── competitor_nemo.py
│       └── llama_guard/         # Llama Guard 3 (S1-S13)
│           └── checker_llamaguard.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main App Component
│   │   ├── api.js               # API Client
│   │   └── components/
│   │       ├── ChatPanel.jsx    # Chat Interface
│   │       ├── SettingsPanel.jsx # Framework & Guard Settings
│   │       └── LogPanel.jsx     # Real-time Log Viewer
│   ├── package.json
│   └── vite.config.js
├── evaluation/
│   ├── dataset.json             # ชุดทดสอบ (Test Cases)
│   └── evaluate.py              # Evaluation Script
├── environment.yml              # Conda Environment
└── README.md
```

---

## 🔌 API Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| `GET` | `/health` | ตรวจสอบสถานะระบบและ GPU |
| `GET` | `/models` | ดึงรายชื่อโมเดลที่ใช้ได้ |
| `GET` | `/frameworks` | ข้อมูล Framework ที่รองรับ |
| `POST` | `/chat` | ส่งข้อความ Chat (ผ่าน Guard Pipeline) |
| `WS` | `/ws/logs` | WebSocket สำหรับ Real-time Logs |

---

## ❓ การแก้ปัญหาเบื้องต้น

| ปัญหา | วิธีแก้ |
|---|---|
| `ollama` command not found | ติดตั้ง Ollama ใหม่ แล้วเปิด Terminal ใหม่ |
| ไม่พบโมเดลใน UI | ตรวจสอบว่า Ollama Server ทำงานอยู่ (`ollama serve`) |
| Backend Error 500 | ตรวจสอบว่า Conda env `Guardrail` ถูก activate แล้ว |
| GPU ไม่ถูกตรวจพบ | ตรวจสอบ CUDA Driver และ `pytorch-cuda` version |
| Frontend ไม่เชื่อมต่อ Backend | ตรวจสอบว่า Backend รันที่ port 8000 |
