import json
import os
import socket
import sys
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import uvicorn

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from services.job_description_intelligence_service import JobDescriptionIntelligenceService


COMPLETE_DESCRIPTION = """Senior Backend Engineer
Location: Bengaluru, India (Hybrid)
Employment Type: Full Time
Salary: ₹18 LPA - ₹25 LPA
Requirements:
- 5+ years experience
- Python
- FastAPI
- PostgreSQL
- AWS
Preferred Qualifications:
- Docker
- Kubernetes
Responsibilities:
- Build REST APIs
- Write unit tests
- Review code
- Mentor junior engineers"""

REQUEST_CASES = {
    "complete": {"title": "Senior Backend Engineer", "description": COMPLETE_DESCRIPTION},
    "minimal": {"description": "Python developer"},
    "empty": {"description": ""},
    "messy": {"description": "need PYTHON!!! remote? docker/aws... 3+ years exp; build APIs"},
}


class JobDescriptionIntelligenceServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_probe:
            socket_probe.bind(("127.0.0.1", 0))
            cls.port = socket_probe.getsockname()[1]
        cls.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=cls.port, log_level="critical"))
        cls.server_thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.server_thread.start()
        deadline = time.monotonic() + 10
        while not cls.server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        if not cls.server.started:
            raise RuntimeError("Test FastAPI server did not start.")

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.server_thread.join(timeout=10)

    @classmethod
    def post(cls, path, payload):
        request = Request(
            f"http://127.0.0.1:{cls.port}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_profile_extracts_job_details_deterministically(self):
        profile = JobDescriptionIntelligenceService().analyze(COMPLETE_DESCRIPTION)
        self.assertEqual(profile.title, "Senior Backend Engineer")
        self.assertIn("Python", profile.required_skills)
        self.assertIn("Amazon Web Services", profile.required_skills)
        self.assertIn("Docker", profile.preferred_skills)
        self.assertEqual(profile.experience.minimum_years, 5)
        self.assertEqual(profile.location.remote_type, "hybrid")
        self.assertEqual(profile.employment.employment_types, [])
        self.assertEqual(len(profile.responsibilities), 4)

    def test_statistics_and_quality_warnings_are_explainable(self):
        service = JobDescriptionIntelligenceService()
        self.assertGreater(service.get_statistics(COMPLETE_DESCRIPTION).word_count, 0)
        warning_codes = {warning.code for warning in service.get_quality_warnings("Short role")}
        self.assertIn("missing_required_skills", warning_codes)
        self.assertIn("low_word_count", warning_codes)

    def test_openapi_publishes_job_intelligence_endpoints(self):
        paths = app.openapi()["paths"]
        self.assertTrue(all(path in paths for path in ("/api/job/analyze", "/api/job/profile", "/api/job/statistics", "/api/job/quality")))

    def test_analyze_endpoint_validates_all_request_cases(self):
        for name, payload in REQUEST_CASES.items():
            with self.subTest(case=name):
                status, body = self.post("/api/job/analyze", payload)
                if name == "empty":
                    self.assertEqual(status, 422)
                else:
                    self.assertEqual(status, 200)
                    self.assertEqual(set(body), {"profile", "statistics", "quality"})
                    self.assert_complete_profile(body["profile"])
                    self.assert_complete_statistics(body["statistics"])
                    self.assert_complete_quality(body["quality"])

    def test_profile_endpoint_validates_all_request_cases(self):
        self.assert_endpoint_cases("/api/job/profile", self.assert_complete_profile)

    def test_statistics_endpoint_validates_all_request_cases(self):
        self.assert_endpoint_cases("/api/job/statistics", self.assert_complete_statistics)

    def test_quality_endpoint_validates_all_request_cases(self):
        self.assert_endpoint_cases("/api/job/quality", self.assert_complete_quality)

    def assert_endpoint_cases(self, path, response_assertion):
        for name, payload in REQUEST_CASES.items():
            with self.subTest(case=name):
                status, body = self.post(path, payload)
                if name == "empty":
                    self.assertEqual(status, 422)
                else:
                    self.assertEqual(status, 200)
                    response_assertion(body)

    def assert_complete_profile(self, body):
        self.assertEqual(set(body), {"title", "required_skills", "preferred_skills", "experience", "education", "location", "salary", "employment", "responsibilities"})
        self.assertTrue(all(value is not None for key, value in body.items() if key != "title"))
        self.assertEqual(set(body["experience"]), {"minimum_years", "maximum_years", "requirements"})
        self.assertEqual(set(body["education"]), {"degrees", "fields"})
        self.assertEqual(set(body["location"]), {"locations", "remote_type"})
        self.assertEqual(set(body["salary"]), {"raw_text", "minimum", "maximum", "currency", "period"})
        self.assertEqual(set(body["employment"]), {"employment_types", "remote_type"})

    def assert_complete_statistics(self, body):
        expected = {"word_count", "character_count", "line_count", "required_skill_count", "preferred_skill_count", "responsibility_count", "experience_requirement_count"}
        self.assertEqual(set(body), expected)
        self.assertTrue(all(isinstance(value, int) and value >= 0 for value in body.values()))

    def assert_complete_quality(self, body):
        self.assertEqual(set(body), {"warnings"})
        for warning in body["warnings"]:
            self.assertEqual(set(warning), {"code", "severity", "message"})
            self.assertTrue(all(isinstance(value, str) and value for value in warning.values()))


if __name__ == "__main__":
    unittest.main()
