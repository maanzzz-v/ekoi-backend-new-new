"""File processing and text extraction utilities."""

import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfReader

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available. PDF processing disabled.")

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. DOCX processing disabled.")


class FileProcessor:
    """File processing and text extraction service."""

    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> str:
        """Extract text from uploaded file."""
        try:
            if file_type.lower() == "pdf":
                return FileProcessor._extract_from_pdf(file_path)
            elif file_type.lower() == "docx":
                return FileProcessor._extract_from_docx(file_path)
            elif file_type.lower() == "txt":
                return FileProcessor._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        if not PDF_AVAILABLE:
            raise RuntimeError("PDF processing not available")

        try:
            with open(file_path, "rb") as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {e}")
            raise

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            raise RuntimeError("DOCX processing not available")

        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading DOCX file {file_path}: {e}")
            raise

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as file:
                    return file.read().strip()
            except Exception as e:
                logger.error(f"Error reading TXT file {file_path}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error reading TXT file {file_path}: {e}")
            raise


class ResumeParser:
    """Resume-specific text parsing and information extraction."""

    @staticmethod
    def parse_resume_text(text: str) -> Dict[str, Any]:
        """Parse resume text and extract structured information."""
        parsed_info = {
            "name": ResumeParser._extract_name(text),
            "email": ResumeParser._extract_email(text),
            "phone": ResumeParser._extract_phone(text),
            "skills": ResumeParser._extract_skills(text),
            "experience": ResumeParser._extract_experience(text),
            "education": ResumeParser._extract_education(text),
            "summary": ResumeParser._extract_summary(text),
        }

        return parsed_info

    @staticmethod
    def _extract_name(text: str) -> Optional[str]:
        """Extract name from resume text."""
        lines = text.split("\n")
        # Often the name is in the first few lines
        for line in lines[:5]:
            line = line.strip()
            if (
                line
                and len(line.split()) <= 4
                and not any(char.isdigit() for char in line)
            ):
                # Simple heuristic: short line without numbers
                if "@" not in line and not line.startswith(
                    ("Email", "Phone", "Address")
                ):
                    return line
        return None

    @staticmethod
    def _extract_email(text: str) -> Optional[str]:
        """Extract email from resume text."""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None

    @staticmethod
    def _extract_phone(text: str) -> Optional[str]:
        """Extract phone number from resume text."""
        phone_patterns = [
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            r"\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b",
            r"\b\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}\b",
        ]

        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None

    @staticmethod
    def _extract_skills(text: str) -> List[str]:
        """Extract skills from resume text."""
        # Common technical skills
        common_skills = [
            "python",
            "java",
            "javascript",
            "c++",
            "c#",
            "html",
            "css",
            "sql",
            "react",
            "angular",
            "vue",
            "node.js",
            "django",
            "flask",
            "spring",
            "aws",
            "azure",
            "docker",
            "kubernetes",
            "git",
            "linux",
            "windows",
            "machine learning",
            "data science",
            "artificial intelligence",
            "tensorflow",
            "pytorch",
            "pandas",
            "numpy",
            "scikit-learn",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "agile",
            "scrum",
            "devops",
            "ci/cd",
            "jenkins",
            "terraform",
        ]

        text_lower = text.lower()
        found_skills = []

        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill.title())

        return list(set(found_skills))  # Remove duplicates

    @staticmethod
    def _extract_experience(text: str) -> List[Dict[str, Any]]:
        """Extract work experience from resume text."""
        # This is a simplified extraction - in practice, you'd use more sophisticated NLP
        experience = []

        # Look for common experience indicators
        exp_patterns = [
            r"(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}|present",
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(19|20)\d{2}",
        ]

        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in exp_patterns):
                if len(line) > 10:  # Avoid short lines
                    experience.append({"description": line, "extracted": True})

        return experience[:5]  # Return top 5 experiences

    @staticmethod
    def _extract_education(text: str) -> List[Dict[str, Any]]:
        """Extract education information from resume text."""
        education = []

        # Common education keywords
        edu_keywords = [
            "bachelor",
            "master",
            "phd",
            "doctorate",
            "degree",
            "university",
            "college",
            "institute",
            "school",
            "education",
            "graduated",
        ]

        lines = text.split("\n")
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in edu_keywords):
                if len(line.strip()) > 10:
                    education.append({"description": line.strip(), "extracted": True})

        return education[:3]  # Return top 3 education entries

    @staticmethod
    def _extract_summary(text: str) -> Optional[str]:
        """Extract summary/objective from resume text."""
        lines = text.split("\n")

        summary_keywords = ["summary", "objective", "profile", "about"]

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in summary_keywords):
                # Look for the next few lines as summary
                summary_lines = []
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.lower().startswith(
                        ("experience", "education", "skills")
                    ):
                        summary_lines.append(next_line)
                    else:
                        break

                if summary_lines:
                    return " ".join(summary_lines)

        # If no explicit summary section, use first paragraph
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1 and len(paragraphs[1].strip()) > 50:
            return paragraphs[1].strip()[:500]  # First 500 chars

        return None

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for better vector indexing."""
        sentences = re.split(r"[.!?]+", text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]  # Return original text if no chunks
