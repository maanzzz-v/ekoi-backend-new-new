#!/usr/bin/env python3
"""Simple test for JD upload API."""

import requests
import json

BASE_URL = "http://localhost:8000"

def simple_test():
    print("🧪 Simple JD Upload Test")
    print("=" * 30)
    
    # Test 1: Health check
    print("\n1. Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test 2: Create session
    print("\n2. Creating session...")
    session_data = {"title": "Test JD Session"}
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat/sessions", json=session_data)
        if response.status_code == 200:
            session_id = response.json()["session"]["id"]
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Session creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return
    
    # Test 3: Upload JD
    print("\n3. Uploading JD...")
    try:
        with open("test_job_description.txt", 'rb') as file:
            files = {'file': ('test_job_description.txt', file, 'text/plain')}
            response = requests.post(
                f"{BASE_URL}/api/v1/jd/upload",
                params={"session_id": session_id},
                files=files
            )
            
            if response.status_code == 200:
                jd_data = response.json()
                print(f"✅ JD uploaded successfully!")
                print(f"   JD ID: {jd_data['job_description_id']}")
                print(f"   File: {jd_data['file_name']}")
            else:
                print(f"❌ JD upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
    except Exception as e:
        print(f"❌ Error uploading JD: {e}")
        return
    
    # Test 4: Search with JD
    print("\n4. Searching with JD...")
    search_data = {"session_id": session_id, "top_k": 5}
    try:
        response = requests.post(f"{BASE_URL}/api/v1/jd/search", json=search_data)
        if response.status_code == 200:
            search_result = response.json()
            print(f"✅ Search completed!")
            print(f"   Found {search_result['total_results']} matches")
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error in search: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    simple_test()
