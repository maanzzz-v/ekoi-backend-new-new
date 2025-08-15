"""Advanced RAG (Retrieval Augmented Generation) service for intelligent resume search."""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from services.resume_service import resume_service
from models.schemas import ResumeMatch

logger = logging.getLogger(__name__)


class RAGService:
    """Service for advanced RAG-based resume search and analysis."""

    def __init__(self):
        self.skill_synonyms = {
            # Programming Languages
            "python": ["python", "py", "django", "flask", "fastapi", "pandas", "numpy"],
            "javascript": [
                "javascript",
                "js",
                "typescript",
                "ts",
                "node",
                "nodejs",
                "react",
                "angular",
                "vue",
            ],
            "java": ["java", "spring", "hibernate", "maven", "gradle"],
            "c#": ["csharp", "c#", "dotnet", ".net", "asp.net"],
            "go": ["golang", "go"],
            "rust": ["rust", "cargo"],
            "php": ["php", "laravel", "symfony", "wordpress"],
            # Frontend Technologies
            "react": ["react", "reactjs", "react.js", "jsx"],
            "angular": ["angular", "angularjs", "angular.js"],
            "vue": ["vue", "vuejs", "vue.js", "nuxt"],
            # Backend Technologies
            "nodejs": ["node", "nodejs", "node.js", "express", "nestjs"],
            "django": ["django", "python web framework"],
            "flask": ["flask", "python microframework"],
            "spring": ["spring", "spring boot", "java framework"],
            # Cloud & DevOps
            "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloud"],
            "azure": ["azure", "microsoft cloud"],
            "gcp": ["gcp", "google cloud", "google cloud platform"],
            "docker": ["docker", "containers", "containerization"],
            "kubernetes": ["kubernetes", "k8s", "container orchestration"],
            "terraform": ["terraform", "infrastructure as code", "iac"],
            # Databases
            "sql": ["sql", "mysql", "postgresql", "sqlite", "database"],
            "mongodb": ["mongodb", "mongo", "nosql", "document database"],
            "redis": ["redis", "cache", "in-memory database"],
            # Machine Learning & AI
            "machine learning": [
                "ml",
                "machine learning",
                "ai",
                "artificial intelligence",
            ],
            "deep learning": ["deep learning", "neural networks", "cnn", "rnn", "lstm"],
            "tensorflow": ["tensorflow", "tf", "keras"],
            "pytorch": ["pytorch", "torch"],
            "scikit-learn": ["sklearn", "scikit-learn", "scikit learn"],
            # Experience Levels
            "senior": ["senior", "sr", "lead", "principal", "experienced"],
            "junior": ["junior", "jr", "entry level", "graduate", "fresh"],
            "mid level": ["mid level", "intermediate", "regular"],
        }

    async def enhanced_search(
        self, query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[ResumeMatch], Dict[str, Any]]:
        """
        Perform enhanced RAG-based search with query understanding and expansion.

        Returns:
            Tuple of (matches, search_metadata)
        """
        logger.info(f"Enhanced RAG search for: '{query}'")

        # Step 1: Analyze and expand the query
        expanded_query = await self._expand_query(query)
        search_intent = self._analyze_intent(query)

        # Step 2: Generate multiple search variations for better recall
        search_variations = await self._generate_search_variations(
            expanded_query, search_intent
        )

        # Step 3: Perform searches with different query variations
        all_matches = []
        for variation in search_variations:
            matches = await resume_service.search_resumes(
                query=variation,
                top_k=top_k * 2,  # Get more results to re-rank
                filters=filters,
            )
            all_matches.extend(matches)

        # Step 4: Re-rank and deduplicate results
        final_matches = await self._rerank_matches(query, all_matches, top_k)

        # Step 5: Generate search metadata
        search_metadata = {
            "original_query": query,
            "expanded_query": expanded_query,
            "search_variations": search_variations,
            "search_intent": search_intent,
            "total_candidates_found": len(all_matches),
            "unique_candidates": len(set(m.id for m in all_matches)),
            "final_results": len(final_matches),
        }

        logger.info(f"Enhanced search completed: {len(final_matches)} final matches")
        return final_matches, search_metadata

    async def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms."""
        expanded_terms = []
        query_lower = query.lower()

        # Add original terms
        expanded_terms.append(query)

        # Add synonyms and related terms
        for skill, synonyms in self.skill_synonyms.items():
            if any(synonym in query_lower for synonym in synonyms):
                # Add the canonical skill name and related terms
                expanded_terms.extend(
                    [skill] + synonyms[:3]
                )  # Limit to avoid too much expansion

        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)

        expanded_query = " ".join(unique_terms)
        logger.info(f"Query expansion: '{query}' -> '{expanded_query}'")
        return expanded_query

    def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the search intent from the query."""
        query_lower = query.lower()

        intent = {
            "primary_skills": [],
            "experience_level": "any",
            "domain": "general",
            "role_type": "general",
            "urgency": "normal",
            "specificity": "medium",
        }

        # Extract primary skills
        for skill, synonyms in self.skill_synonyms.items():
            if any(synonym in query_lower for synonym in synonyms):
                intent["primary_skills"].append(skill)

        # Determine experience level
        if any(
            term in query_lower
            for term in ["senior", "sr", "lead", "principal", "experienced"]
        ):
            intent["experience_level"] = "senior"
        elif any(
            term in query_lower
            for term in ["junior", "jr", "entry", "graduate", "fresh"]
        ):
            intent["experience_level"] = "junior"
        elif any(term in query_lower for term in ["mid", "intermediate"]):
            intent["experience_level"] = "mid"

        # Determine domain
        if any(term in query_lower for term in ["fintech", "finance", "banking"]):
            intent["domain"] = "fintech"
        elif any(term in query_lower for term in ["healthcare", "medical", "health"]):
            intent["domain"] = "healthcare"
        elif any(term in query_lower for term in ["ecommerce", "e-commerce", "retail"]):
            intent["domain"] = "ecommerce"
        elif any(term in query_lower for term in ["gaming", "game", "entertainment"]):
            intent["domain"] = "gaming"

        # Determine role type
        if any(term in query_lower for term in ["frontend", "front-end", "ui", "ux"]):
            intent["role_type"] = "frontend"
        elif any(
            term in query_lower for term in ["backend", "back-end", "api", "server"]
        ):
            intent["role_type"] = "backend"
        elif any(
            term in query_lower for term in ["fullstack", "full-stack", "full stack"]
        ):
            intent["role_type"] = "fullstack"
        elif any(term in query_lower for term in ["devops", "sre", "infrastructure"]):
            intent["role_type"] = "devops"
        elif any(
            term in query_lower
            for term in ["data scientist", "ml engineer", "ai engineer"]
        ):
            intent["role_type"] = "data_science"

        # Determine urgency
        if any(
            term in query_lower for term in ["urgent", "asap", "immediately", "quickly"]
        ):
            intent["urgency"] = "high"

        # Determine specificity
        skill_count = len(intent["primary_skills"])
        if skill_count >= 4:
            intent["specificity"] = "high"
        elif skill_count >= 2:
            intent["specificity"] = "medium"
        else:
            intent["specificity"] = "low"

        return intent

    async def _generate_search_variations(
        self, expanded_query: str, intent: Dict[str, Any]
    ) -> List[str]:
        """Generate multiple search query variations for better recall."""
        variations = [expanded_query]

        # Add role-specific variations
        if intent["role_type"] != "general":
            role_specific = f"{intent['role_type']} developer {expanded_query}"
            variations.append(role_specific)

        # Add experience-level specific variations
        if intent["experience_level"] != "any":
            exp_specific = f"{intent['experience_level']} {expanded_query}"
            variations.append(exp_specific)

        # Add domain-specific variations
        if intent["domain"] != "general":
            domain_specific = f"{expanded_query} {intent['domain']} experience"
            variations.append(domain_specific)

        # Add skill-focused variation
        if intent["primary_skills"]:
            skill_focused = " ".join(intent["primary_skills"][:3])  # Top 3 skills
            variations.append(skill_focused)

        # Limit variations to avoid too many searches
        return variations[:4]

    async def _rerank_matches(
        self, original_query: str, matches: List[ResumeMatch], top_k: int
    ) -> List[ResumeMatch]:
        """Re-rank matches using advanced scoring."""
        if not matches:
            return []

        # Remove duplicates based on resume ID
        unique_matches = {}
        for match in matches:
            if (
                match.id not in unique_matches
                or match.score > unique_matches[match.id].score
            ):
                unique_matches[match.id] = match

        deduplicated_matches = list(unique_matches.values())

        # Enhanced scoring based on query-resume semantic similarity
        for match in deduplicated_matches:
            # Original vector similarity score
            base_score = match.score

            # Bonus for skill alignment
            skill_bonus = await self._calculate_skill_alignment_bonus(
                original_query, match
            )

            # Bonus for experience level match
            exp_bonus = self._calculate_experience_bonus(original_query, match)

            # Combined score
            match.score = base_score + (skill_bonus * 0.2) + (exp_bonus * 0.1)

        # Sort by enhanced score and return top_k
        deduplicated_matches.sort(key=lambda x: x.score, reverse=True)
        return deduplicated_matches[:top_k]

    async def _calculate_skill_alignment_bonus(
        self, query: str, match: ResumeMatch
    ) -> float:
        """Calculate bonus score based on skill alignment."""
        if not match.extracted_info or not match.extracted_info.skills:
            return 0.0

        query_lower = query.lower()
        resume_skills = [skill.lower() for skill in match.extracted_info.skills]

        alignment_score = 0.0
        for skill, synonyms in self.skill_synonyms.items():
            # Check if skill is mentioned in query
            query_mentions_skill = any(synonym in query_lower for synonym in synonyms)

            # Check if skill is in resume
            resume_has_skill = any(
                synonym in " ".join(resume_skills) for synonym in synonyms
            )

            if query_mentions_skill and resume_has_skill:
                alignment_score += 1.0

        # Normalize by number of skills mentioned in query
        query_skill_count = sum(
            1
            for skill, synonyms in self.skill_synonyms.items()
            if any(synonym in query_lower for synonym in synonyms)
        )

        if query_skill_count > 0:
            return alignment_score / query_skill_count

        return 0.0

    def _calculate_experience_bonus(self, query: str, match: ResumeMatch) -> float:
        """Calculate bonus score based on experience level alignment."""
        query_lower = query.lower()

        # Extract years of experience from query
        years_pattern = r"(\d+)\+?\s*years?"
        years_matches = re.findall(years_pattern, query_lower)

        if not years_matches:
            return 0.0

        query_years = int(years_matches[0])

        # Try to extract experience from resume text
        if match.relevant_text:
            resume_years_matches = re.findall(
                years_pattern, match.relevant_text.lower()
            )
            if resume_years_matches:
                resume_years = int(resume_years_matches[0])

                # Give bonus for matching experience range
                if abs(resume_years - query_years) <= 2:
                    return 1.0
                elif abs(resume_years - query_years) <= 5:
                    return 0.5

        return 0.0


# Global RAG service instance
rag_service = RAGService()
