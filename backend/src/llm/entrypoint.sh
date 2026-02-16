#!/bin/bash

# 0. Install curl (เพราะ Image ของ Ollama ไม่มี curl มาให้)
if ! command -v curl &> /dev/null; then
    echo "curl not found. Installing..."
    apt-get update && apt-get install -y curl
fi

# 1. Start Ollama in the background
/bin/ollama serve &

# Record Process ID
pid=$!

# 2. Wait for Ollama to start
sleep 5
echo "⏳ Waiting for Ollama API..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done
echo "✅ Ollama is ready !"

# ---------------------------------------------------------
# 3.1 Pull Chat Model (Typhoon)
# ---------------------------------------------------------
CHAT_MODEL="scb10x/typhoon2.5-qwen3-4b"

if curl -s http://localhost:11434/api/tags | grep -q "$CHAT_MODEL"; then
    echo "Model $CHAT_MODEL already exists. Skipping pull."
else
    echo "⬇️ Pulling model $CHAT_MODEL..."
    ollama pull $CHAT_MODEL
    echo "✅ Model $CHAT_MODEL pulled successfully!"
fi

# ---------------------------------------------------------
# 3.2 Pull Guard Model (Llama Guard 3) <--- เพิ่มตรงนี้ครับ
# ---------------------------------------------------------
GUARD_MODEL="llama-guard3:8b"

if curl -s http://localhost:11434/api/tags | grep -q "$GUARD_MODEL"; then
    echo "Model $GUARD_MODEL already exists. Skipping pull."
else
    echo "⬇️ Pulling model $GUARD_MODEL..."
    ollama pull $GUARD_MODEL
    echo "✅ Model $GUARD_MODEL pulled successfully!"
fi

# 4. Wait for the process to finish
wait $pid