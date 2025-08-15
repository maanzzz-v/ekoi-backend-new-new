"""Chat-based resume search API endpoints with enhanced RAG intelligence."""

from typing import List, Dict, Any
from fastapi import APIRouter, Query

from models.schemas import (
    ChatRequest, ChatResponse, ResumeMatch, CreateSessionRequest, 
    AddMessageRequest, SessionResponse, SessionListResponse, 
    FollowUpRequest, MessageType
)
from services.enhanced_rag_service import enhanced_rag_service
from services.chatbot_optimizer import chatbot_optimizer
from services.session_service import session_service
from services.llm_service import llm_service
from exceptions.custom_exceptions import create_http_exception
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/search", response_model=ChatResponse)
async def chat_search_resumes(request: ChatRequest):
    """
    Intelligent chat-based resume search with optimized UI responses.

    Provides clean, structured responses perfect for frontend integration with:
    - Natural language understanding
    - Semantic candidate matching  
    - Structured UI components
    - Conversation flow suggestions
    - Quick action recommendations
    """
    try:
        logger.info(f"Intelligent chat search: {request.message}")

        # Use enhanced RAG service for intelligent search
        matches, search_metadata = await enhanced_rag_service.intelligent_search(
            query=request.message, 
            top_k=request.top_k, 
            filters=request.filters
        )

        # Optimize response for clean UI integration
        optimized_response = await chatbot_optimizer.optimize_chat_response(
            user_message=request.message,
            matches=matches,
            metadata=search_metadata
        )

        # Structure response for frontend
        response = ChatResponse(
            message=optimized_response["message"],
            query=search_metadata.get("expanded_query", request.message),
            original_message=request.message,
            matches=matches,
            total_results=len(matches),
            success=True,
        )

        # Add UI optimization data to response
        response.ui_components = optimized_response.get("ui_components", {})
        response.conversation_flow = optimized_response.get("conversation_flow", {})
        response.quick_actions = optimized_response.get("quick_actions", [])
        response.response_metadata = optimized_response.get("metadata", {})

        logger.info(f"Optimized chat search completed: {len(matches)} matches with UI components")
        return response

    except Exception as e:
        logger.error(f"Error in intelligent chat search: {e}")
        raise create_http_exception(500, "Error occurred during intelligent search")


@router.post("/analyze")
async def analyze_query(message: str):
    """
    Analyze a natural language query to understand search intent using enhanced RAG.

    This endpoint helps users understand how their query will be processed.
    """
    try:
        # Use enhanced RAG service for advanced query analysis
        analysis = await enhanced_rag_service._analyze_query_intent(message)
        
        # Add helpful suggestions
        analysis["suggestions"] = _get_query_improvement_suggestions(analysis)
        analysis["extracted_keywords"] = enhanced_rag_service._extract_semantic_keywords(message)

        return {
            "original_message": message,
            "intelligence_analysis": analysis,
            "query_quality": _assess_query_quality(analysis),
            "optimization_tips": _get_optimization_tips(analysis)
        }

    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise create_http_exception(500, "Error occurred during intelligent query analysis")


def _get_query_improvement_suggestions(analysis: Dict[str, Any]) -> List[str]:
    """Generate suggestions to improve query based on analysis."""
    suggestions = []
    
    if analysis.get("technical_depth") == "low":
        suggestions.append("Add specific technical skills or programming languages")
    
    if not analysis.get("skill_domains"):
        suggestions.append("Mention specific technologies or skill areas")
    
    if analysis.get("intent_confidence", 0) < 0.7:
        suggestions.append("Be more specific about what type of candidate you're looking for")
    
    experience_indicators = analysis.get("experience_indicators", {})
    if not experience_indicators:
        suggestions.append("Specify experience level (junior, senior, etc.) or years of experience")
    
    return suggestions


def _assess_query_quality(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the quality and completeness of the query."""
    quality_score = 0.5  # Base score
    
    # Add points for various factors
    if analysis.get("intent_confidence", 0) > 0.8:
        quality_score += 0.2
    
    if analysis.get("skill_domains"):
        quality_score += 0.15 * min(len(analysis["skill_domains"]), 2)
    
    if analysis.get("experience_indicators"):
        quality_score += 0.15
    
    if analysis.get("technical_depth") == "high":
        quality_score += 0.1
    
    quality_score = min(quality_score, 1.0)
    
    # Determine quality level
    if quality_score >= 0.8:
        level = "excellent"
    elif quality_score >= 0.6:
        level = "good"
    elif quality_score >= 0.4:
        level = "fair"
    else:
        level = "needs_improvement"
    
    return {
        "score": round(quality_score, 2),
        "level": level,
        "completeness": quality_score
    }


def _get_optimization_tips(analysis: Dict[str, Any]) -> List[str]:
    """Provide optimization tips based on analysis."""
    tips = []
    
    query_type = analysis.get("query_type", "general")
    
    if query_type == "skill_search":
        tips.append("💡 Consider mentioning project context or industry domain")
    elif query_type == "experience_query":
        tips.append("💡 Add specific technical skills to refine results")
    
    if analysis.get("technical_depth") == "high":
        tips.append("🎯 Your query is technically specific - great for precision!")
    else:
        tips.append("🔍 Add more technical details for better matching")
    
    return tips


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
    """Generate a clean, professional response optimized for UI display."""

    if not matches:
        intent = search_metadata.get("search_intent", {})
        
        # Clean, helpful no-results response
        response = f"I couldn't find any candidates matching your specific requirements for '{original_message}'."
        
        # Add constructive suggestions
        suggestions = []
        if intent.get("specificity") == "high":
            suggestions.append("Try broadening your requirements")
        if intent.get("primary_skills"):
            suggestions.append("Consider related technologies or skills")
        
        if suggestions:
            response += f"\n\n💡 **Suggestions:**\n• {chr(10).join(f'• {s}' for s in suggestions)}"
        
        return response

    # Analyze results for clean presentation
    total_matches = len(matches)
    intent = search_metadata.get("search_intent", {})
    best_score = matches[0].score if matches else 0
    
    # Get top candidate info for personalization
    top_candidate = matches[0]
    top_name = "Unknown"
    top_skills = []
    
    if top_candidate.extracted_info:
        top_name = top_candidate.extracted_info.name or "Top candidate"
        top_skills = top_candidate.extracted_info.skills[:4] if top_candidate.extracted_info.skills else []

    # Build response sections
    response_sections = []
    
    # 1. Main result summary (clean and specific)
    if total_matches == 1:
        confidence = "excellent" if best_score > 0.8 else "good" if best_score > 0.6 else "relevant"
        response_sections.append(f"✅ **Found 1 {confidence} candidate match**")
        
        if top_name != "Unknown":
            response_sections.append(f"**{top_name}** shows strong alignment with your requirements.")
    else:
        high_quality = sum(1 for m in matches if m.score > 0.7)
        response_sections.append(f"✅ **Found {total_matches} candidates**")
        
        if high_quality > 0:
            response_sections.append(f"{high_quality} candidates show excellent alignment with your criteria.")
        else:
            response_sections.append("These candidates match your key requirements.")

    # 2. Key skills summary (for UI skill tags)
    if top_skills:
        skills_text = ", ".join(top_skills)
        response_sections.append(f"🔧 **Key skills**: {skills_text}")
    
    # 3. Search intelligence (show the AI's understanding)
    search_insights = []
    
    if intent.get("primary_skills"):
        detected_skills = intent["primary_skills"][:3]
        search_insights.append(f"Focused on: {', '.join(detected_skills)}")
    
    if intent.get("experience_level") != "any":
        search_insights.append(f"Experience level: {intent['experience_level']}")
    
    if intent.get("role_type") != "general":
        search_insights.append(f"Role type: {intent['role_type']}")
    
    if search_insights:
        response_sections.append(f"🎯 **Search focus**: {' • '.join(search_insights)}")

    # 4. Quality indicator for UI
    quality_indicators = []
    if best_score > 0.8:
        quality_indicators.append("High semantic similarity")
    elif best_score > 0.6:
        quality_indicators.append("Good semantic match")
    
    search_variations = len(search_metadata.get("search_variations", []))
    if search_variations > 2:
        quality_indicators.append(f"Used {search_variations} search strategies")
    
    if quality_indicators:
        response_sections.append(f"📊 **Quality**: {' • '.join(quality_indicators)}")

    # Combine sections with clean formatting for UI
    return "\n\n".join(response_sections)


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
# UI OPTIMIZATION ENDPOINTS
# ============================================================================

@router.get("/conversation-starters")
async def get_conversation_starters():
    """
    Get conversation starter suggestions for empty chat state.
    
    Provides pre-made queries to help users get started with the chatbot.
    """
    try:
        starters = chatbot_optimizer.get_conversation_starters()
        templates = chatbot_optimizer.get_search_templates()
        
        return {
            "conversation_starters": starters,
            "search_templates": templates,
            "example_queries": [
                "Find Python developers with 5+ years experience",
                "Show me frontend developers who know React",
                "I need a senior data scientist with ML experience",
                "Looking for DevOps engineers with AWS experience",
                "Find full-stack developers for a startup environment"
            ],
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation starters: {e}")
        raise create_http_exception(500, "Failed to get conversation starters")


@router.post("/optimize-query")
async def optimize_user_query(query: str):
    """
    Optimize and enhance user queries for better search results.
    
    Provides suggestions to improve query quality and search effectiveness.
    """
    try:
        # Analyze query using enhanced RAG
        analysis = await enhanced_rag_service._analyze_query_intent(query)
        
        # Generate optimization suggestions
        suggestions = _get_query_improvement_suggestions(analysis)
        quality_assessment = _assess_query_quality(analysis)
        optimization_tips = _get_optimization_tips(analysis)
        
        # Generate enhanced query alternatives
        enhanced_queries = []
        if analysis.get("skill_domains"):
            for domain in analysis["skill_domains"][:2]:
                enhanced_query = f"Find {domain['description']} professionals with {query.lower()}"
                enhanced_queries.append({
                    "query": enhanced_query,
                    "improvement": f"Added {domain['description']} context",
                    "expected_improvement": "More specific results"
                })
        
        return {
            "original_query": query,
            "query_analysis": {
                "intent_type": analysis.get("query_type", "general"),
                "confidence": analysis.get("intent_confidence", 0),
                "technical_depth": analysis.get("technical_depth", "medium"),
                "detected_skills": [d["domain"] for d in analysis.get("skill_domains", [])]
            },
            "quality_assessment": quality_assessment,
            "optimization_suggestions": suggestions,
            "optimization_tips": optimization_tips,
            "enhanced_alternatives": enhanced_queries,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error optimizing query: {e}")
        raise create_http_exception(500, "Failed to optimize query")


@router.get("/search-insights")
async def get_search_insights():
    """
    Get insights about search patterns and available data.
    
    Helps users understand what types of searches work best.
    """
    try:
        # Get insights from the database about available skills, experience levels, etc.
        from services.resume_service import resume_service
        
        # This would normally come from analytics, but we'll generate sample insights
        insights = {
            "popular_skills": [
                {"skill": "Python", "count": 45, "trend": "increasing"},
                {"skill": "JavaScript", "count": 38, "trend": "stable"},
                {"skill": "React", "count": 32, "trend": "increasing"},
                {"skill": "AWS", "count": 28, "trend": "increasing"},
                {"skill": "Java", "count": 25, "trend": "stable"}
            ],
            "experience_distribution": {
                "junior": "25%",
                "mid_level": "45%", 
                "senior": "25%",
                "lead": "5%"
            },
            "search_tips": [
                "🎯 Be specific about required skills for better matches",
                "⏱️ Mention years of experience to filter by seniority",
                "🏢 Include industry context (fintech, healthcare) for domain expertise",
                "🔧 Use multiple related technologies (React + JavaScript + TypeScript)",
                "📈 Specify role level (senior, junior, lead) for experience matching"
            ],
            "skill_domains": list(enhanced_rag_service.skill_contexts.keys()),
            "success": True
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting search insights: {e}")
        raise create_http_exception(500, "Failed to get search insights")


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS (continued)
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
    Perform intelligent resume search within a chat session with optimized UI responses.
    
    Maintains conversation context and provides structured responses for clean UI integration.
    """
    try:
        # Verify session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise create_http_exception(404, "Session not found")
        
        logger.info(f"Session {session_id} intelligent search: {request.message}")
        
        # Add user message to session
        await session_service.add_message(
            session_id=session_id,
            message_type=MessageType.USER,
            content=request.message
        )
        
        # Perform intelligent search with session context
        matches, search_metadata = await enhanced_rag_service.intelligent_search(
            query=request.message, 
            top_k=request.top_k, 
            filters=request.filters,
            context={"session_id": session_id, "previous_searches": session.context}
        )
        
        # Optimize response for UI with session context
        optimized_response = await chatbot_optimizer.optimize_chat_response(
            user_message=request.message,
            matches=matches,
            metadata=search_metadata,
            session_context=session.context
        )
        
        # Add optimized assistant response to session
        await session_service.add_message(
            session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=optimized_response["message"],
            metadata={
                "search_results": [match.id for match in matches],
                "search_metadata": search_metadata,
                "ui_components": optimized_response.get("ui_components", {}),
                "response_optimization": optimized_response.get("metadata", {})
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
                    "optimization_data": optimized_response.get("metadata", {}),
                    "timestamp": search_metadata.get("timestamp")
                }
            }
        )
        
        # Structure response for frontend
        response = ChatResponse(
            message=optimized_response["message"],
            query=search_metadata.get("expanded_query", request.message),
            original_message=request.message,
            matches=matches,
            total_results=len(matches),
            success=True,
            session_id=session_id
        )
        
        # Add UI optimization data
        response.ui_components = optimized_response.get("ui_components", {})
        response.conversation_flow = optimized_response.get("conversation_flow", {})
        response.quick_actions = optimized_response.get("quick_actions", [])
        response.response_metadata = optimized_response.get("metadata", {})
        
        return response
        
    except Exception as e:
        if "404" in str(e):
            raise
        logger.error(f"Error in session search {session_id}: {e}")
        raise create_http_exception(500, "Intelligent search failed")


@router.post("/sessions/{session_id}/followup")
async def ask_followup_question(session_id: str, request: FollowUpRequest):
    """
    Ask intelligent follow-up questions with optimized UI responses.
    
    Provides detailed candidate analysis with structured data for clean UI display.
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
            response_message = "🔍 **No recent search results to analyze**\n\nPlease perform a resume search first, then I can answer detailed questions about the candidates."
            
            # Create optimized no-context response
            optimized_response = await chatbot_optimizer.optimize_followup_response(
                question=request.question,
                analysis_result=response_message,
                session_context=context
            )
        else:
            # Generate follow-up response based on previous results and current question
            analysis_result = await _generate_followup_response(
                question=request.question,
                previous_results=last_search.get("results", []),
                session_context=context,
                session_messages=session.messages
            )
            
            # Optimize the follow-up response for UI
            optimized_response = await chatbot_optimizer.optimize_followup_response(
                question=request.question,
                analysis_result=analysis_result,
                session_context=context
            )
        
        # Add optimized assistant response to session
        await session_service.add_message(
            session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=optimized_response["message"],
            metadata={
                "followup_question": request.question,
                "analyzed_results": last_search.get("results", []),
                "ui_optimization": optimized_response.get("metadata", {}),
                "response_components": optimized_response.get("ui_components", {})
            }
        )
        
        return {
            "session_id": session_id,
            "question": request.question,
            "answer": optimized_response["message"],
            "ui_components": optimized_response.get("ui_components", {}),
            "conversation_flow": optimized_response.get("conversation_flow", {}),
            "quick_actions": optimized_response.get("quick_actions", []),
            "response_metadata": optimized_response.get("metadata", {}),
            "success": True
        }
        
    except Exception as e:
        if "404" in str(e):
            raise
        logger.error(f"Error in follow-up question {session_id}: {e}")
        raise create_http_exception(500, "Failed to process intelligent follow-up question")


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
    """Generate clean, structured responses to follow-up questions."""
    try:
        # Get the actual resume data for analysis
        from services.resume_service import resume_service
        
        resume_data = []
        for resume_id in previous_results[:5]:  # Limit to top 5 for analysis
            resume = await resume_service.get_resume_by_id(resume_id)
            if resume:
                resume_data.append(resume)
        
        if not resume_data:
            return "❌ **Unable to analyze candidates** - Please perform a new search and try again."
        
        # Analyze the question type and generate appropriate response
        question_lower = question.lower()
        
        # Question categorization with clean responses
        if any(word in question_lower for word in ["why", "reason", "selected", "chosen", "criteria"]):
            return _explain_selection_criteria_clean(resume_data, session_context)
        
        elif any(word in question_lower for word in ["strength", "strong", "best", "top", "advantage"]):
            return _analyze_candidate_strengths_clean(resume_data)
        
        elif any(word in question_lower for word in ["compare", "comparison", "difference", "versus", "vs"]):
            return _compare_candidates_clean(resume_data)
        
        elif any(word in question_lower for word in ["startup", "environment", "culture", "fit", "team"]):
            return _analyze_cultural_fit_clean(resume_data, question)
        
        elif any(word in question_lower for word in ["experience", "years", "senior", "junior", "level"]):
            return _analyze_experience_levels_clean(resume_data)
        
        elif any(word in question_lower for word in ["skill", "technology", "tech", "technical", "programming"]):
            return _analyze_technical_skills_clean(resume_data)
        
        elif any(word in question_lower for word in ["salary", "cost", "budget", "rate", "compensation"]):
            return "💰 **Compensation Analysis**: I don't have salary information in the resumes. Consider discussing compensation during interviews based on market rates for their skill levels."
        
        elif any(word in question_lower for word in ["location", "remote", "office", "onsite", "hybrid"]):
            return _analyze_location_preferences_clean(resume_data)
        
        else:
            # General analysis with clean formatting
            return _provide_general_analysis_clean(resume_data, question)
    
    except Exception as e:
        logger.error(f"Error generating follow-up response: {e}")
        return "⚠️ **Analysis Error**: I encountered an issue while analyzing the candidates. Please try rephrasing your question or perform a new search."


def _explain_selection_criteria_clean(resume_data: List[Dict], context: Dict) -> str:
    """Clean explanation of why candidates were selected."""
    response = "🎯 **Why These Candidates Were Selected**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        experience = resume.get("parsed_info", {}).get("experience", [])
        
        # Build selection criteria
        criteria = []
        
        if len(skills) >= 8:
            criteria.append(f"**Broad skill set** ({len(skills)} skills)")
        elif len(skills) >= 5:
            criteria.append(f"**Relevant skills** ({len(skills)} skills)")
        
        if skills:
            top_skills = skills[:3]
            criteria.append(f"**Key technologies**: {', '.join(top_skills)}")
        
        if len(experience) >= 3:
            criteria.append(f"**Substantial experience** ({len(experience)} roles)")
        elif len(experience) >= 1:
            criteria.append(f"**Professional experience** ({len(experience)} role{'s' if len(experience) > 1 else ''})")
        
        criteria_text = "\n  • ".join(criteria) if criteria else "General technical background"
        
        response += f"**{name}**\n  • {criteria_text}\n\n"
    
    return response.strip()


def _analyze_candidate_strengths_clean(resume_data: List[Dict]) -> str:
    """Clean analysis of candidate strengths."""
    response = "💪 **Candidate Strengths Analysis**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        summary = resume.get("parsed_info", {}).get("summary", "")
        experience = resume.get("parsed_info", {}).get("experience", [])
        
        strengths = []
        
        # Technical strengths
        if len(skills) > 12:
            strengths.append("🔧 **Versatile technologist** - Broad skill portfolio")
        elif len(skills) > 8:
            strengths.append("🔧 **Well-rounded developer** - Solid skill range")
        
        # Experience strengths
        if len(experience) >= 4:
            strengths.append("📈 **Seasoned professional** - Extensive work history")
        elif len(experience) >= 2:
            strengths.append("📈 **Experienced contributor** - Proven track record")
        
        # Domain strengths
        if any(skill.lower() in ["python", "java", "javascript", "c++"] for skill in skills):
            strengths.append("💻 **Strong programming foundation**")
        
        if any(skill.lower() in ["aws", "azure", "docker", "kubernetes"] for skill in skills):
            strengths.append("☁️ **Cloud-native expertise**")
        
        if any(skill.lower() in ["react", "angular", "vue"] for skill in skills):
            strengths.append("🎨 **Modern frontend skills**")
        
        # Leadership indicators
        if "senior" in summary.lower() or "lead" in summary.lower():
            strengths.append("👥 **Leadership experience**")
        
        if not strengths:
            strengths.append("🎯 **Solid technical foundation**")
        
        response += f"**{name}**\n"
        for strength in strengths[:4]:  # Limit to top 4 strengths
            response += f"  • {strength}\n"
        response += "\n"
    
    return response.strip()


def _compare_candidates_clean(resume_data: List[Dict]) -> str:
    """Clean comparison of candidates."""
    if len(resume_data) < 2:
        return "❌ **Comparison requires at least 2 candidates** - Please search for more candidates first."
    
    response = "⚖️ **Candidate Comparison**\n\n"
    
    # Skills comparison
    response += "**🔧 Technical Skills:**\n"
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills_count = len(resume.get("parsed_info", {}).get("skills", []))
        skills = resume.get("parsed_info", {}).get("skills", [])[:4]
        
        skills_preview = f" ({', '.join(skills)}{'...' if len(skills) == 4 else ''})" if skills else ""
        response += f"  • **{name}**: {skills_count} skills{skills_preview}\n"
    
    # Experience comparison
    response += "\n**📈 Professional Experience:**\n"
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        exp_count = len(resume.get("parsed_info", {}).get("experience", []))
        
        exp_level = "Senior" if exp_count >= 4 else "Mid-level" if exp_count >= 2 else "Junior/Entry"
        response += f"  • **{name}**: {exp_count} role(s) - *{exp_level} profile*\n"
    
    # Education comparison
    response += "\n**🎓 Educational Background:**\n"
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        education = resume.get("parsed_info", {}).get("education", [])
        
        edu_summary = f"{len(education)} educational background(s)" if education else "Limited education data"
        response += f"  • **{name}**: {edu_summary}\n"
    
    return response


def _analyze_cultural_fit_clean(resume_data: List[Dict], question: str) -> str:
    """Analyze candidates for cultural/environmental fit."""
    environment = "startup" if "startup" in question.lower() else "corporate"
    
    response = f"🏢 **{environment.title()} Environment Fit Analysis**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        summary = resume.get("parsed_info", {}).get("summary", "")
        
        fit_score = 0
        fit_factors = []
        
        if environment == "startup":
            # Startup fit indicators
            if any(skill.lower() in ["javascript", "python", "react", "node"] for skill in skills):
                fit_score += 2
                fit_factors.append("✅ **Full-stack capabilities**")
                
            if any(skill.lower() in ["aws", "docker", "ci/cd", "kubernetes"] for skill in skills):
                fit_score += 2
                fit_factors.append("✅ **DevOps/Infrastructure skills**")
                
            if len(skills) > 10:
                fit_score += 1
                fit_factors.append("✅ **Versatile skill set**")
                
            if any(word in summary.lower() for word in ["startup", "agile", "fast-paced"]):
                fit_score += 2
                fit_factors.append("✅ **Startup experience mentioned**")
        else:
            # Corporate fit indicators
            if any(skill.lower() in ["java", "c#", ".net", "enterprise"] for skill in skills):
                fit_score += 2
                fit_factors.append("✅ **Enterprise technologies**")
                
            if any(word in summary.lower() for word in ["senior", "lead", "architect"]):
                fit_score += 2
                fit_factors.append("✅ **Leadership experience**")
        
        # Determine fit level
        if fit_score >= 4:
            fit_level = "🟢 **Excellent fit**"
        elif fit_score >= 2:
            fit_level = "🟡 **Good fit**"
        else:
            fit_level = "🔶 **Moderate fit**"
        
        response += f"**{name}** - {fit_level}\n"
        
        if fit_factors:
            for factor in fit_factors[:3]:  # Top 3 factors
                response += f"  • {factor}\n"
        else:
            response += f"  • General technical skills suitable for {environment} environment\n"
        
        response += "\n"
    
    return response.strip()


def _analyze_experience_levels_clean(resume_data: List[Dict]) -> str:
    """Clean analysis of experience levels."""
    response = "📊 **Experience Level Analysis**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        experience = resume.get("parsed_info", {}).get("experience", [])
        summary = resume.get("parsed_info", {}).get("summary", "")
        
        # Determine experience level
        role_count = len(experience)
        
        # Extract years from summary if available
        years_mentioned = "experience not specified"
        if summary:
            import re
            years_match = re.search(r'(\d+)\+?\s*years?', summary.lower())
            if years_match:
                years_mentioned = f"~{years_match.group(1)} years mentioned"
        
        # Classify experience level
        if "senior" in summary.lower() or "lead" in summary.lower() or role_count >= 4:
            level = "🟢 **Senior Level**"
            level_desc = "Extensive experience with leadership potential"
        elif "mid" in summary.lower() or role_count >= 2:
            level = "🟡 **Mid Level**"
            level_desc = "Solid professional experience"
        elif "junior" in summary.lower() or role_count >= 1:
            level = "🔶 **Junior Level**"
            level_desc = "Growing professional with foundational experience"
        else:
            level = "⚪ **Entry Level**"
            level_desc = "Early career professional"
        
        response += f"**{name}** - {level}\n"
        response += f"  • **Profile**: {role_count} role(s) listed, {years_mentioned}\n"
        response += f"  • **Assessment**: {level_desc}\n\n"
    
    return response.strip()


def _analyze_technical_skills_clean(resume_data: List[Dict]) -> str:
    """Clean technical skills analysis."""
    response = "⚙️ **Technical Skills Breakdown**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        
        if not skills:
            response += f"**{name}**: No specific technical skills extracted\n\n"
            continue
        
        # Categorize skills
        categories = {
            "Programming": ["python", "java", "javascript", "c++", "c#", "go", "rust", "php"],
            "Frontend": ["react", "angular", "vue", "html", "css", "typescript"],
            "Backend": ["django", "flask", "spring", "node.js", "express"],
            "Cloud/DevOps": ["aws", "azure", "docker", "kubernetes", "terraform", "ci/cd"],
            "Database": ["sql", "mysql", "postgresql", "mongodb", "redis"],
            "Data/ML": ["machine learning", "tensorflow", "pytorch", "pandas", "numpy"]
        }
        
        skill_breakdown = {}
        for category, category_skills in categories.items():
            matches = [s for s in skills if s.lower() in [cs.lower() for cs in category_skills]]
            if matches:
                skill_breakdown[category] = matches[:3]  # Top 3 per category
        
        response += f"**{name}** ({len(skills)} total skills)\n"
        
        if skill_breakdown:
            for category, category_skills in skill_breakdown.items():
                response += f"  • **{category}**: {', '.join(category_skills)}\n"
        else:
            # Show general skills if no categorization
            response += f"  • **General**: {', '.join(skills[:5])}\n"
        
        response += "\n"
    
    return response.strip()


def _analyze_location_preferences_clean(resume_data: List[Dict]) -> str:
    """Analyze location and remote work preferences."""
    response = "📍 **Location & Work Preferences**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        summary = resume.get("parsed_info", {}).get("summary", "")
        
        # Try to extract location info
        location_info = "Location not specified in resume"
        remote_friendly = "Remote work preference not mentioned"
        
        if summary:
            # Simple location detection
            if any(word in summary.lower() for word in ["remote", "distributed", "anywhere"]):
                remote_friendly = "✅ **Remote work mentioned**"
            elif any(word in summary.lower() for word in ["onsite", "office", "local"]):
                remote_friendly = "🏢 **Prefers office work**"
            
            # Look for city/state mentions (basic)
            import re
            location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*([A-Z]{2})\b'
            location_match = re.search(location_pattern, summary)
            if location_match:
                location_info = f"📍 **{location_match.group(1)}, {location_match.group(2)}**"
        
        response += f"**{name}**\n"
        response += f"  • {location_info}\n"
        response += f"  • {remote_friendly}\n\n"
    
    return response.strip()


def _provide_general_analysis_clean(resume_data: List[Dict], question: str) -> str:
    """Provide clean general analysis for unclear questions."""
    response = f"📋 **General Analysis: '{question}'**\n\n"
    
    for i, resume in enumerate(resume_data[:3], 1):
        name = resume.get("parsed_info", {}).get("name", f"Candidate {i}")
        skills = resume.get("parsed_info", {}).get("skills", [])
        experience = resume.get("parsed_info", {}).get("experience", [])
        summary = resume.get("parsed_info", {}).get("summary", "")
        
        response += f"**{name}**\n"
        response += f"  • **Skills**: {len(skills)} total"
        
        if skills:
            top_skills = skills[:4]
            response += f" ({', '.join(top_skills)}{'...' if len(skills) > 4 else ''})"
        response += "\n"
        
        response += f"  • **Experience**: {len(experience)} role(s) listed\n"
        
        if summary:
            # Truncate summary for clean display
            clean_summary = summary[:120] + "..." if len(summary) > 120 else summary
            response += f"  • **Summary**: {clean_summary}\n"
        
        response += "\n"
    
    return response.strip()
