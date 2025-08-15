"""Service for weighted scoring and ranking of resumes."""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.schemas import (
    WeightageParameters, 
    ResumeMatch, 
    WeightedResumeMatch,
    ExtractedInfo
)
from utils.logger import get_logger

logger = get_logger(__name__)


class WeightedScoringService:
    """Service for calculating weighted scores for resume ranking."""
    
    def __init__(self):
        """Initialize weighted scoring service."""
        self.education_keywords = {
            "phd": {"score": 1.0, "aliases": ["doctorate", "doctoral", "ph.d", "phd"]},
            "masters": {"score": 0.8, "aliases": ["master", "masters", "msc", "mba", "ms", "m.s", "m.tech"]},
            "bachelors": {"score": 0.6, "aliases": ["bachelor", "bachelors", "bsc", "ba", "b.s", "b.tech", "be"]},
            "diploma": {"score": 0.4, "aliases": ["diploma", "certificate", "associate"]},
            "high_school": {"score": 0.2, "aliases": ["high school", "secondary", "12th", "intermediate"]}
        }
        
        self.domain_keywords = {
            "software_engineering": {
                "keywords": ["software", "development", "programming", "coding", "engineer"],
                "technologies": ["java", "python", "javascript", "react", "node", "angular", "spring"]
            },
            "data_science": {
                "keywords": ["data", "analytics", "machine learning", "ai", "statistics"],
                "technologies": ["python", "r", "sql", "pandas", "numpy", "tensorflow", "pytorch"]
            },
            "devops": {
                "keywords": ["devops", "deployment", "infrastructure", "cloud", "automation"],
                "technologies": ["docker", "kubernetes", "aws", "azure", "jenkins", "terraform"]
            },
            "frontend": {
                "keywords": ["frontend", "ui", "ux", "web design", "user interface"],
                "technologies": ["html", "css", "javascript", "react", "angular", "vue", "figma"]
            },
            "backend": {
                "keywords": ["backend", "server", "api", "database", "microservices"],
                "technologies": ["java", "python", "node", "sql", "mongodb", "spring", "express"]
            },
            "mobile": {
                "keywords": ["mobile", "android", "ios", "app development"],
                "technologies": ["swift", "kotlin", "java", "react native", "flutter", "xamarin"]
            },
            "cybersecurity": {
                "keywords": ["security", "cybersecurity", "penetration", "vulnerability", "encryption"],
                "technologies": ["kali", "metasploit", "wireshark", "burp suite", "nmap"]
            },
            "finance": {
                "keywords": ["finance", "banking", "trading", "investment", "fintech"],
                "technologies": ["excel", "bloomberg", "matlab", "r", "python", "sql"]
            }
        }
        
    def calculate_weighted_score(
        self,
        resume_match: ResumeMatch,
        weightage: WeightageParameters,
        job_description: Optional[str] = None,
        query: Optional[str] = None
    ) -> WeightedResumeMatch:
        """
        Calculate weighted score for a resume match.
        
        Args:
            resume_match: Original resume match
            weightage: Weightage parameters
            job_description: Optional job description for context
            query: Optional search query for context
            
        Returns:
            WeightedResumeMatch with detailed scoring breakdown
        """
        try:
            # Initialize score breakdown
            score_breakdown = {
                "education": 0.0,
                "skill_match": 0.0,
                "experience": 0.0,
                "domain_relevance": 0.0
            }
            
            # Combine job description and query for context
            context = ""
            if job_description:
                context += f"{job_description} "
            if query:
                context += f"{query}"
            context = context.lower()
            
            # Calculate individual component scores
            education_score = self._calculate_education_score(resume_match, context)
            skill_score = self._calculate_skill_score(resume_match, context)
            experience_score = self._calculate_experience_score(resume_match, context)
            domain_score = self._calculate_domain_score(resume_match, context)
            
            # Apply weightage
            score_breakdown["education"] = education_score * weightage.education
            score_breakdown["skill_match"] = skill_score * weightage.skill_match
            score_breakdown["experience"] = experience_score * weightage.experience
            score_breakdown["domain_relevance"] = domain_score * weightage.domain_relevance
            
            # Calculate final weighted score
            weighted_score = sum(score_breakdown.values())
            
            # Normalize the score (0.0 to 1.0)
            normalized_score = min(max(weighted_score, 0.0), 1.0)
            
            logger.debug(f"Weighted scoring for {resume_match.file_name}: {score_breakdown}")
            
            return WeightedResumeMatch(
                id=resume_match.id,
                file_name=resume_match.file_name,
                score=normalized_score,
                original_score=resume_match.score,
                weighted_score=normalized_score,
                extracted_info=resume_match.extracted_info,
                relevant_text=resume_match.relevant_text,
                score_breakdown=score_breakdown,
                weightage_applied=weightage
            )
            
        except Exception as e:
            logger.error(f"Error calculating weighted score for {resume_match.file_name}: {e}")
            # Return original match as fallback
            return WeightedResumeMatch(
                id=resume_match.id,
                file_name=resume_match.file_name,
                score=resume_match.score,
                original_score=resume_match.score,
                weighted_score=resume_match.score,
                extracted_info=resume_match.extracted_info,
                relevant_text=resume_match.relevant_text,
                score_breakdown={},
                weightage_applied=weightage
            )
    
    def _calculate_education_score(self, resume_match: ResumeMatch, context: str) -> float:
        """Calculate education component score."""
        try:
            score = 0.0
            max_score = 0.0
            
            if not resume_match.extracted_info or not resume_match.extracted_info.education:
                return 0.0
            
            # Extract education requirements from context
            required_education = self._extract_education_requirements(context)
            
            # Score each education entry
            for education in resume_match.extracted_info.education:
                education_text = str(education).lower()
                
                for edu_level, edu_data in self.education_keywords.items():
                    if any(alias in education_text for alias in edu_data["aliases"]):
                        current_score = edu_data["score"]
                        
                        # Bonus for field relevance
                        if self._is_field_relevant(education_text, context):
                            current_score *= 1.2
                        
                        # Bonus if matches required education
                        if required_education and edu_level in required_education:
                            current_score *= 1.3
                        
                        score = max(score, current_score)
                        max_score = max(max_score, current_score)
            
            # Normalize score
            return min(score / 1.5, 1.0) if score > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating education score: {e}")
            return 0.0
    
    def _calculate_skill_score(self, resume_match: ResumeMatch, context: str) -> float:
        """Calculate skill matching component score."""
        try:
            if not resume_match.extracted_info or not resume_match.extracted_info.skills:
                return 0.0
            
            resume_skills = [skill.lower() for skill in resume_match.extracted_info.skills]
            context_words = set(context.split())
            
            skill_matches = 0
            total_context_skills = 0
            
            # Direct skill matches
            for skill in resume_skills:
                skill_words = set(skill.split())
                if skill_words.intersection(context_words):
                    skill_matches += 1
            
            # Technology-specific matches
            for domain, domain_data in self.domain_keywords.items():
                domain_techs = domain_data["technologies"]
                
                for tech in domain_techs:
                    if tech in context:
                        total_context_skills += 1
                        if any(tech in skill for skill in resume_skills):
                            skill_matches += 1
            
            # Calculate skill alignment ratio
            if total_context_skills > 0:
                skill_ratio = skill_matches / total_context_skills
            else:
                # Fallback: check general skill presence
                skill_ratio = min(len(resume_skills) / 10, 1.0)  # Normalize by expected skill count
            
            return min(skill_ratio, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating skill score: {e}")
            return 0.0
    
    def _calculate_experience_score(self, resume_match: ResumeMatch, context: str) -> float:
        """Calculate experience component score."""
        try:
            if not resume_match.extracted_info:
                return 0.0
            
            # Extract required experience from context
            required_years = self._extract_experience_requirements(context)
            
            # Calculate actual experience
            actual_years = 0
            
            if resume_match.extracted_info.experience:
                # Count experience entries
                actual_years = len(resume_match.extracted_info.experience)
            
            # Also check summary for experience indicators
            if resume_match.extracted_info.summary:
                years_mentioned = re.findall(r'(\d+)[\s]*\+?[\s]*years?', 
                                           resume_match.extracted_info.summary.lower())
                if years_mentioned:
                    actual_years = max(actual_years, max(int(year) for year in years_mentioned))
            
            # Calculate experience score
            if required_years > 0:
                if actual_years >= required_years:
                    # Meets or exceeds requirements
                    score = 0.8 + min((actual_years - required_years) / required_years * 0.2, 0.2)
                else:
                    # Partial experience
                    score = (actual_years / required_years) * 0.8
            else:
                # No specific requirement, score based on overall experience
                score = min(actual_years / 5, 1.0)  # Normalize by 5 years
            
            # Bonus for senior-level experience
            if resume_match.extracted_info.summary:
                summary_lower = resume_match.extracted_info.summary.lower()
                if any(term in summary_lower for term in ["senior", "lead", "principal", "manager"]):
                    score *= 1.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating experience score: {e}")
            return 0.0
    
    def _calculate_domain_score(self, resume_match: ResumeMatch, context: str) -> float:
        """Calculate domain relevance component score."""
        try:
            score = 0.0
            
            # Get all resume text for analysis
            resume_text = ""
            if resume_match.extracted_info:
                if resume_match.extracted_info.summary:
                    resume_text += resume_match.extracted_info.summary + " "
                
                for exp in resume_match.extracted_info.experience or []:
                    resume_text += str(exp) + " "
                
                for skill in resume_match.extracted_info.skills or []:
                    resume_text += skill + " "
            
            resume_text = resume_text.lower()
            
            # Check domain relevance
            for domain, domain_data in self.domain_keywords.items():
                domain_keywords = domain_data["keywords"]
                domain_technologies = domain_data["technologies"]
                
                # Check if domain is relevant to context
                domain_in_context = any(keyword in context for keyword in domain_keywords)
                
                if domain_in_context:
                    # Check domain presence in resume
                    keyword_matches = sum(1 for keyword in domain_keywords if keyword in resume_text)
                    tech_matches = sum(1 for tech in domain_technologies if tech in resume_text)
                    
                    domain_score = (keyword_matches / len(domain_keywords) * 0.6 + 
                                  tech_matches / len(domain_technologies) * 0.4)
                    
                    score = max(score, domain_score)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating domain score: {e}")
            return 0.0
    
    def _extract_education_requirements(self, context: str) -> List[str]:
        """Extract education requirements from context."""
        requirements = []
        
        for edu_level, edu_data in self.education_keywords.items():
            if any(alias in context for alias in edu_data["aliases"]):
                requirements.append(edu_level)
        
        return requirements
    
    def _extract_experience_requirements(self, context: str) -> int:
        """Extract experience requirements from context."""
        # Look for patterns like "5+ years", "3-5 years", etc.
        patterns = [
            r'(\d+)[\s]*\+[\s]*years?',
            r'(\d+)[\s]*to[\s]*\d+[\s]*years?',
            r'(\d+)[\s]*-[\s]*\d+[\s]*years?',
            r'(\d+)[\s]*years?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, context)
            if matches:
                return max(int(match) for match in matches)
        
        return 0
    
    def _is_field_relevant(self, education_text: str, context: str) -> bool:
        """Check if education field is relevant to job context."""
        # Field relevance mapping
        field_mapping = {
            "computer": ["software", "programming", "development", "tech"],
            "engineering": ["engineer", "technical", "development"],
            "business": ["business", "management", "finance", "marketing"],
            "data": ["data", "analytics", "statistics", "science"],
            "design": ["design", "ui", "ux", "creative"]
        }
        
        for field, keywords in field_mapping.items():
            if field in education_text:
                if any(keyword in context for keyword in keywords):
                    return True
        
        return False
