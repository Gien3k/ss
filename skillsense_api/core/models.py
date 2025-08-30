# core/models.py
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Text, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base
import enum

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
    Column('added_at', DateTime(timezone=True), server_default=func.now()),
    extend_existing=True
)

user_skills_table = Table('user_skills', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True),
    extend_existing=True
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    surname = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    description = Column(Text)
    embedding = Column(Vector(1536))
    cv_filepath = Column(String, nullable=True)
    cv_file_hash = Column(String, unique=True, index=True, nullable=True)
    skills = relationship("Skill", secondary=user_skills_table, back_populates="users")
    work_experiences = relationship("WorkExperience", back_populates="user", cascade="all, delete-orphan")
    education_history = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    recruitment_projects = relationship("RecruitmentProject", secondary=project_candidates_table, back_populates="candidates")
    languages = relationship("Language", back_populates="user", cascade="all, delete-orphan")
    publications = relationship("Publication", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    __table_args__ = {'extend_existing': True}

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    users = relationship("User", secondary=user_skills_table, back_populates="skills")
    __table_args__ = {'extend_existing': True}

class RecruitmentProject(Base):
    __tablename__ = "recruitment_projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    candidates = relationship("User", secondary=project_candidates_table, back_populates="recruitment_projects")
    __table_args__ = {'extend_existing': True}

class WorkExperience(Base):
    __tablename__ = "work_experience"
    id = Column(Integer, primary_key=True, index=True)
    position = Column(String)
    company = Column(String)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    duration_months = Column(Integer, nullable=True)
    description = Column(Text)
    technologies_used = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="work_experiences")
    __table_args__ = {'extend_existing': True}

class Education(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String)
    degree = Column(String)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="education_history")
    __table_args__ = {'extend_existing': True}

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    technologies_used = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="projects")
    __table_args__ = {'extend_existing': True}

class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    level = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="languages")
    __table_args__ = {'extend_existing': True}

class Publication(Base):
    __tablename__ = "publications"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    outlet = Column(String, nullable=True)
    date = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="publications")
    __table_args__ = {'extend_existing': True}

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    role = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="activities")
    __table_args__ = {'extend_existing': True}

class CVCache(Base):
    __tablename__ = "cv_cache"
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String, unique=True, index=True, nullable=False)
    parsed_data = Column(JSON, nullable=False)
    __table_args__ = {'extend_existing': True}

class SearchFeedback(Base):
    __tablename__ = "search_feedback"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    rated_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = {'extend_existing': True}
