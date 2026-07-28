"""Deterministic intelligence extracted from an unpersisted job description."""

from __future__ import annotations

import re
from dataclasses import dataclass

from utils.skill_normalization import normalize_skills


TECHNOLOGY_TERMS = (
    "Python", "Java", "C#", "C++", "JavaScript", "TypeScript", "React", "ReactJS",
    "Angular", "Vue.js", "Node.js", "FastAPI", "Django", "Flask", "Spring",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "Terraform", "Jenkins", "Git", "Linux", "AWS", "Azure", "GCP",
    "Amazon Web Services", "Google Cloud Platform", "REST API", "GraphQL",
    "Kafka", "RabbitMQ", "Spark", "Hadoop", "Pandas", "NumPy", "Scikit-learn",
    "Machine Learning", "Data Analysis", "Tableau", "Power BI",
)

REQUIRED_MARKERS = ("required", "requirements", "must have", "minimum qualifications", "what you need")
PREFERRED_MARKERS = ("preferred", "nice to have", "bonus", "desired", "plus", "preferred qualifications")
EMPLOYMENT_TYPES = ("full-time", "part-time", "contract", "temporary", "internship", "freelance", "apprenticeship")
DEGREE_PATTERNS = {
    "Bachelor's": r"\b(?:bachelor(?:'s)?|b\.?s\.?|b\.?a\.?|b\.tech)\b",
    "Master's": r"\b(?:master(?:'s)?|m\.?s\.?|m\.tech|mba)\b",
    "PhD": r"\b(?:ph\.?d\.?|doctorate|doctoral)\b",
    "Associate": r"\bassociate(?:'s)?\b",
}


@dataclass(frozen=True)
class JobExperience:
    minimum_years: int | None
    maximum_years: int | None
    requirements: list[str]


@dataclass(frozen=True)
class JobEducation:
    degrees: list[str]
    fields: list[str]


@dataclass(frozen=True)
class JobLocation:
    locations: list[str]
    remote_type: str | None


@dataclass(frozen=True)
class JobSalary:
    raw_text: str | None
    minimum: int | None
    maximum: int | None
    currency: str | None
    period: str | None


@dataclass(frozen=True)
class JobEmployment:
    employment_types: list[str]
    remote_type: str | None


@dataclass(frozen=True)
class JobProfile:
    title: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    experience: JobExperience
    education: JobEducation
    location: JobLocation
    salary: JobSalary
    employment: JobEmployment
    responsibilities: list[str]


@dataclass(frozen=True)
class JobStatistics:
    word_count: int
    character_count: int
    line_count: int
    required_skill_count: int
    preferred_skill_count: int
    responsibility_count: int
    experience_requirement_count: int


@dataclass(frozen=True)
class JobQualityWarning:
    code: str
    severity: str
    message: str


class JobDescriptionIntelligenceService:
    """Extract explainable job intelligence using deterministic text rules."""

    def analyze(self, description: str, title: str | None = None) -> JobProfile:
        lines = self._meaningful_lines(description)
        required, preferred = self.extract_skills(description)
        location = self.extract_location(description)
        employment = self.extract_employment(description, location.remote_type)
        return JobProfile(
            title=self.extract_title(lines, title),
            required_skills=required,
            preferred_skills=preferred,
            experience=self.extract_experience(description),
            education=self.extract_education(description),
            location=location,
            salary=self.extract_salary(description),
            employment=employment,
            responsibilities=self.extract_responsibilities(lines),
        )

    def get_statistics(self, description: str, title: str | None = None) -> JobStatistics:
        profile = self.analyze(description, title)
        return JobStatistics(
            word_count=len(re.findall(r"\b[\w+#.-]+\b", description)),
            character_count=len(description),
            line_count=len(self._meaningful_lines(description)),
            required_skill_count=len(profile.required_skills),
            preferred_skill_count=len(profile.preferred_skills),
            responsibility_count=len(profile.responsibilities),
            experience_requirement_count=len(profile.experience.requirements),
        )

    def get_quality_warnings(self, description: str, title: str | None = None) -> list[JobQualityWarning]:
        profile = self.analyze(description, title)
        statistics = self.get_statistics(description, title)
        warnings: list[JobQualityWarning] = []
        if not profile.title:
            warnings.append(JobQualityWarning("missing_title", "warning", "Add a job title to make the role clear."))
        if not profile.required_skills:
            warnings.append(JobQualityWarning("missing_required_skills", "warning", "State the required skills or qualifications for the role."))
        if not profile.responsibilities:
            warnings.append(JobQualityWarning("missing_responsibilities", "info", "Add responsibilities so candidates can understand the work."))
        if not profile.location.locations and not profile.location.remote_type:
            warnings.append(JobQualityWarning("missing_location", "info", "Specify a work location or remote-work arrangement."))
        if statistics.word_count < 75:
            warnings.append(JobQualityWarning("low_word_count", "warning", "Job description is short; include sufficient role and qualification detail."))
        if profile.required_skills and profile.preferred_skills:
            overlap = set(profile.required_skills) & set(profile.preferred_skills)
            if overlap:
                warnings.append(JobQualityWarning("overlapping_skill_priority", "info", "Classify each skill as required or preferred, not both."))
        return warnings

    @staticmethod
    def extract_title(lines: list[str], supplied_title: str | None) -> str | None:
        if supplied_title and supplied_title.strip():
            return " ".join(supplied_title.split())
        for line in lines[:5]:
            match = re.match(r"(?:job\s+)?title\s*[:\-]\s*(.+)", line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return lines[0] if lines and len(lines[0]) <= 100 and not lines[0].endswith(":") else None

    @classmethod
    def extract_skills(cls, description: str) -> tuple[list[str], list[str]]:
        """Classify known technology terms using qualification section markers."""
        required: list[str] = []
        preferred: list[str] = []
        priority = "required"
        for line in cls._meaningful_lines(description):
            lowered = line.casefold().rstrip(":")
            if any(marker in lowered for marker in PREFERRED_MARKERS):
                priority = "preferred"
            elif any(marker in lowered for marker in REQUIRED_MARKERS):
                priority = "required"
            skills = cls._skills_in_text(line)
            if priority == "preferred":
                preferred.extend(skills)
            else:
                required.extend(skills)
        normalized_preferred = normalize_skills(preferred)
        normalized_required = normalize_skills(required)
        preferred_keys = {skill.casefold() for skill in normalized_preferred}
        return [skill for skill in normalized_required if skill.casefold() not in preferred_keys], normalized_preferred
    @staticmethod
    def extract_experience(description: str) -> JobExperience:
        requirements: list[str] = []
        minimum_years: int | None = None
        maximum_years: int | None = None
        for match in re.finditer(r"\b(\d+)\s*(?:-|to|Ã¢â‚¬â€œ)\s*(\d+)\+?\s+years?", description, re.IGNORECASE):
            low, high = int(match.group(1)), int(match.group(2))
            minimum_years = low if minimum_years is None else min(minimum_years, low)
            maximum_years = high if maximum_years is None else max(maximum_years, high)
            requirements.append(match.group(0))
        for match in re.finditer(r"\b(\d+)\+?\s+years?(?:\s+of)?\s+(?:experience|exp)\b", description, re.IGNORECASE):
            years = int(match.group(1))
            minimum_years = years if minimum_years is None else min(minimum_years, years)
            requirements.append(match.group(0))
        return JobExperience(minimum_years, maximum_years, list(dict.fromkeys(requirements)))

    @staticmethod
    def extract_education(description: str) -> JobEducation:
        degrees = [name for name, pattern in DEGREE_PATTERNS.items() if re.search(pattern, description, re.IGNORECASE)]
        fields = []
        for field in ("Computer Science", "Engineering", "Information Technology", "Business", "Mathematics", "Data Science"):
            if re.search(rf"\b{re.escape(field)}\b", description, re.IGNORECASE):
                fields.append(field)
        return JobEducation(degrees, fields)

    @staticmethod
    def extract_location(description: str) -> JobLocation:
        lowered = description.casefold()
        remote_type = "remote" if re.search(r"\bremote\b", lowered) else "hybrid" if re.search(r"\bhybrid\b", lowered) else "onsite" if re.search(r"\b(?:on-site|onsite|in-office)\b", lowered) else None
        locations = []
        for match in re.finditer(r"\b(?:location|based in|office)\s*[:\-]?\s*([A-Z][A-Za-z .'-]+(?:,\s*[A-Z][A-Za-z .'-]+)?)", description):
            location = match.group(1).strip(" .")
            if location and location not in locations:
                locations.append(location)
        return JobLocation(locations, remote_type)

    @staticmethod
    def extract_salary(description: str) -> JobSalary:
        salary_match = re.search(r"(?P<currency>[$Ã¢â€šÂ¬Ã‚Â£Ã¢â€šÂ¹]|USD|EUR|GBP|INR)\s*(?P<low>\d{1,3}(?:[, ]\d{3})+|\d{2,3}(?:k|K)?)(?:\s*(?:-|to|Ã¢â‚¬â€œ)\s*(?P<currency2>[$Ã¢â€šÂ¬Ã‚Â£Ã¢â€šÂ¹]|USD|EUR|GBP|INR)?\s*(?P<high>\d{1,3}(?:[, ]\d{3})+|\d{2,3}(?:k|K)?))?\s*(?:/(?P<period>year|yr|month|hour)|per\s+(?P<per_period>year|month|hour))?", description)
        if not salary_match:
            return JobSalary(None, None, None, None, None)
        def amount(value: str | None) -> int | None:
            if not value:
                return None
            cleaned = value.replace(",", "").replace(" ", "")
            return int(float(cleaned[:-1]) * 1000) if cleaned.casefold().endswith("k") else int(cleaned)
        return JobSalary(salary_match.group(0), amount(salary_match.group("low")), amount(salary_match.group("high")), salary_match.group("currency"), salary_match.group("period") or salary_match.group("per_period"))

    @staticmethod
    def extract_employment(description: str, remote_type: str | None) -> JobEmployment:
        lowered = description.casefold()
        return JobEmployment([kind for kind in EMPLOYMENT_TYPES if kind in lowered], remote_type)

    @staticmethod
    def extract_responsibilities(lines: list[str]) -> list[str]:
        section = False
        responsibilities: list[str] = []
        for line in lines:
            normalized = line.casefold().rstrip(":")
            if normalized in {"responsibilities", "what you will do", "what you'll do", "duties"}:
                section = True
                continue
            if section and (normalized in {"requirements", "qualifications", "preferred qualifications", "benefits"}):
                break
            if section and (line.startswith(("-", "*", "Ã¢â‚¬Â¢")) or re.match(r"\d+[.)]", line)):
                responsibilities.append(re.sub(r"^(?:[-*Ã¢â‚¬Â¢]|\d+[.)])\s*", "", line).strip())
        return responsibilities

    @classmethod
    def _skills_in_text(cls, value: str) -> list[str]:
        found = []
        for term in TECHNOLOGY_TERMS:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", value, re.IGNORECASE):
                found.append(term)
        return normalize_skills(found)

    @staticmethod
    def _meaningful_lines(description: str) -> list[str]:
        return [" ".join(line.strip().split()) for line in description.splitlines() if line.strip()]
