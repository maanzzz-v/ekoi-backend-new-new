#!/usr/bin/env python3
"""Test the JD upload and shortlisting process to verify the fix."""

import sys
sys.path.append('./src')
import asyncio
import tempfile
import os
from datetime import datetime

from core.database import db_manager
from core.vector_db import vector_manager
from services.resume_service import resume_service
from services.jd_service import jd_service
from services.session_service import session_service
from services.rag_service import rag_service

class MockUploadFile:
    """Mock UploadFile for testing."""
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self.content = content.encode('utf-8')
        self.size = len(self.content)
    
    async def read(self):
        return self.content

async def test_jd_shortlisting_process():
    """Test the complete JD upload and shortlisting process."""
    print("🎯 TESTING JD SHORTLISTING PROCESS")
    print("=" * 60)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        jd_service.set_vector_manager(vector_manager)
        
        # Step 1: Create a session
        print("1. Creating test session...")
        session = await session_service.create_session(
            title="Test JD Shortlisting Session",
            initial_message="Testing shortlisting with job description"
        )
        session_id = session.id
        print(f"   ✅ Session created: {session_id}")
        
        # Step 2: Create and upload a test JD
        print("2. Creating test job description...")
        test_jd_content = """
Senior Software Engineer - Python/Django

We are seeking a Senior Software Engineer with 5+ years of experience in Python development.

REQUIREMENTS:
- Bachelor's degree in Computer Science or related field
- 5+ years of experience with Python programming
- Strong experience with Django web framework
- Experience with RESTful API development
- Knowledge of PostgreSQL and database design
- Familiarity with AWS cloud services
- Experience with Docker and containerization
- Git version control experience

PREFERRED:
- Experience with React.js or modern JavaScript frameworks
- Knowledge of machine learning libraries (pandas, scikit-learn)
- Experience with CI/CD pipelines
- Startup environment experience

We offer competitive salary, equity, and remote work options.
"""
        
        mock_jd_file = MockUploadFile("senior_python_engineer.txt", test_jd_content)
        
        # Upload the JD
        jd_result = await jd_service.process_jd_file(mock_jd_file, session_id)
        print(f"   ✅ JD uploaded: {jd_result['jd_id']}")
        
        # Step 3: Search for candidates using the JD
        print("3. Searching for matching candidates...")
        search_results = await jd_service.search_resumes_by_jd(session_id, top_k=15)
        
        total_results = search_results['total_results']
        matches = search_results['matches']
        
        print(f"   📊 Search Results:")
        print(f"   Total candidates found: {total_results}")
        
        if total_results >= 10:
            print(f"   ✅ EXCELLENT: Found {total_results} candidates!")
        elif total_results >= 5:
            print(f"   ✅ GOOD: Found {total_results} candidates")
        elif total_results >= 3:
            print(f"   ⚠️  MODERATE: Found {total_results} candidates")
        else:
            print(f"   ❌ POOR: Only {total_results} candidates found")
        
        # Show top candidates
        print(f"\n   🏆 Top Candidates:")
        for i, match in enumerate(matches[:5], 1):
            candidate_name = "Unknown"
            if hasattr(match, 'extracted_info') and match.extracted_info:
                candidate_name = match.extracted_info.name or "Unknown"
            elif isinstance(match, dict) and match.get('extracted_info'):
                candidate_name = match['extracted_info'].get('name', 'Unknown')
            
            score = match.score if hasattr(match, 'score') else match.get('score', 0)
            file_name = match.file_name if hasattr(match, 'file_name') else match.get('file_name', 'Unknown')
            
            print(f"     {i}. {candidate_name} - {file_name} (Score: {score:.3f})")
        
        # Step 4: Test what would be downloaded
        print(f"\n4. Testing download preparation...")
        stored_results = await jd_service.get_session_search_results(session_id)
        if stored_results:
            download_matches = stored_results.get("jd_search_results", {}).get("matches", [])
            print(f"   Stored results: {len(download_matches)} candidates")
            print(f"   Would download: {min(len(download_matches), 10)} candidates")
            
            if len(download_matches) >= 8:
                print(f"   ✅ SUCCESS: Download would include {len(download_matches)} candidates!")
            else:
                print(f"   ❌ ISSUE: Download would only include {len(download_matches)} candidates")
        else:
            print(f"   ❌ No stored results found for download")
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"🎉 SHORTLISTING TEST COMPLETE!")
        print(f"📊 RESULTS SUMMARY:")
        print(f"   Session ID: {session_id}")
        print(f"   Candidates found: {total_results}")
        print(f"   Available for download: {len(download_matches) if stored_results else 0}")
        
        if total_results >= 8:
            print(f"   ✅ ISSUE RESOLVED: Now finding {total_results} candidates instead of just 2!")
        else:
            print(f"   ⚠️  Still need improvement: Only {total_results} candidates found")
        
        return total_results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    result = asyncio.run(test_jd_shortlisting_process())
    print(f"\n🏁 Final result: {result} candidates would be available for download")
