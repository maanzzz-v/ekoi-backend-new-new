"""Resume processing and management service."""

import logging
import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import UploadFile

from models.schemas import ResumeMetadata, ExtractedInfo, ResumeMatch
from core.database import db_manager
from services.file_processor import FileProcessor, ResumeParser
from config.settings import settings

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for managing resume processing and search."""

    def __init__(self, vector_manager=None):
        self.collection_name = "resumes"
        self.vector_manager = vector_manager

    def set_vector_manager(self, vector_manager):
        """Set the vector manager dependency."""
        self.vector_manager = vector_manager

    async def cleanup_invalid_documents(self):
        """Clean up any documents with null _id values."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            # Delete any documents with null _id
            result = await collection.delete_many({"_id": None})
            if result.deleted_count > 0:
                logger.info(
                    f"Cleaned up {result.deleted_count} documents with null _id"
                )
        except Exception as e:
            logger.error(f"Error cleaning up invalid documents: {e}")

    async def process_uploaded_files(self, files: List[UploadFile]) -> Dict[str, Any]:
        """Process multiple uploaded resume files."""
        results = {
            "processed_files": [],
            "failed_files": [],
            "total_files": len(files),
            "success_count": 0,
            "error_count": 0,
        }

        for file in files:
            try:
                # Validate file
                if not self._validate_file(file):
                    results["failed_files"].append(
                        {
                            "filename": file.filename,
                            "error": "Invalid file type or size",
                        }
                    )
                    results["error_count"] += 1
                    continue

                # Process individual file
                file_result = await self._process_single_file(file)
                results["processed_files"].append(file_result)
                results["success_count"] += 1

            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                results["failed_files"].append(
                    {"filename": file.filename, "error": str(e)}
                )
                results["error_count"] += 1

        return results

    async def _process_single_file(self, file: UploadFile) -> Dict[str, Any]:
        """Process a single resume file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file.filename.split('.')[-1]}"
        ) as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)

        try:
            # Extract text from file
            file_type = file.filename.split(".")[-1].lower()
            extracted_text = FileProcessor.extract_text_from_file(temp_path, file_type)

            # Parse resume information
            parsed_info = ResumeParser.parse_resume_text(extracted_text)

            # Create metadata document
            metadata = ResumeMetadata(
                file_name=file.filename,
                file_type=file_type,
                file_size=len(content),
                extracted_text=extracted_text,
                parsed_info=parsed_info,
            )

            # Store in MongoDB
            collection = db_manager.get_collection(self.collection_name)
            # The model's dict() method will automatically exclude None _id values
            metadata_dict = metadata.dict(by_alias=True)

            result = await collection.insert_one(metadata_dict)
            metadata.id = str(result.inserted_id)

            # Process for vector storage
            # Create metadata dict with the new ID for vector storage
            vector_metadata = metadata.dict(by_alias=True)
            vector_metadata["_id"] = str(result.inserted_id)
            vector_ids = await self._store_in_vector_db(extracted_text, vector_metadata)

            # Update metadata with vector IDs
            await collection.update_one(
                {"_id": result.inserted_id},
                {
                    "$set": {
                        "vector_ids": vector_ids,
                        "processed": True,
                        "processing_timestamp": datetime.utcnow(),
                    }
                },
            )

            return {
                "filename": file.filename,
                "document_id": str(result.inserted_id),
                "vector_ids": vector_ids,
                "extracted_info": parsed_info,
                "status": "success",
            }

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def _store_in_vector_db(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[str]:
        """Store resume text in vector database."""
        # Chunk the text for better retrieval
        chunks = ResumeParser.chunk_text(text)

        # Prepare metadata for each chunk
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                **metadata,
                "chunk_index": i,
                "chunk_text": chunk,
                "total_chunks": len(chunks),
            }
            chunk_metadata.append(chunk_meta)

        # Store in vector database
        if not self.vector_manager:
            logger.error("Vector manager is not initialized")
            return []

        logger.info(f"Storing {len(chunks)} chunks in vector database")
        vector_ids = await self.vector_manager.store_vectors(chunks, chunk_metadata)
        logger.info(f"Stored vectors with IDs: {vector_ids}")

        return vector_ids

    def _validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file."""
        if not file.filename:
            return False

        # Check file type
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in settings.allowed_file_types_list:
            return False

        # Check file size (this is approximate since we haven't read the content yet)
        if hasattr(file, "size") and file.size:
            max_size = settings.max_file_size_mb * 1024 * 1024
            if file.size > max_size:
                return False

        return True

    async def search_resumes(
        self, query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[ResumeMatch]:
        """Search for resumes matching the query."""
        logger.info(f"Searching for resumes with query: '{query}', top_k: {top_k}")

        if not self.vector_manager:
            logger.error("Vector manager is not initialized for search")
            return []

        # Search in vector database
        vector_results = await self.vector_manager.search_similar(
            query, top_k * 2, filters
        )

        logger.info(f"Vector search returned {len(vector_results)} results")

        # Get unique document IDs (since we have chunks)
        document_ids = set()
        doc_scores = {}
        doc_metadata = {}

        for vector_id, score, metadata in vector_results:
            doc_id = metadata.get("_id") or metadata.get("id")
            if doc_id and doc_id not in document_ids:
                document_ids.add(doc_id)
                doc_scores[doc_id] = score
                doc_metadata[doc_id] = metadata
            elif doc_id and score > doc_scores.get(doc_id, 0):
                # Update with better score
                doc_scores[doc_id] = score

        # Get full resume metadata from MongoDB
        matches = []
        collection = db_manager.get_collection(self.collection_name)

        for doc_id in list(document_ids)[:top_k]:
            try:
                # Convert string ID back to ObjectId if needed
                if isinstance(doc_id, str):
                    from bson import ObjectId

                    if ObjectId.is_valid(doc_id):
                        doc_id = ObjectId(doc_id)

                resume_doc = await collection.find_one({"_id": doc_id})
                if resume_doc:
                    # Extract relevant information
                    extracted_info = None
                    if resume_doc.get("parsed_info"):
                        extracted_info = ExtractedInfo(**resume_doc["parsed_info"])

                    match = ResumeMatch(
                        id=str(resume_doc["_id"]),
                        file_name=resume_doc["file_name"],
                        score=doc_scores[str(doc_id)],
                        extracted_info=extracted_info,
                        relevant_text=self._get_relevant_text(
                            resume_doc.get("extracted_text", ""), query
                        ),
                    )
                    matches.append(match)

            except Exception as e:
                logger.error(f"Error retrieving resume {doc_id}: {e}")
                continue

        # Sort by score
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches

    def _get_relevant_text(
        self, full_text: str, query: str, max_length: int = 300
    ) -> str:
        """Extract relevant portion of text based on query."""
        if not full_text:
            return ""

        query_words = query.lower().split()
        sentences = full_text.split(".")

        # Find sentences containing query words
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in query_words):
                relevant_sentences.append(sentence.strip())

        # Join relevant sentences up to max_length
        relevant_text = ". ".join(relevant_sentences)
        if len(relevant_text) > max_length:
            relevant_text = relevant_text[:max_length] + "..."

        return relevant_text or full_text[:max_length] + "..."

    async def get_resume_by_id(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """Get resume details by ID."""
        try:
            from bson import ObjectId

            if ObjectId.is_valid(resume_id):
                collection = db_manager.get_collection(self.collection_name)
                resume_doc = await collection.find_one({"_id": ObjectId(resume_id)})
                if resume_doc:
                    resume_doc["_id"] = str(resume_doc["_id"])
                    return resume_doc
        except Exception as e:
            logger.error(f"Error retrieving resume {resume_id}: {e}")

        return None

    async def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume and its vectors."""
        try:
            from bson import ObjectId

            if not ObjectId.is_valid(resume_id):
                return False

            collection = db_manager.get_collection(self.collection_name)

            # Get resume document
            resume_doc = await collection.find_one({"_id": ObjectId(resume_id)})
            if not resume_doc:
                return False

            # Delete vectors
            vector_ids = resume_doc.get("vector_ids", [])
            if vector_ids:
                await self.vector_manager.delete_vectors(vector_ids)

            # Delete from MongoDB
            result = await collection.delete_one({"_id": ObjectId(resume_id)})

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting resume {resume_id}: {e}")
            return False

    async def get_all_resumes(
        self, skip: int = 0, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all resumes with pagination."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            cursor = (
                collection.find().skip(skip).limit(limit).sort("upload_timestamp", -1)
            )

            resumes = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                resumes.append(doc)

            return resumes

        except Exception as e:
            logger.error(f"Error retrieving resumes: {e}")
            return []


# Global resume service instance
resume_service = ResumeService()
