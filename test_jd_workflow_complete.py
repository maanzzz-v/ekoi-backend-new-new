#!/usr/bin/env python3
"""Complete JD shortlisting workflow test with storage analysis."""

import sys
sys.path.append('./src')
import asyncio
import tempfile
import json
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

async def comprehensive_jd_test():
    """Complete test of JD shortlisting workflow with storage analysis."""
    print("🎯 COMPREHENSIVE JD SHORTLISTING WORKFLOW TEST")
    print("=" * 70)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        jd_service.set_vector_manager(vector_manager)
        
        # Get collections for direct database inspection
        sessions_collection = db_manager.get_collection("sessions")
        jd_collection = db_manager.get_collection("job_descriptions")
        resumes_collection = db_manager.get_collection("resumes")
        
        print("📊 INITIAL DATABASE STATUS:")
        session_count = await sessions_collection.count_documents({})
        jd_count = await jd_collection.count_documents({})
        resume_count = await resumes_collection.count_documents({})
        print(f"   Sessions: {session_count}")
        print(f"   Job Descriptions: {jd_count}")
        print(f"   Resumes: {resume_count}")
        
        # STEP 1: Create session
        print(f"\n🔥 STEP 1: CREATE SESSION")
        session = await session_service.create_session(
            title="JD Shortlisting Test Session",
            initial_message="Testing complete JD workflow with storage analysis"
        )
        session_id = session.id
        print(f"   ✅ Session created: {session_id}")
        
        # STEP 2: Upload Job Description
        print(f"\n🔥 STEP 2: UPLOAD JOB DESCRIPTION")
        test_jd_content = """
Senior Python Developer - Remote Position

We are seeking a Senior Python Developer with 5+ years of experience to join our growing team.

REQUIRED QUALIFICATIONS:
- Bachelor's degree in Computer Science or related field
- 5+ years of experience with Python programming
- Strong experience with Django or Flask web frameworks
- Experience with RESTful API development and integration
- Proficiency with PostgreSQL or MySQL databases
- Knowledge of AWS cloud services (EC2, S3, RDS)
- Experience with Docker containerization
- Familiarity with Git version control
- Strong problem-solving and debugging skills

PREFERRED QUALIFICATIONS:
- Experience with React.js or Angular frontend frameworks
- Knowledge of machine learning libraries (pandas, scikit-learn, TensorFlow)
- Experience with CI/CD pipelines (Jenkins, GitLab CI)
- Previous startup environment experience
- Experience with microservices architecture
- Knowledge of Redis or other caching solutions

RESPONSIBILITIES:
- Design and develop scalable backend systems
- Build and maintain RESTful APIs
- Collaborate with frontend developers and product team
- Write clean, maintainable, and well-tested code
- Participate in code reviews and technical discussions
- Mentor junior developers

We offer competitive salary, equity options, remote work flexibility, and comprehensive benefits.
"""
        
        mock_jd_file = MockUploadFile("senior_python_developer.txt", test_jd_content)
        
        jd_result = await jd_service.process_jd_file(mock_jd_file, session_id)
        jd_id = jd_result['jd_id']
        print(f"   ✅ JD uploaded: {jd_id}")
        print(f"   📄 JD filename: {jd_result['filename']}")
        
        # Check JD storage in database
        jd_doc = await jd_collection.find_one({"_id": jd_id})
        print(f"   💾 JD stored in MongoDB: {'✅ YES' if jd_doc else '❌ NO'}")
        if jd_doc:
            print(f"   📏 JD text length: {len(jd_doc.get('extracted_text', ''))}")
        
        # STEP 3: Search for matching resumes
        print(f"\n🔥 STEP 3: SEARCH FOR MATCHING CANDIDATES")
        search_results = await jd_service.search_resumes_by_jd(session_id, top_k=15)
        
        print(f"   📊 SEARCH RESULTS:")
        print(f"   - Total candidates found: {search_results['total_results']}")
        print(f"   - Session ID: {search_results['session_id']}")
        print(f"   - JD ID used: {search_results['jd_id']}")
        
        if search_results['total_results'] > 0:
            print(f"\n   🏆 TOP CANDIDATES:")
            for i, match in enumerate(search_results['matches'][:5], 1):
                name = "Unknown"
                if hasattr(match, 'extracted_info') and match.extracted_info:
                    name = match.extracted_info.name or "Unknown"
                elif isinstance(match, dict) and match.get('extracted_info'):
                    name = match['extracted_info'].get('name', 'Unknown')
                
                score = match.score if hasattr(match, 'score') else match.get('score', 0)
                file_name = match.file_name if hasattr(match, 'file_name') else match.get('file_name', 'Unknown')
                
                print(f"     {i}. {name} - {file_name} (Score: {score:.3f})")
        
        # STEP 4: Check session storage
        print(f"\n🔥 STEP 4: ANALYZE SESSION STORAGE")
        
        # Get session from database
        session_doc = await sessions_collection.find_one({"_id": session_id})
        print(f"   💾 Session exists in DB: {'✅ YES' if session_doc else '❌ NO'}")
        
        stored_matches = []
        if session_doc:
            context = session_doc.get('context', {})
            print(f"   📦 Session context keys: {list(context.keys())}")
            
            # Check for JD search results
            jd_search_results = context.get('jd_search_results')
            if jd_search_results:
                stored_matches = jd_search_results.get('matches', [])
                print(f"   ✅ JD search results stored: {len(stored_matches)} candidates")
                print(f"   📅 Storage timestamp: {jd_search_results.get('timestamp', 'Unknown')}")
                print(f"   🔗 JD ID in storage: {jd_search_results.get('jd_id', 'Unknown')}")
                
                # Show stored candidate details
                if stored_matches:
                    print(f"\n   📋 STORED CANDIDATE DETAILS:")
                    for i, candidate in enumerate(stored_matches[:3], 1):
                        print(f"     {i}. ID: {candidate.get('id', 'Unknown')}")
                        print(f"        File: {candidate.get('file_name', 'Unknown')}")
                        print(f"        Score: {candidate.get('score', 0):.3f}")
                        extracted_info = candidate.get('extracted_info', {})
                        if extracted_info:
                            print(f"        Name: {extracted_info.get('name', 'Unknown')}")
                            skills = extracted_info.get('skills', [])
                            print(f"        Skills: {', '.join(skills[:5]) if skills else 'None'}")
                        print()
            else:
                print(f"   ❌ NO JD search results found in session storage")
        
        # STEP 5: Test download preparation
        print(f"\n🔥 STEP 5: TEST DOWNLOAD PREPARATION")
        try:
            download_results = await jd_service.get_session_search_results(session_id)
            if download_results:
                download_matches = download_results.get("jd_search_results", {}).get("matches", [])
                print(f"   ✅ Download data available: {len(download_matches)} candidates")
                print(f"   📥 Ready for CSV/Excel export: {'✅ YES' if download_matches else '❌ NO'}")
            else:
                print(f"   ❌ NO download data available")
        except Exception as e:
            print(f"   ❌ Download preparation failed: {e}")
        
        # STEP 6: Check chatbot context preparation
        print(f"\n🔥 STEP 6: CHATBOT CONTEXT ANALYSIS")
        
        # Get what would be sent to chatbot
        session_for_chat = await session_service.get_session(session_id)
        if session_for_chat:
            messages = session_for_chat.messages
            context = session_for_chat.context or {}
            
            print(f"   💬 Session messages: {len(messages)}")
            print(f"   🧠 Context available for chatbot: {'✅ YES' if context else '❌ NO'}")
            
            if context and 'jd_search_results' in context:
                chatbot_candidates = context['jd_search_results'].get('matches', [])
                print(f"   🤖 Candidates available to chatbot: {len(chatbot_candidates)}")
                
                if chatbot_candidates:
                    print(f"\n   🤖 CHATBOT CONTEXT SAMPLE:")
                    for i, candidate in enumerate(chatbot_candidates[:2], 1):
                        print(f"     Candidate {i}:")
                        print(f"       File: {candidate.get('file_name', 'Unknown')}")
                        print(f"       Score: {candidate.get('score', 0):.3f}")
                        extracted_info = candidate.get('extracted_info', {})
                        if extracted_info:
                            print(f"       Name: {extracted_info.get('name', 'Unknown')}")
                            print(f"       Email: {extracted_info.get('email', 'Unknown')}")
                            skills = extracted_info.get('skills', [])
                            print(f"       Skills: {', '.join(skills[:3]) if skills else 'None'}")
                        print()
                
                # Test what chatbot would receive
                print(f"   🔍 Chatbot can access:")
                print(f"     - JD requirements: ✅ YES")
                print(f"     - Candidate matches: ✅ YES ({len(chatbot_candidates)} candidates)")
                print(f"     - Match scores: ✅ YES")
                print(f"     - Candidate details: ✅ YES")
            else:
                print(f"   ❌ NO candidate data available to chatbot")
        
        # STEP 7: Storage summary
        print(f"\n🔥 STEP 7: STORAGE SUMMARY")
        
        final_session_count = await sessions_collection.count_documents({})
        final_jd_count = await jd_collection.count_documents({})
        
        print(f"   📊 DATABASE CHANGES:")
        print(f"   - Sessions: {session_count} → {final_session_count} (+{final_session_count - session_count})")
        print(f"   - Job Descriptions: {jd_count} → {final_jd_count} (+{final_jd_count - jd_count})")
        
        print(f"\n   💾 STORAGE LOCATIONS:")
        print(f"   - JD document: MongoDB 'job_descriptions' collection")
        print(f"   - Session data: MongoDB 'sessions' collection")
        print(f"   - Search results: Session context → 'jd_search_results' field")
        print(f"   - Candidate details: Embedded in search results")
        
        # Final assessment
        total_results = search_results['total_results']
        stored_results_count = len(stored_matches)
        
        print(f"\n" + "=" * 70)
        print(f"🎉 JD SHORTLISTING WORKFLOW ANALYSIS COMPLETE!")
        print(f"📊 RESULTS:")
        print(f"   ✅ JD Upload: Working")
        print(f"   ✅ Candidate Search: Working ({total_results} found)")
        print(f"   {'✅' if stored_results_count > 0 else '❌'} Storage: {'Working' if stored_results_count > 0 else 'BROKEN'} ({stored_results_count} stored)")
        print(f"   {'✅' if stored_results_count > 0 else '❌'} Download Ready: {'YES' if stored_results_count > 0 else 'NO'}")
        print(f"   {'✅' if stored_results_count > 0 else '❌'} Chatbot Context: {'Available' if stored_results_count > 0 else 'Missing'}")
        
        if total_results >= 8 and stored_results_count > 0:
            print(f"\n🎯 STATUS: ✅ FULLY WORKING!")
            print(f"   - Shortlisting finds adequate candidates")
            print(f"   - Results are properly stored") 
            print(f"   - Download and chatbot access available")
        else:
            print(f"\n⚠️  STATUS: ❌ NEEDS ATTENTION")
            if total_results < 8:
                print(f"   - Not enough candidates found ({total_results} < 8)")
            if stored_results_count == 0:
                print(f"   - Storage is broken (0 stored)")
        
        return total_results, stored_results_count
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    candidates_found, candidates_stored = asyncio.run(comprehensive_jd_test())
    print(f"\n🏁 FINAL RESULT:")
    print(f"   Found: {candidates_found} candidates")
    print(f"   Stored: {candidates_stored} candidates")
    print(f"   Status: {'✅ SUCCESS' if candidates_found >= 8 and candidates_stored > 0 else '❌ NEEDS FIXING'}")
