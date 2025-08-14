#!/usr/bin/env python3
"""Test script to diagnose the API search issue."""

import asyncio
import sys
sys.path.append('./src')

from core.database import db_manager
from core.vector_db import vector_manager
from services.resume_service import resume_service
from services.rag_service import rag_service

async def test_search_pipeline():
    """Test the search pipeline step by step."""
    print("🔍 Testing Resume Search Pipeline")
    print("=" * 50)
    
    try:
        # Initialize services
        print("1. Initializing services...")
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        
        # Test query
        query = "software engineer"
        print(f"2. Testing query: '{query}'")
        
        # Test vector search directly
        print("3. Testing vector search...")
        vector_results = await vector_manager.search_similar(query, 10)
        print(f"   Vector search returned: {len(vector_results)} results")
        
        # Test resume service search
        print("4. Testing resume service search...")
        resume_matches = await resume_service.search_resumes(query, 10)
        print(f"   Resume service returned: {len(resume_matches)} matches")
        
        for i, match in enumerate(resume_matches[:3], 1):
            print(f"   {i}. {match.file_name} (Score: {match.score:.3f})")
        
        # Test RAG service search
        print("5. Testing RAG service search...")
        rag_matches, rag_metadata = await rag_service.enhanced_search(query, 10)
        print(f"   RAG service returned: {len(rag_matches)} matches")
        
        # Test enhanced RAG service search
        print("6. Testing enhanced RAG service search...")
        print("   (Skipped due to circular import)")
        enhanced_matches = []
        enhanced_metadata = {}
        
        # Analyze the issue
        print("\n🔍 ANALYSIS:")
        print(f"   Vector DB: {len(vector_results)} results")
        print(f"   Resume Service: {len(resume_matches)} results") 
        print(f"   RAG Service: {len(rag_matches)} results")
        
        if len(rag_matches) <= 2:
            print("\n❌ ISSUE CONFIRMED: Only 2 or fewer candidates returned")
            print("   Investigating further...")
            
            # Check if filtering is too strict
            print(f"\n   RAG metadata: {rag_metadata}")
        
        return len(rag_matches)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_search_pipeline())
