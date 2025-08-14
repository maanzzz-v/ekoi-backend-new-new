#!/usr/bin/env python3
"""Quick verification that JD shortlisting now works properly."""

import sys
sys.path.append('./src')
import asyncio
import requests
import tempfile
import os
from datetime import datetime

# Test via direct API calls to match user workflow
BASE_URL = "http://localhost:8000"

async def test_api_workflow():
    """Test the complete API workflow that user follows."""
    print("🎯 TESTING API WORKFLOW FOR JD SHORTLISTING")
    print("=" * 60)
    
    try:
        # Step 1: Create a session via API
        print("1. Creating session via API...")
        session_response = requests.post(f"{BASE_URL}/api/v1/sessions/create", 
                                       json={"title": "API Test Session"})
        
        if session_response.status_code != 200:
            print(f"❌ Session creation failed: {session_response.status_code}")
            return 0
            
        session_data = session_response.json()
        session_id = session_data["session"]["id"]
        print(f"   ✅ Session created: {session_id}")
        
        # Step 2: Upload JD via API
        print("2. Uploading JD via API...")
        test_jd_content = """
Senior Python Developer Job Description

We are seeking a Senior Python Developer with 5+ years of experience.

REQUIREMENTS:
- 5+ years Python programming experience
- Strong Django/Flask experience
- REST API development
- PostgreSQL database knowledge
- AWS cloud experience
- Docker containerization
- Git version control

PREFERRED:
- React.js experience
- Machine learning knowledge
- CI/CD pipeline experience
- Startup environment
"""
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(test_jd_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as file:
                files = {'file': ('test_jd.txt', file, 'text/plain')}
                upload_response = requests.post(
                    f"{BASE_URL}/api/v1/jd/upload",
                    files=files,
                    params={'session_id': session_id}
                )
            
            if upload_response.status_code != 200:
                print(f"❌ JD upload failed: {upload_response.status_code}")
                print(f"Response: {upload_response.text}")
                return 0
                
            upload_data = upload_response.json()
            print(f"   ✅ JD uploaded successfully: {upload_data.get('jd_id', 'unknown')}")
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
        
        # Step 3: Search for candidates via API
        print("3. Searching for candidates via API...")
        search_response = requests.post(
            f"{BASE_URL}/api/v1/jd/search",
            json={
                "session_id": session_id,
                "top_k": 15
            }
        )
        
        if search_response.status_code != 200:
            print(f"❌ Search failed: {search_response.status_code}")
            print(f"Response: {search_response.text}")
            return 0
            
        search_data = search_response.json()
        total_results = search_data.get("total_results", 0)
        matches = search_data.get("matches", [])
        
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
        if matches:
            print(f"\n   🏆 Top Candidates:")
            for i, match in enumerate(matches[:5], 1):
                name = match.get('extracted_info', {}).get('name', 'Unknown') if match.get('extracted_info') else 'Unknown'
                score = match.get('score', 0)
                file_name = match.get('file_name', 'Unknown')
                print(f"     {i}. {name} - {file_name} (Score: {score:.3f})")
        
        # Step 4: Test download endpoint (simulated)
        print(f"\n4. Testing download readiness...")
        download_response = requests.get(f"{BASE_URL}/api/v1/jd/download/shortlisted/{session_id}")
        
        if download_response.status_code == 200:
            print(f"   ✅ Download endpoint ready - candidates available for download")
            download_count = len(matches)  # Assuming all matches would be downloaded
        else:
            print(f"   ⚠️  Download endpoint status: {download_response.status_code}")
            download_count = 0
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"🎉 API WORKFLOW TEST COMPLETE!")
        print(f"📊 RESULTS SUMMARY:")
        print(f"   Session ID: {session_id}")
        print(f"   Candidates found: {total_results}")
        print(f"   Ready for download: {download_count}")
        
        if total_results >= 8:
            print(f"   ✅ ISSUE RESOLVED: Now finding {total_results} candidates instead of just 2!")
            print(f"   🎯 The shortlisting limitation has been fixed!")
        else:
            print(f"   ⚠️  Still need improvement: Only {total_results} candidates found")
        
        return total_results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    print("🚀 Starting server check...")
    
    # Quick server health check
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server health check failed: {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please make sure the server is running with: python src/main.py")
        exit(1)
    
    result = asyncio.run(test_api_workflow())
    print(f"\n🏁 Final result: {result} candidates found - {'FIXED!' if result >= 8 else 'Still needs work'}")
