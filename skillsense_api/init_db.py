# init_db.py
import asyncio
from core.database import engine, Base
from core import models  # Importujemy, aby SQLAlchemy "zobaczyło" nasze modele

async def create_tables():
    """
    Łączy się z bazą danych i tworzy wszystkie tabele zdefiniowane
    w modelach SQLAlchemy.
    """
    print("Rozpoczynam tworzenie tabel w bazie danych...")
    async with engine.begin() as conn:
        # Upuszcza istniejące tabele (opcjonalne, przydatne w dewelopce)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Tworzy wszystkie tabele, które dziedziczą po Base
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tabele zostały pomyślnie utworzone!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
