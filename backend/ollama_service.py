from typing import List, Dict, Any, Generator, AsyncGenerator
from starlette.concurrency import run_in_threadpool
import os
import json
import requests
import torch
from backend.config.settings import OLLAMA_HOST, GPUSTACK_HOST, GPUSTACK_API_KEY


class OllamaService:
    """Ollama backend — uses Ollama REST API."""

    async def check_gpu(self) -> Dict[str, Any]:
        """Check if PyTorch can see the GPU."""
        # Non-blocking check for local torch
        cuda_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_available else "None"
        return {
            "cuda_available": cuda_available,
            "gpu_name": gpu_name,
            "torch_version": torch.__version__
        }

    async def list_models(self) -> List[str]:
        """List available models from Ollama."""
        def _fetch():
            try:
                response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2.0)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return [m["name"] for m in models]
                return []
            except Exception as e:
                print(f"[Ollama] Error listing models: {e}")
                return []
        return await run_in_threadpool(_fetch)

    # Use sync generator for now as FastAPI handles threadpool offloading effectively for iterators
    def chat_stream(self, model: str, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {"model": model, "messages": messages, "stream": True}

        try:
            with requests.post(url, json=payload, stream=True, timeout=60) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        body = json.loads(line)
                        if "message" in body:
                            yield body["message"].get("content", "")
                        if body.get("done", False):
                            break
        except Exception as e:
            yield f"Error calling Ollama: {str(e)}"


class GPUStackService:
    """GPUStack backend — uses OpenAI-compatible API."""

    def __init__(self):
        self.base_url = GPUSTACK_HOST.rstrip("/")
        self.api_key = GPUSTACK_API_KEY

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def check_gpu(self) -> Dict[str, Any]:
        def _check():
            try:
                headers = self._headers()
                resp = requests.get(f"{self.base_url}/v1/gpus", headers=headers, timeout=1.5)
                if resp.status_code == 200:
                    gpus = resp.json().get("data", resp.json().get("items", []))
                    if gpus:
                        gpu_info = gpus[0]
                        return {
                            "cuda_available": True,
                            "gpu_name": gpu_info.get("name", gpu_info.get("gpu_id", "GPUStack GPU")),
                            "gpu_count": len(gpus),
                            "backend": "gpustack",
                        }
            except Exception:
                pass
            
            try:
                resp = requests.get(f"{self.base_url}/v1/models", headers=self._headers(), timeout=1.5)
                if resp.status_code == 200:
                    return {"cuda_available": True, "gpu_name": "GPUStack (connected)", "backend": "gpustack"}
            except Exception:
                pass

            return {"cuda_available": False, "gpu_name": "GPUStack (offline)", "backend": "gpustack"}

        return await run_in_threadpool(_check)

    async def list_models(self) -> List[str]:
        def _fetch():
            try:
                headers = self._headers()
                resp = requests.get(f"{self.base_url}/v1/models", headers=headers, timeout=1.5)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    return [m["id"] for m in data]
                return []
            except Exception as e:
                print(f"[GPUStack] Error listing models: {e}")
                return []
        return await run_in_threadpool(_fetch)

    def chat_stream(self, model: str, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        url = f"{self.base_url}/v1/chat/completions"
        headers = self._headers()
        payload = {"model": model, "messages": messages, "stream": True}

        try:
            with requests.post(url, json=payload, headers=headers, stream=True, timeout=60) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"Error calling GPUStack: {str(e)}"


# --- Singleton instances ---
ollama_service = OllamaService()
gpustack_service = GPUStackService()

def get_service(backend: str = "ollama"):
    if backend == "gpustack":
        return gpustack_service
    return ollama_service
