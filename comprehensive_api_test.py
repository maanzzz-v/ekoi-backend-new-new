#!/usr/bin/env python3
"""
Comprehensive API Testing Script for EKOI Backend
Tests all endpoints including JD upload, storage verification, search, and follow-up questions
"""

import requests
import json
import time
import os
from typing import Dict, Any
import uuid

class EKOIAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_ids = []
        self.jd_ids = []
        self.results = {}
        
    def print_section(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_result(self, endpoint: str, status_code: int, response: Dict[Any, Any]):
        print(f"\n🔍 {endpoint}")
        print(f"Status: {status_code}")
        if status_code == 200:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
        print(f"Response: {json.dumps(response, indent=2)}")
        
    def test_health_endpoints(self):
        """Test health check endpoints"""
        self.print_section("1. HEALTH CHECK ENDPOINTS")
        
        # Basic health
        response = requests.get(f"{self.base_url}/api/v1/health/")
        self.print_result("GET /api/v1/health/", response.status_code, response.json())
        
        # Detailed health
        response = requests.get(f"{self.base_url}/api/v1/health/detailed")
        self.print_result("GET /api/v1/health/detailed", response.status_code, response.json())
        
    def test_jd_upload(self):
        """Test job description upload endpoints"""
        self.print_section("2. JOB DESCRIPTION UPLOAD ENDPOINTS")
        
        # Create a sample job description
        jd_content = """
Senior Python Developer - Remote

We are looking for an experienced Senior Python Developer to join our growing team. 

Requirements:
- 5+ years of experience with Python development
- Strong knowledge of Django and Flask frameworks
- Experience with AWS cloud services (EC2, S3, Lambda)
- Proficiency in React.js for frontend development
- Database experience with PostgreSQL and MongoDB
- Experience with Docker and Kubernetes
- Knowledge of CI/CD pipelines and Jenkins
- Strong problem-solving and communication skills

Responsibilities:
- Design and develop scalable Python applications
- Work with cross-functional teams to deliver high-quality software
- Mentor junior developers
- Participate in code reviews and architectural decisions
- Deploy and maintain applications on AWS infrastructure

Nice to have:
- Experience with machine learning libraries (pandas, numpy, scikit-learn)
- Knowledge of microservices architecture
- Experience with GraphQL APIs
- Previous startup experience
        """
        
        # Test JD upload via text
        jd_data = {
            "job_title": "Senior Python Developer",
            "job_description": jd_content,
            "company_name": "TechCorp Inc",
            "location": "Remote",
            "requirements": [
                "5+ years Python experience",
                "Django/Flask frameworks",
                "AWS cloud services",
                "React.js frontend",
                "PostgreSQL/MongoDB"
            ]
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/jd/upload",
            json=jd_data
        )
        result = response.json()
        self.print_result("POST /api/v1/jd/upload", response.status_code, result)
        
        if response.status_code == 200 and "jd_id" in result:
            self.jd_ids.append(result["jd_id"])
            print(f"🎯 JD ID saved: {result['jd_id']}")
            
    def test_jd_list_and_get(self):
        """Test JD listing and retrieval endpoints"""
        self.print_section("3. JD LISTING AND RETRIEVAL")
        
        # List all JDs
        response = requests.get(f"{self.base_url}/api/v1/jd/")
        self.print_result("GET /api/v1/jd/", response.status_code, response.json())
        
        # Get specific JD if available
        if self.jd_ids:
            jd_id = self.jd_ids[0]
            response = requests.get(f"{self.base_url}/api/v1/jd/{jd_id}")
            self.print_result(f"GET /api/v1/jd/{jd_id}", response.status_code, response.json())
            
    def test_jd_search_and_shortlisting(self):
        """Test JD search and candidate shortlisting"""
        self.print_section("4. JD SEARCH AND SHORTLISTING")
        
        if not self.jd_ids:
            print("❌ No JD IDs available for testing")
            return
            
        jd_id = self.jd_ids[0]
        
        # Test shortlisting candidates for JD
        shortlist_data = {
            "top_k": 5,
            "filters": {
                "min_experience_years": 3,
                "skills": ["Python", "Django", "AWS"]
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/jd/{jd_id}/shortlist",
            json=shortlist_data
        )
        result = response.json()
        self.print_result(f"POST /api/v1/jd/{jd_id}/shortlist", response.status_code, result)
        
        # Store results for follow-up testing
        if response.status_code == 200:
            self.results['shortlist_results'] = result
            
    def test_chat_session_creation(self):
        """Test chat session management"""
        self.print_section("5. CHAT SESSION MANAGEMENT")
        
        # Create new chat session
        session_data = {
            "title": "Python Developer Search Session",
            "initial_message": "I need to find experienced Python developers for our startup"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/sessions",
            json=session_data
        )
        result = response.json()
        self.print_result("POST /api/v1/chat/sessions", response.status_code, result)
        
        if response.status_code == 200 and "session" in result:
            session_id = result["session"]["id"]
            self.session_ids.append(session_id)
            print(f"🎯 Session ID saved: {session_id}")
            
        # Create another session for comparison
        session_data2 = {
            "title": "Frontend Developer Search",
            "initial_message": "Looking for React developers with 3+ years experience"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/sessions",
            json=session_data2
        )
        result = response.json()
        self.print_result("POST /api/v1/chat/sessions (Session 2)", response.status_code, result)
        
        if response.status_code == 200 and "session" in result:
            session_id = result["session"]["id"]
            self.session_ids.append(session_id)
            print(f"🎯 Session ID 2 saved: {session_id}")
            
    def test_chat_search_in_sessions(self):
        """Test search within different chat sessions"""
        self.print_section("6. CHAT SEARCH IN DIFFERENT SESSIONS")
        
        if not self.session_ids:
            print("❌ No session IDs available for testing")
            return
            
        # Test search in first session
        session_id = self.session_ids[0]
        search_data = {
            "message": "Find senior Python developers with Django and AWS experience who have worked in startups",
            "top_k": 5
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/sessions/{session_id}/search",
            json=search_data
        )
        result = response.json()
        self.print_result(f"POST /api/v1/chat/sessions/{session_id}/search", response.status_code, result)
        
        if response.status_code == 200:
            self.results['session1_search'] = result
            
        # Test search in second session (if available)
        if len(self.session_ids) > 1:
            session_id2 = self.session_ids[1]
            search_data2 = {
                "message": "Find React developers with TypeScript experience and good communication skills",
                "top_k": 3
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat/sessions/{session_id2}/search",
                json=search_data2
            )
            result = response.json()
            self.print_result(f"POST /api/v1/chat/sessions/{session_id2}/search", response.status_code, result)
            
            if response.status_code == 200:
                self.results['session2_search'] = result
                
    def test_follow_up_questions(self):
        """Test follow-up questions in chat sessions"""
        self.print_section("7. FOLLOW-UP QUESTIONS AND ANALYSIS")
        
        if not self.session_ids:
            print("❌ No session IDs available for testing")
            return
            
        session_id = self.session_ids[0]
        
        # Follow-up questions to test
        followup_questions = [
            "Why were these candidates selected? What are their key strengths?",
            "How do these Python developers compare in terms of experience level?",
            "Which candidate would be the best fit for a startup environment?",
            "What technical skills do the top 3 candidates have in common?",
            "Who has the most relevant AWS cloud experience among these candidates?"
        ]
        
        for i, question in enumerate(followup_questions, 1):
            print(f"\n--- Follow-up Question {i} ---")
            
            followup_data = {
                "question": question,
                "previous_search_results": self.results.get('session1_search', {}).get('matches', [])
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat/sessions/{session_id}/followup",
                json=followup_data
            )
            result = response.json()
            self.print_result(f"POST /api/v1/chat/sessions/{session_id}/followup", response.status_code, result)
            
            # Wait a bit between questions to avoid overwhelming the API
            time.sleep(2)
            
    def test_standalone_chat_search(self):
        """Test standalone chat search without sessions"""
        self.print_section("8. STANDALONE CHAT SEARCH")
        
        search_queries = [
            "Find experienced full-stack developers with Python and React skills",
            "I need senior software engineers with machine learning experience",
            "Looking for DevOps engineers with Kubernetes and Docker expertise"
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n--- Standalone Search {i} ---")
            
            search_data = {
                "message": query,
                "top_k": 3,
                "filters": {}
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat/search",
                json=search_data
            )
            result = response.json()
            self.print_result("POST /api/v1/chat/search", response.status_code, result)
            
    def test_query_analysis_and_optimization(self):
        """Test query analysis and optimization endpoints"""
        self.print_section("9. QUERY ANALYSIS AND OPTIMIZATION")
        
        # Test query analysis
        analysis_data = {
            "query": "senior react developers with 5 years experience"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/analyze",
            json=analysis_data
        )
        self.print_result("POST /api/v1/chat/analyze", response.status_code, response.json())
        
        # Test query optimization
        optimization_data = {
            "query": "i need someone good with computers"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/optimize",
            json=optimization_data
        )
        self.print_result("POST /api/v1/chat/optimize", response.status_code, response.json())
        
    def test_session_listing(self):
        """Test session listing and retrieval"""
        self.print_section("10. SESSION LISTING AND MANAGEMENT")
        
        # List all sessions
        response = requests.get(f"{self.base_url}/api/v1/chat/sessions")
        self.print_result("GET /api/v1/chat/sessions", response.status_code, response.json())
        
        # Get specific sessions
        for i, session_id in enumerate(self.session_ids):
            response = requests.get(f"{self.base_url}/api/v1/chat/sessions/{session_id}")
            self.print_result(f"GET /api/v1/chat/sessions/{session_id} (Session {i+1})", response.status_code, response.json())
            
    def test_resume_endpoints(self):
        """Test resume-related endpoints"""
        self.print_section("11. RESUME MANAGEMENT ENDPOINTS")
        
        # List resumes
        response = requests.get(f"{self.base_url}/api/v1/resumes/?limit=5")
        self.print_result("GET /api/v1/resumes/", response.status_code, response.json())
        
        # Test basic resume search
        search_data = {
            "query": "Python developer with machine learning experience",
            "limit": 3,
            "filters": {
                "skills": ["Python", "machine learning"]
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/resumes/search",
            json=search_data
        )
        self.print_result("POST /api/v1/resumes/search", response.status_code, response.json())
        
    def verify_database_storage(self):
        """Verify data storage in MongoDB and vector DB"""
        self.print_section("12. DATABASE STORAGE VERIFICATION")
        
        print("🔍 Checking if JD data is stored properly...")
        
        # Check JD storage through API
        if self.jd_ids:
            for jd_id in self.jd_ids:
                response = requests.get(f"{self.base_url}/api/v1/jd/{jd_id}")
                if response.status_code == 200:
                    jd_data = response.json()
                    print(f"✅ JD {jd_id} found in MongoDB")
                    print(f"   - Title: {jd_data.get('job_title', 'N/A')}")
                    print(f"   - Vector Count: {jd_data.get('vector_count', 0)}")
                    print(f"   - Has Vectors: {jd_data.get('has_vectors', False)}")
                else:
                    print(f"❌ JD {jd_id} not found in MongoDB")
                    
        # Check vector database through search results
        print("\n🔍 Verifying vector database storage through search...")
        if 'shortlist_results' in self.results and self.results['shortlist_results'].get('matches'):
            print(f"✅ Vector search returned {len(self.results['shortlist_results']['matches'])} matches")
            print("✅ Vector database is functioning properly")
        else:
            print("⚠️  No search results found - vector database may need verification")
            
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive EKOI API Testing")
        print(f"Base URL: {self.base_url}")
        
        try:
            self.test_health_endpoints()
            self.test_jd_upload()
            time.sleep(2)  # Allow time for processing
            self.test_jd_list_and_get()
            self.test_jd_search_and_shortlisting()
            self.test_chat_session_creation()
            time.sleep(1)
            self.test_chat_search_in_sessions()
            self.test_follow_up_questions()
            self.test_standalone_chat_search()
            self.test_query_analysis_and_optimization()
            self.test_session_listing()
            self.test_resume_endpoints()
            self.verify_database_storage()
            
            self.print_section("TESTING COMPLETE")
            print("✅ All endpoint tests completed!")
            print(f"📊 Created {len(self.session_ids)} chat sessions")
            print(f"📊 Uploaded {len(self.jd_ids)} job descriptions")
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            
        # Cleanup - delete test sessions
        print("\n🧹 Cleaning up test sessions...")
        for session_id in self.session_ids:
            try:
                response = requests.delete(f"{self.base_url}/api/v1/chat/sessions/{session_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted session {session_id}")
                else:
                    print(f"⚠️  Could not delete session {session_id}")
            except:
                print(f"⚠️  Error deleting session {session_id}")

if __name__ == "__main__":
    tester = EKOIAPITester()
    tester.run_comprehensive_test()
