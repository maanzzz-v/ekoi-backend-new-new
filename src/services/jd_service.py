"""Job Description processing and management service."""

import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import UploadFile

from models.schemas import JobDescriptionMetadata, ResumeMatch
from core.database import db_manager
from services.file_processor import FileProcessor, ResumeParser
from services.resume_service import resume_service
from config.settings import settings

logger = logging.getLogger(__name__)


class JDService:
    """Service for managing job description processing and searching."""

    def __init__(self, vector_manager=None):
        self.collection_name = "job_descriptions"
        self.vector_manager = vector_manager

    def set_vector_manager(self, vector_manager):
        """Set the vector manager dependency."""
        self.vector_manager = vector_manager

    async def process_jd_file(self, file: UploadFile, session_id: str) -> Dict[str, Any]:
        """Process a single job description file and store it."""
        
        # Validate file
        if not self._validate_file(file):
            raise ValueError("Invalid file type or size")

        # Create JD directory if it doesn't exist
        jd_dir = os.path.join(os.getcwd(), "job_descriptions")
        os.makedirs(jd_dir, exist_ok=True)
        
        # Create unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split(".")[-1].lower()
        safe_filename = f"{timestamp}_{session_id}_{file.filename}"
        permanent_path = os.path.join(jd_dir, safe_filename)
        
        # Save file permanently
        content = await file.read()
        with open(permanent_path, "wb") as f:
            f.write(content)

        try:
            # Extract text from file
            extracted_text = FileProcessor.extract_text_from_file(permanent_path, file_extension)

            # Parse JD information (similar to resume parsing but for JD)
            parsed_info = self._parse_jd_text(extracted_text)

            # Create metadata document
            metadata = JobDescriptionMetadata(
                file_name=file.filename,
                file_type=file_extension,
                file_size=len(content),
                extracted_text=extracted_text,
                parsed_info=parsed_info,
                file_path=permanent_path,
                session_id=session_id
            )

            # Store in MongoDB
            collection = db_manager.get_collection(self.collection_name)
            metadata_dict = metadata.dict(by_alias=True)
            result = await collection.insert_one(metadata_dict)
            
            # Update processing status
            await collection.update_one(
                {"_id": result.inserted_id},
                {
                    "$set": {
                        "processed": True,
                        "processing_timestamp": datetime.utcnow(),
                    }
                },
            )

            return {
                "jd_id": str(result.inserted_id),
                "filename": file.filename,
                "session_id": session_id,
                "extracted_text": extracted_text,
                "parsed_info": parsed_info,
                "file_path": permanent_path,
                "status": "success"
            }

        except Exception as e:
            # If processing fails, remove the saved file
            if os.path.exists(permanent_path):
                os.unlink(permanent_path)
            raise e

    def _parse_jd_text(self, text: str) -> Dict[str, Any]:
        """Parse job description text to extract key information."""
        
        parsed_info = {
            "job_title": None,
            "company": None,
            "location": None,
            "experience_required": None,
            "skills_required": [],
            "responsibilities": [],
            "qualifications": [],
            "salary_range": None,
            "employment_type": None
        }
        
        lines = text.split('\n')
        text_lower = text.lower()
        
        # Extract job title (usually in the first few lines)
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 100:  # Likely a title
                if any(keyword in line.lower() for keyword in 
                      ['developer', 'engineer', 'analyst', 'manager', 'scientist', 'architect']):
                    parsed_info["job_title"] = line
                    break
        
        # Extract skills (common technical terms)
        skill_patterns = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
            'django', 'flask', 'spring', 'aws', 'azure', 'docker', 'kubernetes',
            'machine learning', 'data science', 'sql', 'mongodb', 'postgresql',
            'git', 'ci/cd', 'devops', 'microservices', 'rest api', 'graphql'
        ]
        
        found_skills = []
        for skill in skill_patterns:
            if skill in text_lower:
                found_skills.append(skill)
        
        parsed_info["skills_required"] = found_skills
        
        # Extract experience requirements
        import re
        exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)'
        exp_matches = re.findall(exp_pattern, text_lower)
        if exp_matches:
            parsed_info["experience_required"] = f"{exp_matches[0]}+ years"
        
        # Extract employment type
        if any(term in text_lower for term in ['full-time', 'full time']):
            parsed_info["employment_type"] = "Full-time"
        elif any(term in text_lower for term in ['part-time', 'part time']):
            parsed_info["employment_type"] = "Part-time"
        elif 'contract' in text_lower:
            parsed_info["employment_type"] = "Contract"
        elif 'remote' in text_lower:
            parsed_info["employment_type"] = "Remote"
        
        return parsed_info

    async def search_resumes_by_jd(
        self, session_id: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for resumes matching the uploaded JD in the session."""
        
        # Get the JD for this session
        jd_doc = await self.get_jd_by_session(session_id)
        if not jd_doc:
            raise ValueError(f"No job description found for session {session_id}")
        
        jd_text = jd_doc.get("extracted_text", "")
        if not jd_text:
            raise ValueError("Job description text is empty")
        
        logger.info(f"Searching resumes using JD from session {session_id}")
        
        # Use the existing resume service search with JD text as query
        matches = await resume_service.search_resumes(
            query=jd_text, 
            top_k=top_k, 
            filters=filters
        )
        
        # Store search results in session history
        await self._store_search_results_in_session(session_id, matches, jd_doc)
        
        return {
            "session_id": session_id,
            "jd_id": str(jd_doc["_id"]),
            "jd_text": jd_text,
            "matches": matches,
            "total_results": len(matches)
        }

    async def get_jd_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get job description by session ID."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            jd_doc = await collection.find_one({"session_id": session_id})
            return jd_doc
        except Exception as e:
            logger.error(f"Error retrieving JD for session {session_id}: {e}")
            return None

    async def _store_search_results_in_session(
        self, session_id: str, matches: List[ResumeMatch], jd_doc: Dict[str, Any]
    ):
        """Store search results as JSON in session context."""
        try:
            # Import here to avoid circular imports
            from services.session_service import session_service
            
            # Convert matches to serializable format
            search_results = {
                "jd_search_results": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "jd_id": str(jd_doc["_id"]),
                    "jd_filename": jd_doc.get("file_name", ""),
                    "jd_text": jd_doc.get("extracted_text", ""),
                    "total_matches": len(matches),
                    "matches": [
                        {
                            "id": match.id,
                            "file_name": match.file_name,
                            "score": match.score,
                            "extracted_info": match.extracted_info.dict() if match.extracted_info else None,
                            "relevant_text": match.relevant_text
                        }
                        for match in matches
                    ]
                }
            }
            
            # Update session context
            await session_service.update_session_context(
                session_id=session_id,
                context=search_results
            )
            
            logger.info(f"Stored {len(matches)} search results in session {session_id}")
            
        except Exception as e:
            logger.error(f"Error storing search results in session: {e}")

    def _validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded JD file."""
        if not file.filename:
            return False

        # Check file type (allow same types as resumes)
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in settings.allowed_file_types_list:
            return False

        # Check file size
        if hasattr(file, "size") and file.size:
            max_size = settings.max_file_size_mb * 1024 * 1024
            if file.size > max_size:
                return False

        return True

    async def get_session_search_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get stored search results from session context."""
        try:
            from services.session_service import session_service
            
            session = await session_service.get_session(session_id)
            if not session or not session.context:
                return None
            
            return session.context.get("jd_search_results")
            
        except Exception as e:
            logger.error(f"Error getting session search results: {e}")
            return None

    async def delete_jd(self, session_id: str) -> bool:
        """Delete job description associated with session."""
        try:
            collection = db_manager.get_collection(self.collection_name)
            
            # Get JD document first
            jd_doc = await collection.find_one({"session_id": session_id})
            if not jd_doc:
                return False
            
            # Delete file from disk
            file_path = jd_doc.get("file_path")
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
            
            # Delete from database
            result = await collection.delete_one({"session_id": session_id})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting JD for session {session_id}: {e}")
            return False


# Global JD service instance
jd_service = JDService()
