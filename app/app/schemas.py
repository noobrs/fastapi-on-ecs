from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class Entity(BaseModel):
    text: str
    label: str
    score: Optional[float] = None


class Section(BaseModel):
    heading: str
    text: str


class ParsedResume(BaseModel):
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    raw_entities: List[Entity] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)


class ProcessResumeRequest(BaseModel):
    resume_id: int
    job_seeker_id: int
    original_file_path: str
    download_url: HttpUrl
    original_filename: str
    mime_type: str
    size: int


class ResumeProcessingResult(BaseModel):
    resume_id: int
    job_seeker_id: int
    redacted_file_path: str
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    feedback: Optional[str] = None


class ProcessedResumeWebhook(BaseModel):
    resume_id: int
    job_seeker_id: int
    redacted_file_path: str
    extracted_skills: List[str] = Field(default_factory=list)
    extracted_education: List[str] = Field(default_factory=list)
    extracted_experiences: List[str] = Field(default_factory=list)
    feedback: Optional[str] = None
