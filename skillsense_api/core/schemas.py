# core/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import List, Optional, Dict, Any, TypeVar, Generic

# --- Schematy Relacyjne ---
class Skill(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class WorkExperience(BaseModel):
    id: int
    position: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = []
    model_config = ConfigDict(from_attributes=True)

class Education(BaseModel):
    id: int
    institution: str
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
        
class Project(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class Language(BaseModel):
    id: int
    name: str
    level: str
    model_config = ConfigDict(from_attributes=True)

class Publication(BaseModel):
    id: int
    title: str
    outlet: Optional[str] = None
    date: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class Certification(BaseModel):
    id: int
    name: str
    issuing_organization: Optional[str] = None
    date_issued: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- Schematy Użytkownika ---

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    surname: Optional[str] = None

class User(UserBase):
    id: int
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    ai_summary: Optional[str] = None
    cv_filepath: Optional[str] = None
    other_data: Optional[List[Dict[str, Any]]] = None

    # POPRAWKA: Przywrócenie wszystkich pól relacji
    skills: List[Skill] = []
    work_experiences: List[WorkExperience] = []
    education_history: List[Education] = []
    projects: List[Project] = []
    languages: List[Language] = []
    publications: List[Publication] = []
    certifications: List[Certification] = []
    
    model_config = ConfigDict(from_attributes=True)

# --- Generyczne Schematy Paginacji ---
DataType = TypeVar('DataType')

class PaginatedResponse(BaseModel, Generic[DataType]):
    total: int
    page: int
    limit: int
    items: List[DataType]

# --- Ulepszone Schematy dla Wyszukiwania ---

class SearchResultProfile(User):
    match_score: float = Field(description="Ocena dopasowania kandydata w skali 0-100.")
    reasoning: Optional[str] = Field(None, description="Uzasadnienie oceny wygenerowane przez LLM.")

class SearchResponse(BaseModel):
    summary: str = Field(description="Podsumowanie wyników wyszukiwania wygenerowane przez LLM.")
    profiles: PaginatedResponse[SearchResultProfile]

# --- Pozostałe Schematy ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
