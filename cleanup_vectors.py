#!/usr/bin/env python3
"""Clean up stale vectors in Pinecone that don't have corresponding MongoDB documents."""

import asyncio
import sys
sys.path.append('./src')

from core.database import db_manager
from core.vector_db import vector_manager
from bson import ObjectId

async def cleanup_stale_vectors():
    """Remove vectors that don't correspond to existing MongoDB documents."""
    print("🧹 Cleaning up stale vectors in Pinecone")
    print("=" * 50)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        
        print("1. Getting all resume IDs from MongoDB...")
        collection = db_manager.get_collection('resumes')
        
        # Get all valid document IDs from MongoDB
        valid_ids = set()
        async for doc in collection.find({}, {'_id': 1}):
            valid_ids.add(str(doc['_id']))
        
        print(f"   Found {len(valid_ids)} valid resumes in MongoDB")
        
        # Test search to identify stale vectors
        print("2. Testing vector search to find stale references...")
        test_queries = [
            "python developer",
            "javascript",
            "data scientist",
            "software engineer"
        ]
        
        stale_vector_ids = set()
        total_vectors_checked = 0
        
        for query in test_queries:
            vector_results = await vector_manager.search_similar(query, 50)
            for vector_id, score, metadata in vector_results:
                total_vectors_checked += 1
                doc_id = metadata.get("_id") or metadata.get("id")
                if doc_id and str(doc_id) not in valid_ids:
                    stale_vector_ids.add(vector_id)
                    
        print(f"   Checked {total_vectors_checked} vectors")
        print(f"   Found {len(stale_vector_ids)} stale vectors")
        
        if stale_vector_ids:
            print("3. Cleaning up stale vectors...")
            # Note: You'd implement delete_vectors method in vector_manager
            print(f"   Would delete: {list(stale_vector_ids)[:10]}...")
            print("   (Vector deletion not implemented yet)")
        else:
            print("3. No stale vectors found!")
            
        # Alternative: Re-index all resumes to ensure consistency
        print("\n💡 RECOMMENDATION:")
        print("   Consider re-indexing all resumes to ensure vector/MongoDB consistency")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(cleanup_stale_vectors())
