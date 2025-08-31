# api.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import os

from core import auth, models, schemas, services
from core.database import SessionLocal, engine
from core.config import settings

models.Base.metadata.create_all(bind=engine)

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

# --- Zależności ---
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- Endpointy (BEZ ukośników na końcu) ---

@app.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    is_authenticated = auth.authenticate_user(form_data.username, form_data.password)
    if not is_authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users", response_model=schemas.UserList, tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    users = services.UserService.get_all_users(db, skip=skip, limit=limit)
    total = db.query(models.User).count()
    return {"items": users, "total": total}

@app.post("/upload-cv", response_model=schemas.User, tags=["CV"])
async def upload_cv(db: Session = Depends(get_db), file: UploadFile = File(...), current_user: str = Depends(auth.get_current_user)):
    return await services.CVService.process_uploaded_cv(db, file, settings.UPLOAD_DIR)

@app.get("/cv/{user_id}", tags=["CV"])
def download_cv(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    user = services.UserService.get_user_by_id(db, user_id=user_id)
    if not user or not user.cv_filepath:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CV file not found.")
    
    safe_base_dir = settings.UPLOAD_DIR.resolve()
    file_path = (safe_base_dir / os.path.basename(user.cv_filepath)).resolve()
    if not str(file_path).startswith(str(safe_base_dir)) or not file_path.exists():
         raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found or access denied.")
    from fastapi.responses import FileResponse
    return FileResponse(path=file_path, media_type='application/pdf')

@app.get("/search", response_model=schemas.SearchResponse, tags=["Search"])
async def search_candidates(query: str, db: Session = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    if not query.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Query cannot be empty.")
    return await services.SearchService.intelligent_search(db, query)
