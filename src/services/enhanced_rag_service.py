"""Enhanced RAG service with advanced query processing and intelligent response generation."""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from services.resume_service import resume_service
from services.rag_service import rag_service
from services.llm_service import llm_service
from controllers.agent_parameters_controller import get_agent_parameters, fetch_agent_parameters  # Assuming these functions exist
from models.schemas import ResumeMatch

logger = logging.getLogger(__name__)


class EnhancedRAGService:
    """Enhanced RAG service for intelligent query processing and response generation."""

    def __init__(self):
        self.query_templates = {
            "skill_search": [
                "find", "search", "looking for", "need", "want", "require"
            ],
            "experience_query": [
                "senior", "junior", "years", "experience", "experienced", "level"
            ],
            "comparison_query": [
                "compare", "vs", "versus", "difference", "better", "best"
            ],
            "specific_role": [
                "developer", "engineer", "architect", "analyst", "scientist", "manager"
            ]
        }
        
        # Enhanced skill mappings with context
        self.skill_contexts = {
            "frontend": {
                "primary": ["react", "angular", "vue", "javascript", "typescript"],
                "related": ["html", "css", "sass", "webpack", "redux", "nextjs"],
                "description": "Frontend development"
            },
            "backend": {
                "primary": ["python", "java", "node.js", "c#", "go", "rust"],
                "related": ["django", "flask", "spring", "express", "fastapi"],
                "description": "Backend development"
            },
            "cloud": {
                "primary": ["aws", "azure", "gcp", "docker", "kubernetes"],
                "related": ["terraform", "jenkins", "ci/cd", "devops", "lambda"],
                "description": "Cloud & DevOps"
            },
            "data": {
                "primary": ["python", "sql", "machine learning", "data science"],
                "related": ["pandas", "numpy", "tensorflow", "pytorch", "tableau"],
                "description": "Data Science & Analytics"
            },
            "mobile": {
                "primary": ["react native", "flutter", "swift", "kotlin"],
                "related": ["ios", "android", "mobile", "app development"],
                "description": "Mobile development"
            }
        }

    async def intelligent_search(
        self, 
        query: str, 
        top_k: int = 10, 
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        enable_slack_notification: bool = True
    ) -> Tuple[List[ResumeMatch], Dict[str, Any]]:
        """
        Perform intelligent search with advanced query understanding.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            filters: Additional filters
            context: Previous conversation context
            enable_slack_notification: Whether to send results to Slack after final ranking
            
        Returns:
            Tuple of (matches, enhanced_metadata)
        """
        logger.info(f"Enhanced intelligent search: '{query[:100]}...'")
        
        # Step 1: Advanced query analysis
        query_analysis = await self._analyze_query_intent(query, context)
        
        # Step 2: Generate optimized search strategy
        search_strategy = await self._create_search_strategy(query_analysis)
        
        # Step 3: Execute multi-faceted search
        matches, base_metadata = await self._execute_strategic_search(
            query, search_strategy, top_k, filters
        )
        
        # Step 4: Enhance results with intelligent insights
        enhanced_metadata = await self._enhance_search_metadata(
            query_analysis, base_metadata, matches
        )
        
        # Step 5: Apply intelligent re-ranking
        final_matches = await self._intelligent_rerank(
            query, matches, query_analysis, top_k
        )
        
        # Step 6: Send results to Slack after final ranking
        await self._send_to_slack_if_enabled(query, final_matches, enhanced_metadata, enable_slack_notification)
        
        logger.info(f"Enhanced search completed: {len(final_matches)} intelligent matches")
        return final_matches, enhanced_metadata

    async def _analyze_query_intent(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Advanced query intent analysis with context awareness."""
        query_lower = query.lower()
        
        analysis = {
            "original_query": query,
            "query_type": "general",
            "intent_confidence": 0.5,
            "skill_domains": [],
            "experience_indicators": {},
            "role_specificity": "general",
            "urgency_level": "normal",
            "search_scope": "broad",
            "context_aware": bool(context),
            "semantic_keywords": [],
            "technical_depth": "medium"
        }
        
        # Detect query type with confidence scoring
        type_scores = {}
        
        # Skill search detection
        if any(term in query_lower for term in self.query_templates["skill_search"]):
            type_scores["skill_search"] = 0.8
        
        # Experience query detection
        if any(term in query_lower for term in self.query_templates["experience_query"]):
            type_scores["experience_query"] = 0.7
        
        # Comparison query detection
        if any(term in query_lower for term in self.query_templates["comparison_query"]):
            type_scores["comparison_query"] = 0.9
        
        # Role-specific detection
        if any(term in query_lower for term in self.query_templates["specific_role"]):
            type_scores["role_specific"] = 0.6
        
        # Set primary query type
        if type_scores:
            primary_type = max(type_scores.items(), key=lambda x: x[1])
            analysis["query_type"] = primary_type[0]
            analysis["intent_confidence"] = primary_type[1]
        
        # Analyze skill domains
        for domain, skills_info in self.skill_contexts.items():
            primary_matches = sum(1 for skill in skills_info["primary"] if skill in query_lower)
            related_matches = sum(1 for skill in skills_info["related"] if skill in query_lower)
            
            if primary_matches > 0 or related_matches > 1:
                domain_score = (primary_matches * 2 + related_matches) / len(skills_info["primary"])
                analysis["skill_domains"].append({
                    "domain": domain,
                    "score": min(domain_score, 1.0),
                    "description": skills_info["description"],
                    "matched_skills": [
                        skill for skill in skills_info["primary"] + skills_info["related"]
                        if skill in query_lower
                    ][:5]
                })
        
        # Sort domains by relevance
        analysis["skill_domains"].sort(key=lambda x: x["score"], reverse=True)
        
        # Extract experience indicators
        years_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
        years_matches = re.findall(years_pattern, query_lower)
        if years_matches:
            analysis["experience_indicators"]["years_mentioned"] = int(years_matches[0])
        
        # Seniority detection
        seniority_terms = {
            "senior": ["senior", "sr", "experienced", "lead"],
            "mid": ["mid", "intermediate", "regular"],
            "junior": ["junior", "jr", "entry", "graduate", "fresh"]
        }
        
        for level, terms in seniority_terms.items():
            if any(term in query_lower for term in terms):
                analysis["experience_indicators"]["level"] = level
                break
        
        # Technical depth assessment
        technical_indicators = len([
            word for word in query_lower.split()
            if any(word in skills for skills_info in self.skill_contexts.values()
                  for skills in [skills_info["primary"], skills_info["related"]]
                  for skill in skills)
        ])
        
        if technical_indicators >= 5:
            analysis["technical_depth"] = "high"
        elif technical_indicators >= 2:
            analysis["technical_depth"] = "medium"
        else:
            analysis["technical_depth"] = "low"
        
        # Extract semantic keywords
        analysis["semantic_keywords"] = self._extract_semantic_keywords(query)
        
        return analysis

    def _extract_semantic_keywords(self, query: str) -> List[str]:
        """Extract semantically meaningful keywords from the query."""
        # Remove stop words and extract meaningful terms
        stop_words = {
            "i", "me", "my", "we", "our", "you", "your", "the", "a", "an",
            "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "from", "up", "about", "into", "through", "during", "before",
            "after", "above", "below", "over", "under", "again", "further",
            "then", "once", "here", "there", "when", "where", "why", "how",
            "all", "any", "both", "each", "few", "more", "most", "other",
            "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "can", "will", "just", "should", "now",
            "find", "search", "looking", "need", "want", "show", "get"
        }
        
        words = [
            word.strip('.,!?;:"()[]{}')
            for word in query.lower().split()
            if len(word) > 2 and word not in stop_words
        ]
        
        return words[:10]  # Return top 10 semantic keywords

    async def _create_search_strategy(self, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create an optimized search strategy based on query analysis."""
        strategy = {
            "primary_approach": "semantic",
            "fallback_approaches": ["keyword", "skill_based"],
            "domain_weights": {},
            "result_diversification": True,
            "precision_mode": False,
            "recall_enhancement": True
        }
        
        # Adjust strategy based on intent confidence
        if query_analysis["intent_confidence"] > 0.8:
            strategy["precision_mode"] = True
            strategy["result_diversification"] = False
        
        # Set domain weights for multi-domain queries
        for domain_info in query_analysis["skill_domains"]:
            strategy["domain_weights"][domain_info["domain"]] = domain_info["score"]
        
        # Adjust approach based on technical depth
        if query_analysis["technical_depth"] == "high":
            strategy["primary_approach"] = "skill_based"
        elif query_analysis["technical_depth"] == "low":
            strategy["recall_enhancement"] = True
            strategy["fallback_approaches"].append("broad_semantic")
        
        return strategy

    async def _execute_strategic_search(
        self, 
        query: str, 
        strategy: Dict[str, Any], 
        top_k: int, 
        filters: Optional[Dict[str, Any]]
    ) -> Tuple[List[ResumeMatch], Dict[str, Any]]:
        """Execute search using the optimized strategy."""
        
        # Use the existing RAG service as the base
        matches, metadata = await rag_service.enhanced_search(
            query=query, 
            top_k=top_k * 2,  # Get more results for re-ranking
            filters=filters
        )
        
        # Enhance metadata with strategy info
        metadata.update({
            "search_strategy": strategy,
            "strategic_approach": strategy["primary_approach"]
        })
        
        return matches, metadata

    async def _enhance_search_metadata(
        self, 
        query_analysis: Dict[str, Any], 
        base_metadata: Dict[str, Any], 
        matches: List[ResumeMatch]
    ) -> Dict[str, Any]:
        """Enhance search metadata with intelligent insights."""
        
        enhanced = {**base_metadata}
        
        # Add query intelligence
        enhanced["query_intelligence"] = {
            "intent_type": query_analysis["query_type"],
            "confidence": query_analysis["intent_confidence"],
            "technical_depth": query_analysis["technical_depth"],
            "detected_domains": [d["domain"] for d in query_analysis["skill_domains"]],
            "semantic_focus": query_analysis["semantic_keywords"][:5]
        }
        
        # Add result quality assessment
        if matches:
            scores = [m.score for m in matches]
            enhanced["result_quality"] = {
                "average_score": sum(scores) / len(scores),
                "score_distribution": {
                    "excellent": sum(1 for s in scores if s > 0.8),
                    "good": sum(1 for s in scores if 0.6 < s <= 0.8),
                    "fair": sum(1 for s in scores if 0.4 < s <= 0.6),
                    "poor": sum(1 for s in scores if s <= 0.4)
                },
                "top_score": max(scores),
                "consistency": min(scores) / max(scores) if max(scores) > 0 else 0
            }
        
        # Add skill distribution analysis
        all_skills = []
        for match in matches[:10]:  # Analyze top 10
            if match.extracted_info and match.extracted_info.skills:
                all_skills.extend(match.extracted_info.skills)
        
        if all_skills:
            from collections import Counter
            skill_counts = Counter(all_skills)
            enhanced["skill_distribution"] = {
                "most_common": skill_counts.most_common(10),
                "total_unique_skills": len(skill_counts),
                "skill_diversity": len(skill_counts) / len(all_skills) if all_skills else 0
            }
        
        return enhanced

    async def _fetch_agent_parameters(self) -> List[Dict[str, Any]]:
        """Fetch agent parameters for use in re-ranking."""
        from controllers.agent_parameters_controller import fetch_agent_parameters
        return fetch_agent_parameters()

    async def _intelligent_rerank(
        self, 
        query: str, 
        matches: List[ResumeMatch], 
        query_analysis: Dict[str, Any], 
        top_k: int
    ) -> List[ResumeMatch]:
        """Re-rank matches intelligently using agent parameters."""
        agent_parameters = await self._fetch_agent_parameters()

        # Example: Use agent parameters to adjust scores
        for match in matches:
            for agent_param in agent_parameters:
                if agent_param['agent_name'] in match.file_name:
                    match.score += (
                        agent_param['parameter1'] * 0.1 +
                        agent_param['parameter2'] * 0.2 +
                        agent_param['parameter3'] * 0.3 +
                        agent_param['parameter4'] * 0.4
                    )

        # Sort matches by updated scores
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:top_k]

    async def generate_intelligent_response(
        self, 
        query: str, 
        matches: List[ResumeMatch], 
        metadata: Dict[str, Any]
    ) -> str:
        """Generate an intelligent, context-aware response."""
        
        if not matches:
            return self._generate_no_results_response(query, metadata)
        
        # Get query intelligence
        query_intel = metadata.get("query_intelligence", {})
        intent_type = query_intel.get("intent_type", "general")
        
        # Generate response based on intent
        if intent_type == "skill_search":
            return self._generate_skill_search_response(query, matches, metadata)
        elif intent_type == "experience_query":
            return self._generate_experience_response(query, matches, metadata)
        elif intent_type == "comparison_query":
            return self._generate_comparison_response(query, matches, metadata)
        else:
            return self._generate_general_response(query, matches, metadata)

    def _generate_no_results_response(self, query: str, metadata: Dict[str, Any]) -> str:
        """Generate helpful no-results response."""
        query_intel = metadata.get("query_intelligence", {})
        
        response = f"🔍 **No matches found for:** '{query}'\n\n"
        
        suggestions = []
        
        if query_intel.get("technical_depth") == "high":
            suggestions.append("Try broadening your technical requirements")
        
        if query_intel.get("detected_domains"):
            domains = query_intel["detected_domains"][:2]
            suggestions.append(f"Consider related domains: {', '.join(domains)}")
        
        if suggestions:
            response += "💡 **Suggestions:**\n"
            for suggestion in suggestions:
                response += f"  • {suggestion}\n"
        
        return response

    def _generate_skill_search_response(
        self, query: str, matches: List[ResumeMatch], metadata: Dict[str, Any]
    ) -> str:
        """Generate response for skill-based searches."""
        count = len(matches)
        quality = metadata.get("result_quality", {})
        
        response = f"🎯 **Found {count} skilled candidate{'s' if count != 1 else ''}**\n\n"
        
        if quality.get("excellent", 0) > 0:
            response += f"✨ {quality['excellent']} candidates show excellent skill alignment\n"
        
        # Highlight key skills
        skill_dist = metadata.get("skill_distribution", {})
        if skill_dist.get("most_common"):
            top_skills = [skill for skill, _ in skill_dist["most_common"][:5]]
            response += f"🔧 **Common skills**: {', '.join(top_skills)}\n"
        
        return response

    def _generate_experience_response(
        self, query: str, matches: List[ResumeMatch], metadata: Dict[str, Any]
    ) -> str:
        """Generate response for experience-focused queries."""
        count = len(matches)
        
        response = f"📈 **Found {count} candidate{'s' if count != 1 else ''} matching experience criteria**\n\n"
        
        # Analyze experience levels in results
        experience_levels = {"senior": 0, "mid": 0, "junior": 0}
        
        for match in matches[:5]:
            if match.extracted_info:
                summary = getattr(match.extracted_info, 'summary', '') or ''
                summary_lower = summary.lower()
                
                if any(term in summary_lower for term in ["senior", "lead", "principal"]):
                    experience_levels["senior"] += 1
                elif any(term in summary_lower for term in ["junior", "entry", "graduate"]):
                    experience_levels["junior"] += 1
                else:
                    experience_levels["mid"] += 1
        
        # Add experience breakdown
        if sum(experience_levels.values()) > 0:
            response += "📊 **Experience breakdown:**\n"
            for level, count in experience_levels.items():
                if count > 0:
                    response += f"  • {level.title()}: {count} candidate{'s' if count != 1 else ''}\n"
        
        return response

    def _generate_comparison_response(
        self, query: str, matches: List[ResumeMatch], metadata: Dict[str, Any]
    ) -> str:
        """Generate response for comparison queries."""
        if len(matches) < 2:
            return "⚖️ **Need at least 2 candidates for comparison** - Please search for more candidates first."
        
        response = f"⚖️ **Comparing {len(matches)} candidates**\n\n"
        
        # Quick comparison metrics
        skill_counts = []
        for match in matches[:3]:
            if match.extracted_info and match.extracted_info.skills:
                skill_counts.append(len(match.extracted_info.skills))
            else:
                skill_counts.append(0)
        
        if skill_counts:
            response += f"🔧 **Skill diversity**: {min(skill_counts)} - {max(skill_counts)} skills per candidate\n"
        
        return response

    def _generate_general_response(
        self, query: str, matches: List[ResumeMatch], metadata: Dict[str, Any]
    ) -> str:
        """Generate general response for unclear intent."""
        count = len(matches)
        quality = metadata.get("result_quality", {})
        
        response = f"📋 **Found {count} relevant candidate{'s' if count != 1 else ''}**\n\n"
        
        if quality.get("average_score", 0) > 0.7:
            response += "✅ **High quality matches** - Strong alignment with your requirements\n"
        elif quality.get("average_score", 0) > 0.5:
            response += "✅ **Good matches** - Relevant candidates identified\n"
        
        return response

    async def _send_to_slack_if_enabled(
        self, 
        query: str, 
        final_matches: List[ResumeMatch], 
        metadata: Dict[str, Any],
        enabled: bool = True
    ) -> bool:
        """
        Send final ranked results to Slack if enabled.
        
        Args:
            query: Original search query
            final_matches: Final ranked matches after re-ranking
            metadata: Enhanced search metadata
            enabled: Whether Slack notifications are enabled (default: True)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not enabled or not final_matches:
            return False
        
        try:
            # Import here to avoid circular imports and ensure it's only loaded when needed
            from services.slack_notification_service import send_matches_to_slack
            import asyncio
            
            # Send to Slack asynchronously (non-blocking)
            task = asyncio.create_task(
                send_matches_to_slack(
                    matches=final_matches,
                    search_query=query,
                    metadata=metadata
                )
            )
            
            # Log the attempt
            logger.info(f"Initiated Slack notification for {len(final_matches)} final ranked matches")
            
            # Don't wait for completion to avoid blocking the main response
            # The task will complete in the background
            return True
            
        except ImportError:
            logger.warning("Slack service not available - skipping notification")
            return False
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            return False


# Global enhanced RAG service instance
enhanced_rag_service = EnhancedRAGService()
