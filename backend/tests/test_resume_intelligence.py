import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.resume import Resume
from services.resume_intelligence_service import ResumeIntelligenceService
from services.resume_service import ResumeNotFoundError


class ResumeLookupService:
    def __init__(self, resume: Resume | None) -> None:
        self.resume = resume

    def get_resume(self, resume_id: int) -> Resume:
        if self.resume is None or resume_id != self.resume.id:
            raise ResumeNotFoundError(f"Resume with ID {resume_id} was not found.")
        return self.resume


def make_resume() -> Resume:
    return Resume(
        id=42,
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="1234567890",
        raw_text=(
            "Ada Lovelace\nada@example.com\n1234567890\n\n"
            "Professional Summary\nBackend engineer\n\n"
            "Skills\nPython, AWS, JavaScript\n\n"
            "Experience\nBuilt reliable services\n\n"
            "Education\nComputer Science\n\n"
            "Projects\nJob Automation Platform"
        ),
        skills=["Python", "AWS", "Amazon Web Services", "JavaScript", "js"],
        education=["Computer Science"],
        experience=["Built reliable services"],
        projects=["Job Automation Platform"],
        filename="ada.pdf",
        content_type="application/pdf",
        file_size=1,
        resume_path="resume/originals/ada.pdf",
        resume_library_id=1,
        version_number=1,
        is_active=True,
    )


class ResumeIntelligenceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ResumeIntelligenceService(ResumeLookupService(make_resume()))

    def test_profile_normalizes_skills_and_detects_sections(self) -> None:
        profile = self.service.get_profile(42)
        self.assertEqual(profile.skills, ["Python", "Amazon Web Services", "JavaScript"])
        self.assertTrue(all(section.detected for section in profile.sections[:5]))
        self.assertEqual(profile.completeness.score, 100)

    def test_statistics_and_quality_identify_duplicate_skills(self) -> None:
        statistics = self.service.get_statistics(42)
        warning_codes = {warning.code for warning in self.service.get_quality_warnings(42)}
        self.assertEqual(statistics.skill_count, 5)
        self.assertEqual(statistics.normalized_skill_count, 3)
        self.assertEqual(statistics.duplicate_skill_count, 2)
        self.assertIn("duplicate_skills", warning_codes)

    def test_unknown_resume_propagates_domain_not_found_error(self) -> None:
        with self.assertRaises(ResumeNotFoundError):
            self.service.get_profile(999)


if __name__ == "__main__":
    unittest.main()
