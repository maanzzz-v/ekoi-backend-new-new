#!/usr/bin/env python3
"""Test script for JD upload API functionality."""

import requests
import json
import time
import sys
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_jd_upload_api():
    """Test the complete JD upload and search workflow."""
    
    print("🧪 Testing JD Upload API")
    print("=" * 50)
    
    # Step 1: Create a chat session first
    print("\n1️⃣ Creating a chat session...")
    session_data = {
        "title": "JD Test Session",
        "initial_message": "Testing JD upload functionality"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat/sessions", json=session_data)
        if response.status_code == 200:
            session_info = response.json()
            session_id = session_info["session"]["id"]
            print(f"✅ Session created successfully: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return False
    
    # Step 2: Upload JD file
    print("\n2️⃣ Uploading job description file...")
    
    jd_file_path = Path("test_job_description.txt")
    if not jd_file_path.exists():
        print(f"❌ JD file not found: {jd_file_path}")
        return False
    
    try:
        with open(jd_file_path, 'rb') as file:
            files = {
                'file': ('test_job_description.txt', file, 'text/plain')
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/jd/upload",
                params={"session_id": session_id},
                files=files
            )
            
            if response.status_code == 200:
                jd_response = response.json()
                print("✅ JD uploaded successfully!")
                print(f"📄 File: {jd_response['file_name']}")
                print(f"🔑 JD ID: {jd_response['job_description_id']}")
                print(f"📝 Extracted text preview: {jd_response['extracted_text'][:100]}...")
                jd_id = jd_response['job_description_id']
            else:
                print(f"❌ JD upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error uploading JD: {e}")
        return False
    
    # Step 3: Test JD-based resume search
    print("\n3️⃣ Testing JD-based resume search...")
    
    search_data = {
        "session_id": session_id,
        "top_k": 5,
        "filters": {}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/jd/search", json=search_data)
        
        if response.status_code == 200:
            search_response = response.json()
            print("✅ JD search completed successfully!")
            print(f"🔍 Total matches found: {search_response['total_results']}")
            print(f"⏱️ Processing time: {search_response['processing_time']:.2f}s")
            print(f"💾 Results stored in session: {search_response['search_results_stored']}")
            
            # Show top matches
            if search_response['matches']:
                print("\n📋 Top matches:")
                for i, match in enumerate(search_response['matches'][:3], 1):
                    print(f"  {i}. {match['file_name']} (Score: {match['score']:.3f})")
                    if match.get('extracted_info') and match['extracted_info'].get('name'):
                        print(f"     Candidate: {match['extracted_info']['name']}")
            else:
                print("ℹ️ No resume matches found")
                
        else:
            print(f"❌ JD search failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in JD search: {e}")
        return False
    
    # Step 4: Test getting stored search results
    print("\n4️⃣ Testing retrieval of stored search results...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/jd/session/{session_id}/results")
        
        if response.status_code == 200:
            stored_results = response.json()
            print("✅ Successfully retrieved stored search results!")
            jd_search_results = stored_results['search_results']
            print(f"📊 Stored results contain {jd_search_results['total_matches']} matches")
            print(f"📅 Search timestamp: {jd_search_results['timestamp']}")
        else:
            print(f"❌ Failed to retrieve stored results: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error retrieving stored results: {e}")
    
    # Step 5: Test follow-up questions
    print("\n5️⃣ Testing follow-up questions...")
    
    followup_questions = [
        "Why is the top candidate the best match?",
        "What are the key skills of the top 3 candidates?",
        "Who has the most Python experience?"
    ]
    
    for i, question in enumerate(followup_questions, 1):
        print(f"\n   Question {i}: {question}")
        
        followup_data = {
            "session_id": session_id,
            "question": question
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/jd/followup", json=followup_data)
            
            if response.status_code == 200:
                followup_response = response.json()
                print(f"   ✅ Answer received ({followup_response['candidates_analyzed']} candidates analyzed)")
                print(f"   💬 Answer preview: {followup_response['answer'][:150]}...")
            else:
                print(f"   ❌ Follow-up failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error in follow-up question: {e}")
    
    # Step 6: Test session information
    print("\n6️⃣ Checking session information...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/sessions/{session_id}")
        
        if response.status_code == 200:
            session_info = response.json()
            session_data = session_info['session']
            print(f"✅ Session retrieved successfully!")
            print(f"📝 Total messages: {len(session_data['messages'])}")
            print(f"💾 Has context data: {'jd_search_results' in (session_data.get('context', {}))}")
            
            # Show recent messages
            if session_data['messages']:
                print("\n📨 Recent messages:")
                for msg in session_data['messages'][-3:]:
                    msg_type = msg['type'].upper()
                    content_preview = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                    print(f"  [{msg_type}]: {content_preview}")
        else:
            print(f"❌ Failed to retrieve session: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error retrieving session: {e}")
    
    print("\n🎉 JD Upload API Test Complete!")
    print(f"🔑 Session ID for manual testing: {session_id}")
    print(f"📄 JD ID for reference: {jd_id}")
    
    return True

def test_api_documentation():
    """Test if the API documentation includes JD endpoints."""
    print("\n📚 Checking API documentation...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation is accessible at http://localhost:8000/docs")
        else:
            print(f"❌ API documentation not accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing API docs: {e}")

def test_health_check():
    """Test server health."""
    print("🏥 Checking server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Server is healthy!")
            print(f"Database: {health_data.get('database', 'Unknown')}")
            print(f"Vector DB: {health_data.get('vector_db', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in health check: {e}")

if __name__ == "__main__":
    print("🚀 JD Upload API Test Suite")
    print("============================")
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test server health first
    test_health_check()
    
    # Test API documentation
    test_api_documentation()
    
    # Run main test suite
    success = test_jd_upload_api()
    
    if success:
        print("\n✅ All tests passed! JD Upload API is working correctly.")
        print("\n🔗 Useful URLs:")
        print("   • API Docs: http://localhost:8000/docs")
        print("   • Health Check: http://localhost:8000/api/v1/health")
        print("   • Root: http://localhost:8000/")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
