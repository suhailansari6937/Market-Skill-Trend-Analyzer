from datetime import datetime, timezone, timedelta
from app.db.database import Base, engine, SessionLocal
from app.models import User, Job
from app.core.security import hash_password
from app.services import extract_skills

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    accounts = [
        ("Admin", "admin@example.com", "Admin123!", "admin"),
        ("Demo Student", "student@example.com", "Student123!", "student"),
        ("Demo Recruiter", "recruiter@example.com", "Recruiter123!", "recruiter"),
    ]
    for name,email,password,role in accounts:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(name=name,email=email,password_hash=hash_password(password),role=role))
    samples = [
      ("Python Developer","DataWorks","Bengaluru","India","Technology","Mid-level","Build APIs using Python, FastAPI, PostgreSQL, Docker and AWS.", "INR",900000,1600000),
      ("Frontend Engineer","Pixel Labs","Remote","India","Technology","Junior","React, JavaScript, TypeScript, HTML, CSS and Git experience required.", "INR",600000,1100000),
      ("Machine Learning Engineer","Nova AI","Hyderabad","India","Technology","Senior","Machine Learning, Python, PyTorch, NLP, Scikit-learn and SQL.", "INR",1500000,2600000),
      ("Data Analyst","Insight Co","Mumbai","India","Finance","Mid-level","SQL, Python, Excel, Power BI, Tableau and communication skills.", "INR",700000,1300000),
      ("Cloud Engineer","CloudNine","London","United Kingdom","Technology","Mid-level","AWS, Azure, Docker, Kubernetes, Linux and CI/CD.", "GBP",50000,75000),
      ("Backend Developer","Northstar","New York","United States","Technology","Senior","Java, Spring Boot, PostgreSQL, Redis, Docker and REST API.", "USD",110000,160000),
      ("Cybersecurity Analyst","SecurePath","Toronto","Canada","Security","Mid-level","Cybersecurity, Linux, Networking, Python and cloud security.", "CAD",75000,105000),
      ("Data Engineer","MetricFlow","Remote","United States","Technology","Mid-level","Python, SQL, Spark, Airflow, AWS and PostgreSQL.", "USD",100000,145000),
      ("Product Manager","Orbit","Delhi","India","Business","Senior","Agile, communication, project management and data analysis.", "INR",1800000,2800000),
      ("QA Automation Engineer","QualityFirst","Pune","India","Technology","Junior","Python, Selenium, Playwright, JavaScript and CI/CD.", "INR",500000,900000),
      ("DevOps Engineer","StackBridge","Berlin","Germany","Technology","Senior","Linux, Docker, Kubernetes, AWS, Git and CI/CD.", "EUR",65000,90000),
      ("Business Analyst","Bright Consulting","Singapore","Singapore","Consulting","Mid-level","SQL, Excel, Power BI, communication and project management.", "SGD",65000,90000),
    ]
    if db.query(Job).count() == 0:
        for i,(title,company,loc,country,industry,exp,desc,currency,smin,smax) in enumerate(samples):
            db.add(Job(title=title,company=company,location=loc,country=country,industry=industry,
                experience_level=exp,description=desc,skills=", ".join(extract_skills(desc)),
                currency=currency,salary_min=smin,salary_max=smax,source="demo",
                posted_at=datetime.now(timezone.utc)-timedelta(days=i*11)))
    db.commit()
    print("Seed complete. Demo accounts created if they did not already exist.")
finally:
    db.close()
