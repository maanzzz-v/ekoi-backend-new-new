#!/usr/bin/env python3
"""Clean up stale vectors in Pinecone that point to non-existent MongoDB documents."""

import sys
import os
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

import asyncio
from core.database import db_manager
from core.vector_db import vector_manager

async def cleanup_stale_vectors():
    """Remove stale vectors that point to deleted MongoDB documents."""
    print("🧹 CLEANING UP STALE VECTORS")
    print("=" * 50)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        
        # Get all resumes from MongoDB
        collection = db_manager.get_collection("resumes")
        mongo_documents = await collection.find({}, {"_id": 1}).to_list(length=None)
        valid_doc_ids = {str(doc["_id"]) for doc in mongo_documents}
        
        print(f"📊 Valid MongoDB documents: {len(valid_doc_ids)}")
        
        # Get all vectors from Pinecone using list operation
        if not vector_manager.pinecone_index:
            print("❌ Pinecone index not available")
            return 0
            
        index = vector_manager.pinecone_index
        
        # List all vectors using describe_index_stats to get total count
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count
        print(f"📊 Total vectors in Pinecone: {total_vectors}")
        
        # Use list() to get vector IDs and metadata
        # Note: Pinecone list has pagination, so we need to handle it
        stale_vectors = []
        vector_count = 0
        
        # Start listing vectors - list() returns a generator of vector IDs
        print("📊 Fetching vectors from Pinecone...")
        vector_ids = list(index.list())
        vector_count = len(vector_ids)
        print(f"📊 Found {vector_count} vectors in Pinecone")
        
        # Get metadata for vectors to check if they're stale
        if vector_ids:
            # Fetch vectors in batches to get metadata
            batch_size = 100
            for i in range(0, len(vector_ids), batch_size):
                batch_ids = vector_ids[i:i + batch_size]
                fetch_result = index.fetch(ids=batch_ids)
                
                for vector_id, vector_data in fetch_result.vectors.items():
                    metadata = vector_data.metadata or {}
                    doc_id = metadata.get('_id')
                    
                    if doc_id and doc_id not in valid_doc_ids:
                        stale_vectors.append(vector_id)
        
        print(f"📊 Checked {vector_count} vectors")
        print(f"❌ Stale vectors found: {len(stale_vectors)}")
        
        if stale_vectors:
            print(f"🗑️  Deleting {len(stale_vectors)} stale vectors...")
            
            # Delete in batches of 100
            batch_size = 100
            deleted_count = 0
            
            for i in range(0, len(stale_vectors), batch_size):
                batch = stale_vectors[i:i + batch_size]
                try:
                    delete_response = index.delete(ids=batch)
                    deleted_count += len(batch)
                    print(f"   Deleted batch {i//batch_size + 1}: {len(batch)} vectors")
                except Exception as e:
                    print(f"   ❌ Error deleting batch {i//batch_size + 1}: {e}")
            
            print(f"✅ Successfully deleted {deleted_count} stale vectors")
        else:
            print(f"✅ No stale vectors found!")
        
        # Verify cleanup
        print(f"\n🔍 VERIFICATION:")
        stats_after = index.describe_index_stats()
        remaining_vectors = stats_after.total_vector_count
        print(f"   Vectors remaining: {remaining_vectors}")
        print(f"   Cleanup success: {total_vectors - remaining_vectors} vectors removed")
        
        return len(stale_vectors)
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    removed = asyncio.run(cleanup_stale_vectors())
    print(f"\n🏁 Cleanup complete: {removed} stale vectors removed")
