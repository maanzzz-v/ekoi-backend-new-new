"""Chat-based resume search API endpoints."""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter

from models.schemas import ChatRequest, ChatResponse, ResumeMatch
from services.rag_service import rag_service
from exceptions.custom_exceptions import create_http_exception

logger = logging.getLogger(__name__)

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
