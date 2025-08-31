# core/services.py
import hashlib
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import asyncio
from typing import List, Dict, Any

from . import crud, models, schemas
from .cv_parser import parse_cv_file
from langchain_openai import OpenAIEmbeddings

embeddings_model = OpenAIEmbeddings()

class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        return crud.get_user(db, user_id=user_id)

    @staticmethod
    def get_all_users(db: Session, skip: int, limit: int):
        return crud.get_users(db, skip=skip, limit=limit)

    @staticmethod
    def create_or_update_user_from_cv(db: Session, parsed_data: Dict[str, Any], cv_path: str, cv_hash: str):
        personal_info = parsed_data.get("personal_info", {})
        email = personal_info.get("email")
        
        user = crud.get_user_by_email(db, email=email)
        if not user:
            user = models.User(email=email)
            db.add(user)
            db.flush()

        # Aktualizacja głównych pól
        name_parts = (personal_info.get("name") or " ").split()
        user.name = name_parts[0]
        user.surname = " ".join(name_parts[1:])
        user.phone = personal_info.get("phone")
        user.linkedin_url = personal_info.get("linkedin")
        user.github_url = personal_info.get("github")
        user.ai_summary = parsed_data.get("ai_summary")
        user.other_data = parsed_data.get("other_data")
        user.cv_filepath = cv_path
        user.cv_file_hash = cv_hash
        
        context_for_embedding = f"Summary: {user.ai_summary} Experience: {' '.join(str(i) for i in parsed_data.get('work_experiences', []))} Projects: {' '.join(str(i) for i in parsed_data.get('projects', []))} Skills: {', '.join(parsed_data.get('skills', []))}"
        user.embedding = embeddings_model.embed_query(context_for_embedding)

        # Zapisywanie relacji
        RELATION_MAP = {
            'work_experiences': models.WorkExperience,
            'education_history': models.Education,
            'projects': models.Project,
            'languages': models.Language,
            'publications': models.Publication,
            'certifications': models.Certification
        }

        for key, model_class in RELATION_MAP.items():
            db.query(model_class).filter(model_class.user_id == user.id).delete()
            for item_data in parsed_data.get(key, []):
                if item_data:
                    db_item = model_class(**item_data, user_id=user.id)
                    db.add(db_item)
        
        # --- POPRAWKA ZAPISYWANIA UMIEJĘTNOŚCI ---
        # Używamy bardziej jawnej metody, aby zapewnić poprawny zapis
        user.skills.clear()
        db.flush()
        skill_objects = [crud.get_or_create_skill(db, s) for s in parsed_data.get("skills", [])]
        for skill_obj in skill_objects:
            user.skills.append(skill_obj)
        
        db.commit()
        db.refresh(user)
        return user

class CVService:
    @staticmethod
    async def process_uploaded_cv(db: Session, file: UploadFile, upload_dir: Path):
        if file.content_type not in ["application/pdf"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Niedozwolony typ pliku.")
        contents = await file.read()
        file_hash = hashlib.sha256(contents).hexdigest()
        unique_filename = f"{file_hash}.pdf"
        file_path = upload_dir / unique_filename
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        try:
            parsed_data = parse_cv_file(str(file_path)) 
        except Exception as e:
            file_path.unlink(missing_ok=True)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Błąd parsowania CV: {e}")
        return UserService.create_or_update_user_from_cv(db, parsed_data, str(file_path), file_hash)

class SearchService:
    _cache = {}
    @staticmethod
    async def intelligent_search(db: Session, query: str):
        await asyncio.sleep(0.5)
        return {"summary": f"Wyniki dla: '{query}'", "profiles": []}
