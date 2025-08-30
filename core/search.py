# core/search.py
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from . import crud

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.0)

def classify_query(query: str) -> dict:
    # ... (bez zmian)
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_template(
        """
        Przeanalizuj zapytanie rekrutera i wyciągnij z niego strukturalne filtry.
        Możliwe filtry to: 'min_experience_score'.
        Jeśli zapytanie mówi o 'doświadczonym kandydacie', 'seniorze', 'ekspercie', ustaw 'min_experience_score' na 2.0.
        Jeśli zapytanie mówi o 'stażyście', 'juniorze', 'studencie', ustaw 'min_experience_score' na 0.0.
        Jeśli nie ma informacji o doświadczeniu, zwróć pusty obiekt.

        Zapytanie: "{query}"

        Zwróć odpowiedź w formacie JSON, np. {{"min_experience_score": 2.0}}
        """
    )
    chain = prompt | llm | parser
    try:
        return chain.invoke({"query": query})
    except Exception:
        return {}
        
def rag_search(db: Session, query: str):
    filters = classify_query(query)
    
    similar_profiles = crud.find_similar_users(db, query, filters=filters, limit=3, score_threshold=0.7)
    
    if not similar_profiles:
        return {"summary": "Niestety, nie znalazłem żadnych kandydatów spełniających podane kryteria.", "profiles": []}
        
    context = "Oto profile kandydatów znalezione w bazie danych:\n\n"
    for i, profile in enumerate(similar_profiles, 1):
        context += f"--- Profil Kandydata {i} ---\n"
        context += f"Imię i nazwisko: {profile.name} {profile.surname}\n"
        context += f"Opis: {profile.description}\n"
        context += f"Umiejętności: {', '.join([s.name for s in profile.skills])}\n"
        context += f"Wskaźnik doświadczenia: {profile.experience_score}\n\n"

    prompt_template = """
    Jesteś inteligentnym asystentem rekrutacyjnym SkillSense. Twoim zadaniem jest analiza profili kandydatów i zwięzła odpowiedź na zapytanie.
    KONTEKST: {context}
    ZAPYTANIE: "{query}"
    INSTRUKCJE: Przeanalizuj podane profile. W 1-2 zdaniach podsumuj, dlaczego są dobrym dopasowaniem. Jeśli jeden kandydat wyróżnia się doświadczeniem (ma wyższy wskaźnik), wspomnij o tym.
    """
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    
    response = chain.invoke({"context": context, "query": query})
    
    return {
        "summary": response.content,
        "profiles": similar_profiles
    }
