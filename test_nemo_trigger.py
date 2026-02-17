import requests, json
url = "http://localhost:8000/chat"
payload = {
    "message": "มีรถไฟไปหาดใหญ่ไหม",
    "model": "scb10x/typhoon2.5-qwen3-4b",
    "framework": "nemo",
    "backend": "ollama",
    "nemo": {"pii": True, "off_topic": True, "jailbreak": True,
             "competitor": True, "toxicity": True, "hallucination": True}
}
print("Sending...")
try:
    r = requests.post(url, json=payload, timeout=120)
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
