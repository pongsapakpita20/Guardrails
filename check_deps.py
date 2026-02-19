import psutil
import torch
import sys

print(f"Python: {sys.version}")
try:
    print(f"psutil: {psutil.__version__}")
    print(f"CPU: {psutil.cpu_percent(interval=0.1)}%")
except Exception as e:
    print(f"psutil error: {e}")

try:
    print(f"torch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Mem: {torch.cuda.memory_allocated(0)}")
except Exception as e:
    print(f"torch error: {e}")
