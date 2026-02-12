from typing import List, Dict, Type
from .base import BaseLLMService
from .ollama import OllamaService

class LLMFactory:
    _providers = {
        "ollama": OllamaService,
        # "gpustack": GPUStackService,  <-- อนาคตเพิ่มตรงนี้
    }
    
    _instances = {}

    @classmethod
    def get_service(cls, provider_id: str) -> BaseLLMService:
        provider_id = provider_id.lower()
        
        if provider_id in cls._instances:
            return cls._instances[provider_id]
        
        service_class = cls._providers.get(provider_id)
        if not service_class:
            raise ValueError(f"Unknown Provider: {provider_id}")
            
        instance = service_class()
        cls._instances[provider_id] = instance
        return instance

    @classmethod
    def get_providers(cls) -> List[Dict[str, str]]:
        return [
            {"id": "ollama", "name": "Local Ollama"},
            # {"id": "gpustack", "name": "GPU Stack"},
        ]