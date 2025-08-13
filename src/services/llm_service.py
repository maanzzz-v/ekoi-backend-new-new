"""LLM service supporting multiple providers (OpenAI, Gemini, Ollama, vLLM)."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio

from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings."""
        pass


class SentenceTransformersProvider(EmbeddingProvider):
    """Sentence Transformers provider for local embeddings."""

    def __init__(self):
        self.model = None
        self.dimension = settings.vector_dimension

    async def initialize(self):
        """Initialize the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np

            self.model = SentenceTransformer(settings.embedding_model)
            # Get actual dimension from model
            test_embedding = self.model.encode("test", convert_to_tensor=False)
            self.dimension = len(test_embedding)

            logger.info(
                f"SentenceTransformers model loaded: {settings.embedding_model}"
            )
            logger.info(f"Embedding dimension: {self.dimension}")

        except ImportError as e:
            logger.error(f"SentenceTransformers not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformers: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if not self.model:
            raise RuntimeError("Model not initialized")

        import numpy as np

        embedding = self.model.encode(text, convert_to_tensor=False)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            raise RuntimeError("Model not initialized")

        import numpy as np

        embeddings = self.model.encode(texts, convert_to_tensor=False)
        # Normalize for cosine similarity
        normalized_embeddings = []
        for embedding in embeddings:
            normalized = embedding / np.linalg.norm(embedding)
            normalized_embeddings.append(normalized.tolist())

        return normalized_embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class OpenAIProvider(EmbeddingProvider):
    """OpenAI embeddings provider."""

    def __init__(self):
        self.client = None
        self.dimension = 1536  # Default for text-embedding-ada-002

    async def initialize(self):
        """Initialize OpenAI client."""
        try:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not provided")

            from openai import AsyncOpenAI

            # Initialize with timeout settings
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=60.0,  # 60 second timeout
                max_retries=3   # Retry failed requests
            )

            # Set dimension based on model
            if "ada-002" in settings.openai_model:
                self.dimension = 1536
            elif "text-embedding-3-small" in settings.openai_model:
                self.dimension = 1536
            elif "text-embedding-3-large" in settings.openai_model:
                self.dimension = 3072

            logger.info(
                f"OpenAI client initialized with model: {settings.openai_model}"
            )

        except ImportError as e:
            logger.error(f"OpenAI library not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text with retry logic."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=settings.openai_model, 
                    input=text,
                    timeout=30.0  # 30 second timeout per request
                )
                return response.data[0].embedding

            except Exception as e:
                logger.warning(f"OpenAI embedding attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"OpenAI embedding error after {max_retries} attempts: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with batch processing and retry logic."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Process in smaller batches to avoid timeouts
        batch_size = 50
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    response = await self.client.embeddings.create(
                        model=settings.openai_model, 
                        input=batch,
                        timeout=60.0  # 60 second timeout for batches
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    break  # Success, break retry loop
                    
                except Exception as e:
                    logger.warning(f"OpenAI batch embedding attempt {attempt + 1} failed for batch {i//batch_size + 1}: {e}")
                    if attempt == max_retries - 1:
                        # If all retries failed, try processing individually
                        logger.warning(f"Batch processing failed, trying individual processing for batch {i//batch_size + 1}")
                        try:
                            for text in batch:
                                individual_embedding = await self.embed_text(text)
                                all_embeddings.append(individual_embedding)
                            break
                        except Exception as individual_error:
                            logger.error(f"Individual processing also failed: {individual_error}")
                            raise e  # Raise original batch error
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return all_embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class GeminiProvider(EmbeddingProvider):
    """Google Gemini embeddings provider."""

    def __init__(self):
        self.model = None
        self.dimension = 768  # Default for embedding-001

    async def initialize(self):
        """Initialize Gemini client."""
        try:
            if not settings.gemini_api_key:
                raise ValueError("Gemini API key not provided")

            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)

            self.model = genai.GenerativeModel("gemini-pro")

            logger.info(
                f"Gemini client initialized with model: {settings.gemini_model}"
            )

        except ImportError as e:
            logger.error(f"Google GenerativeAI library not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        try:
            import google.generativeai as genai

            result = genai.embed_content(
                model=settings.gemini_model,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]

        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class OllamaProvider(EmbeddingProvider):
    """Ollama embeddings provider for local models."""

    def __init__(self):
        self.client = None
        self.dimension = 768  # Default, will be determined during initialization

    async def initialize(self):
        """Initialize Ollama client."""
        try:
            import ollama

            self.client = ollama.AsyncClient(host=settings.ollama_base_url)

            # Test connection and get model info
            try:
                test_response = await self.client.embeddings(
                    model=settings.ollama_model, prompt="test"
                )
                self.dimension = len(test_response["embedding"])
                logger.info(
                    f"Ollama client initialized with model: {settings.ollama_model}"
                )
                logger.info(f"Embedding dimension: {self.dimension}")

            except Exception as e:
                logger.warning(f"Could not test Ollama model: {e}")
                # Use default dimension
                pass

        except ImportError as e:
            logger.error(f"Ollama library not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if not self.client:
            raise RuntimeError("Ollama client not initialized")

        try:
            response = await self.client.embeddings(
                model=settings.ollama_model, prompt=text
            )
            return response["embedding"]

        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class VLLMProvider(EmbeddingProvider):
    """vLLM embeddings provider for self-hosted models."""

    def __init__(self):
        self.base_url = settings.vllm_base_url
        self.dimension = 1024  # Default, will be determined during initialization

    async def initialize(self):
        """Initialize vLLM client."""
        try:
            if not self.base_url:
                raise ValueError("vLLM base URL not provided")

            # Test connection
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code != 200:
                    raise ValueError(f"vLLM server not healthy: {response.status_code}")

            logger.info(f"vLLM client initialized with model: {settings.vllm_model}")

        except ImportError as e:
            logger.error(f"httpx library not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize vLLM: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        return (await self.embed_texts([text]))[0]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            import httpx

            headers = {"Content-Type": "application/json"}
            if settings.vllm_api_key:
                headers["Authorization"] = f"Bearer {settings.vllm_api_key}"

            payload = {"input": texts, "model": settings.vllm_model}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=60.0,
                )
                response.raise_for_status()

                result = response.json()
                embeddings = [item["embedding"] for item in result["data"]]

                # Update dimension if this is our first call
                if embeddings and self.dimension != len(embeddings[0]):
                    self.dimension = len(embeddings[0])
                    logger.info(f"Updated vLLM embedding dimension: {self.dimension}")

                return embeddings

        except Exception as e:
            logger.error(f"vLLM embedding error: {e}")
            raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class LLMService:
    """Service for managing different LLM providers."""

    def __init__(self):
        self.provider: Optional[EmbeddingProvider] = None
        self.provider_name = settings.llm_provider.lower()

    async def initialize(self):
        """Initialize the selected LLM provider."""
        try:
            if self.provider_name == "openai":
                self.provider = OpenAIProvider()
            elif self.provider_name == "gemini":
                self.provider = GeminiProvider()
            elif self.provider_name == "ollama":
                self.provider = OllamaProvider()
            elif self.provider_name == "vllm":
                self.provider = VLLMProvider()
            elif self.provider_name == "sentence-transformers":
                self.provider = SentenceTransformersProvider()
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider_name}")

            await self.provider.initialize()
            logger.info(f"LLM service initialized with provider: {self.provider_name}")

            # Update settings with actual dimension
            settings.vector_dimension = self.provider.get_dimension()

        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self.provider:
            raise RuntimeError("LLM service not initialized")

        return await self.provider.embed_text(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.provider:
            raise RuntimeError("LLM service not initialized")

        return await self.provider.embed_texts(texts)

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if not self.provider:
            return settings.vector_dimension

        return self.provider.get_dimension()

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        return {
            "provider": self.provider_name,
            "dimension": self.get_dimension(),
            "model": self._get_current_model(),
        }

    def _get_current_model(self) -> str:
        """Get the current model name based on provider."""
        if self.provider_name == "openai":
            return settings.openai_model
        elif self.provider_name == "gemini":
            return settings.gemini_model
        elif self.provider_name == "ollama":
            return settings.ollama_model
        elif self.provider_name == "vllm":
            return settings.vllm_model
        elif self.provider_name == "sentence-transformers":
            return settings.embedding_model
        else:
            return "unknown"


# Global LLM service instance
llm_service = LLMService()
