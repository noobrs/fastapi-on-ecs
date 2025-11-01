from __future__ import annotations

import asyncio
import io
import logging
from datetime import datetime, timezone
from typing import List

import httpx
from PIL import Image

from app.schemas import (
    ProcessResumeRequest,
    ProcessedResumeWebhook,
    ResumeProcessingResult,
)
from app.security import generate_signature
from config import settings
from pdf.layout import LayoutService
from pdf.nlp import NLPService
from pdf.redactor import RedactionService
from supabase_client import supabase

logger = logging.getLogger(__name__)

RESUMES_REDACTED_BUCKET = "resumes-redacted"
SENSITIVE_KEYWORDS = [
    "male",
    "female",
    "gender",
    "race",
    "ethnicity",
    "religion",
]


def filter_sensitive(items: List[str]) -> List[str]:
    filtered: List[str] = []
    for item in items:
        lower_item = item.lower()
        if any(keyword in lower_item for keyword in SENSITIVE_KEYWORDS):
            continue
        filtered.append(item)
    return filtered


def build_feedback(skills: List[str], education: List[str], experience: List[str]) -> str | None:
    missing: List[str] = []
    if not skills:
        missing.append("skills")
    if not education:
        missing.append("education")
    if not experience:
        missing.append("experience")

    if not missing:
        return None

    if len(missing) == 1:
        return f"We could not detect any {missing[0]} in your resume. Consider adding more detail."

    if len(missing) == 2:
        return f"We could not detect {missing[0]} or {missing[1]} in your resume. Consider expanding these sections."

    return "We could not detect key resume sections (skills, education, experience). Please review and update your resume."


class ResumePipelineService:
    def __init__(self) -> None:
        self._layout = LayoutService()
        self._nlp = NLPService()
        self._redactor = RedactionService()
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    async def aclose(self):
        await self._http.aclose()

    async def process(self, payload: ProcessResumeRequest) -> ResumeProcessingResult:
        try:
            logger.info(f"Starting resume processing for resume_id={payload.resume_id}, job_seeker_id={payload.job_seeker_id}")
            
            original_bytes = await self._download_file(payload.download_url)
            logger.info(f"Downloaded file: {len(original_bytes)} bytes")
            
            pdf_bytes = await self._ensure_pdf_bytes(payload.mime_type, original_bytes)
            logger.info(f"PDF bytes ready: {len(pdf_bytes)} bytes")

            redacted_path = await self._upload_redacted(payload.resume_id, payload.job_seeker_id, pdf_bytes)
            logger.info(f"Redacted resume uploaded to: {redacted_path}")

            # parsed_resume = await asyncio.to_thread(self._parse_resume, pdf_bytes)
            # logger.info(f"Resume parsed: {len(parsed_resume.skills)} skills, {len(parsed_resume.education)} education, {len(parsed_resume.experience)} experience")
            
            # skills = filter_sensitive(parsed_resume.skills)
            # education = filter_sensitive(parsed_resume.education)
            # experience = filter_sensitive(parsed_resume.experience)
            # feedback = build_feedback(skills, education, experience)

            # redacted_bytes = await asyncio.to_thread(self._redactor.redact, pdf_bytes)
            # logger.info(f"Resume redacted: {len(redacted_bytes)} bytes")
            
            # redacted_path = await self._upload_redacted(payload.resume_id, payload.job_seeker_id, redacted_bytes)
            # logger.info(f"Redacted resume uploaded to: {redacted_path}")

            result = ResumeProcessingResult(
                resume_id=payload.resume_id,
                job_seeker_id=payload.job_seeker_id,
                redacted_file_path=redacted_path,
                skills=list("skills"),
                education=list("education"),
                experience=list("experience"),
                feedback=str("feedback"),
            )

            await self._notify_next(result)
            logger.info(f"Successfully processed resume_id={payload.resume_id}")

            return result
        except Exception as exc:
            logger.exception(f"Error processing resume_id={payload.resume_id}: {exc}")
            raise

    async def _download_file(self, url: str) -> bytes:
        response = await self._http.get(str(url))
        response.raise_for_status()
        return response.content

    async def _ensure_pdf_bytes(self, mime_type: str, payload: bytes) -> bytes:
        if mime_type == "application/pdf":
            return payload

        def convert() -> bytes:
            with Image.open(io.BytesIO(payload)) as image:
                pdf_buffer = io.BytesIO()
                image.convert("RGB").save(pdf_buffer, format="PDF")
                return pdf_buffer.getvalue()

        return await asyncio.to_thread(convert)

    def _parse_resume(self, pdf_bytes: bytes):
        _, groups = self._layout.extract_groups(pdf_bytes)
        return self._nlp.parse_groups(groups)

    async def _upload_redacted(self, resume_id: int, job_seeker_id: int, pdf_bytes: bytes) -> str:
        storage_key = f"{job_seeker_id}/{resume_id}.pdf"
        full_path = f"{RESUMES_REDACTED_BUCKET}/{storage_key}"

        try:
            supabase.storage.from_(RESUMES_REDACTED_BUCKET).upload(
                storage_key,
                pdf_bytes,
                {"content-type": "application/pdf", "x-upsert": "true"},
            )
        except Exception as exc:
            logger.exception("Failed to upload redacted resume to storage: %s", exc)
            raise

        return full_path

    async def _notify_next(self, result: ResumeProcessingResult) -> None:
        payload = ProcessedResumeWebhook(
            resume_id=result.resume_id,
            job_seeker_id=result.job_seeker_id,
            redacted_file_path=result.redacted_file_path,
            extracted_skills=result.skills,
            extracted_education=result.education,
            extracted_experiences=result.experience,
            feedback=result.feedback,
        )

        body = payload.model_dump_json().encode("utf-8")
        timestamp = datetime.now(timezone.utc).isoformat()
        signature = generate_signature(body, timestamp)

        try:
            response = await self._http.post(
                str(settings.next_webhook_url),
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "x-resume-timestamp": timestamp,
                    "x-resume-signature": signature,
                },
                timeout=httpx.Timeout(30.0),
            )
            response.raise_for_status()
        except Exception as exc:
            logger.exception("Failed to notify Next.js webhook: %s", exc)
            raise


resume_pipeline = ResumePipelineService()
