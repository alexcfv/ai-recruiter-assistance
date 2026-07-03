from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GitHubAnalysis(BaseModel):
    code_quality: Optional[str] = Field(None, description="Assessment of code quality")
    technical_depth: Optional[str] = Field(None, description="Assessment of technical depth")
    architecture_patterns: List[str] = Field(default_factory=list)
    key_technologies: List[str] = Field(default_factory=list)
    overall_assessment: Optional[str] = Field(None, description="Overall technical assessment")

class ExperienceItem(BaseModel):
    role: str
    company: str
    description: str

class EducationItem(BaseModel):
    degree: str
    institution: str

class ProjectItem(BaseModel):
    name: str
    description: str

class CandidateProfile(BaseModel):
    summary: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    github_analysis: Optional[GitHubAnalysis] = None

class Candidate(BaseModel):
    source: str
    score: float
    explanation: str
    profile: CandidateProfile

class SearchRequest(BaseModel):
    query: str = Field(..., example="Senior Python Developer with FastAPI experience")
    top_k: int = Field(default=3, ge=1, le=10)

class SearchResponse(BaseModel):
    query: str
    candidates: List[Candidate]
    error: Optional[str] = None

class AnalyticsRequest(BaseModel):
    question: str = Field(..., example="How many candidates know React?")

class AnalyticsResponse(BaseModel):
    question: str
    answer: str

class IndexRequest(BaseModel):
    path: str = Field(..., example="./resumes")

class IndexResponse(BaseModel):
    status: str
    message: str
    indexed_count: int
    new_chunks: int = 0
    files_processed: int = 0
