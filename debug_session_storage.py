#!/usr/bin/env python3
"""Debug the session storage issue and fix it."""

import sys
sys.path.append('./src')
import asyncio
import json

from core.database import db_manager
from services.session_service import session_service

async def debug_session_storage():
    """Debug why search results aren't being stored properly."""
    print("🔍 DEBUGGING SESSION STORAGE ISSUE")
    print("=" * 60)
    
    try:
        await db_manager.connect()
        
        # Create a test session
        print("1. Creating test session...")
        session = await session_service.create_session(
            title="Debug Session Storage",
            initial_message="Testing storage"
        )
        session_id = session.id
        print(f"   ✅ Session created: {session_id}")
        
        # Test storing some context
        print("\n2. Testing context storage...")
        test_context = {
            "jd_search_results": {
                "timestamp": "2025-08-14T12:00:00",
                "jd_id": "test_jd_123",
                "jd_filename": "test.txt",
                "total_matches": 3,
                "matches": [
                    {
                        "id": "resume_1",
                        "file_name": "candidate1.pdf",
                        "score": 0.95,
                        "extracted_info": {"name": "John Doe"}
                    },
                    {
                        "id": "resume_2", 
                        "file_name": "candidate2.pdf",
                        "score": 0.85,
                        "extracted_info": {"name": "Jane Smith"}
                    }
                ]
            }
        }
        
        # Store the context
        success = await session_service.update_session_context(session_id, test_context)
        print(f"   Storage success: {success}")
        
        # Retrieve the session to check if context was stored
        print("\n3. Retrieving stored context...")
        updated_session = await session_service.get_session(session_id)
        
        if updated_session and updated_session.context:
            print(f"   ✅ Context found!")
            print(f"   Context keys: {list(updated_session.context.keys())}")
            
            jd_results = updated_session.context.get("jd_search_results")
            if jd_results:
                print(f"   ✅ JD search results found!")
                print(f"   Total matches: {jd_results.get('total_matches')}")
                print(f"   Matches count: {len(jd_results.get('matches', []))}")
                
                # Show the matches
                for i, match in enumerate(jd_results.get('matches', [])[:3], 1):
                    print(f"      {i}. {match.get('extracted_info', {}).get('name', 'Unknown')} - {match.get('file_name')}")
            else:
                print(f"   ❌ No JD search results found in context")
                print(f"   Available context: {updated_session.context}")
        else:
            print(f"   ❌ No context found in session")
        
        # Test the JD service method
        print("\n4. Testing JD service retrieval method...")
        from services.jd_service import jd_service
        
        stored_results = await jd_service.get_session_search_results(session_id)
        if stored_results:
            print(f"   ✅ JD service can retrieve results!")
            print(f"   Retrieved matches: {len(stored_results.get('matches', []))}")
            print(f"   JD filename: {stored_results.get('jd_filename')}")
        else:
            print(f"   ❌ JD service cannot retrieve results")
        
        print("\n" + "=" * 60)
        print("🎯 DIAGNOSIS:")
        
        if success and updated_session and updated_session.context and stored_results:
            print("   ✅ Session storage is working correctly!")
            print("   The issue might be in the search results format or timing")
        elif success and updated_session and updated_session.context:
            print("   ⚠️  Storage works but JD service retrieval has issues")
        elif success:
            print("   ⚠️  Update reports success but data not persisted")
        else:
            print("   ❌ Session context update is failing")
            
        return {
            "storage_success": success,
            "context_persisted": bool(updated_session and updated_session.context),
            "jd_service_retrieval": bool(stored_results),
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return {}
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    result = asyncio.run(debug_session_storage())
    print(f"\n📋 Debug Results: {json.dumps(result, indent=2)}")
