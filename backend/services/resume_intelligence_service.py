"""Deterministic, reusable resume intelligence derived from parsed resumes."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from models.resume import Resume
from services.resume_service import ResumeService
from utils.text_utils import SECTION_ALIASES


@dataclass(frozen=True)
class ResumeSection:
    """A detected logical section in a resume."""

    name: str
    detected: bool


@dataclass(frozen=True)
class ResumeCompleteness:
    """Explainable completion assessment for the core resume fields."""

    score: int
    present_fields: list[str]
    missing_fields: list[str]


@dataclass(frozen=True)
class ResumeProfile:
    """Normalized profile assembled from an already parsed resume."""

    resume_id: int
    full_name: str | None
    email: str | None
    phone: str | None
    skills: list[str]
    sections: list[ResumeSection]
    completeness: ResumeCompleteness


@dataclass(frozen=True)
class ResumeStatistics:
    """Basic deterministic statistics about a resume's parsed content."""

    word_count: int
    character_count: int
    line_count: int
    skill_count: int
    normalized_skill_count: int
    duplicate_skill_count: int
    detected_section_count: int


@dataclass(frozen=True)
class ResumeQualityWarning:
    """An actionable, rule-based resume quality warning."""

    code: str
    severity: str
    message: str


SKILL_ALIASES = {
    "aws": "Amazon Web Services",
    "amazon web services": "Amazon Web Services",
    "azure": "Microsoft Azure",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "google cloud platform": "Google Cloud Platform",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "reactjs": "React",
    "react js": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue js": "Vue.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "k8s": "Kubernetes",
    "scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "rest": "REST API",
    "rest api": "REST API",
}

SECTION_NAMES = ("summary", "skills", "experience", "education", "projects", "certifications")
SECTION_HEADING_ALIASES = {
    "summary": {"about", "career objective", "objective", "professional summary", "profile", "summary"},
    **SECTION_ALIASES,
    "certifications": {"certificates", "certifications", "licenses and certifications"},
}


class ResumeIntelligenceService:
    """Produce deterministic intelligence views without modifying resume data."""

    def __init__(self, resume_service: ResumeService) -> None:
        self.resume_service = resume_service

    def get_profile(self, resume_id: int) -> ResumeProfile:
        resume = self.resume_service.get_resume(resume_id)
        sections = self.detect_sections(resume)
        return ResumeProfile(
            resume_id=resume.id,
            full_name=resume.full_name,
            email=resume.email,
            phone=resume.phone,
            skills=self.normalize_skills(resume.skills),
            sections=sections,
            completeness=self.analyze_completeness(resume, sections),
        )

    def get_normalized_skills(self, resume_id: int) -> list[str]:
        return self.normalize_skills(self.resume_service.get_resume(resume_id).skills)

    def get_statistics(self, resume_id: int) -> ResumeStatistics:
        resume = self.resume_service.get_resume(resume_id)
        normalized_skills = self.normalize_skills(resume.skills)
        duplicate_count = len(resume.skills) - len(normalized_skills)
        text = resume.raw_text or ""
        sections = self.detect_sections(resume)
        return ResumeStatistics(
            word_count=len(re.findall(r"\b\w+[+#.\-\w]*\b", text)),
            character_count=len(text),
            line_count=len([line for line in text.splitlines() if line.strip()]),
            skill_count=len(resume.skills),
            normalized_skill_count=len(normalized_skills),
            duplicate_skill_count=max(duplicate_count, 0),
            detected_section_count=sum(section.detected for section in sections),
        )

    def get_quality_warnings(self, resume_id: int) -> list[ResumeQualityWarning]:
        resume = self.resume_service.get_resume(resume_id)
        sections = self.detect_sections(resume)
        completeness = self.analyze_completeness(resume, sections)
        statistics = self.get_statistics(resume_id)
        warnings: list[ResumeQualityWarning] = []

        for field in completeness.missing_fields:
            warnings.append(self._missing_field_warning(field))
        if statistics.word_count < 150:
            warnings.append(ResumeQualityWarning(
                "low_word_count", "warning",
                "Resume text is short; add relevant accomplishments and responsibilities.",
            ))
        if statistics.duplicate_skill_count:
            warnings.append(ResumeQualityWarning(
                "duplicate_skills", "info",
                "Remove duplicate or equivalent skills to keep the skills section concise.",
            ))
        return warnings

    @staticmethod
    def normalize_skills(skills: list[str]) -> list[str]:
        """Canonicalize whitespace, aliases, case, and duplicate skills."""
        normalized: list[str] = []
        seen: set[str] = set()
        for skill in skills:
            clean_skill = " ".join(skill.split())
            if not clean_skill:
                continue
            canonical_key = clean_skill.casefold().replace(".", "").replace("-", " ")
            canonical_key = " ".join(canonical_key.split())
            canonical = SKILL_ALIASES.get(canonical_key, clean_skill)
            comparison_key = canonical.casefold()
            if comparison_key not in seen:
                seen.add(comparison_key)
                normalized.append(canonical)
        return normalized

    @staticmethod
    def detect_sections(resume: Resume) -> list[ResumeSection]:
        """Identify common resume sections from headings and parsed fields."""
        headings = {
            ResumeIntelligenceService._normalize_heading(line)
            for line in (resume.raw_text or "").splitlines()
        }
        parsed_values = {
            "skills": resume.skills,
            "experience": resume.experience,
            "education": resume.education,
            "projects": resume.projects,
        }
        return [
            ResumeSection(
                name=name,
                detected=bool(headings & SECTION_HEADING_ALIASES[name])
                or bool(parsed_values.get(name)),
            )
            for name in SECTION_NAMES
        ]

    @staticmethod
    def analyze_completeness(
        resume: Resume,
        sections: list[ResumeSection],
    ) -> ResumeCompleteness:
        """Assess core contact details and substantive resume sections."""
        checks = {
            "name": bool(resume.full_name),
            "email": bool(resume.email),
            "phone": bool(resume.phone),
            **{section.name: section.detected for section in sections if section.name in {"skills", "experience", "education", "projects"}},
        }
        present_fields = [field for field, present in checks.items() if present]
        missing_fields = [field for field, present in checks.items() if not present]
        return ResumeCompleteness(
            score=round(100 * len(present_fields) / len(checks)),
            present_fields=present_fields,
            missing_fields=missing_fields,
        )

    @staticmethod
    def _normalize_heading(value: str) -> str:
        return " ".join(re.sub(r"[^a-z]+", " ", value.casefold()).split())

    @staticmethod
    def _missing_field_warning(field: str) -> ResumeQualityWarning:
        messages = {
            "name": "Add a name so employers can identify the resume owner.",
            "email": "Add a professional email address for employer contact.",
            "phone": "Add a phone number for employer contact.",
            "skills": "Add a skills section with relevant technical or professional skills.",
            "experience": "Add experience entries that describe relevant responsibilities and outcomes.",
            "education": "Add education information relevant to the target roles.",
            "projects": "Consider adding relevant projects to demonstrate practical experience.",
        }
        severity = "warning" if field in {"email", "skills", "experience"} else "info"
        return ResumeQualityWarning(f"missing_{field}", severity, messages[field])
