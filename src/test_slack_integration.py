"""
Simple test script to send resume matches to Slack.

This script demonstrates the easiest way to send your JSON output 
(shortlisted resumes) to Slack after retrieval from vector DB.
"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.slack_notification_service import send_matches_to_slack
from models.schemas import ResumeMatch, ExtractedInfo


def create_sample_matches():
    """Create sample matches for testing (simulating your JSON output from vector DB)."""
    
    # Sample extracted info for candidate 1
    candidate1_info = ExtractedInfo(
        name="Alice Johnson",
        email="alice.johnson@example.com",
        phone="(555) 123-4567",
        skills=["Python", "Django", "AWS", "PostgreSQL", "React", "Docker"],
        experience=[
            {"description": "Senior Software Engineer | TechCorp | 2020 - Present"},
            {"description": "Software Developer | StartupInc | 2018 - 2020"}
        ],
        education=[
            {"description": "BS Computer Science | State University | 2014 - 2018"}
        ],
        summary="Experienced full-stack developer with 5+ years in Python and web development"
    )
    
    # Sample extracted info for candidate 2
    candidate2_info = ExtractedInfo(
        name="Bob Smith",
        email="bob.smith@example.com",
        phone="(555) 987-6543",
        skills=["Python", "Flask", "AWS", "MongoDB", "JavaScript", "Kubernetes"],
        experience=[
            {"description": "Lead Developer | DataSolutions | 2019 - Present"},
            {"description": "Junior Developer | WebAgency | 2017 - 2019"}
        ],
        education=[
            {"description": "MS Software Engineering | Tech Institute | 2015 - 2017"}
        ],
        summary="Python specialist with expertise in cloud technologies and microservices"
    )
    
    # Sample extracted info for candidate 3
    candidate3_info = ExtractedInfo(
        name="Carol Davis",
        email="carol.davis@example.com",
        skills=["Python", "FastAPI", "AWS", "Redis", "Vue.js", "Terraform"],
        experience=[
            {"description": "DevOps Engineer | CloudCorp | 2021 - Present"}
        ],
        summary="DevOps engineer with strong Python and infrastructure automation skills"
    )
    
    # Create ResumeMatch objects (this is your JSON output format)
    matches = [
        ResumeMatch(
            id="resume_001",
            file_name="alice_johnson_resume.pdf",
            score=0.92,
            extracted_info=candidate1_info,
            relevant_text="Senior Software Engineer with extensive Python and Django experience. Led multiple AWS deployments and full-stack development projects."
        ),
        ResumeMatch(
            id="resume_002", 
            file_name="bob_smith_resume.pdf",
            score=0.87,
            extracted_info=candidate2_info,
            relevant_text="Lead Developer specializing in Python microservices architecture. Expert in AWS cloud solutions and modern web technologies."
        ),
        ResumeMatch(
            id="resume_003",
            file_name="carol_davis_resume.pdf", 
            score=0.81,
            extracted_info=candidate3_info,
            relevant_text="DevOps Engineer with strong Python automation skills and cloud infrastructure expertise using AWS and Terraform."
        )
    ]
    
    return matches


async def test_slack_notification():
    """Test sending resume matches to Slack."""
    
    print("🚀 Testing Slack Notification Service")
    print("=" * 40)
    
    # Create sample matches (this represents your JSON output from vector DB)
    matches = create_sample_matches()
    search_query = "Find Python developers with AWS experience"
    
    # Sample metadata (from your search)
    metadata = {
        "search_intent": {
            "primary_skills": ["python", "aws"],
            "experience_level": "senior",
            "role_type": "backend"
        },
        "total_candidates_found": 15,
        "unique_candidates": 3,
        "final_results": 3
    }
    
    print(f"📊 Sending {len(matches)} shortlisted candidates to Slack...")
    print(f"🔍 Search Query: {search_query}")
    print()
    
    # Send to Slack
    success = await send_matches_to_slack(
        matches=matches,
        search_query=search_query,
        metadata=metadata
    )
    
    if success:
        print("✅ Successfully sent resume matches to Slack!")
        print("📱 Check your #test_message channel in Slack")
    else:
        print("❌ Failed to send message to Slack")
        print("🔧 Check your Slack token and channel permissions")
    
    return success


async def test_simple_message():
    """Test sending a simple message to verify Slack connection."""
    
    from services.slack_notification_service import slack_notification_service
    
    print("\n🧪 Testing simple Slack connection...")
    
    simple_message = """🤖 *Resume Indexer Test Message*
✅ Slack integration is working!
📅 This is a test from the Resume Indexer AI system."""
    
    success = await slack_notification_service.send_custom_message(simple_message)
    
    if success:
        print("✅ Simple message sent successfully!")
    else:
        print("❌ Failed to send simple message")
    
    return success


async def main():
    """Main test function."""
    
    print("🎯 Resume Indexer - Slack Integration Test")
    print("=" * 50)
    
    # Test 1: Simple connection test
    print("\n1️⃣ Testing Slack connection...")
    connection_test = await test_simple_message()
    
    if not connection_test:
        print("❌ Slack connection failed. Please check:")
        print("   • Your Slack token is correct")
        print("   • The bot has permission to post in #test_message")
        print("   • Your internet connection is working")
        return
    
    # Test 2: Send formatted resume matches
    print("\n2️⃣ Testing resume matches notification...")
    matches_test = await test_slack_notification()
    
    if matches_test:
        print("\n🎉 All tests passed! Your Slack integration is ready to use.")
        print("\n📋 To use in your code:")
        print("```python")
        print("from services.slack_notification_service import send_matches_to_slack")
        print("")
        print("# After getting matches from your RAG service")
        print("matches, metadata = await rag_service.enhanced_search(query)")
        print("")
        print("# Send to Slack")
        print("await send_matches_to_slack(matches, query, metadata)")
        print("```")
    else:
        print("\n❌ Resume matches test failed")


if __name__ == "__main__":
    """Run the test."""
    asyncio.run(main())
