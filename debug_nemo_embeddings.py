import asyncio
from nemoguardrails import RailsConfig, LLMRails
from nemoguardrails.embeddings.basic import OpenAIEmbeddingModel
import numpy as np

async def test_embeddings():
    config = RailsConfig.from_path("backend/config/nemo")
    rails = LLMRails(config)
    
    # Manually check similarity using the same embedding model
    text = "รถไฟไปหาดใหญ่ไหม"
    
    # Get embedding for input
    # Note: Accessing internal embedding model for debug
    if not rails.embedding_search_provider:
        print("No embedding provider found!")
        return

    print(f"Testing input: '{text}'")
    
    # Search for canonical forms
    results = await rails.embedding_search_provider.search(text)
    
    print("\n--- Top Matches ---")
    for res in results:
        print(f"Canonical: {res.text}")
        print(f"Score: {res.score}")
        print(f"Metadata: {res.metadata}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_embeddings())
