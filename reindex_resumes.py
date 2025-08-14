#!/usr/bin/env python3
"""Re-index all resumes to fix vector/MongoDB inconsistency."""

import asyncio
import sys
sys.path.append('./src')

from core.database import db_manager
from core.vector_db import vector_manager
from services.resume_service import resume_service
from services.file_processor import ResumeParser

async def reindex_all_resumes():
    """Re-index all resumes to ensure vector/MongoDB consistency."""
    print("🔄 Re-indexing all resumes for consistency")
    print("=" * 50)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        
        print("1. Getting all resumes from MongoDB...")
        collection = db_manager.get_collection('resumes')
        
        # Get all resumes
        total_resumes = await collection.count_documents({})
        print(f"   Found {total_resumes} resumes to re-index")
        
        reindexed_count = 0
        skipped_count = 0
        
        async for resume_doc in collection.find({}):
            try:
                file_name = resume_doc.get('file_name', 'unknown')
                extracted_text = resume_doc.get('extracted_text', '')
                
                if not extracted_text or len(extracted_text.strip()) < 10:
                    print(f"   ⏭️  Skipping {file_name} - no text content")
                    skipped_count += 1
                    continue
                
                print(f"   🔄 Re-indexing: {file_name}")
                
                # Process the resume text into chunks and store vectors
                chunks = ResumeParser.chunk_text(extracted_text)
                
                # Create metadata for each chunk
                chunk_metadata = []
                for i, chunk in enumerate(chunks):
                    metadata = {
                        "_id": str(resume_doc["_id"]),
                        "file_name": file_name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "timestamp": resume_doc.get("created_at", ""),
                    }
                    chunk_metadata.append(metadata)
                
                # Store vectors (this will overwrite existing ones with same metadata)
                vector_ids = await vector_manager.store_vectors(chunks, chunk_metadata)
                
                if vector_ids:
                    reindexed_count += 1
                    print(f"      ✅ Stored {len(vector_ids)} vectors")
                else:
                    print(f"      ❌ Failed to store vectors")
                
            except Exception as e:
                print(f"   ❌ Error re-indexing {file_name}: {e}")
                continue
        
        print(f"\n🎉 RE-INDEXING COMPLETE!")
        print(f"   ✅ Successfully re-indexed: {reindexed_count} resumes")
        print(f"   ⏭️  Skipped: {skipped_count} resumes")
        print(f"   📊 Total: {reindexed_count + skipped_count}/{total_resumes}")
        
        # Test the fix
        print(f"\n🧪 Testing search after re-indexing...")
        test_matches = await resume_service.search_resumes("python developer", 10)
        print(f"   Search now returns: {len(test_matches)} matches")
        
        if len(test_matches) >= 5:
            print("   ✅ SUCCESS: Search is now returning more results!")
        else:
            print("   ⚠️  Still fewer results than expected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(reindex_all_resumes())
