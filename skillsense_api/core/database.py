# core/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables. Please check your .env file.")

# Konwersja standardowego URL bazy danych na URL kompatybilny z asyncpg.
# Przykład: "postgresql://user:pass@host/db" -> "postgresql+asyncpg://user:pass@host/db"
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Tworzenie asynchronicznego silnika (engine) bazy danych.
# echo=False w środowisku produkcyjnym dla mniejszej ilości logów.
engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, pool_pre_ping=True)

# Tworzenie asynchronicznej fabryki sesji (sessionmaker).
# To jest zalecany sposób na tworzenie sesji w aplikacjach.
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False # Ważne w aplikacjach async
)

# Deklaratywna baza dla wszystkich modeli SQLAlchemy
Base = declarative_base()

async def get_async_db() -> AsyncSession:
    """
    Asynchroniczna zależność (dependency) dla FastAPI, która dostarcza sesję 
    bazy danych do endpointów.
    
    Zarządza cyklem życia sesji: otwiera ją na początku zapytania i zamyka 
    na końcu, zapewniając prawidłowe zarządzanie zasobami.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
