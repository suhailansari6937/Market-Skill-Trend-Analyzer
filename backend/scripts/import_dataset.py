
import json
import math
from datetime import datetime, timezone

import pandas as pd
from huggingface_hub import hf_hub_download
from sqlalchemy import select, insert

from app.db.database import Base, engine, SessionLocal
from app.models import Job, IngestionRun


REPO_ID = "NextGig-Rocks/global-job-postings-multi-ats"
FILE_NAME = "nextgig_jobs_2026-06.parquet"
BATCH_SIZE = 1000
SOURCE = "NextGig-Rocks"

# Used only when the original posting date is unavailable.
SNAPSHOT_DATE = datetime(2026, 6, 1, tzinfo=timezone.utc)


def clean_text(value, default=""):
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    return str(value).strip() or default


def clean_number(value):
    try:
        if value is None or pd.isna(value):
            return None

        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def clean_skills(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    if isinstance(value, list):
        skills = value
    else:
        text = str(value).strip()

        try:
            parsed = json.loads(text)
            skills = parsed if isinstance(parsed, list) else [text]
        except (json.JSONDecodeError, TypeError):
            skills = [text]

    # Remove empty and duplicate skills.
    result = []
    seen = set()

    for skill in skills:
        skill = str(skill).strip()
        key = skill.casefold()

        if skill and key not in seen:
            seen.add(key)
            result.append(skill)

    return ", ".join(result)


def clean_date(value):
    date = pd.to_datetime(value, errors="coerce", utc=True)

    if pd.isna(date):
        return SNAPSHOT_DATE

    return date.to_pydatetime()


def make_job(row):
    city = clean_text(row.get("city"))
    country = clean_text(row.get("country"), "Unknown")

    location = city if city else clean_text(
        row.get("location_resolved"), "Unknown"
    )

    if location == "Unknown" and country != "Unknown":
        location = country

    return {
        "title": clean_text(row.get("title"), "Untitled")[:200],
        "company": clean_text(row.get("company_name"), "Unknown")[:200],
        "location": location[:200],
        "country": country[:100],
        "industry": clean_text(row.get("industry"), "Other")[:120],
        "experience_level": clean_text(
            row.get("experience_level"), "Not specified"
        )[:80],
        "description": clean_text(row.get("job_description")),
        "skills": clean_skills(row.get("skills_required")),
        "salary_min": clean_number(row.get("salary_min")),
        "salary_max": clean_number(row.get("salary_max")),
        "currency": clean_text(row.get("salary_currency"), "USD")[:12],
        "source_url": "",
        "source": SOURCE,
        "posted_at": clean_date(row.get("date_posted")),
    }


def main():
    print("Downloading dataset...")

    file_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILE_NAME,
        repo_type="dataset"
    )

    print("Reading Parquet file...")
    df = pd.read_parquet(file_path)

    print("Total dataset records:", len(df))

    # Create missing tables without deleting existing data.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    added = 0
    skipped = 0

    try:
        # Load existing job keys to avoid duplicate imports.
        existing_rows = db.execute(
            select(Job.title, Job.company, Job.location)
        ).all()

        seen = {
            (
                str(title).strip().casefold(),
                str(company).strip().casefold(),
                str(location).strip().casefold()
            )
            for title, company, location in existing_rows
        }

        print("Existing jobs:", len(seen))
        print("Importing in batches...")

        batch = []

        for _, row in df.iterrows():
            job = make_job(row)

            key = (
                job["title"].casefold(),
                job["company"].casefold(),
                job["location"].casefold()
            )

            if key in seen:
                skipped += 1
                continue

            seen.add(key)
            batch.append(job)

            if len(batch) >= BATCH_SIZE:
                db.execute(insert(Job), batch)
                db.commit()

                added += len(batch)
                print(f"Imported: {added} | Skipped: {skipped}")
                batch.clear()

        if batch:
            db.execute(insert(Job), batch)
            db.commit()
            added += len(batch)

        db.add(
            IngestionRun(
                source=SOURCE,
                status="completed",
                records_added=added,
                message=f"Imported {added}; skipped {skipped} duplicates."
            )
        )
        db.commit()

        print("\nIMPORT COMPLETED")
        print("Added:", added)
        print("Skipped:", skipped)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
