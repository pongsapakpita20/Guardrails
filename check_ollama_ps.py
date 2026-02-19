import requests
import json

try:
    response = requests.get('http://localhost:11434/api/ps')
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Connection error: {e}")
