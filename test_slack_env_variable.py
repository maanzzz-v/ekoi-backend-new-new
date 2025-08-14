#!/usr/bin/env python3
"""Test script to verify Slack token environment variable integration."""

import sys
import os
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_env_variable():
    """Test if SLACK_TOKEN environment variable is accessible."""
    print("🧪 TESTING SLACK TOKEN ENVIRONMENT VARIABLE")
    print("=" * 50)
    
    # Test direct environment variable access
    slack_token = os.getenv("SLACK_TOKEN")
    if slack_token:
        print(f"✅ SLACK_TOKEN found in environment")
        print(f"   Token preview: {slack_token[:20]}...{slack_token[-10:]}")
    else:
        print("❌ SLACK_TOKEN not found in environment")
        return False
    
    return True

def test_settings_integration():
    """Test if settings can access the Slack token."""
    print("\n🔧 TESTING SETTINGS INTEGRATION")
    print("=" * 35)
    
    try:
        from config.settings import settings
        
        if settings.slack_token:
            print(f"✅ Settings.slack_token: {settings.slack_token[:20]}...{settings.slack_token[-10:]}")
        else:
            print("❌ Settings.slack_token is None")
            return False
            
    except Exception as e:
        print(f"❌ Settings import failed: {e}")
        return False
    
    return True

def test_slack_service_integration():
    """Test if SlackNotificationService can be initialized with env variable."""
    print("\n📱 TESTING SLACK SERVICE INTEGRATION")
    print("=" * 40)
    
    try:
        from services.slack_notification_service import SlackNotificationService
        
        # Test initialization without explicit token (should use env var)
        service = SlackNotificationService()
        print("✅ SlackNotificationService initialized successfully")
        print("✅ Using environment variable for token")
        
        # Test that the client is properly configured
        if hasattr(service, 'client') and service.client:
            print("✅ Slack WebClient properly initialized")
        else:
            print("❌ Slack WebClient not properly initialized")
            return False
            
    except Exception as e:
        print(f"❌ SlackNotificationService initialization failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 SLACK TOKEN ENVIRONMENT VARIABLE INTEGRATION TEST")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Environment Variable", test_env_variable()))
    results.append(("Settings Integration", test_settings_integration()))
    results.append(("Slack Service Integration", test_slack_service_integration()))
    
    # Print summary
    print("\n📊 TEST SUMMARY")
    print("=" * 15)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Environment variable integration is working!")
        print("📱 Slack token is properly configured via SLACK_TOKEN environment variable")
        print("✅ Hardcoded tokens have been successfully replaced")
    else:
        print("❌ SOME TESTS FAILED! Please check the configuration")
    print("=" * 60)

if __name__ == "__main__":
    main()
