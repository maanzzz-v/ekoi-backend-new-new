"""Chat-based resume search API endpoints with session management."""

from typing import List, Dict, Any
from fastapi import APIRouter, Query

from models.schemas import (
    ChatRequest, ChatResponse, ResumeMatch, CreateSessionRequest, 
    AddMessageRequest, SessionResponse, SessionListResponse, 
    FollowUpRequest, MessageType
)
from services.rag_service import rag_service
from services.session_service import session_service
from services.llm_service import llm_service
from exceptions.custom_exceptions import create_http_exception
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/search", response_model=ChatResponse)
async def chat_search_resumes(request: ChatRequest):
    """
    Chat-based resume search with natural language queries using advanced RAG.

    Allows users to search for resumes using conversational queries like:
    - "Find me Python developers with 5+ years experience"
    - "Show me candidates who know React and have worked in fintech"
    - "I need a senior data scientist with ML experience"
    """
    try:
        logger.info(f"Chat search request: {request.message}")

        # Use enhanced RAG search instead of basic keyword matching
        matches, search_metadata = await rag_service.enhanced_search(
            query=request.message, top_k=request.top_k, filters=request.filters
        )

        # Generate a conversational response using search metadata
        response_message = await _generate_rag_response(
            request.message, matches, search_metadata
        )

        response = ChatResponse(
            message=response_message,
            query=search_metadata["expanded_query"],
            original_message=request.message,
            matches=matches,
            total_results=len(matches),
            success=True,
        )

        logger.info(f"Enhanced RAG search completed with {len(matches)} matches")
        return response

    except Exception as e:
        logger.error(f"Error in chat search: {e}")
        raise create_http_exception(500, "Error occurred during chat search")


@router.post("/analyze")
async def analyze_query(message: str):
    """
    Analyze a natural language query to understand search intent using RAG.

    This endpoint helps users understand how their query will be processed.
    """
    try:
        # Use RAG service for advanced query analysis
        expanded_query = await rag_service._expand_query(message)
        search_intent = rag_service._analyze_intent(message)
        search_variations = await rag_service._generate_search_variations(
            expanded_query, search_intent
        )

        # Extract key components from the query
        analysis = {
            "original_message": message,
            "expanded_query": expanded_query,
            "search_intent": search_intent,
            "search_variations": search_variations,
            "extracted_keywords": _extract_keywords(message),
            "suggestions": _get_rag_suggestions(search_intent),
        }

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise create_http_exception(500, "Error occurred during query analysis")


async def _process_chat_query(message: str) -> str:
    """
    Process natural language chat message into a search query.

    Instead of keyword extraction, we'll use the message directly for
    semantic search via embeddings, which is much more powerful for RAG.
    """
    # Enhanced query processing for better semantic search

    # Clean up the message and expand common abbreviations
    processed_message = message.lower().strip()

    # Expand common abbreviations and synonyms to improve matching
    expansions = {
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "js": "javascript",
        "ts": "typescript",
        "db": "database",
        "api": "application programming interface",
        "ui": "user interface",
        "ux": "user experience",
        "fe": "frontend front end",
        "be": "backend back end",
        "fs": "fullstack full stack",
        "devops": "development operations deployment infrastructure",
        "ci/cd": "continuous integration continuous deployment",
        "aws": "amazon web services cloud",
        "gcp": "google cloud platform",
        "k8s": "kubernetes container orchestration",
        "docker": "containerization containers",
        "react": "reactjs react.js frontend library",
        "angular": "angularjs angular.js frontend framework",
        "vue": "vuejs vue.js frontend framework",
        "node": "nodejs node.js backend javascript",
        "python": "python programming language",
        "java": "java programming language",
        "golang": "go programming language",
        "c++": "cplusplus cpp programming language",
        "c#": "csharp dotnet programming language",
    }

    # Apply expansions to make the query more comprehensive for semantic search
    for abbrev, expansion in expansions.items():
        if abbrev in processed_message:
            processed_message = processed_message.replace(
                abbrev, f"{abbrev} {expansion}"
            )

    # Add context for better semantic matching
    context_enhanced_query = f"Resume candidate profile: {processed_message}"

    logger.info(f"Enhanced query: '{message}' -> '{context_enhanced_query}'")
    return context_enhanced_query


async def _generate_rag_response(
    original_message: str, matches: List[ResumeMatch], search_metadata: Dict[str, Any]
) -> str:
    """Generate a conversational response based on RAG search results and metadata."""

    if not matches:
        intent = search_metadata.get("search_intent", {})
        suggestions = []

        if intent.get("specificity") == "high":
            suggestions.append(
                "Your query is very specific - try broadening the requirements"
            )
        if intent.get("primary_skills"):
            alt_skills = [skill for skill in intent["primary_skills"][:3]]
            suggestions.append(
                f"Try searching for related skills like: {', '.join(alt_skills)}"
            )

        suggestion_text = (
            "\n\nSuggestions:\n• " + "\n• ".join(suggestions) if suggestions else ""
        )

        return (
            f"I couldn't find any resumes matching your request: '{original_message}'. "
            f"I searched through {search_metadata.get('total_candidates_found', 0)} candidate profiles.{suggestion_text}"
        )

    # Analyze the search quality and results
    total_matches = len(matches)
    intent = search_metadata.get("search_intent", {})
    unique_candidates = search_metadata.get("unique_candidates", total_matches)

    # Extract insights from top matches
    top_match = matches[0]
    top_skills = []
    all_skills = set()

    for match in matches[:3]:  # Analyze top 3 matches
        if match.extracted_info and match.extracted_info.skills:
            if match == top_match:
                top_skills = match.extracted_info.skills[:5]
            all_skills.update(match.extracted_info.skills)

    # Generate contextual response based on search quality and intent
    response_parts = []

    # Quality assessment
    best_score = matches[0].score if matches else 0
    quality_desc = (
        "excellent" if best_score > 0.8 else "good" if best_score > 0.6 else "potential"
    )

    if total_matches == 1:
        response_parts.append(
            f"I found 1 resume showing {quality_desc} alignment with your requirements."
        )

        if top_skills:
            response_parts.append(
                f"This candidate has experience with: {', '.join(top_skills[:3])}"
            )
            if len(top_skills) > 3:
                response_parts.append(
                    f"Plus {len(top_skills) - 3} other relevant skills."
                )

    else:
        # Multiple matches - provide summary insights
        high_confidence = sum(1 for m in matches if m.score > 0.7)

        if unique_candidates != total_matches:
            response_parts.append(
                f"I found {unique_candidates} unique candidates with {total_matches} matching profile sections."
            )
        else:
            response_parts.append(
                f"I found {total_matches} candidates that match your requirements."
            )

        if high_confidence > 0:
            response_parts.append(
                f"{high_confidence} show strong alignment with your criteria."
            )

        # Highlight common skills across top candidates
        if len(all_skills) > 0:
            common_skills = list(all_skills)[:6]  # Top 6 skills
            response_parts.append(
                f"Key skills among these candidates: {', '.join(common_skills[:4])}"
            )

    # Add search methodology insight
    search_variations = len(search_metadata.get("search_variations", []))
    if search_variations > 1:
        response_parts.append(
            f"I used {search_variations} search variations to find the most relevant matches."
        )

    # Add quality and ranking information
    if best_score > 0.8:
        response_parts.append(
            "These matches show strong semantic similarity to your requirements."
        )
    elif best_score > 0.6:
        response_parts.append(
            "These are relevant matches based on semantic analysis of your criteria."
        )
    else:
        response_parts.append(
            "These are the closest matches found using advanced search techniques."
        )

    # Add helpful context about intent understanding
    if intent.get("primary_skills"):
        detected_skills = intent["primary_skills"][:3]
        response_parts.append(
            f"I focused on candidates with: {', '.join(detected_skills)}"
        )

    if intent.get("experience_level") != "any":
        response_parts.append(
            f"Filtered for {intent['experience_level']} level experience."
        )

    return " ".join(response_parts)


def _get_rag_suggestions(search_intent: Dict[str, Any]) -> List[str]:
    """Generate suggestions to improve the search query based on RAG analysis."""
    suggestions = []

    specificity = search_intent.get("specificity", "medium")
    primary_skills = search_intent.get("primary_skills", [])
    experience_level = search_intent.get("experience_level", "any")

    if specificity == "low":
        suggestions.append(
            "Try adding specific technical skills to narrow down results"
        )
        suggestions.append("Consider mentioning years of experience or seniority level")

    if not primary_skills:
        suggestions.append("Add specific programming languages or technologies")

    if experience_level == "any":
        suggestions.append("Specify the seniority level (junior, senior, lead, etc.)")

    if len(primary_skills) > 5:
        suggestions.append(
            "Consider focusing on the most important 3-4 skills for better results"
        )

    domain = search_intent.get("domain", "general")
    if domain == "general":
        suggestions.append(
            "Mention the industry or domain if relevant (fintech, healthcare, etc.)"
        )

    return suggestions


def _extract_keywords(message: str) -> List[str]:
    """Extract key terms from the message."""
    # Simple keyword extraction - could be enhanced with NLP libraries
    words = message.lower().split()

    # Filter out common stop words
    stop_words = {
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "a",
        "an",
        "the",
        "and",
        "but",
        "if",
        "or",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "find",
        "show",
        "need",
        "want",
        "looking",
    }

    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords[:10]  # Return top 10 keywords


def _analyze_search_intent(message: str) -> Dict[str, Any]:
    """Analyze the search intent from the message."""
    message_lower = message.lower()

    intent = {"type": "general_search", "urgency": "normal", "specificity": "medium"}

    # Determine search type
    if any(
        word in message_lower for word in ["senior", "lead", "principal", "architect"]
    ):
        intent["type"] = "senior_level_search"
    elif any(
        word in message_lower for word in ["junior", "entry", "graduate", "intern"]
    ):
        intent["type"] = "junior_level_search"
    elif any(
        word in message_lower for word in ["urgent", "asap", "immediately", "quickly"]
    ):
        intent["urgency"] = "high"

    # Determine specificity
    tech_mentions = sum(
        1
        for word in ["python", "java", "react", "aws", "machine learning"]
        if word in message_lower
    )
    if tech_mentions >= 3:
        intent["specificity"] = "high"
    elif tech_mentions >= 1:
        intent["specificity"] = "medium"
    else:
        intent["specificity"] = "low"

    return intent


def _get_query_suggestions(message: str) -> List[str]:
    """Generate suggestions to improve the search query."""
    suggestions = []

    message_lower = message.lower()

    if "years" not in message_lower and "experience" in message_lower:
        suggestions.append("Try specifying years of experience (e.g., '5+ years')")

    if not any(tech in message_lower for tech in ["python", "java", "react", "aws"]):
        suggestions.append("Add specific technical skills to narrow down results")

    if not any(level in message_lower for level in ["senior", "junior", "lead"]):
        suggestions.append("Specify the seniority level you're looking for")

    if len(message.split()) < 5:
        suggestions.append("Try providing more details about the role requirements")

    return suggestions


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/sessions", response_model=SessionResponse)
async def create_chat_session(request: CreateSessionRequest):
    """
    Create a new chat session for resume search conversations.
    
    This allows users to maintain conversation context across multiple searches
    and follow-up questions.
    """
    try:
        logger.info(f"Creating new chat session with title: {request.title}")
        
        session = await session_service.create_session(
            title=request.title,
            initial_message=request.initial_message
        )
        
        return SessionResponse(
            session=session,
            message=f"Session '{session.title}' created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise create_http_exception(500, "Failed to create chat session")


@router.get("/sessions", response_model=SessionListResponse)
async def list_chat_sessions(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    active_only: bool = Query(True, description="Only return active sessions")
):
    """
    List all chat sessions with pagination.
    
    Returns sessions ordered by last update time (most recent first).
    """
    try:
        sessions = await session_service.list_sessions(
            limit=limit, 
            skip=skip, 
            active_only=active_only
        )
        
        total = await session_service.get_session_count(active_only=active_only)
        
        return SessionListResponse(
            sessions=sessions,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise create_http_exception(500, "Failed to retrieve sessions")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_chat_session(session_id: str):
    """
    Get a specific chat session by ID.
    
    Returns the complete session including all messages and context.
    """
    try:
        session = await session_service.get_session(session_id)
        
        if not session:
            raise create_http_exception(404, "Session not found")
        
        return SessionResponse(
            session=session,
            message="Session retrieved successfully"
        )
        
    except Exception as e:
        if "404" in str(e):
            raise
        logger.error(f"Error getting session {session_id}: {e}")
        raise create_http_exception(500, "Failed to retrieve session")


@router.post("/sessions/{session_id}/search", response_model=ChatResponse)
async def search_in_session(session_id: str, request: ChatRequest):
    """
    Perform a resume search within a specific chat session.
    
    This maintains conversation context and adds both the user query and 
    assistant response to the session history.
    """
    try:
        # Verify session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        logger.info(f"Session {session_id} search: {request.message}")
        
        # Add user message to session
        await session_service.add_message(
            session_id=session_id,
            message_type=MessageType.USER,
            content=request.message
        )
        
        # Perform the search using enhanced RAG
        matches, search_metadata = await rag_service.enhanced_search(
            query=request.message, 
            top_k=request.top_k, 
            filters=request.filters
        )
        
        # Generate response
        response_message = await _generate_rag_response(
            request.message, matches, search_metadata
        )
        
        # Add assistant response to session
        await session_service.add_message(
            session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=response_message,
            metadata={
                "search_results": [match.id for match in matches],
                "search_metadata": search_metadata
            }
        )
        
        # Update session context with latest search results
        await session_service.update_session_context(
            session_id=session_id,
            context={
                "last_search": {
                    "query": request.message,
                    "results": [match.id for match in matches],
                    "total_results": len(matches),
                    "timestamp": search_metadata.get("timestamp")
                }
            }
        )
        
        response = ChatResponse(
            message=response_message,
            query=search_metadata["expanded_query"],
            original_message=request.message,
            matches=matches,
            total_results=len(matches),
            success=True,
            session_id=session_id
        )
        
        return response
        
    except Exception as e:
        if "404" in str(e):
            raise
        logger.error(f"Error in session search {session_id}: {e}")
        raise create_http_exception(500, "Search failed")


@router.post("/sessions/{session_id}/followup")
async def ask_followup_question(session_id: str, request: FollowUpRequest):
    """
    Ask follow-up questions about previous search results.
    
    Examples:
    - "Why were these candidates selected?"
    - "What are the key strengths of the top candidate?"
    - "How do these candidates compare in terms of experience?"
    - "Which candidate would be best for a startup environment?"
    """
    try:
        # Verify session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        logger.info(f"Follow-up question in session {session_id}: {request.question}")
        
        # Add user question to session
        await session_service.add_message(
            session_id=session_id,
            message_type=MessageType.USER,
            content=request.question
        )
        
        # Get context from session (previous search results)
        context = session.context or {}
        last_search = context.get("last_search", {})
        
        if not last_search.get("results"):
            # No previous search results to analyze
            response_message = "I don't have any recent search results to analyze. Please perform a resume search first, then I can answer follow-up questions about the candidates."
        else:
            # Generate follow-up response based on previous results and current question
            response_message = await _generate_followup_response(
                question=request.question,
                previous_results=last_search.get("results", []),
                session_context=context,
                session_messages=session.messages
            )
        
        # Add assistant response to session
        await session_service.add_message(
            session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=response_message,
            metadata={
                "followup_question": request.question,
                "analyzed_results": last_search.get("results", [])
            }
        )
        
        return {
            "session_id": session_id,
            "question": request.question,
            "answer": response_message,
            "success": True
        }
        
    except Exception as e:
        if "404" in str(e):
            raise
        logger.error(f"Error in follow-up question {session_id}: {e}")
        raise create_http_exception(500, "Failed to process follow-up question")


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete (deactivate) a chat session.
    
    This marks the session as inactive rather than permanently deleting it.
    """
    try:
        success = await session_service.delete_session(session_id)
        
        if not success:
            raise create_http_exception(404, "Session not found")
        
        return {
            "session_id": session_id,
            "message": "Session deleted successfully",
            "success": True
        }
        
    except Exception as e:
        if "404" in str(e):
            raise
        logger.error(f"Error deleting session {session_id}: {e}")
        raise create_http_exception(500, "Failed to delete session")


# ============================================================================
# HELPER FUNCTIONS FOR FOLLOW-UP QUESTIONS
# ============================================================================

async def _generate_followup_response(
    question: str, 
    previous_results: List[str], 
    session_context: Dict[str, Any],
    session_messages: List[Any]
) -> str:
    """Generate intelligent responses to follow-up questions about search results."""
    try:
        # Get the actual resume data for analysis
        from services.resume_service import resume_service
        
        resume_data = []
        for resume_id in previous_results[:5]:  # Limit to top 5 for analysis
            resume = await resume_service.get_resume_by_id(resume_id)
            if resume:
                resume_data.append(resume)
        
        if not resume_data:
            return "I couldn't retrieve the resume data for analysis. Please try searching again."
        
        # Analyze the question type and generate appropriate response
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["why", "reason", "selected", "chosen"]):
            return _explain_selection_criteria(resume_data, session_context)
        
        elif any(word in question_lower for word in ["strength", "strong", "best", "top"]):
            return _analyze_candidate_strengths(resume_data)
        
        elif any(word in question_lower for word in ["compare", "comparison", "difference"]):
            return _compare_candidates(resume_data)
        
        elif any(word in question_lower for word in ["startup", "environment", "culture", "fit"]):
            return _analyze_cultural_fit(resume_data, question)
        
        elif any(word in question_lower for word in ["experience", "years", "senior", "junior"]):
            return _analyze_experience_levels(resume_data)
        
        elif any(word in question_lower for word in ["skill", "technology", "tech", "technical"]):
            return _analyze_technical_skills(resume_data)
        
        else:
            # General analysis
            return _provide_general_analysis(resume_data, question)
    
    except Exception as e:
        logger.error(f"Error generating follow-up response: {e}")
        return "I encountered an error while analyzing the candidates. Please try rephrasing your question."


def _explain_selection_criteria(resume_data: List[Dict], context: Dict) -> str:
    """Explain why these candidates were selected."""
    explanations = []
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        experience = resume.get("parsed_info", {}).get("experience", [])
        
        key_skills = skills[:5] if skills else []
        exp_summary = f"{len(experience)} role(s)" if experience else "Limited experience data"
        
        explanations.append(
            f"**{name}**: Selected for {', '.join(key_skills[:3])} skills "
            f"and {exp_summary}. Strong technical profile."
        )
    
    return f"Here's why these candidates were selected:\n\n" + "\n\n".join(explanations)


def _analyze_candidate_strengths(resume_data: List[Dict]) -> str:
    """Analyze the key strengths of candidates."""
    analyses = []
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        summary = resume.get("parsed_info", {}).get("summary", "")
        
        # Identify key strengths
        strengths = []
        if len(skills) > 10:
            strengths.append(f"Diverse skill set ({len(skills)} skills)")
        
        if any(skill.lower() in ["python", "java", "javascript"] for skill in skills):
            strengths.append("Strong programming background")
        
        if any(skill.lower() in ["aws", "azure", "docker", "kubernetes"] for skill in skills):
            strengths.append("Cloud & DevOps expertise")
        
        if "senior" in summary.lower() or "lead" in summary.lower():
            strengths.append("Senior-level experience")
        
        strength_text = ", ".join(strengths) if strengths else "Solid technical foundation"
        analyses.append(f"**{name}**: {strength_text}")
    
    return f"Key strengths of the top candidates:\n\n" + "\n\n".join(analyses)


def _compare_candidates(resume_data: List[Dict]) -> str:
    """Compare candidates across different dimensions."""
    if len(resume_data) < 2:
        return "I need at least 2 candidates to make a comparison."
    
    comparison = "**Candidate Comparison:**\n\n"
    
    # Compare skills diversity
    comparison += "**Skill Diversity:**\n"
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills_count = len(resume.get("parsed_info", {}).get("skills", []))
        comparison += f"• {name}: {skills_count} skills\n"
    
    # Compare experience
    comparison += "\n**Experience Overview:**\n"
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        experience = resume.get("parsed_info", {}).get("experience", [])
        exp_count = len(experience)
        comparison += f"• {name}: {exp_count} role(s) listed\n"
    
    return comparison


def _analyze_cultural_fit(resume_data: List[Dict], question: str) -> str:
    """Analyze candidates for cultural/environmental fit."""
    environment = "startup" if "startup" in question.lower() else "corporate"
    
    analysis = f"**Candidates for {environment} environment:**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        summary = resume.get("parsed_info", {}).get("summary", "")
        
        fit_indicators = []
        
        if environment == "startup":
            if any(skill.lower() in ["javascript", "python", "react", "node"] for skill in skills):
                fit_indicators.append("Full-stack capabilities")
            if any(skill.lower() in ["aws", "docker", "ci/cd"] for skill in skills):
                fit_indicators.append("DevOps/Cloud skills")
            if len(skills) > 8:
                fit_indicators.append("Versatile skill set")
        
        fit_text = ", ".join(fit_indicators) if fit_indicators else "General technical skills"
        analysis += f"**{name}**: {fit_text}\n"
    
    return analysis


def _analyze_experience_levels(resume_data: List[Dict]) -> str:
    """Analyze experience levels of candidates."""
    analysis = "**Experience Level Analysis:**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        experience = resume.get("parsed_info", {}).get("experience", [])
        summary = resume.get("parsed_info", {}).get("summary", "")
        
        # Try to infer experience level
        level = "Unknown"
        if "senior" in summary.lower():
            level = "Senior"
        elif "lead" in summary.lower():
            level = "Lead/Principal"
        elif "junior" in summary.lower():
            level = "Junior"
        elif len(experience) >= 3:
            level = "Mid to Senior"
        elif len(experience) >= 1:
            level = "Mid-level"
        
        analysis += f"**{name}**: {level} ({len(experience)} roles listed)\n"
    
    return analysis


def _analyze_technical_skills(resume_data: List[Dict]) -> str:
    """Analyze technical skills across candidates."""
    analysis = "**Technical Skills Analysis:**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        
        # Categorize skills
        languages = [s for s in skills if s.lower() in ["python", "java", "javascript", "c++", "go", "rust"]]
        frameworks = [s for s in skills if s.lower() in ["react", "django", "flask", "spring", "node.js"]]
        cloud = [s for s in skills if s.lower() in ["aws", "azure", "docker", "kubernetes", "terraform"]]
        
        analysis += f"**{name}**:\n"
        if languages:
            analysis += f"  • Languages: {', '.join(languages[:3])}\n"
        if frameworks:
            analysis += f"  • Frameworks: {', '.join(frameworks[:3])}\n"
        if cloud:
            analysis += f"  • Cloud/DevOps: {', '.join(cloud[:3])}\n"
        analysis += "\n"
    
    return analysis


def _provide_general_analysis(resume_data: List[Dict], question: str) -> str:
    """Provide general analysis when question type is unclear."""
    analysis = f"**Analysis for: '{question}'**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        summary = resume.get("parsed_info", {}).get("summary", "")[:200] + "..."
        
        analysis += f"**{name}**:\n"
        analysis += f"• Skills: {len(skills)} total ({', '.join(skills[:5])}{'...' if len(skills) > 5 else ''})\n"
        analysis += f"• Summary: {summary}\n\n"
    
    return analysis
