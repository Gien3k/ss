# api.py
import os
import shutil
import uuid
import hashlib
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from core.database import engine, Base, get_db
from core import crud, models, search

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkillSense API",
    description="Inteligentne API do wyszukiwania i zarządzania talentami.",
    version="6.0.1" # Wersja 6.0.1 - Poprawka składni
)

origins = ["http://34.70.6.174", "http://localhost", "http://127.0.0.1", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- POPRAWIONE Schematy Pydantic ---

class SkillSchema(BaseModel):
    name: str
    class Config:
        from_attributes = True

class WorkExperienceSchema(BaseModel):
    position: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = []
    class Config:
        from_attributes = True

class EducationSchema(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    class Config:
        from_attributes = True

class ProjectSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = []
    class Config:
        from_attributes = True

class LanguageSchema(BaseModel):
    name: str
    level: str
    class Config:
        from_attributes = True

class PublicationSchema(BaseModel):
    title: str
    outlet: Optional[str] = None
    date: Optional[str] = None
    class Config:
        from_attributes = True

class ActivitySchema(BaseModel):
    name: str
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    class Config:
        from_attributes = True

class UserProfileSchema(BaseModel):
    id: int
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    description: Optional[str] = None
    match_score: Optional[int] = None
    cv_filepath: Optional[str] = None
    skills: List[SkillSchema] = []
    work_experiences: List[WorkExperienceSchema] = []
    education_history: List[EducationSchema] = []
    projects: List[ProjectSchema] = []
    languages: List[LanguageSchema] = []
    publications: List[PublicationSchema] = []
    activities: List[ActivitySchema] = []
    class Config:
        from_attributes = True

class SearchResponseSchema(BaseModel):
    summary: str
    profiles: List[UserProfileSchema]

class TextInput(BaseModel):
    description: str

class FeedbackInput(BaseModel):
    query: str
    rated_user_id: int
    rating: str

class ProjectCandidateSchema(UserProfileSchema):
    status: models.CandidateStatusEnum
    notes: Optional[str] = None

class RecruitmentProjectSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class RecruitmentProjectDetailSchema(RecruitmentProjectSchema):
    candidates_with_status: List[ProjectCandidateSchema] = []

class CreateProjectInput(BaseModel):
    name: str
    description: Optional[str] = None

class AddCandidateInput(BaseModel):
    user_id: int

class UpdateCandidateInput(BaseModel):
    status: models.CandidateStatusEnum
    notes: Optional[str] = None

class GenerateQuestionsInput(BaseModel):
    user_id: int
    query: str

# --- Endpointy ---
@app.on_event("startup")
async def startup_event(): print("API gotowe do pracy. Wersja 6.0.1 (Finalna) jest aktywna.")

@app.post("/upload-cv")
async def upload_cv(db: Session = Depends(get_db), file: UploadFile = File(...)):
    cv_dir = "uploads/cvs"; os.makedirs(cv_dir, exist_ok=True)
    file_content = await file.read(); file_hash = hashlib.sha256(file_content).hexdigest()
    if cached_result := crud.get_cached_cv_result(db, file_hash):
        if not crud.get_user_by_email(db, cached_result.parsed_data.get("personal_info", {}).get("email")):
            crud.create_user_profile(db=db, parsed_data=cached_result.parsed_data, cv_file_hash=file_hash)
        return {"status": "success_from_cache", "data": cached_result.parsed_data}
    await file.seek(0); file_extension = os.path.splitext(file.filename)[1]; unique_filename = f"{uuid.uuid4()}{file_extension}"; file_path = os.path.join(cv_dir, unique_filename)
    try:
        with open(file_path, "wb") as buffer: buffer.write(file_content)
        structured_data = search.parse_cv_file(file_path)
        crud.cache_cv_result(db, file_hash, structured_data)
        crud.create_user_profile(db=db, parsed_data=structured_data, cv_filepath=file_path, cv_file_hash=file_hash)
        return {"status": "success_processed", "data": structured_data}
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Wystąpił wewnętrzny błąd serwera: {e}")

@app.post("/process-text")
async def process_text(text_input: TextInput, db: Session = Depends(get_db)):
    try:
        structured_data = search.extract_structured_data(text_input.description)
        crud.create_user_profile(db=db, parsed_data=structured_data)
        return {"status": "success", "data": structured_data}
    except Exception as e: raise HTTPException(status_code=500, detail="Wystąpił wewnętrzny błąd serwera.")

@app.get("/users", response_model=List[UserProfileSchema])
async def get_users(search_query: str | None = None, db: Session = Depends(get_db)):
    return crud.get_all_users(db, search=search_query)

@app.get("/cv/{user_id}")
async def get_cv_file(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.cv_filepath or not os.path.exists(user.cv_filepath): raise HTTPException(status_code=404, detail="Nie znaleziono pliku CV.")
    return FileResponse(path=user.cv_filepath, media_type='application/pdf')

@app.get("/search", response_model=SearchResponseSchema)
async def search_profiles(query: str, db: Session = Depends(get_db)):
    if not query: raise HTTPException(status_code=400, detail="Parametr 'query' nie może być pusty.")
    try: return search.rag_search(db=db, query=query)
    except Exception as e: traceback.print_exc(); raise HTTPException(status_code=500, detail=f"Wystąpił wewnętrzny błąd serwera: {e}")

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackInput, db: Session = Depends(get_db)):
    crud.save_feedback(db, feedback.query, feedback.rated_user_id, feedback.rating)
    return {"status": "success"}

@app.post("/generate-interview-questions", response_model=List[str])
async def generate_questions(input_data: GenerateQuestionsInput, db: Session = Depends(get_db)):
    user = db.query(models.User).options(joinedload(models.User.skills)).filter(models.User.id == input_data.user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony.")
    return search.generate_interview_questions(user, input_data.query)

@app.post("/projects", response_model=RecruitmentProjectSchema)
async def create_project(project_data: CreateProjectInput, db: Session = Depends(get_db)): return crud.create_recruitment_project(db, name=project_data.name, description=project_data.description)

@app.get("/projects", response_model=List[RecruitmentProjectSchema])
async def get_projects(db: Session = Depends(get_db)): return crud.get_all_recruitment_projects(db)

@app.get("/projects/{project_id}", response_model=RecruitmentProjectDetailSchema)
async def get_project_details(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project_with_candidates(db, project_id)
    if not project: raise HTTPException(status_code=404, detail="Projekt nie został znaleziony.")
    return project

@app.post("/projects/{project_id}/candidates", status_code=201)
async def add_candidate_to_project_endpoint(project_id: int, candidate_data: AddCandidateInput, db: Session = Depends(get_db)):
    crud.add_candidate_to_project(db, project_id=project_id, user_id=candidate_data.user_id)
    return {"status": "success"}

@app.put("/projects/{project_id}/candidates/{user_id}")
async def update_candidate_in_project_endpoint(project_id: int, user_id: int, update_data: UpdateCandidateInput, db: Session = Depends(get_db)):
    crud.update_candidate_in_project(db, project_id=project_id, user_id=user_id, status=update_data.status, notes=update_data.notes)
    return {"status": "success"}

@app.get("/health")
async def health_check(): return {"status": "ok"}
