# api.py
import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Zaktualizowane importy, aby wskazywały na nowe, asynchroniczne moduły
from core import auth, models, schemas, services, search_logic
from core.database import engine, get_async_db  # Używamy asynchronicznej zależności
from core.config import settings

# UWAGA: W środowisku produkcyjnym, tworzenie tabel powinno być zarządzane 
# przez narzędzia migracji jak Alembic, a nie `create_all`.
# Ta linia jest tu dla uproszczenia demonstracji.
# async def create_tables():
#     async with engine.begin() as conn:
#         await conn.run_sync(models.Base.metadata.create_all)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# --- KONFIGURACJA CORS ---
origins = [
    "http://localhost", "http://localhost:5173",
    "http://127.0.0.1", "http://127.0.0.1:5173",
    "http://10.128.0.2", "http://34.70.6.174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Endpointy (w pełni asynchroniczne) ---

@app.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # W asynchronicznej aplikacji, ta logika również powinna być async, 
    # jeśli np. użytkownicy byliby w bazie danych.
    is_authenticated = auth.authenticate_user(form_data.username, form_data.password)
    if not is_authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/search", response_model=schemas.SearchResponse, tags=["Search"])
async def search_candidates(
    query: str = Query(..., min_length=3, description="Zapytanie w języku naturalnym"),
    skip: int = Query(0, ge=0, description="Liczba profili do pominięcia (offset)"),
    limit: int = Query(10, ge=1, le=50, description="Liczba profili na stronę"),
    db: AsyncSession = Depends(get_async_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    PERFEKCYJNY, wieloetapowy endpoint wyszukiwania kandydatów.
    - Głęboko analizuje zapytanie.
    - Używa wielowarstwowego wyszukiwania hybrydowego (Vector + FTS + Filtry).
    - Stosuje zaawansowany re-ranking oparty na LLM.
    - Zwraca spersonalizowane podsumowanie i paginowane wyniki.
    """
    if not query.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Query cannot be empty.")
    
    try:
        # Wywołanie nowej, perfekcyjnej logiki wyszukiwania
        return await search_logic.perfected_search_pipeline(
            db=db, query=query, skip=skip, limit=limit
        )
    except Exception as e:
        # Zaawansowana obsługa błędów
        print(f"Błąd krytyczny w potoku wyszukiwania: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Wystąpił nieoczekiwany błąd podczas przetwarzania zapytania.")

@app.get("/users", response_model=schemas.PaginatedResponse[schemas.User], tags=["Users"])
async def read_users(
    skip: int = 0, limit: int = 100, 
    db: AsyncSession = Depends(get_async_db), 
    current_user: str = Depends(auth.get_current_user)
):
    """Pobiera paginowaną listę wszystkich użytkowników w systemie."""
    users_data = await services.UserService.get_all_users(db, skip=skip, limit=limit)
    return users_data

@app.post("/upload-cv", response_model=schemas.User, tags=["CV"])
async def upload_cv(
    db: AsyncSession = Depends(get_async_db), 
    file: UploadFile = File(...), 
    current_user: str = Depends(auth.get_current_user)
):
    """Przesyła plik CV, przetwarza go i tworzy lub aktualizuje profil kandydata."""
    return await services.CVService.process_uploaded_cv(db, file, settings.UPLOAD_DIR)

@app.get("/cv/{user_id}", tags=["CV"])
async def download_cv(
    user_id: int, 
    db: AsyncSession = Depends(get_async_db), 
    current_user: str = Depends(auth.get_current_user)
):
    """Pobiera oryginalny plik CV dla danego użytkownika."""
    user = await services.UserService.get_user_by_id(db, user_id=user_id)
    if not user or not user.cv_filepath:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CV file not found.")
    
    safe_base_dir = settings.UPLOAD_DIR.resolve()
    file_path = (safe_base_dir / os.path.basename(user.cv_filepath)).resolve()
    
    if not str(file_path).startswith(str(safe_base_dir)) or not file_path.exists():
         raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found or access denied.")
         
    return FileResponse(path=file_path, media_type='application/pdf')
