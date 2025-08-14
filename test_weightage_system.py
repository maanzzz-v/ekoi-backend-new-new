"""Comprehensive test script for the weightage-based resume ranking system."""

import asyncio
import json
import time
from typing import Dict, Any, List
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = f"test_session_{int(time.time())}"


class WeightageSystemTester:
    """Comprehensive tester for the weightage-based ranking system."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id = TEST_SESSION_ID
        
    def test_health(self) -> bool:
        """Test if the application is running."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health")
            return response.status_code == 200
        except:
            return False
    
    def test_set_weightage(self, weightage_params: Dict[str, float]) -> Dict[str, Any]:
        """Test setting weightage parameters."""
        print(f"🔧 Setting weightage parameters: {weightage_params}")
        
        payload = {
            "weightage": weightage_params,
            "session_id": self.session_id
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/weightage/set",
            json=payload
        )
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        return result
    
    def test_get_weightage(self) -> Dict[str, Any]:
        """Test getting weightage parameters."""
        print(f"📊 Getting weightage parameters for session: {self.session_id}")
        
        response = requests.get(
            f"{self.base_url}/api/v1/weightage/get",
            params={"session_id": self.session_id}
        )
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        return result
    
    def test_parameter_info(self) -> Dict[str, Any]:
        """Test getting parameter information."""
        print("📋 Getting parameter information...")
        
        response = requests.get(f"{self.base_url}/api/v1/weightage/parameters/info")
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Available presets: {list(result.get('presets', {}).keys())}")
        
        return result
    
    def test_weighted_search(
        self, 
        query: str, 
        job_description: str = None,
        custom_weightage: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Test weighted search functionality."""
        print(f"🔍 Testing weighted search: '{query}'")
        
        payload = {
            "message": query,
            "session_id": self.session_id,
            "top_k": 5
        }
        
        if job_description:
            payload["job_description"] = job_description
            
        if custom_weightage:
            payload["weightage"] = custom_weightage
        
        response = requests.post(
            f"{self.base_url}/api/v1/weightage/search",
            json=payload
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Found {result['total_results']} candidates")
            print(f"   Processing time: {result['processing_time']:.2f}s")
            
            # Show top results with score breakdown
            for i, match in enumerate(result['matches'][:3], 1):
                print(f"   {i}. {match['file_name']} (Score: {match['weighted_score']:.3f})")
                breakdown = match['score_breakdown']
                print(f"      Education: {breakdown.get('education', 0):.3f} | "
                      f"Skills: {breakdown.get('skill_match', 0):.3f} | "
                      f"Experience: {breakdown.get('experience', 0):.3f} | "
                      f"Domain: {breakdown.get('domain_relevance', 0):.3f}")
            
            return result
        else:
            print(f"   Error: {response.text}")
            return {"error": response.text}
    
    def test_reset_weightage(self) -> Dict[str, Any]:
        """Test resetting weightage to defaults."""
        print("🔄 Resetting weightage to defaults...")
        
        response = requests.post(
            f"{self.base_url}/api/v1/weightage/reset",
            params={"session_id": self.session_id}
        )
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result['weightage'], indent=2)}")
        
        return result
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite."""
        print("🚀 Starting Comprehensive Weightage System Test")
        print("=" * 60)
        
        # Test 1: Health check
        print("\n1. Health Check")
        if not self.test_health():
            print("❌ Application is not running!")
            return
        print("✅ Application is healthy")
        
        # Test 2: Get parameter information
        print("\n2. Parameter Information")
        self.test_parameter_info()
        
        # Test 3: Test different weightage presets
        presets = {
            "technical_role": {
                "education": 0.1,
                "skill_match": 0.4,
                "experience": 0.3,
                "domain_relevance": 0.2
            },
            "academic_role": {
                "education": 0.4,
                "skill_match": 0.2,
                "experience": 0.2,
                "domain_relevance": 0.2
            },
            "senior_management": {
                "education": 0.15,
                "skill_match": 0.2,
                "experience": 0.4,
                "domain_relevance": 0.25
            }
        }
        
        test_queries = [
            "Find senior Python developers with 5+ years experience",
            "Looking for data scientists with PhD in machine learning",
            "Need frontend developers skilled in React and TypeScript"
        ]
        
        job_descriptions = {
            "Python Developer": """
            We are looking for a Senior Python Developer to join our backend team.
            Required: 5+ years Python experience, Django/Flask, SQL databases, AWS
            Preferred: Docker, Kubernetes, microservices architecture
            """,
            "Data Scientist": """
            Seeking PhD-level Data Scientist for our AI research team.
            Required: PhD in Computer Science/Statistics, Python, ML/DL frameworks
            Preferred: Research publications, TensorFlow/PyTorch experience
            """,
            "Frontend Developer": """
            Frontend Developer needed for our web application team.
            Required: React, TypeScript, 3+ years experience, responsive design
            Preferred: Next.js, state management (Redux/Zustand), testing
            """
        }
        
        for preset_name, weightage in presets.items():
            print(f"\n3.{list(presets.keys()).index(preset_name) + 1} Testing {preset_name.replace('_', ' ').title()} Preset")
            print("-" * 40)
            
            # Set weightage
            self.test_set_weightage(weightage)
            
            # Test with different queries
            for query in test_queries[:2]:  # Test with first 2 queries
                print(f"\n   Testing query: {query}")
                
                # Choose appropriate job description
                job_desc = None
                if "Python" in query:
                    job_desc = job_descriptions["Python Developer"]
                elif "data scientist" in query.lower():
                    job_desc = job_descriptions["Data Scientist"]
                elif "frontend" in query.lower():
                    job_desc = job_descriptions["Frontend Developer"]
                
                result = self.test_weighted_search(query, job_desc)
                time.sleep(1)  # Brief pause between tests
        
        # Test 4: Custom weightage validation
        print("\n4. Custom Weightage Validation")
        print("-" * 40)
        
        # Test invalid weightage (doesn't sum to 1.0)
        print("   Testing invalid weightage (sum != 1.0)...")
        invalid_weightage = {
            "education": 0.5,
            "skill_match": 0.5,
            "experience": 0.5,
            "domain_relevance": 0.5
        }
        
        try:
            self.test_set_weightage(invalid_weightage)
        except Exception as e:
            print(f"   ✅ Correctly rejected invalid weightage: {e}")
        
        # Test 5: Comparison of different weightage approaches
        print("\n5. Weightage Comparison")
        print("-" * 40)
        
        comparison_query = "Find experienced software engineers with strong technical skills"
        comparison_job_desc = "Looking for software engineers with 3-5 years experience in full-stack development"
        
        # Skill-focused weightage
        skill_focused = {
            "education": 0.1,
            "skill_match": 0.5,
            "experience": 0.2,
            "domain_relevance": 0.2
        }
        
        # Experience-focused weightage
        experience_focused = {
            "education": 0.1,
            "skill_match": 0.2,
            "experience": 0.5,
            "domain_relevance": 0.2
        }
        
        # Balanced weightage
        balanced = {
            "education": 0.25,
            "skill_match": 0.25,
            "experience": 0.25,
            "domain_relevance": 0.25
        }
        
        approaches = {
            "Skill-Focused": skill_focused,
            "Experience-Focused": experience_focused,
            "Balanced": balanced
        }
        
        for approach_name, weightage in approaches.items():
            print(f"\n   {approach_name} Approach:")
            result = self.test_weighted_search(
                comparison_query, 
                comparison_job_desc, 
                custom_weightage=weightage
            )
            time.sleep(1)
        
        # Test 6: Reset to defaults
        print("\n6. Reset to Defaults")
        print("-" * 40)
        self.test_reset_weightage()
        
        # Final verification
        print("\n7. Final Verification")
        print("-" * 40)
        self.test_get_weightage()
        
        print("\n✅ Comprehensive Weightage System Test Completed!")
        print("=" * 60)


def main():
    """Run the test suite."""
    tester = WeightageSystemTester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
