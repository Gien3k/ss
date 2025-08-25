# api.py
import os
import shutil
import uuid
import hashlib
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from core.database import engine, Base, get_db
from core import crud, models
from core.cv_parser import parse_cv_file, extract_structured_data
from core.search import rag_search

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkillSense API",
    description="Inteligentne API do wyszukiwania zasobów uczelni.",
    version="2.0.0" # Wersja 2.0!
)

origins = ["http://34.70.6.174", "http://localhost", "http://127.0.0.1"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Kompletne schematy Pydantic ---
class SkillSchema(BaseModel):
    name: str
    class Config: from_attributes = True
class WorkExperienceSchema(BaseModel):
    position: Optional[str] = Field(None)
    company: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    class Config: from_attributes = True
class EducationSchema(BaseModel):
    institution: Optional[str] = Field(None)
    degree: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    class Config: from_attributes = True
class ProjectSchema(BaseModel):
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    class Config: from_attributes = True
class UserProfileSchema(BaseModel):
    id: int
    name: Optional[str] = Field(None)
    surname: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    linkedin_url: Optional[str] = Field(None)
    github_url: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    experience_score: Optional[float] = Field(None)
    cv_filepath: Optional[str] = Field(None)
    skills: List[SkillSchema] = []
    work_experiences: List[WorkExperienceSchema] = []
    education_history: List[EducationSchema] = []
    projects: List[ProjectSchema] = []
    class Config: from_attributes = True
class SearchResponseSchema(BaseModel):
    summary: str
    profiles: List[UserProfileSchema]
class TextInput(BaseModel):
    description: str

@app.on_event("startup")
async def startup_event():
    print("API gotowe do pracy. Wersja 2.0 z inteligentnym przetwarzaniem jest aktywna.")

@app.post("/upload-cv")
async def upload_cv(db: Session = Depends(get_db), file: UploadFile = File(...)):
    cv_dir = "uploads/cvs"
    os.makedirs(cv_dir, exist_ok=True)
    
    file_content = await file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    cached_result = crud.get_cached_cv_result(db, file_hash)
    if cached_result:
        print(f"Zwracanie wyniku z cache dla pliku o hashu: {file_hash}")
        personal_info = cached_result.parsed_data.get("personal_info", {})
        existing_user = crud.get_user_by_email(db, personal_info.get("email"))
        if not existing_user:
            crud.create_user_profile(db=db, parsed_data=cached_result.parsed_data, cv_file_hash=file_hash)
        return {"status": "success_from_cache", "data": cached_result.parsed_data}

    await file.seek(0)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(cv_dir, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        structured_data = parse_cv_file(file_path)
        
        crud.cache_cv_result(db, file_hash, structured_data)
        crud.create_user_profile(db=db, parsed_data=structured_data, cv_filepath=file_path, cv_file_hash=file_hash)
        
        return {"status": "success_processed", "data": structured_data}
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        print(f"Wystąpił błąd w /upload-cv: {e}")
        raise HTTPException(status_code=500, detail=f"Wystąpił wewnętrzny błąd serwera: {e}")

@app.post("/process-text")
async def process_text(text_input: TextInput, db: Session = Depends(get_db)):
    # ... (bez zmian - cache dla tekstu można dodać w przyszłości) ...
    try:
        structured_data = extract_structured_data(text_input.description)
        crud.create_user_profile(db=db, parsed_data=structured_data)
        return {"status": "success", "data": structured_data}
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd w /process-text: {e}")
        raise HTTPException(status_code=500, detail="Wystąpił wewnętrzny błąd serwera.")
        
@app.get("/users", response_model=List[UserProfileSchema])
async def get_users(search: str | None = None, db: Session = Depends(get_db)):
    return crud.get_all_users(db, search=search)

@app.get("/cv/{user_id}")
async def get_cv_file(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.cv_filepath or not os.path.exists(user.cv_filepath):
        raise HTTPException(status_code=404, detail="Nie znaleziono pliku CV.")
    return FileResponse(path=user.cv_filepath, media_type='application/pdf')

@app.get("/search", response_model=SearchResponseSchema)
async def search_profiles(query: str, db: Session = Depends(get_db)):
    if not query:
        raise HTTPException(status_code=400, detail="Parametr 'query' nie może być pusty.")
    try:
        results = rag_search(db=db, query=query)
        return results
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd w /search: {e}")
        raise HTTPException(status_code=500, detail="Wystąpił błąd podczas wyszukiwania.")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
