# core/crud.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from . import models, schemas

# --- Funkcje Użytkownika ---

def get_user(db: Session, user_id: int):
    return db.query(models.User).options(
        joinedload(models.User.skills),
        joinedload(models.User.work_experiences),
        joinedload(models.User.education_history),
        joinedload(models.User.projects),
        joinedload(models.User.languages),
        joinedload(models.User.publications),
        joinedload(models.User.certifications)
    ).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    query = db.query(models.User).options(
        joinedload(models.User.skills),
        joinedload(models.User.work_experiences),
        joinedload(models.User.education_history),
        joinedload(models.User.projects),
        joinedload(models.User.languages),
        joinedload(models.User.publications),
        joinedload(models.User.certifications)
    )
    return query.order_by(models.User.surname, models.User.name).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, name=user.name, surname=user.surname)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Funkcje Umiejętności (Skills) ---

def get_skill_by_name(db: Session, name: str) -> Optional[models.Skill]:
    return db.query(models.Skill).filter(models.Skill.name.ilike(name)).first()

def create_skill(db: Session, name: str) -> models.Skill:
    db_skill = models.Skill(name=name)
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

# **** PRZYWRÓCONA, KLUCZOWA FUNKCJA ****
def get_or_create_skill(db: Session, name: str) -> models.Skill:
    """
    Pobiera umiejętność z bazy danych po nazwie. Jeśli nie istnieje, tworzy ją.
    """
    skill = get_skill_by_name(db, name=name)
    if not skill:
        skill = create_skill(db, name=name)
    return skill
