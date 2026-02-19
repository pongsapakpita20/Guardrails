import subprocess
import os

try:
    # Query compute apps: name, pid, used_memory
    result = subprocess.run(
        ['nvidia-smi', '--query-compute-apps=process_name,pid,used_memory', '--format=csv,noheader,nounits'],
        capture_output=True, text=True
    )
    print("--- nvidia-smi output ---")
    print(result.stdout)
    print("-------------------------")
except FileNotFoundError:
    print("nvidia-smi not found")
except Exception as e:
    print(f"Error: {e}")
