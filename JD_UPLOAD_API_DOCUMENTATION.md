# 📄 **JD Upload API Endpoint Documentation**

## 🎯 **Complete JD Upload & Search API Reference**

### **Base URL**

```
http://localhost:8000
```

---

## **1. 📤 JD Upload Endpoint**

### **Endpoint Details**

- **URL**: `POST /api/v1/jd/upload`
- **Purpose**: Upload a job description file and associate it with a chat session
- **Content-Type**: `multipart/form-data`
- **Authentication**: None required

### **Request Parameters**

#### **Form Data**

```
session_id: string (required) - Chat session ID to associate the JD with
file: File (required) - Job description file (PDF or TXT format)
```

#### **JavaScript/Frontend Example**

```javascript
// Example: Upload JD file
const uploadJD = async (sessionId, file) => {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("file", file);

  try {
    const response = await fetch("http://localhost:8000/api/v1/jd/upload", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();
    console.log("JD Upload Result:", result);
    return result;
  } catch (error) {
    console.error("JD Upload Error:", error);
    throw error;
  }
};

// Usage
const fileInput = document.getElementById("jd-file");
const file = fileInput.files[0];
const sessionId = "your-session-id";

uploadJD(sessionId, file);
```

#### **cURL Example**

```bash
curl -X POST "http://localhost:8000/api/v1/jd/upload" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/job_description.pdf"
```

### **Response Format**

#### **Success Response (200)**

```json
{
  "message": "Job description 'Senior_Python_Developer.pdf' uploaded and processed successfully",
  "job_description_id": "jd_67890abcdef",
  "file_name": "Senior_Python_Developer.pdf",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "extracted_text": "Senior Python Developer Position\n\nWe are seeking an experienced Senior Python Developer with 5+ years of experience...",
  "success": true
}
```

#### **Error Responses**

```json
// 404 - Session not found
{
    "error": "Session not found"
}

// 400 - Invalid file format
{
    "error": "Invalid file format. Only PDF and TXT files are supported"
}

// 500 - Server error
{
    "error": "Error occurred during job description upload"
}
```

---

## **2. 🔍 JD Search Endpoint**

### **Endpoint Details**

- **URL**: `POST /api/v1/jd/search`
- **Purpose**: Search for resumes matching the uploaded job description
- **Content-Type**: `application/json`

### **Request Body**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "top_k": 10,
  "filters": {
    "experience_years": 5,
    "skills": ["python", "django"]
  }
}
```

#### **JavaScript Example**

```javascript
const searchResumes = async (sessionId, topK = 10, filters = null) => {
  try {
    const response = await fetch("http://localhost:8000/api/v1/jd/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        top_k: topK,
        filters: filters,
      }),
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Search Error:", error);
    throw error;
  }
};
```

### **Response Format**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_description_id": "jd_67890abcdef",
  "job_description_text": "Senior Python Developer Position\n\nWe are seeking an experienced...",
  "matches": [
    {
      "id": "resume_12345",
      "file_name": "john_smith_resume.pdf",
      "score": 0.92,
      "original_score": 0.87,
      "weighted_score": 0.92,
      "extracted_info": {
        "name": "John Smith",
        "email": "john.smith@email.com",
        "skills": ["Python", "Django", "PostgreSQL", "AWS"],
        "experience": [
          "Senior Software Engineer at TechCorp (2021-Present)",
          "Software Engineer at StartupXYZ (2018-2021)"
        ],
        "education": ["Master of Science in Computer Science"],
        "summary": "Experienced Senior Software Engineer with 7 years..."
      },
      "relevant_text": "Python development, Django framework, RESTful APIs...",
      "score_breakdown": {
        "education": 0.25,
        "skill_match": 0.35,
        "experience": 0.24,
        "domain_relevance": 0.15
      },
      "weightage_applied": {
        "education": 0.25,
        "skill_match": 0.35,
        "experience": 0.25,
        "domain_relevance": 0.15
      }
    }
  ],
  "total_results": 25,
  "processing_time": 2.34,
  "search_results_stored": true,
  "success": true
}
```

---

## **3. 💬 JD Follow-up Questions Endpoint**

### **Endpoint Details**

- **URL**: `POST /api/v1/jd/followup`
- **Purpose**: Ask follow-up questions about the stored search results

### **Request Body**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Which candidates have the most Python experience?"
}
```

### **Response Format**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Which candidates have the most Python experience?",
  "answer": "Based on the search results, the top 3 candidates with the most Python experience are:\n\n1. John Smith - 7 years of Python development...",
  "candidates_analyzed": 25,
  "jd_filename": "Senior_Python_Developer.pdf",
  "success": true
}
```

---

## **4. 📊 Get Search Results Endpoint**

### **Endpoint Details**

- **URL**: `GET /api/v1/jd/session/{session_id}/results`
- **Purpose**: Retrieve stored search results for a session

### **JavaScript Example**

```javascript
const getSearchResults = async (sessionId) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/jd/session/${sessionId}/results`
    );
    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Get Results Error:", error);
    throw error;
  }
};
```

### **Response Format**

```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "search_results": {
        "jd_id": "jd_67890abcdef",
        "jd_text": "Senior Python Developer Position...",
        "jd_filename": "Senior_Python_Developer.pdf",
        "matches": [...],
        "total_matches": 25,
        "search_timestamp": "2025-08-14T10:30:00Z"
    },
    "success": true
}
```

---

## **5. � Download Shortlisted Resumes Endpoint**

### **Endpoint Details**

- **URL**: `GET /api/v1/jd/session/{session_id}/download?top_n=10&format=zip`
- **Purpose**: Download the shortlisted resume files as a ZIP package
- **Content-Type**: Returns `application/zip`

### **Query Parameters**

- `top_n`: Number of top candidates to download (default: 10, max: 50)
- `format`: Download format - only 'zip' supported currently

### **JavaScript Example**

```javascript
const downloadShortlistedResumes = async (sessionId, topN = 10) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/jd/session/${sessionId}/download?top_n=${topN}&format=zip`
    );

    if (!response.ok) {
      throw new Error("Download failed");
    }

    // Get the filename from headers
    const filename =
      response.headers
        .get("Content-Disposition")
        ?.split("filename=")[1]
        ?.replace(/"/g, "") ||
      `shortlisted_candidates_${sessionId.slice(0, 8)}.zip`;

    // Convert response to blob and trigger download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    // Cleanup
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    return {
      success: true,
      filename: filename,
      totalCandidates: response.headers.get("X-Total-Candidates"),
      filesIncluded: response.headers.get("X-Files-Included"),
    };
  } catch (error) {
    console.error("Download Error:", error);
    throw error;
  }
};

// Usage
downloadShortlistedResumes("your-session-id", 15);
```

### **Response Format**

- **Success**: Returns ZIP file for download
- **Headers**:
  ```
  Content-Type: application/zip
  Content-Disposition: attachment; filename=shortlisted_candidates_abc12345_10_resumes.zip
  X-Total-Candidates: 10
  X-Files-Included: 8
  ```

### **ZIP File Contents**

The downloaded ZIP file contains:

1. **SHORTLIST_SUMMARY.txt** - Detailed report with:

   - Job description details
   - Candidate rankings and scores
   - Score breakdowns (Education, Skills, Experience, Domain)
   - Contact information and skills summary

2. **Resume Files** - Named as:
   ```
   Rank_01_Score_0.92_John_Smith_resume.pdf
   Rank_02_Score_0.87_Jane_Doe_cv.pdf
   Rank_03_Score_0.84_Bob_Wilson_resume.pdf
   ```

### **cURL Example**

```bash
curl -X GET "http://localhost:8000/api/v1/jd/session/550e8400-e29b-41d4-a716-446655440000/download?top_n=5" \
  -H "Accept: application/zip" \
  -o "shortlisted_candidates.zip"
```

### **Error Responses**

```json
// 404 - Session not found
{
    "error": "Session not found"
}

// 404 - No search results
{
    "error": "No JD search results found for this session. Please upload a JD and search first."
}

// 404 - No files found
{
    "error": "No resume files could be found for download"
}
```

---

## **6. �🗑️ Delete JD Endpoint**

## **6. 🗑️ Delete JD Endpoint**

### **Endpoint Details**

- **URL**: `DELETE /api/v1/jd/session/{session_id}`
- **Purpose**: Delete the job description associated with a session

### **JavaScript Example**

```javascript
const deleteJD = async (sessionId) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/jd/session/${sessionId}`,
      {
        method: "DELETE",
      }
    );
    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Delete JD Error:", error);
    throw error;
  }
};
```

---

## **🚀 Complete Frontend Integration Example**

### **React Component Example**

```jsx
import React, { useState } from "react";

const JDUploadComponent = ({ sessionId }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [results, setResults] = useState(null);

  const handleFileUpload = async () => {
    if (!file || !sessionId) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("session_id", sessionId);
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/api/v1/jd/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      console.log("Upload successful:", result);

      // Automatically search after upload
      await handleSearch();
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async () => {
    setSearching(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/jd/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          top_k: 20,
        }),
      });

      const result = await response.json();
      setResults(result);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setSearching(false);
    }
  };

  const handleDownload = async (topN = 10) => {
    setDownloading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/jd/session/${sessionId}/download?top_n=${topN}&format=zip`
      );

      if (!response.ok) {
        throw new Error("Download failed");
      }

      const filename =
        response.headers
          .get("Content-Disposition")
          ?.split("filename=")[1]
          ?.replace(/"/g, "") ||
        `shortlisted_candidates_${sessionId.slice(0, 8)}.zip`;

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();

      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Download failed:", error);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div>
      <div>
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button onClick={handleFileUpload} disabled={!file || uploading}>
          {uploading ? "Uploading..." : "Upload JD"}
        </button>
      </div>

      {results && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <h3>Search Results ({results.total_results} candidates found)</h3>
            <div>
              <button
                onClick={() => handleDownload(5)}
                disabled={downloading}
                style={{ marginRight: "10px" }}
              >
                {downloading ? "Downloading..." : "Download Top 5"}
              </button>
              <button onClick={() => handleDownload(10)} disabled={downloading}>
                {downloading ? "Downloading..." : "Download Top 10"}
              </button>
            </div>
          </div>

          <div>
            {results.matches.slice(0, 10).map((candidate, index) => (
              <div
                key={index}
                style={{
                  border: "1px solid #ccc",
                  margin: "10px",
                  padding: "10px",
                }}
              >
                <h4>
                  #{index + 1} -{" "}
                  {candidate.extracted_info?.name || candidate.file_name}
                </h4>
                <p>
                  <strong>Score:</strong> {(candidate.score * 100).toFixed(1)}%
                </p>
                <p>
                  <strong>Skills:</strong>{" "}
                  {candidate.extracted_info?.skills?.join(", ") || "N/A"}
                </p>
                <p>
                  <strong>Experience:</strong>{" "}
                  {candidate.extracted_info?.experience?.length || 0} roles
                </p>

                {candidate.score_breakdown && (
                  <div style={{ fontSize: "0.9em", color: "#666" }}>
                    <strong>Score Breakdown:</strong>
                    <span>
                      {" "}
                      Education: {(
                        candidate.score_breakdown.education * 100
                      ).toFixed(0)}%
                    </span>
                    <span>
                      {" "}
                      | Skills: {(
                        candidate.score_breakdown.skill_match * 100
                      ).toFixed(0)}%
                    </span>
                    <span>
                      {" "}
                      | Experience: {(
                        candidate.score_breakdown.experience * 100
                      ).toFixed(0)}%
                    </span>
                    <span>
                      {" "}
                      | Domain: {(
                        candidate.score_breakdown.domain_relevance * 100
                      ).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default JDUploadComponent;
```

---

## **📝 Integration Checklist**

### **Frontend Requirements**

- [ ] File input component for PDF/TXT uploads
- [ ] Session management (session_id)
- [ ] Form data handling for file uploads
- [ ] JSON request/response handling
- [ ] **File download handling with Blob API**
- [ ] Error handling for various HTTP status codes
- [ ] Loading states for upload, search, and download operations

### **Enhanced Workflow Implementation**

1. **Create Session** → Get session_id
2. **Upload JD** → `POST /api/v1/jd/upload`
3. **Search Resumes** → `POST /api/v1/jd/search`
4. **Display Results** → Parse response.matches array
5. **Download Shortlisted** → `GET /api/v1/jd/session/{session_id}/download`
6. **Follow-up Questions** → `POST /api/v1/jd/followup`

### **Download Features**

- **ZIP Package**: Contains original resume files + summary report
- **Smart Naming**: Files named with rank, score, and candidate name
- **Detailed Summary**: Complete report with scores and candidate details
- **Flexible Count**: Download top 5, 10, 15, or custom number
- **Progress Tracking**: Headers show total candidates vs. files included

### **Error Handling**

```javascript
const handleAPIError = (response) => {
  if (!response.ok) {
    switch (response.status) {
      case 404:
        throw new Error("Session not found or no search results available");
      case 400:
        throw new Error("Invalid request or file format");
      case 500:
        throw new Error("Server error occurred");
      default:
        throw new Error("Unknown error occurred");
    }
  }
  return response.json();
};
```

## **🎯 New Download Endpoint Summary**

**URL**: `GET /api/v1/jd/session/{session_id}/download?top_n=10`

**What you get**:

- ZIP file with top N resume files
- Detailed summary report (TXT format)
- Smart file naming with ranks and scores
- Contact info and skills breakdown

**Perfect for**: Recruiters who need to download and review the best candidates offline, share with hiring managers, or archive shortlisted candidates.

This completes your JD upload → search → download workflow! 🚀
