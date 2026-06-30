import re
from collections.abc import Iterable

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)[\s.-]?)?"
    r"\d{3,5}[\s.-]?\d{3,5}(?!\w)"
)
HEADING_PATTERN = re.compile(r"[^a-z]+")

SECTION_ALIASES: dict[str, set[str]] = {
    "education": {
        "academic background",
        "academic qualifications",
        "education",
        "educational background",
        "qualifications",
    },
    "projects": {
        "academic projects",
        "key projects",
        "personal projects",
        "project experience",
        "projects",
    },
    "experience": {
        "employment history",
        "experience",
        "internship experience",
        "internships",
        "professional experience",
        "work experience",
        "work history",
    },
    "skills": {
        "competencies",
        "core competencies",
        "skills",
        "technical skills",
        "technologies",
    },
}

SKILL_NAMES = (
    "Amazon Web Services",
    "Microsoft Azure",
    "Google Cloud Platform",
    "Machine Learning",
    "Artificial Intelligence",
    "Natural Language Processing",
    "Data Analysis",
    "Data Science",
    "Deep Learning",
    "REST API",
    "FastAPI",
    "Django",
    "Flask",
    "React",
    "Angular",
    "Vue.js",
    "Node.js",
    "Express.js",
    "TypeScript",
    "JavaScript",
    "Python",
    "Java",
    "C++",
    "C#",
    "Go",
    "Rust",
    "PHP",
    "Ruby",
    "Kotlin",
    "Swift",
    "HTML",
    "CSS",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Git",
    "Linux",
    "Playwright",
    "Selenium",
    "PyTorch",
    "TensorFlow",
    "Pandas",
    "NumPy",
    "Scikit-learn",
    "Power BI",
    "Tableau",
    "Excel",
)

_ALL_SECTION_HEADINGS = {
    heading
    for aliases in SECTION_ALIASES.values()
    for heading in aliases
}


def normalize_text(text: str) -> str:
    """Normalize PDF text while retaining meaningful line boundaries."""
    normalized_lines: list[str] = []
    previous_line_was_empty = False

    for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        clean_line = re.sub(r"[ \t]+", " ", line).strip()
        if clean_line:
            normalized_lines.append(clean_line)
            previous_line_was_empty = False
        elif normalized_lines and not previous_line_was_empty:
            normalized_lines.append("")
            previous_line_was_empty = True

    return "\n".join(normalized_lines).strip()


def find_email(text: str) -> str | None:
    """Return the first email address found in text."""
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def find_phone(text: str) -> str | None:
    """Return the first plausible phone number found in text."""
    for match in PHONE_PATTERN.finditer(text):
        candidate = match.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 15:
            return re.sub(r"\s+", " ", candidate)
    return None


def find_name(text: str) -> str | None:
    """Infer a candidate name from the first few non-empty resume lines."""
    excluded_terms = {
        "curriculum vitae",
        "email",
        "linkedin",
        "portfolio",
        "profile",
        "resume",
        "summary",
    }
    lines = (line.strip(" |•-\t") for line in text.splitlines())

    for line in list(filter(None, lines))[:8]:
        lowered = line.lower()
        words = line.split()
        if (
            lowered in excluded_terms
            or any(term in lowered for term in ("@", "http://", "https://", "www."))
            or any(character.isdigit() for character in line)
            or not 2 <= len(words) <= 5
            or len(line) > 80
        ):
            continue
        if all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ.'’-]+", word) for word in words):
            return line
    return None


def find_skills(text: str) -> list[str]:
    """Return known technical skills mentioned in resume text."""
    found: list[str] = []
    for skill in SKILL_NAMES:
        pattern = rf"(?<![\w+#]){re.escape(skill)}(?![\w+#])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(skill)
    return found


def extract_section(text: str, section_name: str) -> list[str]:
    """Extract non-heading lines belonging to a recognized resume section."""
    target_headings = SECTION_ALIASES[section_name]
    collected: list[str] = []
    collecting = False

    for line in text.splitlines():
        normalized_heading = _normalize_heading(line)
        if normalized_heading in _ALL_SECTION_HEADINGS:
            if collecting and normalized_heading not in target_headings:
                break
            collecting = normalized_heading in target_headings
            continue
        if collecting and line.strip():
            collected.append(line.strip())

    return _deduplicate(collected)


def _normalize_heading(line: str) -> str:
    return HEADING_PATTERN.sub(" ", line.lower()).strip()


def _deduplicate(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        comparison_value = value.casefold()
        if comparison_value not in seen:
            seen.add(comparison_value)
            unique_values.append(value)
    return unique_values
