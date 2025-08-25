# core/crud.py
import re
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings
from . import models

embeddings_model = OpenAIEmbeddings()

def get_cached_cv_result(db: Session, file_hash: str):
    """Sprawdza, czy przetworzone CV jest już w cache."""
    return db.query(models.CVCache).filter(models.CVCache.file_hash == file_hash).first()

def cache_cv_result(db: Session, file_hash: str, parsed_data: dict):
    """Zapisuje wynik parsowania CV do cache."""
    db_cache = models.CVCache(file_hash=file_hash, parsed_data=parsed_data)
    db.add(db_cache)
    db.commit()

def calculate_duration_in_months(start_date_str: str, end_date_str: str) -> int | None:
    # ... (bez zmian)
    try:
        start_match = re.search(r'(\d{1,2})?\.?(\d{4})', start_date_str)
        end_match = re.search(r'(\d{1,2})?\.?(\d{4})', end_date_str) if "obecnie" not in end_date_str.lower() else None
        start_month = int(start_match.group(1)) if start_match.group(1) else 1
        start_year = int(start_match.group(2))
        start_date = datetime(start_year, start_month, 1)
        if "obecnie" in end_date_str.lower():
            end_date = datetime.now()
        else:
            end_month = int(end_match.group(1)) if end_match.group(1) else 12
            end_year = int(end_match.group(2))
            end_date = datetime(end_year, end_month, 1)
        return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
    except Exception:
        return None

def calculate_experience_score(parsed_data: dict) -> float:
    # ... (bez zmian)
    score = 0.0
    total_months = 0
    for exp in parsed_data.get("work_experience", []):
        duration = calculate_duration_in_months(exp.get("start_date", ""), exp.get("end_date", ""))
        if duration:
            total_months += duration
    score += total_months / 12.0
    score += len(parsed_data.get("projects", [])) * 0.5
    score += len(parsed_data.get("achievements", [])) * 1.0
    return round(score, 2)

def get_skill_by_name(db: Session, skill_name: str):
    return db.query(models.Skill).filter(models.Skill.name == skill_name).first()

def create_skill(db: Session, skill_name: str):
    db_skill = models.Skill(name=skill_name)
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

def get_or_create_skill(db: Session, skill_name: str):
    skill = get_skill_by_name(db, skill_name)
    if not skill:
        skill = create_skill(db, skill_name)
    return skill

def get_user_by_email(db: Session, email: str):
    """Sprawdza, czy użytkownik o danym emailu już istnieje."""
    if not email:
        return None
    return db.query(models.User).filter(models.User.email == email).first()

def create_user_profile(db: Session, parsed_data: dict, cv_filepath: str | None = None, cv_file_hash: str | None = None):
    personal_info = parsed_data.get("personal_info") or {}
    full_name = (personal_info.get("name") or "Brak Imienia").split()
    name = full_name[0]
    surname = " ".join(full_name[1:]) if len(full_name) > 1 else ""
    summary = parsed_data.get("summary", "")
    embedding = embeddings_model.embed_query(summary)
    experience_score = calculate_experience_score(parsed_data)
    
    db_user = get_user_by_email(db, personal_info.get("email"))
    if db_user:
        print(f"Aktualizacja istniejącego użytkownika: {db_user.email}")
        db_user.name = name
        db_user.surname = surname
    else:
        print(f"Tworzenie nowego użytkownika: {personal_info.get('email')}")
        db_user = models.User(
            name=name, surname=surname, email=personal_info.get("email"),
            phone=personal_info.get("phone"), linkedin_url=personal_info.get("linkedin"),
            github_url=personal_info.get("github"), description=summary,
            embedding=embedding, cv_filepath=cv_filepath, 
            experience_score=experience_score, cv_file_hash=cv_file_hash
        )
        db.add(db_user)
    
    skills_dict = parsed_data.get("skills") or {}
    all_skills = list(set(
        (skills_dict.get("programming_languages") or []) +
        (skills_dict.get("tools_and_technologies") or []) +
        (skills_dict.get("methodologies") or []) +
        (skills_dict.get("languages") or [])
    ))
    
    db_user.skills = [] 
    for skill_name in all_skills:
        if skill_name:
            skill_obj = get_or_create_skill(db, skill_name)
            db_user.skills.append(skill_obj)

    db.query(models.WorkExperience).filter(models.WorkExperience.user_id == db_user.id).delete()
    for exp in parsed_data.get("work_experience") or []:
        duration = calculate_duration_in_months(exp.get("start_date", "") or "", exp.get("end_date", "") or "")
        db_exp = models.WorkExperience(
            position=exp.get("position"), company=exp.get("company"),
            start_date=exp.get("start_date"), end_date=exp.get("end_date"),
            description=exp.get("description"), user=db_user, duration_months=duration
        )
        db.add(db_exp)

    db.query(models.Education).filter(models.Education.user_id == db_user.id).delete()
    for edu in parsed_data.get("education") or []:
        db_edu = models.Education(
            institution=edu.get("institution"), degree=edu.get("degree"),
            start_date=edu.get("start_date"), end_date=edu.get("end_date"),
            user=db_user
        )
        db.add(db_edu)

    db.query(models.Project).filter(models.Project.user_id == db_user.id).delete()
    for proj in parsed_data.get("projects") or []:
        db_proj = models.Project(
            name=proj.get("name"), description=proj.get("description"), user=db_user
        )
        db.add(db_proj)

    db.commit()
    db.refresh(db_user)
    return db_user
    
def find_similar_users(db: Session, query: str, filters: dict, limit: int = 10, score_threshold: float = 0.7):
    base_query = db.query(models.User)
    if filters.get("min_experience_score"):
        base_query = base_query.filter(models.User.experience_score >= filters["min_experience_score"])
    candidate_ids = [user.id for user in base_query.all()]
    if not candidate_ids:
        return []
    query_embedding = embeddings_model.embed_query(query)
    similar_users = db.query(models.User).filter(models.User.id.in_(candidate_ids)).filter(
        models.User.embedding.l2_distance(query_embedding) < score_threshold
    ).order_by(
        models.User.embedding.l2_distance(query_embedding)
    ).limit(limit).all()
    return similar_users
    
def get_all_users(db: Session, search: str | None = None):
    query = db.query(models.User)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            models.User.name.ilike(search_term) | models.User.surname.ilike(search_term)
        )
    return query.order_by(models.User.surname).all()
