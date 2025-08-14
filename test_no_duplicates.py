#!/usr/bin/env python3
"""Test duplicate prevention during resume upload."""

import sys
sys.path.append('./src')
import asyncio
import tempfile
import os
from datetime import datetime

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

async def test_duplicate_prevention():
    """Test that duplicate uploads are prevented."""
    print("🛡️  TESTING DUPLICATE PREVENTION")
    print("=" * 50)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        
        # Create test content
        test_content = """
        John Doe
        Software Engineer
        Email: john.doe@example.com
        Phone: (555) 123-4567
        
        EXPERIENCE:
        - Senior Python Developer at TechCorp (2020-2023)
        - Backend Engineer at StartupXYZ (2018-2020)
        
        SKILLS:
        Python, Django, PostgreSQL, AWS, Docker
        """
        
        test_file = MockUploadFile("john_doe_test_resume.txt", test_content)
        
        print("1. First upload attempt...")
        try:
            result1 = await resume_service._process_single_file(test_file)
            print(f"   ✅ First upload successful: {result1['document_id']}")
        except Exception as e:
            print(f"   ❌ First upload failed: {e}")
            return False
        
        print("\n2. Second upload attempt (immediate duplicate)...")
        test_file2 = MockUploadFile("john_doe_test_resume.txt", test_content)
        try:
            result2 = await resume_service._process_single_file(test_file2)
            print(f"   ❌ FAILURE: Second upload succeeded when it should have been blocked!")
            print(f"   Document ID: {result2['document_id']}")
            return False
        except Exception as e:
            if "Duplicate file upload detected" in str(e):
                print(f"   ✅ SUCCESS: Duplicate correctly prevented - {e}")
            else:
                print(f"   ❌ Unexpected error: {e}")
                return False
        
        print("\n3. Third upload attempt (same content, different name)...")
        test_file3 = MockUploadFile("john_doe_resume_copy.txt", test_content)
        try:
            result3 = await resume_service._process_single_file(test_file3)
            print(f"   ❌ FAILURE: Content duplicate succeeded when it should have been blocked!")
            print(f"   Document ID: {result3['document_id']}")
            return False
        except Exception as e:
            if "Duplicate file upload detected" in str(e):
                print(f"   ✅ SUCCESS: Content duplicate correctly prevented - {e}")
            else:
                print(f"   ❌ Unexpected error: {e}")
                return False
        
        print("\n4. Fourth upload attempt (different content)...")
        different_content = """
        Jane Smith
        Data Scientist
        Email: jane.smith@example.com
        
        EXPERIENCE:
        - Senior Data Scientist at DataCorp (2019-2023)
        - ML Engineer at AIStartup (2017-2019)
        
        SKILLS:
        Python, Machine Learning, TensorFlow, Pandas
        """
        test_file4 = MockUploadFile("jane_smith_resume.txt", different_content)
        try:
            result4 = await resume_service._process_single_file(test_file4)
            print(f"   ✅ SUCCESS: Different content uploaded successfully: {result4['document_id']}")
        except Exception as e:
            print(f"   ❌ FAILURE: Different content should have been allowed: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 DUPLICATE PREVENTION TEST COMPLETE!")
        print("✅ All duplicate scenarios handled correctly")
        print("✅ New content uploads work normally")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    success = asyncio.run(test_duplicate_prevention())
    if success:
        print("\n🎯 DUPLICATE PREVENTION IS WORKING!")
        print("💡 Future uploads will automatically prevent duplicates")
    else:
        print("\n❌ DUPLICATE PREVENTION NEEDS FIXING")
