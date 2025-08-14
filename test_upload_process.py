#!/usr/bin/env python3
"""Test resume upload process to identify issues."""

import sys
sys.path.append('./src')
import asyncio
import tempfile
import os
from io import BytesIO
from fastapi import UploadFile

from core.database import db_manager
from core.vector_db import vector_manager
from services.resume_service import resume_service

class MockUploadFile:
    """Mock UploadFile for testing."""
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self.content = content.encode('utf-8')
        self.size = len(self.content)
    
    async def read(self):
        return self.content

async def test_upload_process():
    """Test the complete upload process."""
    print("🧪 TESTING RESUME UPLOAD PROCESS")
    print("=" * 50)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        
        # Create test resume content
        test_resume_content = """
John Doe
Software Engineer
Email: john.doe@email.com
Phone: 123-456-7890

EXPERIENCE:
Senior Software Engineer at ABC Company (2020-2023)
- Developed web applications using Python and Django
- Implemented REST APIs and microservices
- Worked with AWS cloud services

SKILLS:
Python, Django, JavaScript, React, AWS, Docker, PostgreSQL

EDUCATION:
Bachelor of Science in Computer Science
University of Technology (2016-2020)
"""
        
        # Create mock upload file
        mock_file = MockUploadFile("test_upload_resume.txt", test_resume_content)
        
        print("1. Testing file validation...")
        is_valid = resume_service._validate_file(mock_file)
        print(f"   File validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
        
        if not is_valid:
            print("   Issue: File validation failed")
            return
        
        print("2. Testing single file processing...")
        try:
            result = await resume_service._process_single_file(mock_file)
            print(f"   ✅ File processed successfully!")
            print(f"   Document ID: {result['document_id']}")
            print(f"   Vector IDs: {len(result.get('vector_ids', []))} vectors")
            print(f"   Status: {result['status']}")
            
            # Verify in database
            collection = db_manager.get_collection('resumes')
            doc = await collection.find_one({"file_name": "test_upload_resume.txt"})
            if doc:
                print(f"   ✅ Document found in MongoDB: {doc['_id']}")
                print(f"   Processed: {doc.get('processed', False)}")
                print(f"   Has extracted text: {bool(doc.get('extracted_text'))}")
                print(f"   Has parsed info: {bool(doc.get('parsed_info'))}")
            else:
                print(f"   ❌ Document NOT found in MongoDB")
                
        except Exception as e:
            print(f"   ❌ File processing failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("3. Testing complete upload flow...")
        try:
            files = [mock_file]
            upload_results = await resume_service.process_uploaded_files(files)
            print(f"   Total files: {upload_results['total_files']}")
            print(f"   Success count: {upload_results['success_count']}")
            print(f"   Error count: {upload_results['error_count']}")
            
            if upload_results['success_count'] > 0:
                print(f"   ✅ Upload flow working correctly!")
            else:
                print(f"   ❌ Upload flow failed!")
                print(f"   Failed files: {upload_results['failed_files']}")
                
        except Exception as e:
            print(f"   ❌ Upload flow failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Check final database state
        print("\n4. Final database check...")
        collection = db_manager.get_collection('resumes')
        total_count = await collection.count_documents({})
        recent_count = await collection.count_documents({"file_name": {"$regex": "test_upload"}})
        print(f"   Total resumes in DB: {total_count}")
        print(f"   Test resumes: {recent_count}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_upload_process())
