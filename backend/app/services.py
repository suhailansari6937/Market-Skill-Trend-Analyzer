
import re
from collections import Counter

from sqlalchemy.orm import Session
from app.models import Job, Notification


SKILL_TERMS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#",
    "Go", "PHP", "Ruby", "SQL", "PostgreSQL", "MySQL",
    "MongoDB", "Redis", "FastAPI", "Django", "Flask",
    "Spring Boot", "React", "Angular", "Vue", "Node.js",
    "HTML", "CSS", "Tailwind CSS", "AWS", "Azure", "GCP",
    "Docker", "Kubernetes", "Linux", "Git", "CI/CD",
    "Machine Learning", "Deep Learning", "NLP",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas",
    "NumPy", "Power BI", "Tableau", "Excel", "Spark",
    "Hadoop", "Airflow", "Cybersecurity", "Networking",
    "Selenium", "Playwright", "REST API", "GraphQL",
    "Agile", "Communication", "Project Management"
]


def extract_skills(text: str) -> list[str]:
    if not text:
        return []

    found = []
    low = text.lower()

    for skill in SKILL_TERMS:
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(skill.lower())
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, low):
            found.append(skill)

    return found


def job_to_dict(j: Job):
    return {
        "id": j.id,
        "title": j.title,
        "company": j.company,
        "location": j.location,
        "country": j.country,
        "industry": j.industry,
        "experience_level": j.experience_level,
        "description": (j.description or "")[:500],
        "skills": [
            x.strip()
            for x in (j.skills or "").split(",")
            if x.strip()
        ],
        "salary_min": j.salary_min,
        "salary_max": j.salary_max,
        "currency": j.currency,
        "source_url": j.source_url,
        "posted_at": j.posted_at.isoformat() if j.posted_at else None
    }


def split_skills(value):
    """Return unique, normalized skill labels from one job posting."""
    if not value:
        return []

    result = []
    seen = set()

    for item in value.split(","):
        skill = item.strip()
        key = skill.casefold()

        if skill and key not in seen:
            seen.add(key)
            result.append(skill)

    return result


def skill_counts(db: Session, country: str | None = None):
    query = db.query(Job.skills)

    if country:
        query = (
            db.query(Job.skills)
            .filter(Job.country.ilike(f"%{country}%"))
        )

    counts = Counter()

    for (skills,) in query.yield_per(2000):
        for skill in split_skills(skills):
            counts[skill.casefold()] += 1

    return counts


def top_skills(
    db: Session,
    limit: int = 10,
    country: str | None = None
):
    counts = skill_counts(db, country)

    return [
        {
            "skill": skill,
            "count": count
        }
        for skill, count in counts.most_common(limit)
    ]


def country_distribution(db: Session):
    rows = (
        db.query(Job.country, __import__("sqlalchemy").func.count(Job.id))
        .filter(
            Job.country.isnot(None),
            Job.country != "Unknown"
        )
        .group_by(Job.country)
        .order_by(__import__("sqlalchemy").func.count(Job.id).desc())
        .limit(10)
        .all()
    )

    return [
        {"name": country, "count": count}
        for country, count in rows
    ]


def industry_distribution(db: Session):
    from sqlalchemy import func

    rows = (
        db.query(Job.industry, func.count(Job.id))
        .filter(
            Job.industry.isnot(None),
            Job.industry != "Unknown"
        )
        .group_by(Job.industry)
        .order_by(func.count(Job.id).desc())
        .limit(10)
        .all()
    )

    return [
        {"name": industry, "count": count}
        for industry, count in rows
    ]


def experience_distribution(db: Session):
    from sqlalchemy import func

    rows = (
        db.query(Job.experience_level, func.count(Job.id))
        .filter(
            Job.experience_level.isnot(None),
            Job.experience_level != "Not specified"
        )
        .group_by(Job.experience_level)
        .order_by(func.count(Job.id).desc())
        .all()
    )

    return [
        {"experience": level, "count": count}
        for level, count in rows
    ]


def analyze_skill(db: Session, requested_skill: str):
    """
    Match complete comma-separated skill tokens.
    Avoid substring matches such as Java matching JavaScript.
    """
    target = requested_skill.strip().casefold()

    related = Counter()
    countries = Counter()
    industries = Counter()
    matching_jobs = 0

    query = db.query(
        Job.skills,
        Job.country,
        Job.industry
    )

    for skills, country, industry in query.yield_per(2000):
        job_skills = split_skills(skills)
        normalized = {s.casefold() for s in job_skills}

        if target not in normalized:
            continue

        matching_jobs += 1

        if country and country != "Unknown":
            countries[country] += 1

        if industry and industry != "Unknown":
            industries[industry] += 1

        for skill in job_skills:
            if skill.casefold() != target:
                related[skill] += 1

    if matching_jobs == 0:
        return None

    return {
        "skill": requested_skill,
        "job_count": matching_jobs,
        "countries": dict(countries),
        "industries": dict(industries),
        "country_breakdown": [
            {"name": name, "count": count}
            for name, count in countries.most_common(10)
        ],
        "industry_breakdown": [
            {"name": name, "count": count}
            for name, count in industries.most_common(10)
        ],
        "related_skills": [
            {"skill": name, "count": count}
            for name, count in related.most_common(10)
        ],
        "note": (
            "Counts are based on exact skill tokens in the currently "
            "imported job postings. Missing skill fields are not inferred."
        )
    }


def add_notification(db: Session, user_id: int, message: str):
    db.add(
        Notification(
            user_id=user_id,
            message=message
        )
    )
    db.commit()
