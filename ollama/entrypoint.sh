#!/bin/bash

# 0. Install curl (à¹€à¸žà¸£à¸²à¸° Image à¸‚à¸­à¸‡ Ollama à¹„à¸¡à¹ˆà¸¡à¸µ curl à¸¡à¸²à¹ƒà¸«à¹‰)
if ! command -v curl &> /dev/null; then
    echo "âš™ï¸ curl not found. Installing..."
    apt-get update && apt-get install -y curl
fi

# 1. Start Ollama in the background
/bin/ollama serve &

# Record Process ID
pid=$!

# 2. Wait for Ollama to start
sleep 5
echo " Waiting for Ollama API..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done
echo " Ollama is ready 👌 !"

# 3. Pull Model (Check if exists first)
MODEL_NAME="qwen3:1.7b"

if curl -s http://localhost:11434/api/tags | grep -q "$MODEL_NAME"; then
    echo "âœ… Model $MODEL_NAME already exists. Skipping pull."
else
    echo "ðŸ“¥ Pulling model $MODEL_NAME..."
    ollama pull $MODEL_NAME
    echo "âœ… Model pulled successfully!"
fi

# 4. Wait for the process to finish
wait $pid