# core/crud.py
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional, Sequence, Dict

from . import models, schemas

# --- Domyślne opcje ładowania relacji dla User ---
# POPRAWKA: Dodanie brakujących relacji, aby dane były zawsze wczytywane
DEFAULT_USER_LOADER_OPTIONS = [
    selectinload(models.User.skills),
    selectinload(models.User.work_experiences),
    selectinload(models.User.education_history),
    selectinload(models.User.projects),
    selectinload(models.User.languages),
    selectinload(models.User.publications),
    selectinload(models.User.certifications),
]

# --- Funkcje CRUD dla Użytkownika (w pełni asynchroniczne) ---

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Asynchronicznie pobiera użytkownika po ID z załadowanymi relacjami."""
    result = await db.execute(
        select(models.User).options(*DEFAULT_USER_LOADER_OPTIONS).filter(models.User.id == user_id)
    )
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    """Asynchronicznie pobiera użytkownika po adresie email."""
    stmt = (
        select(models.User)
        .options(*DEFAULT_USER_LOADER_OPTIONS)
        .filter(models.User.email == email)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_all_users(db: AsyncSession, skip: int, limit: int) -> Dict:
    """Asynchronicznie pobiera paginowaną listę wszystkich użytkowników."""
    count_query = select(func.count()).select_from(models.User)
    total = (await db.execute(count_query)).scalar_one()

    query = (
        select(models.User)
        .options(*DEFAULT_USER_LOADER_OPTIONS)
        .order_by(models.User.surname, models.User.name)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {"total": total, "page": (skip // limit) + 1, "limit": limit, "items": users}


# --- Funkcje CRUD dla Umiejętności (w pełni asynchroniczne) ---

async def get_skill_by_name(db: AsyncSession, name: str) -> Optional[models.Skill]:
    """Asynchronicznie pobiera umiejętność po nazwie."""
    result = await db.execute(select(models.Skill).filter(models.Skill.name.ilike(name)))
    return result.scalars().first()

async def get_or_create_skill(db: AsyncSession, name: str) -> models.Skill:
    """Asynchronicznie pobiera umiejętność z bazy danych lub ją tworzy."""
    skill = await get_skill_by_name(db, name=name)
    if not skill:
        skill = models.Skill(name=name)
        db.add(skill)
        await db.flush()
        await db.refresh(skill)
    return skill

# --- Nowe, wyspecjalizowane funkcje wyszukiwania ---

async def vector_search_users(db: AsyncSession, query_embedding: List[float], limit: int = 50) -> Sequence[models.User]:
    """Asynchronicznie wyszukiwanie wektorowe."""
    stmt = (
        select(models.User)
        .order_by(models.User.embedding.l2_distance(query_embedding))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def full_text_search_users(db: AsyncSession, query_text: str, limit: int = 50) -> Sequence[models.User]:
    """Asynchroniczne wyszukiwanie pełnotekstowe z użyciem tsvector."""
    if not query_text or not query_text.strip():
        return []
        
    ts_query_text = " & ".join(query_text.strip().split())
    
    stmt = (
        select(models.User)
        .filter(models.User.tsvector_col.match(ts_query_text, postgresql_regconfig='english'))
        .order_by(func.ts_rank(models.User.tsvector_col, func.to_tsquery('english', ts_query_text)).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_users_by_ids_with_filters(
    db: AsyncSession, 
    user_ids: List[int],
    required_skills: Optional[List[str]] = None
) -> List[models.User]:
    """
    Pobiera pełne profile użytkowników na podstawie listy ID i aplikuje dodatkowe,
    precycyjne filtry.
    """
    if not user_ids:
        return []

    stmt = select(models.User).options(*DEFAULT_USER_LOADER_OPTIONS).filter(models.User.id.in_(user_ids))

    if required_skills:
        for skill in required_skills:
            stmt = stmt.filter(models.User.skills.any(models.Skill.name.ilike(skill)))
            
    result = await db.execute(stmt)
    
    results_map = {user.id: user for user in result.scalars().all()}
    sorted_results = [results_map[id] for id in user_ids if id in results_map]
    
    return sorted_results
