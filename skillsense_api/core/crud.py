# core/crud.py
import re
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, text
from langchain_openai import OpenAIEmbeddings
from typing import List
from . import models

embeddings_model = OpenAIEmbeddings()

def get_cached_cv_result(db: Session, file_hash: str):
    return db.query(models.CVCache).filter(models.CVCache.file_hash == file_hash).first()

def cache_cv_result(db: Session, file_hash: str, parsed_data: dict):
    db_cache = models.CVCache(file_hash=file_hash, parsed_data=parsed_data)
    db.add(db_cache)
    db.commit()

def calculate_duration_in_months(start_date_str: str, end_date_str: str) -> int | None:
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

def get_skill_by_name(db: Session, skill_name: str):
    return db.query(models.Skill).filter(models.Skill.name.ilike(skill_name)).first()

def get_or_create_skill(db: Session, skill_name: str):
    skill = get_skill_by_name(db, skill_name)
    if not skill:
        skill = models.Skill(name=skill_name)
        db.add(skill)
        db.commit()
        db.refresh(skill)
    return skill

def get_user_by_email(db: Session, email: str):
    if not email: return None
    return db.query(models.User).filter(models.User.email == email).first()

def create_user_profile(db: Session, parsed_data: dict, cv_filepath: str | None = None, cv_file_hash: str | None = None):
    personal_info = parsed_data.get("personal_info") or {}
    full_name = (personal_info.get("name") or "Brak Imienia").split(); name = full_name[0]; surname = " ".join(full_name[1:]) if len(full_name) > 1 else ""
    summary_text = parsed_data.get("summary", ""); experience_text = " ".join([exp.get("description", "") for exp in parsed_data.get("work_experience", [])]); projects_text = " ".join([proj.get("description", "") for proj in parsed_data.get("projects", [])])
    full_context_for_embedding = f"{summary_text} {experience_text} {projects_text}"; embedding = embeddings_model.embed_query(full_context_for_embedding)
    
    db_user = get_user_by_email(db, personal_info.get("email"))
    if db_user:
        for key, value in personal_info.items(): setattr(db_user, f"{key}_url" if key in ['linkedin', 'github'] else key, value)
        db_user.name, db_user.surname, db_user.embedding, db_user.description = name, surname, embedding, summary_text
    else:
        db_user = models.User(name=name, surname=surname, email=personal_info.get("email"), phone=personal_info.get("phone"), linkedin_url=personal_info.get("linkedin"), github_url=personal_info.get("github"), description=summary_text, embedding=embedding, cv_filepath=cv_filepath, cv_file_hash=cv_file_hash)
        db.add(db_user)

    db_user.skills = [get_or_create_skill(db, s.strip()) for s in parsed_data.get("all_skills", []) if s]
    
    related_models = [
        (models.WorkExperience, "work_experience"), (models.Education, "education"),
        (models.Project, "projects"), (models.Language, "languages"),
        (models.Publication, "publications"), (models.Activity, "activities")
    ]
    for model_cls, key in related_models:
        db.query(model_cls).filter(model_cls.user_id == db_user.id).delete(synchronize_session=False)
        for item_data in parsed_data.get(key, []):
            if key == "work_experience": item_data['duration_months'] = calculate_duration_in_months(item_data.get("start_date", "") or "", item_data.get("end_date", "") or "")
            if item_data: db.add(model_cls(**item_data, user=db_user))
    
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_users(db: Session, search: str | None = None):
    query = db.query(models.User).options(
        joinedload(models.User.skills), 
        joinedload(models.User.work_experiences), 
        joinedload(models.User.education_history), 
        joinedload(models.User.projects), 
        joinedload(models.User.languages), 
        joinedload(models.User.publications), 
        joinedload(models.User.activities)
    )
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(models.User.name.ilike(search_term), models.User.surname.ilike(search_term)))
    return query.order_by(models.User.surname).all()

def get_all_skill_names(db: Session) -> List[str]:
    return [name for name, in db.query(models.Skill.name).all()]

def keyword_search_users(db: Session, keywords: List[str], limit: int = 20) -> List[models.User]:
    if not keywords: return []
    query = db.query(models.User).options(joinedload(models.User.skills))
    search_conditions = [or_(models.User.description.ilike(f"%{k}%"), models.User.skills.any(models.Skill.name.ilike(f"%{k}%"))) for k in keywords]
    query = query.filter(and_(*search_conditions))
    return query.limit(limit).all()

def vector_search_users(db: Session, query_text: str, limit: int = 20) -> List[tuple[models.User, float]]:
    query_embedding = embeddings_model.embed_query(query_text)
    return db.query(models.User, models.User.embedding.l2_distance(query_embedding).label("distance")).options(joinedload(models.User.skills), joinedload(models.User.education_history)).order_by("distance").limit(limit).all()

def save_feedback(db: Session, query: str, rated_user_id: int, rating: str):
    feedback_entry = models.SearchFeedback(query=query, rated_user_id=rated_user_id, rating=rating)
    db.add(feedback_entry)
    db.commit()

def create_recruitment_project(db: Session, name: str, description: str | None) -> models.RecruitmentProject:
    db_project = models.RecruitmentProject(name=name, description=description)
    db.add(db_project)
    db.commit()
    return db_project

def get_all_recruitment_projects(db: Session):
    return db.query(models.RecruitmentProject).order_by(models.RecruitmentProject.created_at.desc()).all()

def get_project_with_candidates(db: Session, project_id: int):
    project = db.query(models.RecruitmentProject).filter(models.RecruitmentProject.id == project_id).first()
    if not project: return None
    stmt = text("SELECT u.*, pc.status, pc.notes FROM users u JOIN project_candidates pc ON u.id = pc.user_id WHERE pc.project_id = :project_id ORDER BY pc.added_at DESC")
    candidates_results = db.execute(stmt, {"project_id": project_id}).mappings().all(); user_ids = [c['id'] for c in candidates_results]
    if not user_ids: project.candidates_with_status = []; return project
    users_with_relations = db.query(models.User).options(joinedload(models.User.skills), joinedload(models.User.work_experiences), joinedload(models.User.education_history), joinedload(models.User.projects), joinedload(models.User.languages), joinedload(models.User.publications), joinedload(models.User.activities)).filter(models.User.id.in_(user_ids)).all()
    users_map = {user.id: user for user in users_with_relations}; final_candidates = []
    for cand_data in candidates_results:
        user_obj = users_map.get(cand_data['id'])
        if user_obj:
            user_dict = {c.name: getattr(user_obj, c.name) for c in user_obj.__table__.columns}
            user_dict.update({'status': models.CandidateStatusEnum[cand_data['status']].value, 'notes': cand_data['notes'], 'skills': user_obj.skills, 'work_experiences': user_obj.work_experiences, 'education_history': user_obj.education_history, 'projects': user_obj.projects, 'languages': user_obj.languages, 'publications': user_obj.publications, 'activities': user_obj.activities})
            final_candidates.append(user_dict)
    project.candidates_with_status = final_candidates; return project

def add_candidate_to_project(db: Session, project_id: int, user_id: int):
    stmt_check = text("SELECT 1 FROM project_candidates WHERE project_id=:p_id AND user_id=:u_id")
    if db.execute(stmt_check, {"p_id": project_id, "u_id": user_id}).first(): return
    stmt = text("INSERT INTO project_candidates (project_id, user_id, status) VALUES (:p_id, :u_id, :status)")
    db.execute(stmt, {"p_id": project_id, "u_id": user_id, "status": models.CandidateStatusEnum.new.name}); db.commit()

def update_candidate_in_project(db: Session, project_id: int, user_id: int, status: models.CandidateStatusEnum, notes: str | None):
    stmt = text("UPDATE project_candidates SET status = :status, notes = :notes WHERE project_id = :p_id AND user_id = :u_id")
    db.execute(stmt, {"status": status.name, "notes": notes, "p_id": project_id, "u_id": user_id}); db.commit()
