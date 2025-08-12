"""Chat-based resume search API endpoints."""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter

from models.schemas import ChatRequest, ChatResponse, ResumeMatch
from services.resume_service import resume_service
from exceptions.custom_exceptions import create_http_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/search", response_model=ChatResponse)
async def chat_search_resumes(request: ChatRequest):
    """
    Chat-based resume search with natural language queries.

    Allows users to search for resumes using conversational queries like:
    - "Find me Python developers with 5+ years experience"
    - "Show me candidates who know React and have worked in fintech"
    - "I need a senior data scientist with ML experience"
    """
    try:
        logger.info(f"Chat search request: {request.message}")

        # Process the natural language query
        processed_query = await _process_chat_query(request.message)

        # Search for matching resumes
        matches = await resume_service.search_resumes(
            query=processed_query, top_k=request.top_k, filters=request.filters
        )

        # Generate a conversational response
        response_message = await _generate_chat_response(
            request.message, matches, processed_query
        )

        response = ChatResponse(
            message=response_message,
            query=processed_query,
            original_message=request.message,
            matches=matches,
            total_results=len(matches),
            success=True,
        )

        logger.info(f"Chat search completed with {len(matches)} matches")
        return response

    except Exception as e:
        logger.error(f"Error in chat search: {e}")
        raise create_http_exception(500, "Error occurred during chat search")


@router.post("/analyze")
async def analyze_query(message: str):
    """
    Analyze a natural language query to understand search intent.

    This endpoint helps users understand how their query will be processed.
    """
    try:
        processed_query = await _process_chat_query(message)

        # Extract key components from the query
        analysis = {
            "original_message": message,
            "processed_query": processed_query,
            "extracted_keywords": _extract_keywords(message),
            "search_intent": _analyze_search_intent(message),
            "suggestions": _get_query_suggestions(message),
        }

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise create_http_exception(500, "Error occurred during query analysis")


async def _process_chat_query(message: str) -> str:
    """
    Process natural language chat message into a search query.

    This function extracts key search terms and requirements from
    conversational text to create an effective vector search query.
    """
    # For now, we'll use a simple keyword extraction approach
    # In the future, this could be enhanced with LLM-based query processing

    # Common patterns to extract
    keywords = []

    # Technical skills
    tech_skills = [
        "python",
        "java",
        "javascript",
        "react",
        "angular",
        "vue",
        "node.js",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "machine learning",
        "data science",
        "sql",
        "mongodb",
        "postgresql",
        "ai",
        "ml",
        "deep learning",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "fastapi",
        "django",
        "flask",
        "spring",
        "hibernate",
        "microservices",
        "rest",
        "api",
        "graphql",
        "html",
        "css",
        "typescript",
        "go",
        "rust",
        "c++",
        "c#",
        ".net",
        "devops",
        "ci/cd",
        "jenkins",
        "git",
        "github",
        "gitlab",
    ]

    # Experience levels
    experience_levels = [
        "junior",
        "senior",
        "lead",
        "principal",
        "architect",
        "manager",
        "director",
        "entry level",
        "mid level",
        "experienced",
    ]

    # Industries/domains
    industries = [
        "fintech",
        "healthcare",
        "e-commerce",
        "education",
        "gaming",
        "startup",
        "enterprise",
        "saas",
        "mobile",
        "web",
        "backend",
        "frontend",
        "fullstack",
        "full stack",
    ]

    message_lower = message.lower()

    # Extract technical skills
    for skill in tech_skills:
        if skill in message_lower:
            keywords.append(skill)

    # Extract experience levels
    for level in experience_levels:
        if level in message_lower:
            keywords.append(level)

    # Extract industries
    for industry in industries:
        if industry in message_lower:
            keywords.append(industry)

    # Extract years of experience
    import re

    years_pattern = r"(\d+)\+?\s*years?"
    years_matches = re.findall(years_pattern, message_lower)
    for years in years_matches:
        keywords.append(f"{years} years experience")

    # If no specific keywords found, use the original message
    if not keywords:
        return message

    # Combine keywords into a search query
    processed_query = " ".join(keywords)

    logger.info(f"Processed query: '{message}' -> '{processed_query}'")
    return processed_query


async def _generate_chat_response(
    original_message: str, matches: List[ResumeMatch], processed_query: str
) -> str:
    """Generate a conversational response based on search results."""

    if not matches:
        return f"I couldn't find any resumes matching your request: '{original_message}'. Try using different keywords or broadening your search criteria."

    if len(matches) == 1:
        match = matches[0]
        skills = (
            ", ".join(match.extracted_info.skills[:5])
            if match.extracted_info and match.extracted_info.skills
            else "various skills"
        )
        return f"I found 1 resume that matches your criteria. The candidate has experience with {skills} and seems like a good fit for your requirements."

    top_skills = []
    if matches[0].extracted_info and matches[0].extracted_info.skills:
        top_skills = matches[0].extracted_info.skills[:3]

    skills_text = (
        f" The top candidate has experience with {', '.join(top_skills)}."
        if top_skills
        else ""
    )

    return f"I found {len(matches)} resumes that match your request.{skills_text} Here are the candidates ranked by relevance to your query."


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
