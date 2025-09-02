# core/search_logic.py
import asyncio
import logging
from typing import List, Dict, Any, Set, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field

from . import crud, schemas

# --- Konfiguracja ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inicjalizacja Modeli AI ---
query_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
rerank_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
summary_llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
embeddings_model = OpenAIEmbeddings(model="text-embedding-ada-002") # 1536 wymiarów

# --- Krok 1: Zaawansowane Przetwarzanie Zapytań ---
class QueryDeconstruction(BaseModel):
    semantic_query: str = Field(description="Główne, semantyczne zapytanie do wyszukiwania wektorowego, oczyszczone z konkretnych filtrów.")
    required_skills: List[str] = Field(default=[], description="Lista umiejętności, które MUSZĄ wystąpić u kandydata.")
    nice_to_have_skills: List[str] = Field(default=[], description="Lista umiejętności, które są dodatkowym atutem.")
    experience_years: Optional[int] = Field(None, description="Minimalne wymagane lata doświadczenia komercyjnego.")

async def deconstruct_query(query: str) -> QueryDeconstruction:
    parser = JsonOutputParser(pydantic_object=QueryDeconstruction)
    prompt = ChatPromptTemplate.from_template(
        template="""
        Twoim zadaniem jest precyzyjna analiza zapytania rekrutacyjnego. Rozłóż je na komponenty zgodnie z podanym schematem JSON.
        Bądź dokładny. Umiejętności takie jak 'Python', 'React', 'SQL' umieść w listach. Doświadczenie podaj jako liczbę całkowitą.
        Zapytanie: "{query}"
        {format_instructions}
        """,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | query_llm | parser
    try:
        result = await chain.ainvoke({"query": query})
        return QueryDeconstruction(**result)
    except Exception as e:
        logger.error(f"Błąd podczas dekonstrukcji zapytania: {e}. Używam fallback.")
        return QueryDeconstruction(semantic_query=query)

# --- Krok 2: Wielowarstwowe Wyszukiwanie Hybrydowe ---
async def hybrid_search(db: AsyncSession, deconstructed_query: QueryDeconstruction) -> List[Any]:
    embedding_task = asyncio.create_task(
        embeddings_model.aembed_query(deconstructed_query.semantic_query)
    )
    all_skills = list(set(deconstructed_query.required_skills + deconstructed_query.nice_to_have_skills))
    fts_task = asyncio.create_task(
        crud.full_text_search_users(db, query_text=" ".join(all_skills))
    )
    
    query_embedding, fts_results = await asyncio.gather(embedding_task, fts_task)
    vector_results = await crud.vector_search_users(db, query_embedding=query_embedding)
    
    ranked_list: Dict[int, float] = {}
    k = 60

    for rank, doc in enumerate(fts_results):
        if doc.id not in ranked_list:
            ranked_list[doc.id] = 0.0
        ranked_list[doc.id] += 1.0 / (k + rank)
        
    for rank, doc in enumerate(vector_results):
        if doc.id not in ranked_list:
            ranked_list[doc.id] = 0.0
        ranked_list[doc.id] += 1.0 / (k + rank)

    sorted_ids = sorted(ranked_list.keys(), key=lambda id: ranked_list[id], reverse=True)
    
    if not sorted_ids:
        return []
    
    initial_candidates = await crud.get_users_by_ids_with_filters(
        db, 
        user_ids=sorted_ids,
        required_skills=deconstructed_query.required_skills
    )
    return initial_candidates

# --- Krok 3: Dynamiczny Re-ranking z Kontekstem ---
async def rerank_candidates(query: str, candidates: List[Any]) -> List[Dict[str, Any]]:
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_template(
        template="""
        Oceń dopasowanie kandydata do zapytania. Zwróć JSON z kluczami 'score' (0-100) i 'reasoning' (krótkie uzasadnienie).
        Zapytanie: "{query}"
        --- Profil Kandydata ---
        {context}
        ---
        {format_instructions}
        """,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | rerank_llm | parser

    async def rate_candidate(candidate):
        context = (f"Podsumowanie: {candidate.ai_summary}\n"
                   f"Umiejętności: {', '.join([s.name for s in candidate.skills])}\n"
                   f"Doświadczenie: {' '.join([w.position + ' w ' + w.company for w in candidate.work_experiences])}")
        try:
            result = await chain.ainvoke({"query": query, "context": context})
            return {
                "profile": candidate,
                "match_score": float(result.get("score", 0)),
                "reasoning": result.get("reasoning", "Brak uzasadnienia.")
            }
        except Exception as e:
            logger.error(f"Błąd re-rankingu dla kandydata {candidate.id}: {e}")
            return None

    tasks = [rate_candidate(c) for c in candidates]
    results = await asyncio.gather(*tasks)
    
    valid_results = [r for r in results if r and r["match_score"] > 35]
    valid_results.sort(key=lambda x: x["match_score"], reverse=True)
    return valid_results

# --- Krok 4: Generowanie Odpowiedzi ---
async def generate_final_summary(query: str, top_candidates: List[Dict[str, Any]]) -> str:
    if not top_candidates:
        return "Niestety, po dokładnej analizie nie znalazłem kandydatów spełniających podane kryteria."

    context = "\n\n".join([
        f"Kandydat: {c['profile'].name} {c['profile'].surname}\nDopasowanie: {c['match_score']:.0f}%\nUzasadnienie: {c['reasoning']}"
        for c in top_candidates
    ])
    prompt = ChatPromptTemplate.from_template(
        template="""
        Jesteś asystentem rekrutacyjnym. Stwórz zwięzłe podsumowanie dla rekrutera. 
        Wskaż 2-3 najlepszych kandydatów i wyjaśnij, dlaczego pasują do zapytania.
        Oryginalne zapytanie: "{query}"
        --- Kontekst Kandydatów ---
        {context}
        ---
        Twoje podsumowanie:
        """
    )
    chain = prompt | summary_llm | StrOutputParser()
    return await chain.ainvoke({"query": query, "context": context})

# --- Główny Potok Wyszukiwania ---
async def perfected_search_pipeline(db: AsyncSession, query: str, skip: int, limit: int) -> schemas.SearchResponse:
    logger.info(f"Rozpoczynam wyszukiwanie dla zapytania: '{query}'")
    
    deconstructed_query = await deconstruct_query(query)
    logger.info(f"Wynik dekonstrukcji: {deconstructed_query.model_dump_json(indent=2)}")
    
    initial_candidates = await hybrid_search(db, deconstructed_query)
    logger.info(f"Znaleziono {len(initial_candidates)} kandydatów po wyszukiwaniu hybrydowym i filtrowaniu.")
    if not initial_candidates:
        return schemas.SearchResponse(summary="Nie znaleziono kandydatów pasujących do podstawowych kryteriów.", profiles=schemas.PaginatedResponse(total=0, page=1, limit=limit, items=[]))

    reranked_candidates = await rerank_candidates(query, initial_candidates)
    logger.info(f"Pozostało {len(reranked_candidates)} kandydatów po re-rankingu.")
    
    total_results = len(reranked_candidates)
    paginated_candidates = reranked_candidates[skip : skip + limit]

    summary = await generate_final_summary(query, paginated_candidates[:3])
    logger.info("Wygenerowano finalne podsumowanie.")

    response_profiles = [
        schemas.SearchResultProfile(
            **c["profile"].__dict__,
            match_score=c["match_score"],
            reasoning=c["reasoning"]
        ) for c in paginated_candidates
    ]
    
    paginated_response = schemas.PaginatedResponse(
        total=total_results,
        page=(skip // limit) + 1,
        limit=limit,
        items=response_profiles
    )
    
    return schemas.SearchResponse(summary=summary, profiles=paginated_response)
