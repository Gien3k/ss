# core/cv_parser.py
import os
import re
from unstructured.partition.pdf import partition_pdf
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional

# Definicja precyzyjnej struktury wyjściowej dla AI
class PersonalInfo(BaseModel):
    name: Optional[str] = Field(description="Imię i nazwisko kandydata")
    email: Optional[str] = Field(description="Adres email kandydata")
    phone: Optional[str] = Field(description="Numer telefonu kandydata")
    linkedin: Optional[str] = Field(description="Pełny link do profilu LinkedIn")
    github: Optional[str] = Field(description="Pełny link do profilu GitHub")

class WorkExperience(BaseModel):
    position: Optional[str] = Field(description="Stanowisko")
    company: Optional[str] = Field(description="Nazwa firmy")
    start_date: Optional[str] = Field(description="Data rozpoczęcia (format MM.RRRR)")
    end_date: Optional[str] = Field(description="Data zakończenia (format MM.RRRR lub 'Obecnie')")
    description: Optional[str] = Field(description="Opis obowiązków i osiągnięć")

class Education(BaseModel):
    institution: Optional[str] = Field(description="Nazwa uczelni")
    degree: Optional[str] = Field(description="Kierunek i stopień studiów")
    start_date: Optional[str] = Field(description="Rok rozpoczęcia")
    end_date: Optional[str] = Field(description="Rok zakończenia (lub planowany)")

class Skills(BaseModel):
    programming_languages: Optional[List[str]] = Field(description="Lista języków programowania")
    tools_and_technologies: Optional[List[str]] = Field(description="Lista narzędzi i technologii")
    methodologies: Optional[List[str]] = Field(description="Lista metodyk, np. Agile, Scrum")
    languages: Optional[List[str]] = Field(description="Lista języków obcych z poziomem")

class Project(BaseModel):
    name: Optional[str] = Field(description="Nazwa projektu")
    description: Optional[str] = Field(description="Opis projektu i użytych technologii")

class CVData(BaseModel):
    personal_info: PersonalInfo
    summary: str = Field(description="Profesjonalne podsumowanie kandydata w 3-4 zdaniach")
    work_experience: List[WorkExperience]
    education: List[Education]
    skills: Skills
    projects: List[Project]
    achievements: List[str] = Field(description="Lista konkretnych osiągnięć")

# Inicjalizacja modelu z włączonym structured_output
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.0).with_structured_output(CVData)

def clean_cv_text(text: str) -> str:
    """Usuwa nieistotne fragmenty z tekstu CV, aby zmniejszyć zużycie tokenów."""
    # Usuwanie klauzul RODO i podobnych
    text = re.sub(r'Wyrażam zgodę na przetwarzanie.*?RODO\)\.', '', text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()

def extract_structured_data(text: str) -> dict:
    """Używa zaawansowanego promptu i structured_output do wyciągnięcia danych."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Jesteś wysoce precyzyjnym systemem do parsowania CV. Twoim zadaniem jest przekształcenie surowego tekstu z CV w ustrukturyzowany format. Bądź bardzo dokładny. Jeśli jakaś informacja nie występuje, pomiń ją."),
        ("human", "Przeanalizuj poniższy tekst z CV:\n\n---\n```\n{cv_text}\n```\n---")
    ])
    chain = prompt | llm
    response = chain.invoke({"cv_text": text})
    return response.dict()

def parse_cv_file(file_path: str) -> dict:
    """Orkiestruje procesem parsowania pliku CV."""
    elements = partition_pdf(filename=file_path, strategy="hi_res", languages=['pol', 'eng'])
    text = "\n\n".join([str(el) for el in elements])
    if not text.strip():
        raise ValueError("Nie udało się odczytać tekstu z pliku.")
    
    cleaned_text = clean_cv_text(text)
    return extract_structured_data(cleaned_text)
