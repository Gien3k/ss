# core/search.py
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from . import crud, models
from .cv_parser import parse_cv_file, extract_structured_data

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

class DeconstructedQuery(BaseModel):
    explicit_skills: List[str] = Field(default=[], description="Lista konkretnych technologii, narzędzi lub umiejętności wprost wymienionych w zapytaniu (np. 'Python', 'React').")
    implied_abilities: List[str] = Field(default=[], description="Lista ogólnych zdolności, funkcji lub ról, o które pyta użytkownik (np. 'potrafi budować API', 'doświadczenie z chmurą', 'jest analitykiem danych').")

def deconstruct_query_with_llm(query: str) -> dict:
    parser = PydanticOutputParser(pydantic_object=DeconstructedQuery)
    prompt = ChatPromptTemplate.from_template("Twoim zadaniem jest dogłębna analiza zapytania rekrutacyjnego. Rozłóż je na dwie kategorie: konkretne, twarde umiejętności oraz ogólne, implikowane zdolności lub role.\nZapytanie: \"{query}\"\n{format_instructions}", partial_variables={"format_instructions": parser.get_format_instructions()})
    chain = prompt | llm | parser
    try: return chain.invoke({"query": query}).dict()
    except Exception: return {"explicit_skills": [], "implied_abilities": []}

def verify_ability_with_llm(profile_context: str, ability: str) -> bool:
    prompt = ChatPromptTemplate.from_template("Biorąc pod uwagę poniższy kontekst z profilu kandydata, odpowiedz 'tak' lub 'nie', czy posiada on następującą zdolność: '{ability}'.\nKontekst: {profile_context}")
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"profile_context": profile_context, "ability": ability})
    return "tak" in response.lower()

def rag_search(db: Session, query: str):
    deconstructed_query = deconstruct_query_with_llm(query)
    all_keywords = list(set(deconstructed_query.get('explicit_skills', [])))
    keyword_results = crud.keyword_search_users(db, keywords=all_keywords) if all_keywords else []
    vector_results_with_distance = crud.vector_search_users(db, query_text=query)
    
    candidates_to_analyze: Dict[int, Dict] = {}
    for user in keyword_results: candidates_to_analyze[user.id] = {"profile": user, "distance": 1.0}
    for user, distance in vector_results_with_distance:
        if user.id not in candidates_to_analyze: candidates_to_analyze[user.id] = {"profile": user, "distance": distance}
    if not candidates_to_analyze: return {"summary": "Niestety, nie znalazłem żadnych kandydatów w bazie danych.", "profiles": []}

    ranked_profiles = []
    for data in candidates_to_analyze.values():
        profile = data['profile']
        profile_context = f"Edukacja: {[edu.degree for edu in profile.education_history]}. Umiejętności: {[s.name for s in profile.skills]}. Doświadczenie i projekty: {profile.description}"
        abilities_score = 0
        if implied_abilities := deconstructed_query.get('implied_abilities', []):
            verified_abilities = sum(1 for ability in implied_abilities if verify_ability_with_llm(profile_context, ability))
            abilities_score = verified_abilities / len(implied_abilities)
        skills_score = 0
        if explicit_skills := deconstructed_query.get('explicit_skills', []):
            user_skills_set = {s.name.lower() for s in profile.skills}
            matched_skills = sum(1 for skill in explicit_skills if skill.lower() in user_skills_set)
            skills_score = matched_skills / len(explicit_skills)
        semantic_score = max(0, 1 - data['distance'])
        match_score = round(((abilities_score * 0.5) + (skills_score * 0.3) + (semantic_score * 0.2)) * 100)
        if match_score > 35: ranked_profiles.append({"profile": profile, "match_score": match_score})

    ranked_profiles.sort(key=lambda x: x['match_score'], reverse=True)
    top_profiles = ranked_profiles[:5]
    if not top_profiles: return {"summary": "Znalazłem kandydatów, ale po dogłębnej analizie żaden nie pasował wystarczająco do zapytania.", "profiles": []}
    
    context = "Oto profile kandydatów:\n" + "\n".join([f"- Profil: {item['profile'].name} {item['profile'].surname}, Umiejętności: {', '.join([s.name for s in item['profile'].skills])}, DOPASOWANIE: {item['match_score']}%" for item in top_profiles[:3]])
    prompt = ChatPromptTemplate.from_template("Jesteś asystentem rekrutacyjnym. Przeanalizuj profile i odpowiedz na zapytanie. W 1-2 zdaniach podsumuj, dlaczego kandydaci pasują. Wskaż najlepszego.\nKONTEKST: {context}\nZAPYTANIE: \"{query}\"")
    summary = (prompt | llm | StrOutputParser()).invoke({"context": context, "query": query})
    
    final_profiles_response = []
    for item in top_profiles:
        profile = item['profile']
        profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
        profile_dict.update({'skills': profile.skills, 'work_experiences': profile.work_experiences, 'education_history': profile.education_history, 'projects': profile.projects, 'languages': profile.languages, 'publications': profile.publications, 'activities': profile.activities, 'match_score': item['match_score']})
        final_profiles_response.append(profile_dict)

    return {"summary": summary, "profiles": final_profiles_response}

def generate_interview_questions(user: models.User, query: str) -> List[str]:
    skills_str = ", ".join([s.name for s in user.skills])
    prompt = ChatPromptTemplate.from_template("Jesteś rekruterem technicznym. Stwórz 5 pytań na rozmowę kwalifikacyjną.\nZAPYTANIE: \"{query}\"\nPROFIL KANDYDATA: Imię: {name} {surname}, Podsumowanie: {description}, Umiejętności: {skills}\nNa podstawie danych, stwórz 5 konkretnych pytań. Zwróć listę JSON, np. [\"Pytanie 1\", ...].")
    return (prompt | llm | JsonOutputParser()).invoke({"query": query, "name": user.name, "surname": user.surname, "description": user.description, "skills": skills_str})
