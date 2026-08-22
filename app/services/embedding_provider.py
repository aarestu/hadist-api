from abc import ABC, abstractmethod
from typing import List
import logging
from app.infrastructure.config import VectorSearchConfig

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract Base Class untuk Embedding Providers."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Menghasilkan list vector embedding dari list teks."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Menghasilkan vector embedding dari kueri pencarian."""
        pass


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """Provider embedding menggunakan SentenceTransformers (Lokal / Open-Source)."""

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "auto"):
        self.model_name = model_name
        self.device = device
        
        target_device = None
        if device != "auto":
            target_device = device
        else:
            try:
                import torch
                if torch.cuda.is_available():
                    target_device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    target_device = "mps"
            except ImportError:
                pass

        logger.info(f"Loading SentenceTransformer model: '{model_name}' on device: '{target_device or 'default (auto)'}'...")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device=target_device)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        import torch

        # Use inference mode to disable gradient calculation and save VRAM
        with torch.inference_mode():
            embeddings = self.model.encode(
                texts,
                show_progress_bar=False,
                normalize_embeddings=True,
                batch_size=len(texts),
            )
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        import torch
        with torch.inference_mode():
            embedding = self.model.encode(
                query, show_progress_bar=False, normalize_embeddings=True
            )
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return embedding.tolist()


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Provider embedding menggunakan OpenAI API."""

    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        if not api_key:
            raise ValueError("OpenAI API key required for OpenAIEmbeddingProvider")
        self.api_key = api_key
        self.model_name = model_name
        import httpx
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        url = "https://api.openai.com/v1/embeddings"
        payload = {
            "input": texts,
            "model": self.model_name
        }
        resp = self.client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()["data"]
        # Maintain order
        data_sorted = sorted(data, key=lambda x: x["index"])
        return [item["embedding"] for item in data_sorted]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]


def get_embedding_provider(config: VectorSearchConfig) -> BaseEmbeddingProvider:
    """Factory function untuk inisialisasi Embedding Provider berdasarkan konfigurasi."""
    provider_type = config.provider.lower()
    if provider_type in ["sentence-transformers", "local"]:
        return SentenceTransformerEmbeddingProvider(
            model_name=config.model_name,
            device=config.device,
        )
    elif provider_type == "openai":
        return OpenAIEmbeddingProvider(
            api_key=config.openai_api_key,
            model_name=config.openai_model
        )
    else:
        raise ValueError(f"Unsupported embedding provider type: {config.provider}")
