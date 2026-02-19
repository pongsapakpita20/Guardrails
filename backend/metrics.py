"""
Lightweight CPU/GPU metrics for logging. Optional psutil for CPU.
"""
from typing import Dict, Any

def get_resource_metrics() -> Dict[str, Any]:
    """Return current CPU and GPU usage for log. Safe to call; missing deps return N/A."""
    out: Dict[str, Any] = {"cpu_percent": None, "gpu_mem_mb": None, "gpu_name": None}

    print("[Metrics] Checking resources...")
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.05)
        out["cpu_percent"] = round(cpu, 1)
        print(f"[Metrics] CPU: {out['cpu_percent']}%")
    except ImportError:
        print("[Metrics] 'psutil' module not found. Install it to see CPU usage.")
    except Exception as e:
        print(f"[Metrics] CPU Error: {e}")

    try:
        import torch
        if torch.cuda.is_available():
            out["gpu_name"] = torch.cuda.get_device_name(0)
            # Memory allocated by current process (MB)
            out["gpu_mem_mb"] = round(torch.cuda.memory_allocated(0) / (1024 ** 2), 2)
            print(f"[Metrics] GPU: {out['gpu_mem_mb']}MB")
        else:
            print("[Metrics] CUDA not available.")
    except ImportError:
        print("[Metrics] 'torch' not found. GPU metrics unavailable.")
    except Exception as e:
        print(f"[Metrics] GPU Error: {e}")

    return out
