# core/models.py
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Text, JSON, DateTime, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base
import enum

# ... (reszta pliku, CandidateStatusEnum, tabele pośredniczące... bez zmian) ...
class CandidateStatusEnum(enum.Enum):
    new = "Nowy"
    screening = "Screening"
    interview = "Rozmowa"
    offer = "Oferta"
    hired = "Zatrudniony"
    rejected = "Odrzucony"

project_candidates_table = Table('project_candidates', Base.metadata,
    Column('project_id', Integer, ForeignKey('recruitment_projects.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('status', Enum(CandidateStatusEnum, native_enum=False), default=CandidateStatusEnum.new, nullable=False),
    Column('notes', Text, nullable=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now())
)

user_skills_table = Table('user_skills', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)
    surname = Column(String, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    ai_summary = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    cv_filepath = Column(String, nullable=True)
    cv_file_hash = Column(String, unique=True, index=True, nullable=True)
    other_data = Column(JSON, nullable=True)

    skills = relationship("Skill", secondary=user_skills_table, back_populates="users")
    work_experiences = relationship("WorkExperience", back_populates="user", cascade="all, delete-orphan")
    education_history = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="user", cascade="all, delete-orphan")
    publications = relationship("Publication", back_populates="user", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="user", cascade="all, delete-orphan")
    recruitment_projects = relationship("RecruitmentProject", secondary=project_candidates_table, back_populates="candidates")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    users = relationship("User", secondary=user_skills_table, back_populates="skills")


class WorkExperience(Base):
    __tablename__ = "work_experience"
    id = Column(Integer, primary_key=True, index=True)
    position = Column(String)
    company = Column(String)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    technologies_used = Column(JSON, nullable=True) # <-- DODANA BRAKUJĄCA KOLUMNA
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="work_experiences")

# ... (reszta modeli: Education, Project, etc. bez zmian) ...
class Education(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String)
    degree = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="education_history")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="projects")

class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    level = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="languages")

class Publication(Base):
    __tablename__ = "publications"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    outlet = Column(String, nullable=True)
    date = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="publications")

class Certification(Base):
    __tablename__ = "certifications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    issuing_organization = Column(String, nullable=True)
    date_issued = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="certifications")

class RecruitmentProject(Base):
    __tablename__ = "recruitment_projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    candidates = relationship("User", secondary=project_candidates_table, back_populates="recruitment_projects")

class CVCache(Base):
    __tablename__ = "cv_cache"
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String, unique=True, index=True, nullable=False)
    parsed_data = Column(JSON, nullable=False)

class SearchFeedback(Base):
    __tablename__ = "search_feedback"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    rated_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
