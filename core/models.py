# core/models.py
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .database import Base

user_skills_table = Table('user_skills', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
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
    experience_score = Column(Float, default=0.0)
    embedding = Column(Vector(1536))
    cv_filepath = Column(String, nullable=True)
    cv_file_hash = Column(String, unique=True, index=True, nullable=True) # Do cache'owania

    skills = relationship("Skill", secondary=user_skills_table, back_populates="users")
    work_experiences = relationship("WorkExperience", back_populates="user", cascade="all, delete-orphan")
    education_history = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

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
    duration_months = Column(Integer, nullable=True)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="work_experiences")

class Education(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String)
    degree = Column(String)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="education_history")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="projects")

class CVCache(Base):
    __tablename__ = "cv_cache"
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String, unique=True, index=True, nullable=False)
    parsed_data = Column(JSON, nullable=False)
