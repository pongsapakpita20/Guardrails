import os
import requests
import json
import sys
import time

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = "scb10x/typhoon2.5-qwen3-4b"

def check_ollama_running():
    try:
        response = requests.get(f"{OLLAMA_HOST}/")
        if response.status_code == 200:
            print(f"✅ Ollama is running at {OLLAMA_HOST}")
            return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to Ollama at {OLLAMA_HOST}")
        print("Please make sure Ollama is installed and running.")
        return False
    return False

def check_model_exists():
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                if model["name"].startswith(MODEL_NAME):
                    print(f"✅ Model '{MODEL_NAME}' is already available.")
                    return True
        print(f"⚠️ Model '{MODEL_NAME}' not found locally.")
        return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def pull_model():
    print(f"⬇️ Pulling model '{MODEL_NAME}'... This may take a while.")
    try:
        # Stream the pull response
        response = requests.post(f"{OLLAMA_HOST}/api/pull", json={"name": MODEL_NAME}, stream=True)
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                status = data.get("status")
                completed = data.get("completed")
                total = data.get("total")
                
                if completed and total:
                    percent = (completed / total) * 100
                    print(f"\rDownloading: {percent:.1f}% - {status}", end="")
                else:
                    print(f"\r{status}", end="")
        print("\n✅ Model pulled successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Error pulling model: {e}")
        return False

def run_inference(prompt):
    print(f"\n🚀 Running inference with prompt: '{prompt}'")
    try:
        data = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True # Stream for better UX
        }
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json=data, stream=True)
        
        print("\n--- Response ---")
        for line in response.iter_lines():
            if line:
                json_part = json.loads(line)
                chunk = json_part.get("response", "")
                print(chunk, end="", flush=True)
                if json_part.get("done"):
                    print("\n\n✅ Done!")
    except Exception as e:
        print(f"\n❌ Error running inference: {e}")

if __name__ == "__main__":
    print("--- Guardrails Local Runner ---\n")
    
    if not check_ollama_running():
        sys.exit(1)
        
    if not check_model_exists():
        if not pull_model():
            sys.exit(1)
            

    
    # Simple loop for interaction
    while True:
        try:
            user_input = input("\nParsed Prompt (or 'exit'): ")
            if user_input.lower() in ["exit", "quit"]:
                break
            run_inference(user_input)
        except KeyboardInterrupt:
            break