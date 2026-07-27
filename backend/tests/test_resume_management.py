import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.resume import Resume, ResumeLibrary
from services.resume_service import ResumeService


class FakeRepository:
    def __init__(self, library, versions):
        self.library = library
        self.versions = versions
        self.updated_library = None
        self.deleted_library = None
        self.next_id = 100

    def get_library_by_id(self, library_id):
        return self.library if library_id == self.library.id else None

    def get_library_by_name(self, name):
        return self.library if name == self.library.name else None

    def update_library(self, library):
        self.updated_library = library
        return library

    def list_versions_by_library(self, library_id):
        return self.versions if library_id == self.library.id else []

    def get_active_by_library(self, library_id):
        return next((item for item in self.versions if item.is_active), None)

    def get_latest_version_number_by_library(self, library_id):
        return max(item.version_number for item in self.versions)

    def update_many(self, versions):
        return versions

    def create(self, resume):
        resume.id = self.next_id
        self.next_id += 1
        self.versions.append(resume)
        return resume

    def update(self, resume):
        return resume

    def get_by_id_for_library(self, resume_id, library_id):
        return next((item for item in self.versions if item.id == resume_id), None)

    def delete_library_transactionally(self, library):
        self.deleted_library = library
        self.versions.clear()


def make_resume(resume_id, version, active, path="resume/originals/test.pdf"):
    return Resume(
        id=resume_id,
        filename="test.pdf",
        content_type="application/pdf",
        file_size=5,
        resume_path=path,
        raw_text="content",
        resume_library_id=1,
        root_resume_id=1,
        version_number=version,
        is_active=active,
        skills=["Python"],
        education=[],
        projects=[],
        experience=[],
    )


class ResumeManagementTests(unittest.TestCase):
    def setUp(self):
        self.library = ResumeLibrary(id=1, name="Backend Resume")
        self.old = make_resume(10, 1, False)
        self.current = make_resume(11, 2, True)
        self.repository = FakeRepository(self.library, [self.old, self.current])
        self.service = ResumeService(self.repository, parser=None)

    def test_rename_normalizes_name(self):
        renamed = self.service.rename_resume_library(1, "  Platform   Resume ")
        self.assertEqual(renamed.name, "Platform Resume")

    def test_restore_creates_new_active_version(self):
        restored = self.service.restore_library_version(1, 10)
        self.assertEqual(restored.version_number, 3)
        self.assertTrue(restored.is_active)
        self.assertFalse(self.current.is_active)
        self.assertEqual(restored.raw_text, self.old.raw_text)
        self.assertEqual(restored.resume_path, self.old.resume_path)

    def test_paginated_search_uses_offset_and_total(self):
        self.repository.count_libraries = lambda search: 1
        self.repository.list_libraries = lambda *args: [self.library]
        libraries, total = self.service.list_resume_library_page(2, 5, "Backend")
        self.assertEqual(libraries, [self.library])
        self.assertEqual(total, 1)

    def test_delete_stages_file_before_removing_records(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            resume_file = Path(temporary_directory) / "test.pdf"
            resume_file.write_bytes(b"%PDF-")
            with patch("services.resume_service.get_stored_resume_path", return_value=resume_file):
                self.service.delete_resume_library(1)
            self.assertEqual(self.repository.deleted_library, self.library)
            self.assertFalse(resume_file.exists())


if __name__ == "__main__":
    unittest.main()
