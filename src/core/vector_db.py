"""Vector database management with Pinecone and FAISS."""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from config.settings import settings
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not available. Vector operations will use FAISS only.")

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available.")


class VectorManager:
    """Vector database manager with Pinecone and FAISS support."""

    def __init__(self):
        self.pinecone_client = None
        self.pinecone_index = None
        self.faiss_index = None
        self.id_to_metadata = {}  # For FAISS metadata storage
        self.vector_counter = 0

    async def initialize(self) -> None:
        """Initialize vector database connections and embedding model."""
        try:
            # Initialize LLM service first
            logger.info("Initializing LLM service...")
            await llm_service.initialize()

            # Initialize Pinecone if available
            if PINECONE_AVAILABLE:
                await self._initialize_pinecone()

            # Initialize FAISS as fallback
            if FAISS_AVAILABLE:
                self._initialize_faiss()

            logger.info("Vector manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize vector manager: {e}")
            raise

    async def _initialize_pinecone(self) -> None:
        """Initialize Pinecone connection."""
        try:
            self.pinecone_client = Pinecone(api_key=settings.pinecone_api_key)

            # Check if index exists, create if not
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [index.name for index in existing_indexes]

            if settings.pinecone_index_name not in index_names:
                logger.info(f"Creating Pinecone index: {settings.pinecone_index_name}")
                self.pinecone_client.create_index(
                    name=settings.pinecone_index_name,
                    dimension=llm_service.get_dimension(),
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws", region=settings.pinecone_environment
                    ),
                )

            self.pinecone_index = self.pinecone_client.Index(
                settings.pinecone_index_name
            )
            logger.info("Pinecone initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            # Continue without Pinecone
            self.pinecone_client = None
            self.pinecone_index = None

    def _initialize_faiss(self) -> None:
        """Initialize FAISS index."""
        try:
            # Create FAISS index for cosine similarity
            self.faiss_index = faiss.IndexFlatIP(llm_service.get_dimension())
            logger.info("FAISS index initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            self.faiss_index = None

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        return await llm_service.embed_text(text)

    async def store_vectors(
        self, texts: List[str], metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """Store text embeddings in vector database."""
        logger.info(f"Storing {len(texts)} vectors")

        if len(texts) != len(metadata):
            raise ValueError("Texts and metadata must have same length")

        try:
            # Generate embeddings using LLM service
            logger.info("Generating embeddings...")
            embeddings = await llm_service.embed_texts(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")

            vector_ids = []

            # Store in Pinecone if available
            if self.pinecone_index:
                logger.info("Storing in Pinecone...")
                vector_ids = await self._store_in_pinecone(embeddings, metadata)
                logger.info(f"Pinecone storage result: {vector_ids}")

            # Store in FAISS as backup/alternative
            if self.faiss_index:
                logger.info("Storing in FAISS...")
                faiss_ids = self._store_in_faiss(embeddings, metadata)
                logger.info(f"FAISS storage result: {faiss_ids}")
                if not vector_ids:  # Use FAISS IDs if Pinecone failed
                    vector_ids = faiss_ids

            if not vector_ids:
                logger.warning("No vector IDs returned from storage")
            else:
                logger.info(f"Successfully stored {len(vector_ids)} vectors")

            return vector_ids

        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
            raise

    def _sanitize_metadata_for_pinecone(
        self, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sanitize metadata for Pinecone storage (convert unsupported types)."""
        sanitized = {}

        for key, value in metadata.items():
            if value is None:
                # Skip None values entirely as Pinecone doesn't accept null
                continue
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                # Convert list to string representation for Pinecone
                sanitized[key] = str(value)
            elif isinstance(value, dict):
                # Convert dict to string representation for Pinecone
                sanitized[key] = str(value)
            elif hasattr(value, "isoformat"):  # datetime objects
                sanitized[key] = value.isoformat()
            else:
                # Convert other types to string
                sanitized[key] = str(value)

        return sanitized

    async def _store_in_pinecone(
        self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """Store embeddings in Pinecone."""
        try:
            vectors = []
            vector_ids = []

            for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
                vector_id = f"resume_{self.vector_counter}_{i}"
                # Sanitize metadata for Pinecone compatibility
                sanitized_meta = self._sanitize_metadata_for_pinecone(meta)
                logger.debug(f"Original metadata keys: {list(meta.keys())}")
                logger.debug(f"Sanitized metadata keys: {list(sanitized_meta.keys())}")
                vectors.append(
                    {"id": vector_id, "values": embedding, "metadata": sanitized_meta}
                )
                vector_ids.append(vector_id)

            self.pinecone_index.upsert(vectors=vectors)
            self.vector_counter += len(vectors)

            logger.info(f"Stored {len(vectors)} vectors in Pinecone")
            return vector_ids

        except Exception as e:
            logger.error(f"Failed to store vectors in Pinecone: {e}")
            return []

    def _store_in_faiss(
        self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """Store embeddings in FAISS."""
        try:
            embeddings_array = np.array(embeddings, dtype=np.float32)

            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_array)

            # Get starting index
            start_idx = self.faiss_index.ntotal

            # Add vectors to FAISS
            self.faiss_index.add(embeddings_array)

            # Store metadata separately
            vector_ids = []
            for i, meta in enumerate(metadata):
                vector_id = f"faiss_{start_idx + i}"
                self.id_to_metadata[vector_id] = meta
                vector_ids.append(vector_id)

            logger.info(f"Stored {len(embeddings)} vectors in FAISS")
            return vector_ids

        except Exception as e:
            logger.error(f"Failed to store vectors in FAISS: {e}")
            return []

    async def search_similar(
        self, query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors."""
        logger.info(
            f"Searching for similar vectors with query: '{query[:100]}...', top_k: {top_k}"
        )

        try:
            query_embedding = await self.embed_text(query)
            logger.info(
                f"Generated query embedding with dimension: {len(query_embedding)}"
            )

            results = []

            # Search in Pinecone if available
            if self.pinecone_index:
                logger.info("Searching in Pinecone...")
                pinecone_results = await self._search_pinecone(
                    query_embedding, top_k, filters
                )
                logger.info(f"Pinecone returned {len(pinecone_results)} results")
                results.extend(pinecone_results)

            # Search in FAISS if no Pinecone results or as fallback
            if not results and self.faiss_index:
                logger.info("Searching in FAISS...")
                faiss_results = self._search_faiss(query_embedding, top_k)
                logger.info(f"FAISS returned {len(faiss_results)} results")
                results.extend(faiss_results)

            # Sort by score and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            final_results = results[:top_k]
            logger.info(f"Returning {len(final_results)} final results")

            return final_results

        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            return []

    async def _search_pinecone(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search in Pinecone index."""
        try:
            response = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filters,
            )

            results = []
            for match in response["matches"]:
                results.append((match["id"], match["score"], match.get("metadata", {})))

            return results

        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            return []

    def _search_faiss(
        self, query_embedding: List[float], top_k: int
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search in FAISS index."""
        try:
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)

            scores, indices = self.faiss_index.search(query_array, top_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:  # Valid result
                    vector_id = f"faiss_{idx}"
                    metadata = self.id_to_metadata.get(vector_id, {})
                    results.append((vector_id, float(score), metadata))

            return results

        except Exception as e:
            logger.error(f"Failed to search FAISS: {e}")
            return []

    async def delete_vectors(self, vector_ids: List[str]) -> bool:
        """Delete vectors from the database."""
        success = True

        # Delete from Pinecone
        if self.pinecone_index:
            try:
                pinecone_ids = [
                    vid for vid in vector_ids if not vid.startswith("faiss_")
                ]
                if pinecone_ids:
                    self.pinecone_index.delete(ids=pinecone_ids)
            except Exception as e:
                logger.error(f"Failed to delete from Pinecone: {e}")
                success = False

        # Delete from FAISS metadata (FAISS doesn't support deletion)
        for vector_id in vector_ids:
            if vector_id in self.id_to_metadata:
                del self.id_to_metadata[vector_id]

        return success


# Global vector manager instance
vector_manager = VectorManager()
