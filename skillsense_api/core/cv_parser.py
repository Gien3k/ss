# core/cv_parser.py
import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from unstructured.partition.pdf import partition_pdf
import json

llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
summary_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# --- Schematy Pydantic (bez zmian) ---
class PersonalInfo(BaseModel): name: Optional[str] = None; email: Optional[str] = None; phone: Optional[str] = None; linkedin: Optional[str] = None; github: Optional[str] = None
class WorkExperience(BaseModel): position: str; company: str; start_date: Optional[str] = None; end_date: Optional[str] = None; description: Optional[str] = None; technologies_used: Optional[List[str]] = []
class Education(BaseModel): institution: str; degree: Optional[str] = None; start_date: Optional[str] = None; end_date: Optional[str] = None
class Project(BaseModel): name: str; description: Optional[str] = None
class Language(BaseModel): name: str; level: str
class Publication(BaseModel): title: str; outlet: Optional[str] = None; date: Optional[str] = None
class Certification(BaseModel): name: str; issuing_organization: Optional[str] = None; date_issued: Optional[str] = None

class FullCVData(BaseModel):
    personal_info: PersonalInfo
    summary: Optional[str] = Field(None)
    work_experiences: List[WorkExperience]
    education_history: List[Education]
    projects_and_achievements: List[Project]
    all_skills: List[str]
    languages: List[Language]
    publications: List[Publication]
    certifications: List[Certification]
    other_data: Optional[List[Dict[str, str]]] = Field(None, description="Inne sekcje, w formacie [{'Nagłówek': 'Treść'}]")

def parse_cv_file(file_path: str) -> dict:
    print("\n--- OSTATECZNY, NIEZAWODNY PROCES PARSOWANIA v3 ---")
    
    try:
        elements = partition_pdf(filename=file_path, strategy="hi_res", infer_table_structure=True)
        text = "\n\n".join([str(el) for el in elements])
        text = re.sub(r'\s*\d+\s*/\s*\d+\s*', '', text)
        print("1. Tekst z CV został pomyślnie odczytany.")
    except Exception as e:
        raise ValueError(f"KRYTYCZNY BŁĄD ODCZYTU PDF: {e}")

    # --- POPRAWIONY PROMPT ---
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Twoim zadaniem jest wcielenie się w rolę super-precyzyjnego analityka danych HR. Przeanalizuj poniższy tekst z CV i bezbłędnie wypełnij schemat JSON.
        Bądź absolutnie kompletny. Zwróć szczególną uwagę na wyciągnięcie WSZYSTKICH danych kontaktowych.
        WAŻNE REGUŁY:
        - Działalność w kołach naukowych traktuj jako DOŚWIADCZENIE ZAWODOWE.
        - Osiągnięcia i hackathony traktuj jako PROJEKTY.
        - Wszystkie pozostałe sekcje (np. Zainteresowania) umieść w `other_data` jako listę obiektów `[{{\'nazwa_sekcji\': \'treść_sekcji\'}}]`.
        """),
        ("human", "Przeanalizuj poniższy tekst z CV i wyekstrahuj z niego wszystkie dane zgodnie z podanym schematem:\n\n---\n{cv_text}\n---")
    ])
    
    chain = prompt | llm.with_structured_output(FullCVData)
    
    print("2. Wysyłam pełny tekst CV do AI w celu kompletnej ekstrakcji...")
    structured_output = chain.invoke({"cv_text": text})
    
    parsed_data = structured_output.dict()
    print("3. Otrzymano kompletne, ustrukturyzowane dane od AI.")
    
    parsed_data['projects'] = parsed_data.pop('projects_and_achievements')
    
    summary_prompt = ChatPromptTemplate.from_template("Napisz profesjonalne podsumowanie kandydata (3-4 zdania) na podstawie danych.\nDANE:\n{data}")
    summary_chain = summary_prompt | summary_llm | StrOutputParser()
    parsed_data['ai_summary'] = summary_chain.invoke({"data": json.dumps(parsed_data, indent=2, ensure_ascii=False)})
    print("4. Wygenerowano podsumowanie AI.")

    parsed_data['skills'] = parsed_data.pop('all_skills')

    print("--- PARSOWANIE ZAKOŃCZONE PEŁNYM SUKCESEM ---")
    return parsed_data
