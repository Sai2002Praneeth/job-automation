"""Deterministic skill canonicalization shared by intelligence services."""

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
