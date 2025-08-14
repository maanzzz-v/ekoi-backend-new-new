#!/usr/bin/env python3
"""
Test script to demonstrate OpenAI GPT-4 integration with the JD upload and follow-up functionality.
"""

import asyncio
import json
import aiohttp
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_openai_integration():
    """Test the complete OpenAI integration workflow."""
    print("🚀 Testing OpenAI GPT-4 Integration with JD Upload and Follow-up")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a new chat session
        print("\n1️⃣ Creating a new chat session...")
        create_session_request = {
            "title": "OpenAI GPT-4 Integration Test",
            "initial_message": "Testing JD upload and OpenAI-powered follow-up questions"
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/chat/sessions",
            json=create_session_request,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                session_data = await response.json()
                session_id = session_data["session"]["id"]
                print(f"✅ Session created: {session_id}")
            else:
                error_text = await response.text()
                print(f"❌ Failed to create session: {response.status} - {error_text}")
                return
        
        # Step 2: Upload a job description
        print("\n2️⃣ Uploading job description...")
        jd_file_path = Path("test_job_description.txt")
        
        if not jd_file_path.exists():
            print(f"❌ JD file not found: {jd_file_path}")
            return
            
        data = aiohttp.FormData()
        data.add_field('file', open(jd_file_path, 'rb'), filename='test_job_description.txt')
        
        async with session.post(
            f"{BASE_URL}/api/v1/jd/upload?session_id={session_id}", 
            data=data
        ) as response:
            if response.status == 200:
                upload_result = await response.json()
                print(f"✅ JD uploaded successfully: {upload_result['job_description_id']}")
            else:
                error_text = await response.text()
                print(f"❌ Failed to upload JD: {response.status} - {error_text}")
                return
        
        # Step 3: Search for matching resumes
        print("\n3️⃣ Searching for matching candidates...")
        search_request = {
            "session_id": session_id,
            "limit": 5
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/jd/search", 
            json=search_request,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                search_results = await response.json()
                print(f"✅ Found {len(search_results['matches'])} matching candidates")
                for i, candidate in enumerate(search_results['matches'][:3], 1):
                    print(f"   {i}. {candidate['extracted_info']['name']} (Score: {candidate['score']:.3f})")
            else:
                error_text = await response.text()
                print(f"❌ Failed to search candidates: {response.status} - {error_text}")
                return
        
        # Step 4: Test OpenAI GPT-4 follow-up questions
        print("\n4️⃣ Testing OpenAI GPT-4 powered follow-up questions...")
        
        questions = [
            "Why are these candidates the best match for this role?",
            "What are the key technical skills I should focus on during interviews?",
            "Compare the experience levels of the top 3 candidates",
            "What questions should I ask to assess their Python framework knowledge?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n🤖 Question {i}: {question}")
            
            followup_request = {
                "session_id": session_id,
                "question": question
            }
            
            async with session.post(
                f"{BASE_URL}/api/v1/jd/followup",
                json=followup_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    followup_result = await response.json()
                    answer = followup_result["answer"]
                    print(f"💡 GPT-4 Answer: {answer[:200]}..." if len(answer) > 200 else f"💡 GPT-4 Answer: {answer}")
                    print(f"📊 Analyzed {followup_result['candidates_analyzed']} candidates")
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get follow-up answer: {response.status} - {error_text}")
            
            # Small delay between questions
            await asyncio.sleep(1)
        
        print("\n🎉 OpenAI GPT-4 Integration Test Completed Successfully!")
        print("=" * 60)
        print(f"Session ID for further testing: {session_id}")

if __name__ == "__main__":
    asyncio.run(test_openai_integration())
