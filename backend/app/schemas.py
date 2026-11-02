from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "student"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    skills: str = ""
    target_role: str = ""
    model_config = ConfigDict(from_attributes=True)

class JobIn(BaseModel):
    title: str
    company: str = "Unknown"
    location: str = "Unknown"
    country: str = "Unknown"
    industry: str = "Other"
    experience_level: str = "Not specified"
    description: str
    skills: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "USD"
    source_url: str = ""
    source: str = "manual"

class ProfileIn(BaseModel):
    skills: str = ""
    target_role: str = ""

class CompareIn(BaseModel):
    skills: list[str] = Field(min_length=2, max_length=5)
