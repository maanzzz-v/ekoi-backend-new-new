#!/usr/bin/env python3
"""Complete end-to-end test of JD workflow showing all steps and data flow."""

import sys
sys.path.append('./src')
import asyncio
import tempfile
import os
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

async def check_database_state():
    """Check the current state of MongoDB and Pinecone."""
    print("🔍 CHECKING DATABASE STATE")
    print("=" * 60)
    
    try:
        # Check MongoDB collections
        print("📊 MongoDB Collections:")
        
        # Check resumes collection
        resumes_collection = db_manager.get_collection("resumes")
        resume_count = await resumes_collection.count_documents({})
        print(f"   Resumes collection: {resume_count} documents")
        
        # Get some sample resume IDs
        sample_resumes = await resumes_collection.find({}, {"_id": 1, "file_name": 1}).limit(5).to_list(length=5)
        print(f"   Sample resume IDs:")
        for resume in sample_resumes:
            print(f"     - {resume['_id']} ({resume.get('file_name', 'Unknown')})")
        
        # Check sessions collection
        sessions_collection = db_manager.get_collection("sessions")
        session_count = await sessions_collection.count_documents({})
        print(f"   Sessions collection: {session_count} documents")
        
        # Check JD collection
        jd_collection = db_manager.get_collection("job_descriptions")
        jd_count = await jd_collection.count_documents({})
        print(f"   Job descriptions collection: {jd_count} documents")
        
        # Check Pinecone vectors
        print(f"\n🔗 Pinecone Vector Database:")
        index_stats = await vector_manager.get_index_stats()
        print(f"   Total vectors: {index_stats.get('total_vector_count', 0)}")
        print(f"   Index dimension: {index_stats.get('dimension', 'Unknown')}")
        
        return {
            "mongodb_resumes": resume_count,
            "mongodb_sessions": session_count,
            "mongodb_jds": jd_count,
            "pinecone_vectors": index_stats.get('total_vector_count', 0),
            "sample_resume_ids": [str(r['_id']) for r in sample_resumes]
        }
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return {}

async def investigate_missing_documents():
    """Investigate why documents are not found in MongoDB."""
    print("\n🕵️ INVESTIGATING MISSING DOCUMENTS")
    print("=" * 60)
    
    try:
        # Query some vectors from Pinecone
        print("1. Querying Pinecone vectors...")
        query_vector = [0.1] * 1536  # Dummy vector for querying
        vector_results = await vector_manager.query_vectors(
            vector=query_vector,
            top_k=10,
            include_metadata=True
        )
        
        print(f"   Found {len(vector_results)} vectors in Pinecone")
        
        # Check if the documents exist in MongoDB
        print("\n2. Checking corresponding MongoDB documents...")
        resumes_collection = db_manager.get_collection("resumes")
        
        missing_count = 0
        found_count = 0
        
        for i, result in enumerate(vector_results[:10]):
            vector_id = result.get('id')
            metadata = result.get('metadata', {})
            document_id = metadata.get('document_id')
            
            print(f"\n   Vector {i+1}:")
            print(f"     Vector ID: {vector_id}")
            print(f"     Document ID: {document_id}")
            
            if document_id:
                # Try to find the document in MongoDB
                try:
                    from bson import ObjectId
                    doc = await resumes_collection.find_one({"_id": ObjectId(document_id)})
                    if doc:
                        print(f"     ✅ Document found: {doc.get('file_name', 'Unknown')}")
                        found_count += 1
                    else:
                        print(f"     ❌ Document NOT found in MongoDB")
                        missing_count += 1
                except Exception as e:
                    print(f"     ❌ Error checking document: {e}")
                    missing_count += 1
            else:
                print(f"     ⚠️  No document_id in metadata")
        
        print(f"\n📊 Summary:")
        print(f"   Documents found: {found_count}")
        print(f"   Documents missing: {missing_count}")
        print(f"   Missing percentage: {(missing_count / (found_count + missing_count) * 100):.1f}%")
        
        return missing_count, found_count
        
    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        return 0, 0

async def test_complete_jd_workflow():
    """Test the complete JD workflow from start to finish."""
    print("\n🎯 COMPLETE JD WORKFLOW TEST")
    print("=" * 60)
    
    workflow_data = {}
    
    try:
        # Initialize services
        print("STEP 1: Initializing services...")
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        jd_service.set_vector_manager(vector_manager)
        print("   ✅ All services initialized")
        
        # Check database state first
        db_state = await check_database_state()
        workflow_data['database_state'] = db_state
        
        # Investigate missing documents
        missing, found = await investigate_missing_documents()
        workflow_data['missing_docs'] = missing
        workflow_data['found_docs'] = found
        
        # Create a session
        print("\nSTEP 2: Creating session...")
        session = await session_service.create_session(
            title="Complete Workflow Test",
            initial_message="Testing complete JD workflow"
        )
        session_id = session.id
        workflow_data['session_id'] = session_id
        print(f"   ✅ Session created: {session_id}")
        
        # Create and upload JD
        print("\nSTEP 3: Uploading Job Description...")
        test_jd_content = """
Senior Full Stack Developer Position

We are looking for an experienced Full Stack Developer to join our team.

REQUIRED SKILLS:
- 5+ years of Python programming experience
- Strong experience with Django or Flask frameworks
- Frontend development with React.js or Angular
- RESTful API design and development
- Database experience (PostgreSQL, MongoDB)
- Version control with Git
- AWS cloud services experience
- Docker containerization knowledge

PREFERRED QUALIFICATIONS:
- Bachelor's degree in Computer Science
- Experience with microservices architecture
- CI/CD pipeline setup and management
- Machine learning or data science background
- Startup or agile development environment experience

RESPONSIBILITIES:
- Design and develop scalable web applications
- Collaborate with cross-functional teams
- Mentor junior developers
- Participate in code reviews and technical discussions

We offer competitive salary, equity options, and remote work flexibility.
"""
        
        mock_jd_file = MockUploadFile("senior_fullstack_developer.txt", test_jd_content)
        
        jd_result = await jd_service.process_jd_file(mock_jd_file, session_id)
        jd_id = jd_result['jd_id']
        workflow_data['jd_upload'] = jd_result
        
        print(f"   ✅ JD uploaded:")
        print(f"      JD ID: {jd_id}")
        print(f"      File processed: {jd_result.get('processed', False)}")
        print(f"      Text length: {len(jd_result.get('extracted_text', ''))}")
        
        # Search for matching candidates
        print("\nSTEP 4: Searching for matching candidates...")
        search_results = await jd_service.search_resumes_by_jd(session_id, top_k=15)
        
        total_results = search_results['total_results']
        matches = search_results['matches']
        workflow_data['search_results'] = {
            'total': total_results,
            'jd_id': search_results['jd_id'],
            'match_count': len(matches)
        }
        
        print(f"   📊 Search completed:")
        print(f"      Total candidates found: {total_results}")
        print(f"      Matches returned: {len(matches)}")
        print(f"      JD used: {search_results['jd_id']}")
        
        # Show top candidates with detailed info
        print(f"\n   🏆 Top Matching Candidates:")
        for i, match in enumerate(matches[:8], 1):
            # Handle different match formats
            if hasattr(match, 'extracted_info'):
                name = match.extracted_info.name if match.extracted_info else "Unknown"
                file_name = match.file_name
                score = match.score
                match_id = match.id
            else:
                name = match.get('extracted_info', {}).get('name', 'Unknown') if match.get('extracted_info') else 'Unknown'
                file_name = match.get('file_name', 'Unknown')
                score = match.get('score', 0)
                match_id = match.get('id', 'Unknown')
            
            print(f"      {i}. {name}")
            print(f"         File: {file_name}")
            print(f"         Score: {score:.3f}")
            print(f"         ID: {match_id}")
        
        # Check stored session results for download
        print(f"\nSTEP 5: Checking stored results for download...")
        stored_results = await jd_service.get_session_search_results(session_id)
        
        if stored_results:
            jd_search_data = stored_results.get("jd_search_results", {})
            stored_matches = jd_search_data.get("matches", [])
            workflow_data['download_ready'] = {
                'available': True,
                'count': len(stored_matches),
                'timestamp': jd_search_data.get('timestamp'),
                'jd_filename': jd_search_data.get('jd_filename')
            }
            
            print(f"   ✅ Results stored for download:")
            print(f"      Candidates available: {len(stored_matches)}")
            print(f"      Storage timestamp: {jd_search_data.get('timestamp')}")
            print(f"      JD filename: {jd_search_data.get('jd_filename')}")
            
            # Show what would be downloaded
            print(f"\n   📦 Download Preview (first 5):")
            for i, stored_match in enumerate(stored_matches[:5], 1):
                name = stored_match.get('extracted_info', {}).get('name', 'Unknown') if stored_match.get('extracted_info') else 'Unknown'
                file_name = stored_match.get('file_name', 'Unknown')
                score = stored_match.get('score', 0)
                print(f"      {i}. {name} - {file_name} (Score: {score:.3f})")
                
        else:
            workflow_data['download_ready'] = {'available': False, 'count': 0}
            print(f"   ❌ No results stored for download")
        
        # Test chatbot context preparation
        print(f"\nSTEP 6: Testing chatbot context...")
        
        # Simulate what gets sent to chatbot
        chatbot_context = {
            'session_id': session_id,
            'jd_uploaded': True,
            'jd_filename': mock_jd_file.filename,
            'candidates_found': total_results,
            'top_candidates': []
        }
        
        # Prepare top candidates info for chatbot
        for i, match in enumerate(matches[:5], 1):
            if hasattr(match, 'extracted_info'):
                candidate_info = {
                    'rank': i,
                    'name': match.extracted_info.name if match.extracted_info else "Unknown",
                    'file_name': match.file_name,
                    'score': round(match.score, 3),
                    'skills': match.extracted_info.skills if match.extracted_info else [],
                    'experience': match.extracted_info.experience if match.extracted_info else []
                }
            else:
                candidate_info = {
                    'rank': i,
                    'name': match.get('extracted_info', {}).get('name', 'Unknown') if match.get('extracted_info') else 'Unknown',
                    'file_name': match.get('file_name', 'Unknown'),
                    'score': round(match.get('score', 0), 3),
                    'skills': match.get('extracted_info', {}).get('skills', []) if match.get('extracted_info') else [],
                    'experience': match.get('extracted_info', {}).get('experience', []) if match.get('extracted_info') else []
                }
            
            chatbot_context['top_candidates'].append(candidate_info)
        
        workflow_data['chatbot_context'] = chatbot_context
        
        print(f"   ✅ Chatbot context prepared:")
        print(f"      Session linked: {chatbot_context['session_id']}")
        print(f"      JD processed: {chatbot_context['jd_uploaded']}")
        print(f"      Candidates to discuss: {len(chatbot_context['top_candidates'])}")
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"🎉 COMPLETE WORKFLOW TEST FINISHED!")
        print(f"📊 FINAL SUMMARY:")
        print(f"   Session ID: {session_id}")
        print(f"   JD uploaded: ✅ {jd_id}")
        print(f"   Candidates found: {total_results}")
        print(f"   Ready for download: {len(stored_matches) if stored_results else 0}")
        print(f"   Chatbot context: ✅ Prepared")
        print(f"   Missing documents: {missing} out of {missing + found}")
        
        if total_results >= 8:
            print(f"   ✅ WORKFLOW SUCCESS: {total_results} candidates available!")
        else:
            print(f"   ⚠️  Limited results: Only {total_results} candidates found")
        
        # Return comprehensive workflow data
        return workflow_data
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return workflow_data
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    print("🚀 STARTING COMPLETE JD WORKFLOW ANALYSIS")
    print("=" * 80)
    
    result = asyncio.run(test_complete_jd_workflow())
    
    print(f"\n" + "=" * 80)
    print(f"📋 WORKFLOW DATA SUMMARY:")
    print(json.dumps(result, indent=2, default=str))
    print(f"=" * 80)
