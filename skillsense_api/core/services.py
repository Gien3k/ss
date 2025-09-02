
# core/services.py
import asyncio
import hashlib
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
# POPRAWKA: Importujemy 'delete' bezpośrednio z sqlalchemy
from sqlalchemy import func, delete
from typing import Dict, Any

from . import crud, models, schemas
from .cv_parser import parse_cv_file
from langchain_openai import OpenAIEmbeddings

embeddings_model = OpenAIEmbeddings(model="text-embedding-ada-002")

class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        return await crud.get_user_by_id(db, user_id=user_id)

    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int, limit: int) -> Dict:
        return await crud.get_all_users(db, skip=skip, limit=limit)

    @staticmethod
    async def create_or_update_user_from_cv(db: AsyncSession, parsed_data: Dict[str, Any], cv_path: str, cv_hash: str):
        personal_info = parsed_data.get("personal_info", {})
        email = personal_info.get("email")
        
        user = await crud.get_user_by_email(db, email=email)
        
        if not user:
            user = models.User(email=email)
            db.add(user)
        
        # Aktualizacja głównych pól
        name_parts = (personal_info.get("name") or " ").split()
        user.name = name_parts[0]
        user.surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        user.phone = personal_info.get("phone")
        user.linkedin_url = personal_info.get("linkedin")
        user.github_url = personal_info.get("github")
        user.ai_summary = parsed_data.get("ai_summary")
        user.other_data = parsed_data.get("other_data")
        user.cv_filepath = cv_path
        user.cv_file_hash = cv_hash
        
        context_for_embedding = f"Summary: {user.ai_summary} Experience: {' '.join(str(i) for i in parsed_data.get('work_experiences', []))} Projects: {' '.join(str(i) for i in parsed_data.get('projects', []))} Skills: {', '.join(parsed_data.get('skills', []))}"
        user.embedding = await embeddings_model.aembed_query(context_for_embedding)
        user.tsvector_col = func.to_tsvector('english', context_for_embedding)

        # Commit podstawowych danych, aby uzyskać ID
        await db.commit()
        await db.refresh(user)

        # Zarządzanie relacjami
        RELATION_MAP = {
            'work_experiences': models.WorkExperience,
            'education_history': models.Education,
            'projects': models.Project,
            'languages': models.Language,
            'publications': models.Publication,
            'certifications': models.Certification,
        }

        for key, model_class in RELATION_MAP.items():
            # POPRAWKA: Używamy 'delete' zamiast 'func.delete'
            await db.execute(delete(model_class).where(model_class.user_id == user.id))
            
            for item_data in parsed_data.get(key, []):
                if item_data:
                    db_item = model_class(**item_data, user_id=user.id)
                    db.add(db_item)

        skill_objects = [await crud.get_or_create_skill(db, s) for s in parsed_data.get("skills", [])]
        user.skills = skill_objects
        
        await db.commit()
        await db.refresh(user)
        
        return user

class CVService:
    @staticmethod
    async def process_uploaded_cv(db: AsyncSession, file: UploadFile, upload_dir: Path):
        if file.content_type not in ["application/pdf"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Niedozwolony typ pliku.")
        
        contents = await file.read()
        file_hash = hashlib.sha256(contents).hexdigest()
        unique_filename = f"{file_hash}.pdf"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
            
        try:
            parsed_data = await asyncio.to_thread(parse_cv_file, str(file_path))
        except Exception as e:
            file_path.unlink(missing_ok=True)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Błąd parsowania CV: {e}")
            
        return await UserService.create_or_update_user_from_cv(db, parsed_data, str(file_path), file_hash)
