"""
DETAILED SCORING EXAMPLE: JD Upload + Resume Matching

This example shows exactly how scores are calculated when you upload a JD 
and search for matching resumes, including weighted scoring.
"""

# ====================================================================================
# EXAMPLE JOB DESCRIPTION (What you upload)
# ====================================================================================

EXAMPLE_JD = """
Senior Python Developer - Tech Company

We are looking for a Senior Python Developer with 5+ years of experience.

Requirements:
- Bachelor's degree in Computer Science or related field
- 5+ years of experience in Python development
- Strong experience with Django or Flask frameworks
- Experience with RESTful API development
- Knowledge of PostgreSQL and MongoDB databases
- Familiarity with AWS cloud services
- Experience with Docker and containerization
- Understanding of CI/CD pipelines

Preferred:
- Master's degree preferred
- Experience with React.js for full-stack development
- Knowledge of machine learning libraries
- Experience in a startup environment
"""

# ====================================================================================
# EXAMPLE RESUME (What gets matched)
# ====================================================================================

EXAMPLE_RESUME = """
John Smith
Senior Software Engineer
Email: john.smith@email.com

SUMMARY:
Experienced Senior Software Engineer with 7 years of professional experience in 
Python development and full-stack web applications. Expertise in Django, Flask, 
and modern web technologies. Strong background in cloud deployment and DevOps practices.

EDUCATION:
Master of Science in Computer Science
University of Technology (2016-2018)

Bachelor of Science in Computer Science  
Tech University (2012-2016)

EXPERIENCE:
Senior Software Engineer | TechCorp | 2021 - Present
- Lead development of microservices using Python and Django
- Implemented RESTful APIs serving 100k+ daily requests
- Managed PostgreSQL and MongoDB databases
- Deployed applications on AWS using Docker containers

Software Engineer | StartupXYZ | 2018 - 2021  
- Developed full-stack applications using Python/Django and React
- Built CI/CD pipelines using Jenkins and GitLab
- Optimized database queries improving performance by 40%

SKILLS:
Python, Django, Flask, JavaScript, React.js, PostgreSQL, MongoDB, 
AWS, Docker, Kubernetes, Git, CI/CD, REST APIs, Machine Learning
"""

# ====================================================================================
# STEP-BY-STEP SCORING PROCESS
# ====================================================================================

"""
STEP 1: VECTOR SIMILARITY SCORING (Primary Score)
===============================================

1.1) JD Text → LLM Embeddings (OpenAI text-embedding-ada-002)
    - JD gets converted to 1536-dimensional vector
    - Captures semantic meaning of job requirements

1.2) Resume Text → LLM Embeddings (stored during upload)
    - Resume chunks converted to 1536-dimensional vectors
    - Stored in Pinecone vector database

1.3) Cosine Similarity Calculation
    similarity = dot_product(jd_vector, resume_vector) / (||jd_vector|| * ||resume_vector||)
    
    For our example:
    Vector Similarity Score = 0.847  (84.7% semantic similarity)
"""

# ====================================================================================
# STEP 2: WEIGHTED SCORING BREAKDOWN
# ====================================================================================

"""
STEP 2: WEIGHTED COMPONENT SCORING
==================================

Default Weightage Parameters:
- education: 0.25      (25% weight)
- skill_match: 0.35    (35% weight)  
- experience: 0.25     (25% weight)
- domain_relevance: 0.15 (15% weight)
"""

# Education Score Calculation
EDUCATION_SCORING = {
    "analysis": {
        "resume_education": ["Master of Science in Computer Science", "Bachelor of Science in Computer Science"],
        "jd_requirement": "Bachelor's degree in Computer Science (Master's preferred)",
        "education_level_score": 0.8,  # Masters = 0.8 base score
        "field_relevance_bonus": 1.2,  # CS field matches job requirement (+20%)
        "requirement_match_bonus": 1.3, # Exceeds minimum requirement (+30%)
        "raw_score": 0.8 * 1.2 * 1.3,  # 1.248
        "normalized_score": 1.0,        # Capped at 1.0
        "weighted_score": 1.0 * 0.25    # 0.25
    }
}

# Skill Matching Score Calculation  
SKILL_MATCHING = {
    "analysis": {
        "jd_skills": ["python", "django", "flask", "postgresql", "mongodb", "aws", "docker", "ci/cd"],
        "resume_skills": ["python", "django", "flask", "postgresql", "mongodb", "aws", "docker", "kubernetes", "ci/cd", "react.js", "machine learning"],
        "direct_matches": 8,           # Direct skill overlaps
        "total_jd_skills": 8,          # Skills required in JD
        "skill_ratio": 8/8,            # 1.0 (100% match)
        "bonus_skills": 3,             # React, Kubernetes, ML (extras)
        "raw_score": 1.0,              # Perfect skill alignment
        "weighted_score": 1.0 * 0.35   # 0.35
    }
}

# Experience Score Calculation
EXPERIENCE_SCORING = {
    "analysis": {
        "jd_requirement": "5+ years",
        "resume_experience": "7 years (2018-2025)",
        "required_years": 5,
        "actual_years": 7,
        "base_score": 0.8,             # Meets requirement
        "excess_bonus": (7-5)/5 * 0.2, # 0.08 for 2 extra years
        "senior_bonus": 0.1,           # "Senior" title bonus (+10%)
        "raw_score": 0.8 + 0.08 + 0.1, # 0.98
        "normalized_score": 0.98,       # Within bounds
        "weighted_score": 0.98 * 0.25   # 0.245
    }
}

# Domain Relevance Score Calculation
DOMAIN_RELEVANCE = {
    "analysis": {
        "jd_domain": "software_engineering",
        "domain_keywords": ["software", "development", "programming", "engineer"],
        "domain_technologies": ["python", "django", "api", "database"],
        "keyword_matches": 4,           # All domain keywords found
        "tech_matches": 4,              # All tech keywords found  
        "keyword_score": 4/4 * 0.6,    # 0.6
        "tech_score": 4/4 * 0.4,       # 0.4
        "raw_score": 0.6 + 0.4,        # 1.0
        "weighted_score": 1.0 * 0.15    # 0.15
    }
}

# ====================================================================================
# STEP 3: FINAL SCORE CALCULATION
# ====================================================================================

FINAL_SCORING = {
    "components": {
        "education_weighted": 0.25,      # 25% of total
        "skill_weighted": 0.35,          # 35% of total  
        "experience_weighted": 0.245,     # 24.5% of total
        "domain_weighted": 0.15          # 15% of total
    },
    "calculations": {
        "total_weighted_score": 0.25 + 0.35 + 0.245 + 0.15,  # 0.995
        "original_vector_score": 0.847,                        # From vector similarity
        "final_score": 0.995,                                  # Weighted score (used for ranking)
        "confidence_level": "excellent"                        # >0.9 = excellent match
    }
}

# ====================================================================================
# STEP 4: SCORE INTERPRETATION
# ====================================================================================

SCORE_INTERPRETATION = {
    "final_weighted_score": 0.995,
    "meaning": "Exceptional match - candidate exceeds all requirements",
    "breakdown_explanation": {
        "education": "Perfect match - Master's in CS exceeds Bachelor's requirement",
        "skills": "100% skill alignment - has all required + bonus skills",
        "experience": "Exceeds requirement - 7 years vs 5 required + senior level",
        "domain": "Perfect domain fit - software engineering background"
    },
    "ranking": "Top candidate - should be first in results",
    "hiring_recommendation": "Strong hire - meets and exceeds all criteria"
}

# ====================================================================================
# COMPARISON WITH OTHER CANDIDATES
# ====================================================================================

CANDIDATE_COMPARISON = [
    {
        "name": "John Smith (our example)",
        "final_score": 0.995,
        "rank": 1,
        "status": "Excellent match"
    },
    {
        "name": "Jane Doe", 
        "final_score": 0.876,
        "rank": 2,
        "status": "Very good match - Bachelor's, 6 years exp, some skills missing"
    },
    {
        "name": "Bob Wilson",
        "final_score": 0.734,
        "rank": 3, 
        "status": "Good match - meets minimum requirements"
    },
    {
        "name": "Alice Cooper",
        "final_score": 0.623,
        "rank": 4,
        "status": "Moderate match - junior level, some skills gaps"
    }
]

print("="*80)
print("RESUME SCORING DETAILED BREAKDOWN")
print("="*80)

print(f"Original Vector Similarity: {FINAL_SCORING['calculations']['original_vector_score']}")
print(f"Final Weighted Score: {FINAL_SCORING['calculations']['final_score']}")
print(f"Confidence Level: {FINAL_SCORING['calculations']['confidence_level']}")

print("\nComponent Breakdown:")
print(f"• Education (25%): {EDUCATION_SCORING['analysis']['weighted_score']}")
print(f"• Skills (35%): {SKILL_MATCHING['analysis']['weighted_score']}")  
print(f"• Experience (25%): {EXPERIENCE_SCORING['analysis']['weighted_score']}")
print(f"• Domain (15%): {DOMAIN_RELEVANCE['analysis']['weighted_score']}")

print(f"\nTotal Weighted Score: {sum([0.25, 0.35, 0.245, 0.15])}")
