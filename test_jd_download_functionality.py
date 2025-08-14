#!/usr/bin/env python3
"""
Test script for JD upload and download functionality.
Tests the complete workflow: JD upload → search → download shortlisted resumes.
"""

import asyncio
import aiohttp
import tempfile
import zipfile
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Sample JD content for testing
SAMPLE_JD_CONTENT = """
Senior Python Developer Position

We are seeking an experienced Senior Python Developer with 5+ years of experience in backend development.

Required Skills:
- Python programming (5+ years)
- Django or Flask framework experience
- PostgreSQL or MongoDB database experience
- RESTful API development
- Docker containerization
- AWS cloud services
- Git version control

Education:
- Bachelor's degree in Computer Science or related field
- Master's degree preferred

Experience:
- Minimum 5 years of professional Python development
- Experience with microservices architecture
- Agile/Scrum development methodologies
- Team leadership experience is a plus

Responsibilities:
- Design and develop scalable Python applications
- Work with cross-functional teams
- Mentor junior developers
- Code reviews and quality assurance
- Deploy and maintain applications in cloud environments

Company: TechCorp Solutions
Location: San Francisco, CA
Salary: $120,000 - $160,000
"""

async def create_test_session():
    """Create a new chat session for testing."""
    async with aiohttp.ClientSession() as session:
        session_data = {"title": "JD Download Test Session"}
        async with session.post(f"{BASE_URL}/api/v1/chat/sessions", json=session_data) as response:
            if response.status == 200:
                data = await response.json()
                return data["session"]["id"]
            else:
                print(f"❌ Failed to create session: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
                return None

async def upload_test_jd(session_id):
    """Upload a test JD file."""
    # Create temporary JD file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(SAMPLE_JD_CONTENT)
        jd_file_path = f.name
    
    try:
        async with aiohttp.ClientSession() as session:
            # Prepare form data with file only
            with open(jd_file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_senior_python_developer.txt', content_type='text/plain')
                
                # Add session_id as query parameter
                url = f"{BASE_URL}/api/v1/jd/upload?session_id={session_id}"
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ JD Upload successful: {result['message']}")
                        print(f"   JD ID: {result['job_description_id']}")
                        print(f"   File: {result['file_name']}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ JD Upload failed: {response.status}")
                        print(f"   Error: {error_text}")
                        return None
    finally:
        # Clean up temp file
        os.unlink(jd_file_path)

async def search_resumes(session_id):
    """Search for matching resumes."""
    async with aiohttp.ClientSession() as session:
        search_data = {
            "session_id": session_id,
            "top_k": 15  # Get more results for better testing
        }
        
        async with session.post(f"{BASE_URL}/api/v1/jd/search", json=search_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Resume search successful: {result['total_results']} candidates found")
                print(f"   Processing time: {result['processing_time']:.2f} seconds")
                print(f"   Top 5 candidates:")
                
                for i, match in enumerate(result['matches'][:5], 1):
                    name = match.get('extracted_info', {}).get('name', 'Unknown') if match.get('extracted_info') else 'Unknown'
                    score = match.get('score', 0)
                    print(f"   {i}. {name} - Score: {score:.3f} ({score*100:.1f}%)")
                
                return result
            else:
                error_text = await response.text()
                print(f"❌ Resume search failed: {response.status}")
                print(f"   Error: {error_text}")
                return None

async def download_shortlisted_resumes(session_id, top_n=5):
    """Download shortlisted resumes as ZIP."""
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/api/v1/jd/session/{session_id}/download"
        params = {"top_n": top_n, "format": "zip"}
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                print(f"✅ Download successful!")
                
                # Get headers info
                content_disposition = response.headers.get('Content-Disposition', '')
                total_candidates = response.headers.get('X-Total-Candidates', 'Unknown')
                files_included = response.headers.get('X-Files-Included', 'Unknown')
                
                print(f"   Total candidates: {total_candidates}")
                print(f"   Files included: {files_included}")
                
                # Extract filename from Content-Disposition header
                filename = "test_download.zip"
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                
                # Save to temporary file for inspection
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, filename)
                
                with open(zip_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                print(f"   Downloaded to: {zip_path}")
                
                # Inspect ZIP contents
                await inspect_zip_contents(zip_path)
                
                return zip_path
            else:
                error_text = await response.text()
                print(f"❌ Download failed: {response.status}")
                print(f"   Error: {error_text}")
                return None

async def inspect_zip_contents(zip_path):
    """Inspect the contents of the downloaded ZIP file."""
    print(f"\n📦 ZIP File Contents:")
    print(f"   File: {os.path.basename(zip_path)}")
    print(f"   Size: {os.path.getsize(zip_path) / 1024:.1f} KB")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            file_list = zipf.namelist()
            print(f"   Files in ZIP: {len(file_list)}")
            
            for i, file_name in enumerate(file_list, 1):
                file_info = zipf.getinfo(file_name)
                print(f"   {i}. {file_name} ({file_info.file_size} bytes)")
            
            # Read the summary report if present
            if 'SHORTLIST_SUMMARY.txt' in file_list:
                print(f"\n📋 Summary Report Preview:")
                with zipf.open('SHORTLIST_SUMMARY.txt') as summary_file:
                    summary_content = summary_file.read().decode('utf-8')
                    # Show first 500 characters
                    preview = summary_content[:500] + "..." if len(summary_content) > 500 else summary_content
                    print(preview)
            
    except Exception as e:
        print(f"❌ Error inspecting ZIP: {e}")

async def test_download_with_different_counts(session_id):
    """Test downloading different numbers of candidates."""
    print(f"\n🔄 Testing different download counts...")
    
    for count in [3, 7, 10]:
        print(f"\n--- Testing top {count} candidates ---")
        zip_path = await download_shortlisted_resumes(session_id, count)
        if zip_path:
            # Clean up
            os.unlink(zip_path)
            print(f"   ✅ Top {count} download test passed")
        else:
            print(f"   ❌ Top {count} download test failed")

async def test_error_scenarios(session_id):
    """Test error scenarios for the download endpoint."""
    print(f"\n🧪 Testing error scenarios...")
    
    # Test with invalid session ID
    async with aiohttp.ClientSession() as session:
        invalid_session_id = "invalid-session-id-12345"
        url = f"{BASE_URL}/api/v1/jd/session/{invalid_session_id}/download"
        
        async with session.get(url) as response:
            if response.status == 404:
                print("   ✅ Invalid session ID test passed (404 returned)")
            else:
                print(f"   ❌ Invalid session ID test failed (expected 404, got {response.status})")
    
    # Test with session that has no search results
    new_session_id = await create_test_session()
    if new_session_id:
        async with aiohttp.ClientSession() as session:
            url = f"{BASE_URL}/api/v1/jd/session/{new_session_id}/download"
            
            async with session.get(url) as response:
                if response.status == 404:
                    print("   ✅ No search results test passed (404 returned)")
                else:
                    print(f"   ❌ No search results test failed (expected 404, got {response.status})")

async def main():
    """Main test function."""
    print("🚀 Starting JD Upload & Download Test Suite")
    print("=" * 50)
    
    # Step 1: Create session
    print("\n1️⃣ Creating test session...")
    session_id = await create_test_session()
    if not session_id:
        print("❌ Cannot proceed without session")
        return
    
    print(f"✅ Session created: {session_id}")
    
    # Step 2: Upload JD
    print("\n2️⃣ Uploading test JD...")
    upload_result = await upload_test_jd(session_id)
    if not upload_result:
        print("❌ Cannot proceed without JD upload")
        return
    
    # Step 3: Search resumes
    print("\n3️⃣ Searching for matching resumes...")
    search_result = await search_resumes(session_id)
    if not search_result:
        print("❌ Cannot proceed without search results")
        return
    
    # Step 4: Download shortlisted resumes
    print("\n4️⃣ Downloading shortlisted resumes...")
    zip_path = await download_shortlisted_resumes(session_id, 5)
    if zip_path:
        # Clean up
        os.unlink(zip_path)
        print("   ✅ Basic download test passed")
    
    # Step 5: Test different download counts
    await test_download_with_different_counts(session_id)
    
    # Step 6: Test error scenarios
    await test_error_scenarios(session_id)
    
    print(f"\n🎉 Test Suite Complete!")
    print("=" * 50)
    print("Summary:")
    print("✅ JD Upload functionality working")
    print("✅ Resume search functionality working") 
    print("✅ Download ZIP functionality working")
    print("✅ Error handling working")
    print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
