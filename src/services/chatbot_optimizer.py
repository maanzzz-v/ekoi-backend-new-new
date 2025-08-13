"""Chatbot optimization service for clean UI responses and refined interactions."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from services.enhanced_rag_service import enhanced_rag_service
from models.schemas import ResumeMatch, ChatMessage, MessageType

logger = logging.getLogger(__name__)


class ChatbotOptimizationService:
    """Service for optimizing chatbot responses for UI display and user experience."""

    def __init__(self):
        self.response_templates = {
            "greeting": {
                "patterns": ["hello", "hi", "hey", "good morning", "good afternoon"],
                "responses": [
                    "👋 **Hello!** I'm your AI recruitment assistant. I can help you find the perfect candidates by searching through resumes.\n\n**Try asking me:**\n• 'Find Python developers with 5+ years experience'\n• 'Show me frontend developers who know React'\n• 'I need a senior data scientist'",
                    "🎯 **Hi there!** Ready to find your next great hire? I can search through candidate profiles using natural language.\n\n**Example searches:**\n• 'Looking for DevOps engineers with AWS experience'\n• 'Find full-stack developers for a startup'\n• 'Show me candidates with machine learning skills'"
                ]
            },
            "help": {
                "patterns": ["help", "how to", "what can", "commands", "instructions"],
                "responses": [
                    "🔍 **I can help you find candidates!** Here's what I do:\n\n**Search Capabilities:**\n• Natural language candidate search\n• Skill-based filtering\n• Experience level matching\n• Industry-specific searches\n\n**Example queries:**\n• 'Find senior React developers'\n• 'Show me Python engineers with AI experience'\n• 'I need full-stack developers for fintech'\n\n**Follow-up questions:**\n• 'Why was this candidate selected?'\n• 'Compare these candidates'\n• 'Who has the most experience?'"
                ]
            },
            "capabilities": {
                "patterns": ["what can you do", "features", "abilities", "functions"],
                "responses": [
                    "🚀 **My capabilities include:**\n\n**🔍 Smart Search:**\n• Semantic understanding of job requirements\n• Skill synonym recognition (JS = JavaScript)\n• Experience level detection\n• Multi-faceted candidate matching\n\n**🎯 Intelligent Analysis:**\n• Candidate strength assessment\n• Skill gap identification\n• Cultural fit evaluation\n• Experience comparison\n\n**💬 Conversational:**\n• Follow-up question answering\n• Context-aware responses\n• Search refinement suggestions\n• Natural language interaction"
                ]
            }
        }
        
        self.conversation_starters = [
            "What type of role are you looking to fill today?",
            "Tell me about the ideal candidate you're seeking.",
            "What technical skills are most important for this position?",
            "Are you looking for a specific experience level?",
            "Which technologies should the candidate be familiar with?"
        ]

    async def optimize_chat_response(
        self, 
        user_message: str, 
        matches: List[ResumeMatch], 
        metadata: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize chat response for clean UI display and better user experience.
        
        Returns optimized response with structured data for UI components.
        """
        logger.info(f"Optimizing chat response for: '{user_message[:50]}...'")
        
        # Check for special conversation patterns first
        special_response = self._handle_special_patterns(user_message)
        if special_response:
            return special_response
        
        # Generate base response using enhanced RAG
        base_response = await enhanced_rag_service.generate_intelligent_response(
            user_message, matches, metadata
        )
        
        # Structure the response for UI optimization
        optimized_response = {
            "message": self._clean_response_formatting(base_response),
            "ui_components": self._extract_ui_components(matches, metadata),
            "conversation_flow": self._suggest_conversation_flow(user_message, matches, metadata),
            "quick_actions": self._generate_quick_actions(matches, metadata),
            "metadata": {
                "response_type": self._classify_response_type(user_message, matches),
                "confidence_level": self._calculate_confidence_level(matches, metadata),
                "search_quality": metadata.get("result_quality", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return optimized_response

    def _handle_special_patterns(self, message: str) -> Optional[Dict[str, Any]]:
        """Handle special conversation patterns like greetings, help requests."""
        message_lower = message.lower().strip()
        
        for pattern_type, pattern_info in self.response_templates.items():
            if any(pattern in message_lower for pattern in pattern_info["patterns"]):
                import random
                response_text = random.choice(pattern_info["responses"])
                
                return {
                    "message": response_text,
                    "ui_components": {
                        "show_search_suggestions": True,
                        "highlight_capabilities": True,
                        "candidate_cards": []
                    },
                    "conversation_flow": {
                        "next_suggestions": self.conversation_starters[:3],
                        "flow_type": pattern_type
                    },
                    "quick_actions": [
                        {"label": "Search Python developers", "query": "Find Python developers with 3+ years experience"},
                        {"label": "Search Frontend engineers", "query": "Show me React developers"},
                        {"label": "Search Data scientists", "query": "Find data scientists with ML experience"}
                    ],
                    "metadata": {
                        "response_type": "special_pattern",
                        "pattern_type": pattern_type,
                        "confidence_level": "high",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
        
        return None

    def _clean_response_formatting(self, response: str) -> str:
        """Clean and optimize response formatting for UI display."""
        # Remove excessive whitespace
        cleaned = " ".join(response.split())
        
        # Ensure consistent emoji spacing
        import re
        cleaned = re.sub(r'([🎯🔍📊✅⚡🚀💪📈⚖️🏢🎨☁️👥🔧💻])\s*', r'\1 ', cleaned)
        
        # Clean up bullet points for better UI rendering
        cleaned = cleaned.replace('•', '•')
        cleaned = cleaned.replace('*', '•')
        
        return cleaned.strip()

    def _extract_ui_components(self, matches: List[ResumeMatch], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data for UI components."""
        components = {
            "candidate_cards": [],
            "skill_tags": [],
            "experience_chart": {},
            "quality_indicators": {},
            "search_insights": {}
        }
        
        # Generate candidate cards for UI
        for i, match in enumerate(matches[:5]):  # Top 5 for UI display
            card_data = {
                "id": match.id,
                "rank": i + 1,
                "score": round(match.score, 3),
                "name": "Unknown",
                "title": "Candidate",
                "skills": [],
                "experience_summary": "",
                "match_highlights": [],
                "file_name": match.file_name if hasattr(match, 'file_name') else f"resume_{i+1}.pdf"
            }
            
            if match.extracted_info:
                card_data["name"] = match.extracted_info.name or f"Candidate {i+1}"
                card_data["skills"] = match.extracted_info.skills[:8] if match.extracted_info.skills else []
                
                # Generate experience summary
                if match.extracted_info.experience:
                    exp_count = len(match.extracted_info.experience)
                    card_data["experience_summary"] = f"{exp_count} role{'s' if exp_count != 1 else ''} listed"
                
                # Generate match highlights
                if match.relevant_text:
                    highlights = match.relevant_text[:200] + "..." if len(match.relevant_text) > 200 else match.relevant_text
                    card_data["match_highlights"] = [highlights]
            
            components["candidate_cards"].append(card_data)
        
        # Extract skill tags from all matches
        all_skills = set()
        for match in matches:
            if match.extracted_info and match.extracted_info.skills:
                all_skills.update(match.extracted_info.skills[:5])
        
        components["skill_tags"] = list(all_skills)[:15]  # Top 15 skills
        
        # Generate experience chart data
        experience_levels = {"Junior": 0, "Mid-level": 0, "Senior": 0, "Lead": 0}
        for match in matches:
            if match.extracted_info:
                summary = getattr(match.extracted_info, 'summary', '') or ''
                if any(term in summary.lower() for term in ["senior", "sr"]):
                    experience_levels["Senior"] += 1
                elif any(term in summary.lower() for term in ["lead", "principal", "architect"]):
                    experience_levels["Lead"] += 1
                elif any(term in summary.lower() for term in ["junior", "jr", "entry"]):
                    experience_levels["Junior"] += 1
                else:
                    experience_levels["Mid-level"] += 1
        
        components["experience_chart"] = experience_levels
        
        # Quality indicators for UI
        quality = metadata.get("result_quality", {})
        components["quality_indicators"] = {
            "total_matches": len(matches),
            "high_quality": quality.get("excellent", 0),
            "average_score": round(quality.get("average_score", 0), 2),
            "consistency": round(quality.get("consistency", 0), 2)
        }
        
        # Search insights
        query_intel = metadata.get("query_intelligence", {})
        components["search_insights"] = {
            "detected_domains": query_intel.get("detected_domains", []),
            "technical_depth": query_intel.get("technical_depth", "medium"),
            "intent_confidence": round(query_intel.get("confidence", 0), 2)
        }
        
        return components

    def _suggest_conversation_flow(
        self, user_message: str, matches: List[ResumeMatch], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest next conversation steps for better user flow."""
        flow = {
            "next_suggestions": [],
            "follow_up_questions": [],
            "refinement_options": [],
            "flow_type": "search_results"
        }
        
        if matches:
            # Suggest follow-up questions based on results
            flow["follow_up_questions"] = [
                f"Why is {matches[0].extracted_info.name if matches[0].extracted_info and matches[0].extracted_info.name else 'the top candidate'} the best match?",
                "Compare the technical skills of these candidates",
                "Who has the most relevant experience?",
                "Which candidate would fit best in a startup environment?"
            ]
            
            # Suggest search refinements
            if len(matches) > 10:
                flow["refinement_options"] = [
                    "Add more specific technical requirements",
                    "Filter by years of experience",
                    "Focus on a specific technology stack"
                ]
            elif len(matches) < 3:
                flow["refinement_options"] = [
                    "Broaden the search criteria",
                    "Consider related technologies",
                    "Include junior-level candidates"
                ]
        else:
            # No results - suggest alternatives
            flow["next_suggestions"] = [
                "Try a broader search with fewer requirements",
                "Search for related skills or technologies",
                "Consider different experience levels"
            ]
            flow["flow_type"] = "no_results"
        
        return flow

    def _generate_quick_actions(self, matches: List[ResumeMatch], metadata: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate quick action buttons for the UI."""
        actions = []
        
        if matches:
            # Result-based actions
            actions.extend([
                {"label": "📧 Contact top candidate", "action": "contact", "target": matches[0].id if matches else ""},
                {"label": "📋 Compare all candidates", "action": "compare", "query": "Compare these candidates in detail"},
                {"label": "🔍 Refine search", "action": "refine", "query": ""}
            ])
            
            # Smart suggestions based on found skills
            detected_skills = set()
            for match in matches[:3]:
                if match.extracted_info and match.extracted_info.skills:
                    detected_skills.update(match.extracted_info.skills[:3])
            
            if detected_skills:
                related_searches = [
                    {"label": f"Find more {skill} experts", "action": "search", "query": f"Find candidates with {skill} expertise"}
                    for skill in list(detected_skills)[:2]
                ]
                actions.extend(related_searches)
        else:
            # No results actions
            actions.extend([
                {"label": "🔍 Try broader search", "action": "search", "query": "Find developers with relevant experience"},
                {"label": "💡 Get search tips", "action": "help", "query": "help"},
                {"label": "📝 Modify criteria", "action": "refine", "query": ""}
            ])
        
        return actions[:6]  # Limit to 6 actions for clean UI

    def _classify_response_type(self, user_message: str, matches: List[ResumeMatch]) -> str:
        """Classify the type of response for UI rendering optimization."""
        message_lower = user_message.lower()
        
        if not matches:
            return "no_results"
        elif len(matches) == 1:
            return "single_match"
        elif len(matches) <= 5:
            return "few_matches"
        elif len(matches) <= 15:
            return "multiple_matches"
        else:
            return "many_matches"

    def _calculate_confidence_level(self, matches: List[ResumeMatch], metadata: Dict[str, Any]) -> str:
        """Calculate overall confidence level for UI display."""
        if not matches:
            return "low"
        
        quality = metadata.get("result_quality", {})
        avg_score = quality.get("average_score", 0)
        excellent_count = quality.get("excellent", 0)
        
        if avg_score > 0.8 and excellent_count > 0:
            return "high"
        elif avg_score > 0.6:
            return "medium"
        else:
            return "low"

    async def optimize_followup_response(
        self, 
        question: str, 
        analysis_result: str, 
        session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize follow-up question responses for UI display."""
        return {
            "message": self._clean_response_formatting(analysis_result),
            "ui_components": {
                "show_analysis": True,
                "candidate_comparison": True,
                "detailed_view": True
            },
            "conversation_flow": {
                "next_suggestions": [
                    "Ask another follow-up question",
                    "Search for more candidates",
                    "Refine the original search"
                ],
                "flow_type": "follow_up_analysis"
            },
            "quick_actions": [
                {"label": "🔍 Find similar candidates", "action": "search", "query": "Find more candidates like these"},
                {"label": "📊 Detailed comparison", "action": "compare", "query": "Provide detailed comparison of these candidates"},
                {"label": "💼 Next steps", "action": "next", "query": "What should I do next with these candidates?"}
            ],
            "metadata": {
                "response_type": "follow_up_analysis",
                "confidence_level": "high",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    def get_conversation_starters(self) -> List[Dict[str, str]]:
        """Get conversation starter suggestions for empty chat state."""
        return [
            {"text": "Find Python developers with 5+ years experience", "category": "technical"},
            {"text": "Show me frontend developers who know React", "category": "frontend"},
            {"text": "I need a senior data scientist with ML experience", "category": "data_science"},
            {"text": "Looking for DevOps engineers with AWS experience", "category": "devops"},
            {"text": "Find full-stack developers for a startup environment", "category": "startup"},
            {"text": "Show me candidates with machine learning and Python skills", "category": "ai_ml"}
        ]

    def get_search_templates(self) -> Dict[str, List[str]]:
        """Get search templates for quick user assistance."""
        return {
            "by_technology": [
                "Find {technology} developers",
                "Show me candidates with {technology} experience",
                "I need someone who knows {technology}"
            ],
            "by_experience": [
                "Find {level} developers with {years}+ years experience",
                "Show me {level} candidates",
                "I need {level} level professionals"
            ],
            "by_role": [
                "Find {role} candidates",
                "Show me {role} professionals",
                "I need a {role} for my team"
            ],
            "by_domain": [
                "Find developers with {domain} experience",
                "Show me candidates who worked in {domain}",
                "I need someone with {domain} background"
            ]
        }


# Global chatbot optimization service
chatbot_optimizer = ChatbotOptimizationService()
