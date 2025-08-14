#!/usr/bin/env python3
"""Final verification of the shortlisting fix."""

import sys
sys.path.append('./src')
import asyncio

from core.database import db_manager
from core.vector_db import vector_manager
from services.resume_service import resume_service

async def verify_fix():
    """Quick verification that we now get more results."""
    print("🔍 FINAL VERIFICATION OF SHORTLISTING FIX")
    print("=" * 50)
    
    try:
        # Initialize services
        await db_manager.connect()
        await vector_manager.initialize()
        resume_service.set_vector_manager(vector_manager)
        
        # Test search with job requirements
        test_query = "Senior Python Developer with Django experience and AWS cloud knowledge"
        
        print(f"Testing search query: '{test_query}'")
        print("Searching...")
        
        # Search using enhanced resume service
        matches = await resume_service.search_resumes(query=test_query, top_k=10)
        
        total_results = len(matches)
        print(f"\n📊 RESULTS:")
        print(f"   Total candidates found: {total_results}")
        
        if total_results >= 10:
            print(f"   ✅ EXCELLENT: Found {total_results} candidates!")
            status = "FIXED"
        elif total_results >= 5:
            print(f"   ✅ GOOD: Found {total_results} candidates") 
            status = "IMPROVED"
        elif total_results >= 3:
            print(f"   ⚠️  MODERATE: Found {total_results} candidates")
            status = "PARTIALLY_FIXED"
        else:
            print(f"   ❌ POOR: Only {total_results} candidates found")
            status = "NOT_FIXED"
        
        # Show summary
        print(f"\n🎯 VERIFICATION RESULT:")
        print(f"   Before fix: 2 candidates")
        print(f"   After fix: {total_results} candidates") 
        print(f"   Status: {status}")
        
        if total_results > 2:
            print(f"   ✅ SUCCESS: Shortlisting limitation has been resolved!")
            print(f"   📈 Improvement: {((total_results - 2) / 2 * 100):.0f}% increase in candidates")
        
        return total_results
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return 0
    
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    result = asyncio.run(verify_fix())
    print(f"\n🏁 FINAL STATUS: {'✅ ISSUE RESOLVED' if result > 2 else '❌ STILL NEEDS WORK'}")
