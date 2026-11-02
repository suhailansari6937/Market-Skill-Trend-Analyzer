
from app.db.database import SessionLocal
from app.models import Job

import re
import json
from collections import Counter


COUNTRY_MAP = {
    "usa": "United States",
    "us": "United States",
    "u.s.": "United States",
    "united states of america": "United States",
    "united states": "United States",

    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "united kingdom": "United Kingdom",

    "india": "India",
    "canada": "Canada",
    "australia": "Australia",
    "germany": "Germany",
    "france": "France",
    "singapore": "Singapore",
    "ireland": "Ireland",
    "netherlands": "Netherlands",
    "spain": "Spain",
    "japan": "Japan",
    "china": "China",
    "brazil": "Brazil",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
}


SKILL_ALIASES = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "reactjs": "React",
    "react.js": "React",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "ai": "Artificial Intelligence",
    "nlp": "NLP",
    "sql": "SQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "aws": "AWS",
    "gcp": "GCP",
    "api": "API",
    "rest api": "REST API",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "ci/cd": "CI/CD",
    "c++": "C++",
    "c#": "C#",
    "html": "HTML",
    "css": "CSS",
    "ai/ml": "AI/ML",
}


# Canonical labels for known skills
CANONICAL_SKILLS = {
    skill.casefold(): skill
    for skill in [
        "Python", "Java", "JavaScript", "TypeScript",
        "C++", "C#", "Go", "PHP", "Ruby", "SQL",
        "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "FastAPI", "Django", "Flask", "Spring Boot",
        "React", "Angular", "Vue", "Node.js",
        "HTML", "CSS", "Tailwind CSS",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes",
        "Linux", "Git", "CI/CD", "Machine Learning",
        "Deep Learning", "NLP", "TensorFlow", "PyTorch",
        "Scikit-learn", "Pandas", "NumPy",
        "Power BI", "Tableau", "Excel",
        "Spark", "Hadoop", "Airflow",
        "Cybersecurity", "Networking",
        "Selenium", "Playwright", "REST API",
        "GraphQL", "Agile", "Communication",
        "Project Management", "Artificial Intelligence",
        "API", "AI/ML"
    ]
}


def normalize_country(value):
    if not value:
        return "Unknown"

    value = str(value).strip()

    if value.lower() in ("unknown", "nan", "none"):
        return "Unknown"

    return COUNTRY_MAP.get(value.casefold(), value)


def normalize_skill(value):
    value = str(value).strip()

    if not value:
        return ""

    key = value.casefold()

    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]

    if key in CANONICAL_SKILLS:
        return CANONICAL_SKILLS[key]

    # Preserve unrecognized skills, with consistent spacing.
    return re.sub(r"\s+", " ", value)


def normalize_skills(value):
    if not value:
        return ""

    skills = value.split(",")
    normalized = []
    seen = set()

    for skill in skills:
        skill = normalize_skill(skill)

        if skill and skill.casefold() not in seen:
            seen.add(skill.casefold())
            normalized.append(skill)

    return ", ".join(normalized)


def main():
    db = SessionLocal()

    updated = 0
    country_changes = Counter()
    skill_changes = 0
    industry_changes = 0

    try:
        total = db.query(Job).count()
        print("Total jobs:", total)
        print("Starting normalization...")

        query = db.query(Job).yield_per(1000)

        for job in query:

            old_country = job.country or "Unknown"
            new_country = normalize_country(old_country)

            if old_country != new_country:
                country_changes[f"{old_country} -> {new_country}"] += 1
                job.country = new_country

            old_skills = job.skills or ""
            new_skills = normalize_skills(old_skills)

            if old_skills != new_skills:
                job.skills = new_skills
                skill_changes += 1

            # Imported missing industries were assigned "Other".
            if not job.industry or job.industry.strip().casefold() in (
                "other", "nan", "none", ""
            ):
                job.industry = "Unknown"
                industry_changes += 1

            updated += 1

            if updated % 10000 == 0:
                db.commit()
                print(f"Processed {updated}/{total}")

        db.commit()

        print("\nNORMALIZATION COMPLETED")
        print("Total processed:", updated)
        print("Country changes:", sum(country_changes.values()))
        print("Skills updated:", skill_changes)
        print("Industries marked Unknown:", industry_changes)

        print("\nCountry changes:")
        for change, count in country_changes.most_common(20):
            print(change, ":", count)

        print("\nFinal job count:", db.query(Job).count())

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
