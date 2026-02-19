"""
Lightweight CPU/GPU metrics for logging. Optional psutil for CPU.
"""
from typing import Dict, Any

def get_resource_metrics() -> Dict[str, Any]:
    """Return current CPU and GPU usage for log. Safe to call; missing deps return N/A."""
    out: Dict[str, Any] = {
        "cpu_percent": None, "cpu_cores": None, "cpu_threads": None,
        "ram_percent": None, "ram_used_mb": None, "ram_used_gb": None, "ram_total_gb": None,
        "process_mem_mb": None, "process_mem_gb": None, "process_threads": None,
        "gpu_mem_mb": None, "gpu_mem_gb": None, "gpu_percent": None, "gpu_name": None
    }

    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        out["cpu_percent"] = round(cpu, 1)
        out["cpu_cores"] = psutil.cpu_count(logical=False)
        out["cpu_threads"] = psutil.cpu_count(logical=True)
        
        # System RAM
        mem = psutil.virtual_memory()
        out["ram_percent"] = mem.percent
        out["ram_used_mb"] = round(mem.used / (1024 ** 2), 2)
        out["ram_used_gb"] = round(mem.used / (1024 ** 3), 2)
        out["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)

        # Process Memory (App Usage)
        process = psutil.Process()
        mem_info = process.memory_info()
        out["process_mem_mb"] = round(mem_info.rss / (1024 ** 2), 2)
        out["process_mem_gb"] = round(mem_info.rss / (1024 ** 3), 2)
        out["process_threads"] = process.num_threads()
    except ImportError:
        print("[Metrics] 'psutil' module not found.")
    except Exception as e:
        print(f"[Metrics] CPU/RAM Error: {e}")

    # GPU: Get specific usage from Ollama API
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/ps", timeout=0.2)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("models", [])
            total_vram_bytes = sum(m.get("size_vram", 0) for m in models)
            
            # MB
            out["gpu_mem_mb"] = round(total_vram_bytes / (1024 ** 2), 2)
            # GB
            out["gpu_mem_gb"] = round(total_vram_bytes / (1024 ** 3), 2)
            
            # % Usage (Model VRAM / Total System VRAM)
            total_system_vram = 0
            try:
                import torch
                if torch.cuda.is_available():
                    out["gpu_name"] = torch.cuda.get_device_name(0)
                    # free, total = torch.cuda.mem_get_info(0)
                    _, total_system_vram = torch.cuda.mem_get_info(0)
            except:
                out["gpu_name"] = "Ollama GPU"
            
            if total_system_vram > 0:
                out["gpu_percent"] = round((total_vram_bytes / total_system_vram) * 100, 1)
            else:
                out["gpu_percent"] = 0.0

    except Exception as e:
        # print(f"[Metrics] Ollama GPU Check Error: {e}") 
        pass

    return out
