# core/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any

# --- Schematy Relacyjne ---

class Skill(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class WorkExperience(BaseModel):
    id: int
    position: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    class Config:
        from_attributes = True

class Education(BaseModel):
    id: int
    institution: str
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    class Config:
        from_attributes = True
        
class Project(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    class Config:
        from_attributes = True

class Language(BaseModel):
    id: int
    name: str
    level: str
    class Config:
        from_attributes = True

class Publication(BaseModel):
    id: int
    title: str
    outlet: Optional[str] = None
    date: Optional[str] = None
    class Config:
        from_attributes = True

class Certification(BaseModel):
    id: int
    name: str
    issuing_organization: Optional[str] = None
    date_issued: Optional[str] = None
    class Config:
        from_attributes = True

# --- Schematy Użytkownika (Z POPRAWKĄ) ---

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    surname: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    ai_summary: Optional[str] = None
    cv_filepath: Optional[str] = None
    other_data: Optional[List[Dict[str, Any]]] = None

    skills: List[Skill] = []
    work_experiences: List[WorkExperience] = []
    education_history: List[Education] = []
    projects: List[Project] = []
    languages: List[Language] = []
    publications: List[Publication] = []
    certifications: List[Certification] = []
    
    class Config:
        from_attributes = True

class UserList(BaseModel):
    items: List[User]
    total: int

# --- Pozostałe Schematy ---

class SearchResultProfile(User):
    match_score: int

class SearchResponse(BaseModel):
    summary: str
    profiles: List[SearchResultProfile]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
