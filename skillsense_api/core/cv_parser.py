# core/cv_parser.py
import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from unstructured.partition.pdf import partition_pdf

SKILL_NORMALIZATION_MAP = {
    "react.js": "React", "reactjs": "React", "node.js": "Node.js", "nodejs": "Node.js", "express.js": "Express",
    "vue.js": "Vue.js", "angular.js": "Angular", "next.js": "Next.js", "nest.js": "NestJS", "python": "Python",
    "django": "Django", "fastapi": "FastAPI", "flask": "Flask", "java": "Java", "spring": "Spring",
    "springboot": "Spring Boot", "c#": "C#", ".net": ".NET", "javascript": "JavaScript", "typescript": "TypeScript",
    "html5": "HTML", "css3": "CSS", "sql": "SQL", "postgresql": "PostgreSQL", "mysql": "MySQL",
    "mongodb": "MongoDB", "docker": "Docker", "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "google cloud": "GCP", "gcp": "GCP", "git": "Git", "scrum": "Scrum", "agile": "Agile", "jira": "Jira",
    "pl/sql": "PL/SQL", "r": "R", "bash": "Bash"
}

def normalize_skill(skill_name: str) -> str:
    return SKILL_NORMALIZATION_MAP.get(skill_name.lower().strip(), skill_name.strip())

class PersonalInfo(BaseModel):
    name: Optional[str] = Field(None, description="Imię i nazwisko kandydata")
    email: Optional[str] = Field(None, description="Adres email kandydata")
    phone: Optional[str] = Field(None, description="Numer telefonu kandydata")
    linkedin: Optional[str] = Field(None, description="Pełny link lub nazwa użytkownika do profilu LinkedIn")
    github: Optional[str] = Field(None, description="Pełny link lub nazwa użytkownika do profilu GitHub")

class Language(BaseModel):
    name: str = Field(description="Nazwa języka obcego")
    level: str = Field(description="Poziom zaawansowania, np. 'B2', 'C1', 'Natywny'")

class Publication(BaseModel):
    title: str = Field(description="Tytuł publikacji naukowej")
    outlet: Optional[str] = Field(None, description="Miejsce publikacji (np. nazwa konferencji, czasopisma)")
    date: Optional[str] = Field(None, description="Data publikacji")

class Activity(BaseModel):
    name: str = Field(description="Nazwa działalności, np. 'Koło Naukowe Machine Learning'")
    role: Optional[str] = Field(None, description="Rola w tej działalności, np. 'Członek', 'Przewodniczący'")
    start_date: Optional[str] = Field(None, description="Data rozpoczęcia")
    end_date: Optional[str] = Field(None, description="Data zakończenia")
    description: Optional[str] = Field(None, description="Krótki opis działalności")

class WorkExperience(BaseModel):
    position: Optional[str] = Field(None, description="Stanowisko")
    company: Optional[str] = Field(None, description="Nazwa firmy")
    start_date: Optional[str] = Field(None, description="Data rozpoczęcia (format MM.RRRR)")
    end_date: Optional[str] = Field(None, description="Data zakończenia (format MM.RRRR lub 'Obecnie')")
    description: Optional[str] = Field(None, description="Opis obowiązków i osiągnięć")
    technologies_used: List[str] = []

class Project(BaseModel):
    name: Optional[str] = Field(None, description="Nazwa projektu")
    description: Optional[str] = Field(None, description="Opis projektu")
    technologies_used: List[str] = []
    
class Education(BaseModel):
    institution: Optional[str] = Field(None, description="Nazwa uczelni")
    degree: Optional[str] = Field(None, description="Kierunek i stopień studiów")
    start_date: Optional[str] = Field(None, description="Rok rozpoczęcia")
    end_date: Optional[str] = Field(None, description="Rok zakończenia (lub planowany)")

class CVData(BaseModel):
    personal_info: PersonalInfo
    summary: Optional[str] = Field(None, description="Sekcja 'O mnie' lub 'Podsumowanie'")
    work_experience: List[WorkExperience]
    education: List[Education]
    all_skills: List[str] = Field(default=[], description="Kompletna, płaska lista WSZYSTKICH zidentyfikowanych umiejętności, technologii, narzędzi z całego CV.")
    languages: List[Language]
    publications: List[Publication]
    activities: List[Activity] = Field(description="Działalność dodatkowa, np. koła naukowe, organizacje studenckie.")
    projects: List[Project]

extraction_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0).with_structured_output(CVData)
relation_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

def _post_process_data(data: dict) -> dict:
    if p_info := data.get("personal_info"):
        if linkedin := p_info.get("linkedin"):
            if not linkedin.startswith("http"): p_info["linkedin"] = f"https://www.linkedin.com/in/{linkedin}"
        if github := p_info.get("github"):
            if not github.startswith("http"): p_info["github"] = f"https://github.com/{github}"
    if skills := data.get("all_skills"):
        data["all_skills"] = list(set(normalize_skill(s) for s in skills if s))
    return data

def extract_structured_data(text: str) -> dict:
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", "Twoim zadaniem jest BARDZO DOKŁADNA ekstrakcja informacji z CV do formatu JSON. Wyciągnij WSZYSTKIE informacje z sekcji: dane personalne (w tym nazwy użytkownika github/linkedin), O mnie (jako summary), Doświadczenie, Edukacja, Umiejętności (wszystkie), Języki (z poziomami), Publikacje, oraz Koła Naukowe/Działalność dodatkową (jako activities). Bądź precyzyjny i kompletny."),
        ("human", "Przeanalizuj poniższy tekst z CV i wyciągnij z niego dane:\n\n---\n```\n{cv_text}\n```\n---")
    ])
    initial_data = (extraction_prompt | extraction_llm).invoke({"cv_text": text})
    context = f"Lista umiejętności: {initial_data.all_skills}\nDoświadczenie: {[exp.dict() for exp in initial_data.work_experience]}\nProjekty: {[proj.dict() for proj in initial_data.projects]}"
    relation_prompt = ChatPromptTemplate.from_template("Mając kontekst, dla każdego doświadczenia i projektu, wylistuj z 'listy umiejętności', które najprawdopodobniej były w nich używane. Zwróć JSON: {{\"work_experience\": [{{ \"position\": \"...\", \"technologies_used\": [...] }}]}}\nKontekst:\n{context}")
    relations = (relation_prompt | relation_llm | JsonOutputParser()).invoke({"context": context})
    final_data = initial_data.dict()
    for exp in final_data.get('work_experience', []):
        for rel_exp in relations.get('work_experience', []):
            if exp.get('position') == rel_exp.get('position'): exp['technologies_used'] = rel_exp.get('technologies_used', [])
    return _post_process_data(final_data)

def parse_cv_file(file_path: str) -> dict:
    try:
        elements = partition_pdf(filename=file_path, strategy="hi_res", languages=['pol', 'eng'])
        text = "\n\n".join([str(el) for el in elements])
    except Exception:
        elements = partition_pdf(filename=file_path, strategy="fast", languages=['pol', 'eng'])
        text = "\n\n".join([str(el) for el in elements])
    if not text.strip(): raise ValueError("Nie udało się odczytać tekstu z pliku.")
    return extract_structured_data(text)
