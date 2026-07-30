import os
import requests
from typing import List

class EmbeddingClient:
    """Client for generating text embeddings."""
    
    def __init__(self):
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.hf_model = os.getenv("HF_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.local_endpoint = os.getenv("LOCAL_EMBEDDING_ENDPOINT")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        
        # Try local endpoint first
        if self.local_endpoint:
            try:
                return self._embed_local(texts)
            except Exception as e:
                print(f"Local embedding failed: {e}")
        
        # Fall back to Hugging Face
        if self.hf_api_key:
            try:
                return self._embed_huggingface(texts)
            except Exception as e:
                print(f"Hugging Face embedding failed: {e}")
        
        # Return empty vectors if all fail
        print("Warning: No embedding service available, returning zero vectors")
        return [[0.0] * 384 for _ in texts]  # MiniLM-L6-v2 outputs 384 dimensions
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Use local embedding endpoint (e.g., Ollama)."""
        response = requests.post(
            self.local_endpoint,
            json={"texts": texts},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embeddings"]
    
    def _embed_huggingface(self, texts: List[str]) -> List[List[float]]:
        """Use Hugging Face Inference API."""
        API_URL = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        headers = {"Authorization": f"Bearer {self.hf_api_key}"}
        
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": texts},
            timeout=30
        )
        response.raise_for_status()
        
        # Handle different response formats
        result = response.json()
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "embeddings" in result:
            return result["embeddings"]
        else:
            raise ValueError(f"Unexpected response format: {result}")

# Singleton instance
_client = None

def get_embed_client() -> EmbeddingClient:
    """Get or create embedding client singleton."""
    global _client
    if _client is None:
        _client = EmbeddingClient()
    return _client
