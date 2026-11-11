import csv, io
from sqlalchemy import func
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pypdf import PdfReader
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, get_current_user, require_roles
from app.db.database import Base, engine, get_db
from app.models import User, Job, IngestionRun, SavedSearch, Notification
from app.schemas import (
    RegisterIn, LoginIn, UserOut, JobIn,
    ProfileIn, CompareIn, ExperiencePredictionIn
)

import joblib
from pathlib import Path
from app.services import (
    extract_skills,
    job_to_dict,
    skill_counts,
    add_notification,
    top_skills,
    country_distribution,
    industry_distribution,
    experience_distribution,
    analyze_skill
)
Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0", description="Job market analytics and skill trend API")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# Load trained ML model
MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "ml"
    / "experience_level_model.joblib"
)

experience_model = joblib.load(MODEL_PATH) 

@app.get("/")
def root():
    return {"message": settings.app_name, "docs": "/docs"}

@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    return {"status": "ok", "database": "connected", "jobs": db.query(Job).count()}

@app.post("/api/v1/ml/predict-experience")
def predict_experience(data: ExperiencePredictionIn):

    probabilities = experience_model.predict_proba(
        [data.description]
    )[0]

    predicted_class = experience_model.predict(
        [data.description]
    )[0]

    class_probabilities = {
        str(label): round(float(prob), 4)
        for label, prob in zip(
            experience_model.classes_,
            probabilities
        )
    }

    return {
        "predicted_experience": str(predicted_class),
        "confidence": round(float(max(probabilities)), 4),
        "probabilities": class_probabilities
    }

@app.post("/api/v1/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.role not in ("student", "recruiter"):
        raise HTTPException(400, "Role must be student or recruiter")
    if db.query(User).filter(func.lower(User.email) == data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name, email=data.email.lower(), password_hash=hash_password(data.password), role=data.role)
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": UserOut.model_validate(user)}

@app.post("/api/v1/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer", "user": UserOut.model_validate(user)}

@app.get("/api/v1/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@app.get("/api/v1/jobs")
def jobs(q: str = "", country: str = "", industry: str = "", experience: str = "", limit: int = Query(50, le=200), offset: int = 0, db: Session = Depends(get_db)):
    query = db.query(Job)
    if q:
        term = f"%{q}%"
        query = query.filter(or_(Job.title.ilike(term), Job.company.ilike(term), Job.description.ilike(term), Job.skills.ilike(term)))
    if country: query = query.filter(Job.country.ilike(f"%{country}%"))
    if industry: query = query.filter(Job.industry.ilike(f"%{industry}%"))
    if experience: query = query.filter(Job.experience_level.ilike(f"%{experience}%"))
    total = query.count()
    rows = query.order_by(Job.posted_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [job_to_dict(j) for j in rows]}

@app.get("/api/v1/analytics/overview")
def overview(db: Session = Depends(get_db)):
    counts = skill_counts(db)

    top = [
        {"skill": k, "count": v}
        for k, v in counts.most_common(12)
    ]

    countries = country_distribution(db)
    industries = industry_distribution(db)

    return {
        "total_jobs": db.query(Job).count(),
        "total_skills": len(counts),
        "top_skills": top,
        "countries": countries,
        "industries": industries
    }

@app.get("/api/v1/analytics/top-skills")
def analytics_top_skills(
    limit: int = Query(10, ge=1, le=50),
    country: str = "",
    db: Session = Depends(get_db)
):
    return top_skills(db, limit, country or None)


@app.get("/api/v1/analytics/countries")
def analytics_countries(db: Session = Depends(get_db)):
    return country_distribution(db)


@app.get("/api/v1/analytics/industries")
def analytics_industries(db: Session = Depends(get_db)):
    return industry_distribution(db)


@app.get("/api/v1/analytics/experience")
def analytics_experience(db: Session = Depends(get_db)):
    return experience_distribution(db)


@app.get("/api/v1/analytics/skills/{skill}")
def skill_detail(skill: str, db: Session = Depends(get_db)):
    result = analyze_skill(db, skill)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No job postings found for this exact skill"
        )

    return result

@app.post("/api/v1/analytics/compare")
def compare(data: CompareIn, db: Session = Depends(get_db)):
    counts = skill_counts(db)
    result = []
    for skill in data.skills:
        matching = db.query(Job).filter(Job.skills.ilike(f"%{skill}%")).all()
        result.append({"skill": skill, "job_count": len(matching), "countries": len(set(j.country for j in matching)),
                       "industries": len(set(j.industry for j in matching))})
    return {"comparison": result, "basis": "Current ingested job postings"}

@app.get("/api/v1/analytics/top-skills")
def analytics_top_skills(
    limit: int = Query(20, ge=1, le=50),
    country: str = "",
    db: Session = Depends(get_db)
):
    return top_skills(
        db,
        limit=limit,
        country=country or None
    )


@app.get("/api/v1/analytics/countries")
def analytics_countries(db: Session = Depends(get_db)):
    return country_distribution(db)


@app.get("/api/v1/analytics/industries")
def analytics_industries(db: Session = Depends(get_db)):
    return industry_distribution(db)


@app.get("/api/v1/analytics/experience")
def analytics_experience(db: Session = Depends(get_db)):
    return experience_distribution(db)

@app.put("/api/v1/profile")
def update_profile(data: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.skills = data.skills
    user.target_role = data.target_role
    db.commit()
    return {"message": "Profile updated", "skills": user.skills, "target_role": user.target_role}

@app.post("/api/v1/resumes/analyze")
async def analyze_resume(file: UploadFile = File(...), user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Please upload a PDF resume")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024: raise HTTPException(413, "Maximum PDF size is 5 MB")
    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        raise HTTPException(400, "Could not read this PDF")
    skills = extract_skills(text)
    return {"filename": file.filename, "extracted_skills": skills, "message": "Review these extracted skills and save them to your profile."}

@app.get("/api/v1/recommendations")
def recommendations(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    current = {x.strip().lower() for x in user.skills.split(",") if x.strip()}
    target = user.target_role.strip()
    rows = db.query(Job)
    if target: rows = rows.filter(Job.title.ilike(f"%{target}%"))
    rows = rows.all()
    from collections import Counter
    counts = Counter()
    for j in rows:
        for s in j.skills.split(","):
            if s.strip() and s.strip().lower() not in current: counts[s.strip()] += 1
    return {"target_role": target, "existing_skills": sorted(current),
            "recommendations": [{"skill": s, "job_count": n, "reason": f"Appears in {n} matching job postings"} for s,n in counts.most_common(15)]}

@app.get("/api/v1/recommendations/skill-gap")
def skill_gap(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    if not user.target_role: raise HTTPException(400, "Set a target role in your profile first")
    rows = db.query(Job).filter(Job.title.ilike(f"%{user.target_role}%")).all()
    counts = {}
    for j in rows:
        for s in j.skills.split(","):
            if s.strip(): counts[s.strip()] = counts.get(s.strip(), 0) + 1
    existing = {x.strip().lower() for x in user.skills.split(",") if x.strip()}
    required = sorted(counts, key=counts.get, reverse=True)[:20]
    matched = [s for s in required if s.lower() in existing]
    missing = [s for s in required if s.lower() not in existing]
    return {"target_role": user.target_role, "matched": matched, "missing": missing, "jobs_analyzed": len(rows)}

@app.post("/api/v1/saved-searches")
def save_search(query: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = SavedSearch(user_id=user.id, query=query); db.add(item); db.commit()
    return {"message": "Search saved"}

@app.get("/api/v1/notifications")
def notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(30).all()
    return [{"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at.isoformat()} for n in rows]

@app.get("/api/v1/admin/overview")
def admin_overview(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    latest = db.query(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(10).all()
    return {"users": db.query(User).count(), "jobs": db.query(Job).count(),
            "runs": [{"id": r.id, "source": r.source, "status": r.status, "records_added": r.records_added, "message": r.message, "created_at": r.created_at.isoformat()} for r in latest]}

@app.post("/api/v1/admin/ingest-csv")
async def ingest_csv(file: UploadFile = File(...), user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(400, "Upload a CSV file")
    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    required = {"title", "company", "location", "description"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(400, f"CSV must contain columns: {', '.join(sorted(required))}")
    added = 0
    for row in reader:
        title = (row.get("title") or "").strip()
        company = (row.get("company") or "Unknown").strip()
        description = (row.get("description") or "").strip()
        if not title or not description: continue
        existing = db.query(Job).filter(Job.title == title, Job.company == company, Job.location == row.get("location", "")).first()
        if existing: continue
        skills = row.get("skills") or ", ".join(extract_skills(description))
        db.add(Job(title=title, company=company, location=row.get("location") or "Unknown",
            country=row.get("country") or "Unknown", industry=row.get("industry") or "Other",
            experience_level=row.get("experience_level") or "Not specified", description=description,
            skills=skills, salary_min=parse_float(row.get("salary_min")), salary_max=parse_float(row.get("salary_max")),
            currency=row.get("currency") or "USD", source_url=row.get("source_url") or "", source="csv"))
        added += 1
    run = IngestionRun(source=file.filename, status="completed", records_added=added, message="CSV imported")
    db.add(run); db.commit()
    return {"records_added": added, "status": "completed"}

def parse_float(value):
    try: return float(value) if value not in (None, "") else None
    except ValueError: return None

@app.get("/api/v1/admin/users")
def admin_users(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return [{"id":u.id,"name":u.name,"email":u.email,"role":u.role} for u in db.query(User).order_by(User.id).all()]
