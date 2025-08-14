#!/usr/bin/env python3
"""Clean up duplicate resumes from MongoDB."""

import sys
sys.path.append('./src')
import asyncio
from core.database import db_manager

async def clean_duplicates():
    """Remove duplicate resume entries."""
    print("🧹 CLEANING DUPLICATE RESUMES")
    print("=" * 50)
    
    try:
        await db_manager.connect()
        collection = db_manager.get_collection("resumes")
        
        # Find duplicates
        duplicates_cursor = collection.aggregate([
            {"$group": {
                "_id": "$file_name", 
                "count": {"$sum": 1},
                "docs": {"$push": {"id": "$_id", "upload_timestamp": "$upload_timestamp"}}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ])
        
        duplicates = await duplicates_cursor.to_list(length=None)
        
        if not duplicates:
            print("✅ No duplicates found!")
            return
        
        print(f"Found {len(duplicates)} sets of duplicates")
        
        total_removed = 0
        for dup in duplicates:
            filename = dup['_id']
            docs = dup['docs']
            
            # Sort by upload timestamp and keep the first one
            docs.sort(key=lambda x: x['upload_timestamp'])
            keep_doc = docs[0]
            remove_docs = docs[1:]
            
            print(f"\n📄 {filename}:")
            print(f"  ✅ Keeping: {keep_doc['id']} ({keep_doc['upload_timestamp']})")
            
            for doc in remove_docs:
                print(f"  ❌ Removing: {doc['id']} ({doc['upload_timestamp']})")
                await collection.delete_one({"_id": doc['id']})
                total_removed += 1
        
        print(f"\n🎯 CLEANUP SUMMARY:")
        print(f"   Duplicate sets: {len(duplicates)}")
        print(f"   Documents removed: {total_removed}")
        print(f"   ✅ Database cleaned!")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(clean_duplicates())
