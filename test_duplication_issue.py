#!/usr/bin/env python3
"""Test script to reproduce and diagnose the resume duplication issue."""

import sys
sys.path.append('./src')
import asyncio
import tempfile
import os
from datetime import datetime

from core.database import db_manager
from core.vector_db import vector_manager
from services.resume_service import resume_service
from utils.logger import get_logger

logger = get_logger(__name__)

class MockUploadFile:
    """Mock UploadFile for testing."""
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self.content = content.encode('utf-8')
        self.size = len(self.content)
    
    async def read(self):
        return self.content

async def test_duplication_issue():
    """Test to reproduce the resume duplication problem."""
    print("🔍 TESTING RESUME DUPLICATION ISSUE")
    print("=" * 60)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        
        # Get initial count
        collection = db_manager.get_collection("resumes")
        initial_count = await collection.count_documents({})
        print(f"📊 Initial resume count in MongoDB: {initial_count}")
        
        # Create test resume
        test_content = """
John Doe
Software Engineer
Email: john.doe@example.com
Phone: +1-555-123-4567

EXPERIENCE:
- 5 years Python development
- Django web framework
- RESTful API design
- PostgreSQL databases

SKILLS:
Python, Django, REST APIs, PostgreSQL, Git
"""
        
        # Create a single test file
        test_file = MockUploadFile("test_resume_duplication.txt", test_content)
        
        print(f"📄 Testing upload of: {test_file.filename}")
        print(f"📦 File size: {test_file.size} bytes")
        
        # Test single file upload
        print("\n1. Testing single file upload...")
        result = await resume_service.process_uploaded_files([test_file])
        
        print(f"   ✅ Upload result:")
        print(f"   - Total files: {result['total_files']}")
        print(f"   - Success count: {result['success_count']}")
        print(f"   - Error count: {result['error_count']}")
        print(f"   - Processed files: {len(result['processed_files'])}")
        
        # Check database count after upload
        after_upload_count = await collection.count_documents({})
        print(f"\n📊 Resume count after upload: {after_upload_count}")
        print(f"📈 Documents added: {after_upload_count - initial_count}")
        
        if after_upload_count - initial_count > 1:
            print(f"❌ DUPLICATION DETECTED: {after_upload_count - initial_count} documents added for 1 file!")
        else:
            print(f"✅ NO DUPLICATION: Exactly 1 document added for 1 file")
        
        # Test the collection for duplicates
        print(f"\n2. Checking for duplicate entries...")
        
        # Find documents with the same filename
        duplicate_cursor = collection.aggregate([
            {"$group": {
                "_id": "$file_name", 
                "count": {"$sum": 1},
                "docs": {"$push": "$$ROOT"}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ])
        
        duplicates = await duplicate_cursor.to_list(length=None)
        
        if duplicates:
            print(f"❌ Found {len(duplicates)} sets of duplicate files:")
            for dup in duplicates:
                print(f"   - '{dup['_id']}': {dup['count']} copies")
                for doc in dup['docs']:
                    print(f"     ID: {doc['_id']}, Upload: {doc.get('upload_timestamp', 'Unknown')}")
        else:
            print(f"✅ No duplicates found in database")
        
        # Test with multiple files
        print(f"\n3. Testing with multiple files...")
        test_files = [
            MockUploadFile("resume_1.txt", test_content.replace("John Doe", "Alice Smith")),
            MockUploadFile("resume_2.txt", test_content.replace("John Doe", "Bob Johnson")),
            MockUploadFile("resume_3.txt", test_content.replace("John Doe", "Carol Davis"))
        ]
        
        before_batch_count = await collection.count_documents({})
        print(f"   📊 Count before batch upload: {before_batch_count}")
        
        batch_result = await resume_service.process_uploaded_files(test_files)
        
        after_batch_count = await collection.count_documents({})
        print(f"   📊 Count after batch upload: {after_batch_count}")
        print(f"   📈 Documents added: {after_batch_count - before_batch_count}")
        print(f"   🎯 Expected: {len(test_files)}, Actual: {after_batch_count - before_batch_count}")
        
        if after_batch_count - before_batch_count > len(test_files):
            print(f"   ❌ BATCH DUPLICATION: {after_batch_count - before_batch_count} docs for {len(test_files)} files")
        else:
            print(f"   ✅ BATCH OK: Correct number of documents added")
        
        # Summary
        final_count = await collection.count_documents({})
        total_added = final_count - initial_count
        expected_total = 1 + len(test_files)  # 1 single + 3 batch
        
        print(f"\n" + "=" * 60)
        print(f"📋 FINAL SUMMARY:")
        print(f"   Initial count: {initial_count}")
        print(f"   Final count: {final_count}")
        print(f"   Total added: {total_added}")
        print(f"   Expected: {expected_total}")
        
        if total_added == expected_total:
            print(f"   ✅ SUCCESS: No duplication detected!")
        else:
            print(f"   ❌ ISSUE: Duplication detected - {total_added - expected_total} extra documents")
        
        return total_added == expected_total
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    success = asyncio.run(test_duplication_issue())
    print(f"\n🏁 Test result: {'✅ PASSED' if success else '❌ FAILED'}")
