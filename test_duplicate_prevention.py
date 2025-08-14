#!/usr/bin/env python3
"""
Test script to demonstrate the duplicate prevention functionality.
"""

import asyncio
import json
import aiohttp
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_duplicate_prevention():
    """Test the duplicate prevention functionality."""
    print("🔄 Testing Resume Upload Duplicate Prevention")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Check initial count
        print("\n1️⃣ Checking initial resume count...")
        async with session.get(f"{BASE_URL}/api/v1/resumes/") as response:
            if response.status == 200:
                data = await response.json()
                initial_count = data["pagination"]["total"]
                print(f"✅ Initial resume count: {initial_count}")
            else:
                print(f"❌ Failed to get initial count: {response.status}")
                return
        
        # Step 2: Upload a new file
        print("\n2️⃣ Uploading a new test file...")
        test_file = Path("test_new_resume.txt")
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return
        
        data = aiohttp.FormData()
        data.add_field('files', open(test_file, 'rb'), filename='test_new_resume.txt')
        
        async with session.post(f"{BASE_URL}/api/v1/resumes/upload", data=data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Upload result: {result['message']}")
                new_upload = len(result['uploaded_files']) > 0
            else:
                error_text = await response.text()
                print(f"❌ Failed to upload: {response.status} - {error_text}")
                return
        
        # Step 3: Check count after upload
        print("\n3️⃣ Checking count after upload...")
        async with session.get(f"{BASE_URL}/api/v1/resumes/") as response:
            if response.status == 200:
                data = await response.json()
                after_upload_count = data["pagination"]["total"]
                print(f"✅ Count after upload: {after_upload_count}")
                if new_upload:
                    expected = initial_count + 1
                    if after_upload_count == expected:
                        print(f"✅ Count increased correctly ({initial_count} → {after_upload_count})")
                    else:
                        print(f"⚠️ Unexpected count change ({initial_count} → {after_upload_count})")
                else:
                    print("ℹ️ File was detected as duplicate, count should remain same")
            else:
                print(f"❌ Failed to get count: {response.status}")
        
        # Step 4: Try to upload the same file again (should be prevented)
        print("\n4️⃣ Attempting to upload the same file again (should be prevented)...")
        
        data = aiohttp.FormData()
        data.add_field('files', open(test_file, 'rb'), filename='test_new_resume.txt')
        
        async with session.post(f"{BASE_URL}/api/v1/resumes/upload", data=data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Duplicate prevention result: {result['message']}")
                
                if "Skipped" in result['message'] and "duplicate" in result['message']:
                    print("✅ Duplicate prevention working correctly!")
                elif len(result['uploaded_files']) == 0:
                    print("✅ No files uploaded (duplicate prevented)")
                else:
                    print("⚠️ File was uploaded again - duplicate prevention may not be working")
            else:
                error_text = await response.text()
                print(f"❌ Failed to test duplicate: {response.status} - {error_text}")
        
        # Step 5: Check final count
        print("\n5️⃣ Checking final count...")
        async with session.get(f"{BASE_URL}/api/v1/resumes/") as response:
            if response.status == 200:
                data = await response.json()
                final_count = data["pagination"]["total"]
                print(f"✅ Final count: {final_count}")
                
                if final_count == after_upload_count:
                    print("✅ Count remained same - duplicate prevention successful!")
                else:
                    print(f"⚠️ Count changed unexpectedly ({after_upload_count} → {final_count})")
            else:
                print(f"❌ Failed to get final count: {response.status}")
        
        # Step 6: Test cleanup endpoint
        print("\n6️⃣ Testing duplicate cleanup endpoint...")
        async with session.post(f"{BASE_URL}/api/v1/resumes/cleanup-duplicates") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Cleanup result: {result['message']}")
                print(f"   • Before cleanup: {result['resumes_before']}")
                print(f"   • After cleanup: {result['resumes_after']}")
                print(f"   • Duplicates removed: {result['duplicates_removed']}")
            else:
                error_text = await response.text()
                print(f"❌ Failed to test cleanup: {response.status} - {error_text}")
        
        print("\n🎉 Duplicate Prevention Test Completed!")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_duplicate_prevention())
