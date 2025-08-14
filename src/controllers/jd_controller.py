"""Job Description upload and processing API endpoints."""

import time
import os
import zipfile
import tempfile
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from models.schemas import (
    JDUploadResponse, 
    JDSearchRequest, 
    JDSearchResponse,
    SessionJDFollowUpRequest
)
from services.jd_service import jd_service
from services.session_service import session_service
from services.llm_service import llm_service
from exceptions.custom_exceptions import create_http_exception
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/jd", tags=["job-description"])


@router.post("/upload", response_model=JDUploadResponse)
async def upload_job_description(
    session_id: str,
    file: UploadFile = File(..., description="Job description file (PDF or TXT)")
):
    """
    Upload a job description file and associate it with a chat session.
    
    This endpoint processes the JD file and stores it for later use in resume searching.
    """
    try:
        # Verify session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        logger.info(f"Processing JD upload for session {session_id}: {file.filename}")
        
        # Process the JD file
        result = await jd_service.process_jd_file(file, session_id)
        
        # Add message to session about JD upload
        await session_service.add_message(
            session_id=session_id,
            message_type="system",
            content=f"Job description '{file.filename}' uploaded successfully. You can now search for matching candidates or ask follow-up questions.",
            metadata={
                "jd_upload": True,
                "jd_id": result["jd_id"],
                "filename": file.filename
            }
        )
        
        response = JDUploadResponse(
            message=f"Job description '{file.filename}' uploaded and processed successfully",
            job_description_id=result["jd_id"],
            file_name=file.filename,
            session_id=session_id,
            extracted_text=result["extracted_text"][:500] + "..." if len(result["extracted_text"]) > 500 else result["extracted_text"],
            success=True
        )
        
        logger.info(f"JD upload completed for session {session_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in JD upload: {e}")
        raise create_http_exception(400, str(e))
    except Exception as e:
        logger.error(f"Error uploading JD: {e}")
        raise create_http_exception(500, "Error occurred during job description upload")


@router.post("/search", response_model=JDSearchResponse)
async def search_resumes_by_jd(request: JDSearchRequest):
    """
    Search for resumes matching the uploaded job description.
    
    This performs similarity search between the JD and all resumes in the database,
    then stores the results in the session history as JSON.
    """
    try:
        start_time = time.time()
        
        # Verify session exists
        session = await session_service.get_session(request.session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        logger.info(f"Starting JD-based resume search for session {request.session_id}")
        
        # Perform the search
        search_result = await jd_service.search_resumes_by_jd(
            session_id=request.session_id,
            top_k=request.top_k,
            filters=request.filters
        )
        
        processing_time = time.time() - start_time
        
        # Add search message to session
        await session_service.add_message(
            session_id=request.session_id,
            message_type="assistant",
            content=f"Found {search_result['total_results']} candidates matching your job description. Results have been analyzed and stored. You can now ask follow-up questions about these candidates.",
            metadata={
                "jd_search": True,
                "total_results": search_result['total_results'],
                "processing_time": processing_time,
                "jd_id": search_result['jd_id']
            }
        )
        
        response = JDSearchResponse(
            session_id=request.session_id,
            job_description_id=search_result['jd_id'],
            job_description_text=search_result['jd_text'][:300] + "..." if len(search_result['jd_text']) > 300 else search_result['jd_text'],
            matches=search_result['matches'],
            total_results=search_result['total_results'],
            processing_time=processing_time,
            search_results_stored=True,
            success=True
        )
        
        logger.info(f"JD search completed: {search_result['total_results']} matches in {processing_time:.2f}s")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in JD search: {e}")
        raise create_http_exception(400, str(e))
    except Exception as e:
        logger.error(f"Error in JD search: {e}")
        raise create_http_exception(500, "Error occurred during job description search")


@router.post("/followup")
async def jd_followup_question(request: SessionJDFollowUpRequest):
    """
    Ask follow-up questions about the JD search results stored in session.
    
    This uses the stored JSON search results and LLM to provide intelligent answers
    about the shortlisted candidates.
    """
    try:
        # Verify session exists
        session = await session_service.get_session(request.session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        logger.info(f"Processing JD follow-up question for session {request.session_id}: {request.question}")
        
        # Get stored search results from session
        search_results = await jd_service.get_session_search_results(request.session_id)
        if not search_results:
            raise create_http_exception(400, "No job description search results found in this session. Please upload a JD and search first.")
        
        # Add user question to session
        await session_service.add_message(
            session_id=request.session_id,
            message_type="user",
            content=request.question
        )
        
        # Generate LLM response using stored search results
        llm_response = await _generate_jd_followup_response(
            question=request.question,
            search_results=search_results,
            session=session
        )
        
        # Add LLM response to session
        await session_service.add_message(
            session_id=request.session_id,
            message_type="assistant",
            content=llm_response,
            metadata={
                "jd_followup": True,
                "question": request.question,
                "used_stored_results": True,
                "candidates_analyzed": len(search_results.get("matches", []))
            }
        )
        
        return {
            "session_id": request.session_id,
            "question": request.question,
            "answer": llm_response,
            "candidates_analyzed": len(search_results.get("matches", [])),
            "jd_filename": search_results.get("jd_filename", ""),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in JD follow-up: {e}")
        raise create_http_exception(500, "Error occurred while processing follow-up question")


@router.get("/session/{session_id}/results")
async def get_jd_search_results(session_id: str):
    """
    Get the stored JD search results for a session.
    
    Returns the JSON data stored in session context from the previous search.
    """
    try:
        # Verify session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        # Get stored search results
        search_results = await jd_service.get_session_search_results(session_id)
        if not search_results:
            raise create_http_exception(404, "No JD search results found for this session")
        
        return {
            "session_id": session_id,
            "search_results": search_results,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting JD search results: {e}")
        raise create_http_exception(500, "Error occurred while retrieving search results")


@router.delete("/session/{session_id}")
async def delete_session_jd(session_id: str):
    """
    Delete the job description associated with a session.
    
    This removes both the file and database records.
    """
    try:
        success = await jd_service.delete_jd(session_id)
        
        if not success:
            raise create_http_exception(404, "No job description found for this session")
        
        return {
            "session_id": session_id,
            "message": "Job description deleted successfully",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting JD: {e}")
        raise create_http_exception(500, "Error occurred while deleting job description")


@router.get("/session/{session_id}/download")
async def download_shortlisted_resumes(
    session_id: str,
    top_n: int = 10,
    format: str = "zip"
):
    """
    Download shortlisted resumes from JD search results.
    
    Args:
        session_id: Session ID containing the JD search results
        top_n: Number of top candidates to download (default: 10)
        format: Download format - 'zip' for ZIP file (default: zip)
    
    Returns:
        ZIP file containing the top N shortlisted resume files
    """
    try:
        # Verify session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        # Get stored search results
        search_results = await jd_service.get_session_search_results(session_id)
        if not search_results:
            raise create_http_exception(404, "No JD search results found for this session. Please upload a JD and search first.")
        
        matches = search_results.get("matches", [])
        if not matches:
            raise create_http_exception(404, "No candidate matches found in search results")
        
        # Limit to top N candidates
        top_matches = matches[:top_n]
        
        logger.info(f"Preparing download of top {len(top_matches)} candidates for session {session_id}")
        
        # Create temporary directory for ZIP file
        temp_dir = tempfile.mkdtemp()
        zip_filename = f"shortlisted_candidates_{session_id[:8]}_{len(top_matches)}_resumes.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # Create ZIP file with resume files
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add a summary text file
            summary_content = _create_summary_report(search_results, top_matches)
            zipf.writestr("SHORTLIST_SUMMARY.txt", summary_content)
            
            # Get resume files from database and add to ZIP
            resume_files_added = 0
            for i, match in enumerate(top_matches, 1):
                try:
                    resume_file_path = await _get_resume_file_path(match["id"])
                    if resume_file_path and os.path.exists(resume_file_path):
                        # Create a meaningful filename for the ZIP
                        candidate_name = match.get("extracted_info", {}).get("name", "Unknown") if match.get("extracted_info") else "Unknown"
                        original_filename = match.get("file_name", f"resume_{i}")
                        score = match.get("score", 0)
                        
                        # Clean candidate name for filename
                        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).strip()
                        safe_name = safe_name.replace(' ', '_')
                        
                        # Create descriptive filename
                        file_extension = os.path.splitext(original_filename)[1]
                        zip_filename_inner = f"Rank_{i:02d}_Score_{score:.2f}_{safe_name}_{original_filename}"
                        
                        # Add file to ZIP
                        zipf.write(resume_file_path, zip_filename_inner)
                        resume_files_added += 1
                        
                        logger.debug(f"Added resume {i}: {zip_filename_inner}")
                        
                    else:
                        logger.warning(f"Resume file not found for candidate {i}: {match.get('file_name', 'Unknown')}")
                        
                except Exception as e:
                    logger.error(f"Error adding resume {i} to ZIP: {e}")
                    continue
        
        if resume_files_added == 0:
            # Clean up and return error
            os.unlink(zip_path)
            os.rmdir(temp_dir)
            raise create_http_exception(404, "No resume files could be found for download")
        
        logger.info(f"Created ZIP file with {resume_files_added} resumes: {zip_path}")
        
        # Return the ZIP file for download
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type='application/zip',
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "X-Total-Candidates": str(len(top_matches)),
                "X-Files-Included": str(resume_files_added)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating download package: {e}")
        raise create_http_exception(500, "Error occurred while preparing download")


# Helper function for generating LLM responses
async def _generate_jd_followup_response(
    question: str, 
    search_results: dict, 
    session
) -> str:
    """Generate intelligent follow-up response using LLM and stored search results."""
    
    # Prepare context for LLM
    jd_text = search_results.get("jd_text", "")
    matches = search_results.get("matches", [])
    total_matches = search_results.get("total_matches", 0)
    
    # Build candidate summary for LLM context
    candidates_summary = []
    for i, match in enumerate(matches[:10], 1):  # Limit to top 10 for LLM context
        candidate_info = {
            "rank": i,
            "filename": match.get("file_name", ""),
            "score": match.get("score", 0),
            "name": match.get("extracted_info", {}).get("name", "Unknown") if match.get("extracted_info") else "Unknown",
            "skills": match.get("extracted_info", {}).get("skills", []) if match.get("extracted_info") else [],
            "experience": len(match.get("extracted_info", {}).get("experience", [])) if match.get("extracted_info") else 0,
            "relevant_text": match.get("relevant_text", "")[:200]  # Truncate for context
        }
        candidates_summary.append(candidate_info)
    
    # Create LLM prompt
    llm_prompt = f"""
You are an AI recruitment assistant analyzing candidate search results based on a job description.

JOB DESCRIPTION:
{jd_text[:1000]}...

SEARCH RESULTS SUMMARY:
- Total candidates found: {total_matches}
- Top {len(candidates_summary)} candidates analyzed

CANDIDATE DETAILS:
{_format_candidates_for_llm(candidates_summary)}

USER QUESTION: {question}

Please provide a detailed, professional answer based on the search results. Focus on:
1. Direct answer to the user's question
2. Specific candidate details when relevant
3. Data-driven insights from the search results
4. Actionable recommendations

Keep the response structured and professional, suitable for recruitment decision-making.
"""
    
    try:
        # Use LLM service to generate response
        llm_response = await llm_service.generate_response(
            prompt=llm_prompt,
            max_tokens=800,
            temperature=0.3  # Lower temperature for more factual responses
        )
        
        return llm_response
        
    except Exception as e:
        logger.error(f"Error generating LLM response: {e}")
        # Fallback response
        return f"I found {total_matches} candidates matching your job description. However, I'm having trouble processing your specific question right now. Please try rephrasing your question or ask about specific aspects like candidate skills, experience levels, or top matches."


def _format_candidates_for_llm(candidates_summary: list) -> str:
    """Format candidate data for LLM context."""
    formatted = []
    
    for candidate in candidates_summary:
        skills_text = ", ".join(candidate["skills"][:5]) if candidate["skills"] else "No skills listed"
        
        candidate_text = f"""
Candidate {candidate['rank']}: {candidate['name']}
- File: {candidate['filename']}
- Match Score: {candidate['score']:.2f}
- Skills: {skills_text}
- Experience: {candidate['experience']} roles listed
- Relevant Text: {candidate['relevant_text']}
"""
        formatted.append(candidate_text.strip())
    
    return "\n\n".join(formatted)


async def _get_resume_file_path(resume_id: str) -> Optional[str]:
    """Get the file path for a resume from the database."""
    try:
        from core.database import db_manager
        from bson import ObjectId
        
        collection = db_manager.get_collection("resumes")
        
        # Try to convert to ObjectId if it's a valid ObjectId string
        try:
            object_id = ObjectId(resume_id)
            resume_doc = await collection.find_one({"_id": object_id})
        except:
            # If not a valid ObjectId, search by string ID
            resume_doc = await collection.find_one({"_id": resume_id})
        
        if resume_doc:
            return resume_doc.get("file_path")
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting resume file path for {resume_id}: {e}")
        return None


def _create_summary_report(search_results: dict, top_matches: list) -> str:
    """Create a summary report for the shortlisted candidates."""
    
    jd_info = {
        "filename": search_results.get("jd_filename", "Unknown"),
        "text_preview": search_results.get("jd_text", "")[:500] + "..." if len(search_results.get("jd_text", "")) > 500 else search_results.get("jd_text", ""),
        "total_candidates": search_results.get("total_matches", 0),
        "shortlisted": len(top_matches),
        "timestamp": search_results.get("timestamp", "Unknown")
    }
    
    summary = f"""
==============================================
SHORTLISTED CANDIDATES SUMMARY REPORT
==============================================

Job Description: {jd_info['filename']}
Generated: {jd_info['timestamp']}
Total Candidates Analyzed: {jd_info['total_candidates']}
Shortlisted Candidates: {jd_info['shortlisted']}

==============================================
JOB DESCRIPTION PREVIEW:
==============================================
{jd_info['text_preview']}

==============================================
SHORTLISTED CANDIDATES DETAILS:
==============================================

"""
    
    for i, match in enumerate(top_matches, 1):
        candidate_info = match.get("extracted_info", {}) or {}
        score_breakdown = match.get("score_breakdown", {})
        
        candidate_name = candidate_info.get("name", "Unknown")
        candidate_email = candidate_info.get("email", "Not provided")
        candidate_skills = candidate_info.get("skills", [])
        candidate_experience = candidate_info.get("experience", [])
        overall_score = match.get("score", 0)
        
        summary += f"""
RANK {i}: {candidate_name}
{"-" * 50}
File: {match.get('file_name', 'Unknown')}
Email: {candidate_email}
Overall Score: {overall_score:.3f} ({overall_score*100:.1f}%)

Score Breakdown:
- Education: {score_breakdown.get('education', 0):.3f}
- Skills: {score_breakdown.get('skill_match', 0):.3f} 
- Experience: {score_breakdown.get('experience', 0):.3f}
- Domain: {score_breakdown.get('domain_relevance', 0):.3f}

Top Skills: {', '.join(candidate_skills[:8]) if candidate_skills else 'No skills listed'}

Experience Summary:
{chr(10).join([f"• {exp}" for exp in candidate_experience[:3]]) if candidate_experience else "• No experience details available"}

Relevant Text:
{match.get('relevant_text', 'No relevant text available')[:200]}...

==============================================
"""

    summary += f"""

==============================================
NOTES:
==============================================
- Candidates are ranked by overall weighted score
- Score components: Education (25%), Skills (35%), Experience (25%), Domain (15%)
- Files are named with rank, score, and candidate name for easy identification
- This report was generated automatically by the Resume Indexer AI system

End of Report
==============================================
"""
    
    return summary
