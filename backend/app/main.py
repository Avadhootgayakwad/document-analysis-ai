from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db

# Import API routers
from app.api.documents import router as documents_router
from app.api.intelligence import router as intelligence_router
from app.api.chat import router as chat_router
from app.api.summaries import router as summaries_router
from app.api.notes import router as notes_router

@asynccontextmanager
async def lifespan(app: FastAPI):
  
    init_db()

    print("=" * 50)
    print("DOCUMIND AI BACKEND STARTED")
    print("SQLite database initialized")
    print("Document Management API registered")
    print("Document Intelligence API registered")
    print("=" * 50)
    print("AI Chat API registered")
    print("AI Summaries API registered")
    print("Smart Notes API registered")

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered document management, "
        "analysis and intelligent chat platform."
    ),
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Register API routers
app.include_router(documents_router)
app.include_router(intelligence_router)
app.include_router(chat_router)
app.include_router(summaries_router)
app.include_router(notes_router)

@app.get("/")
def root():

    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/api/health")
def health_check():

    return {
        "status": "healthy",
        "backend": "FastAPI",
        "database": "SQLite",
        "version": settings.APP_VERSION
    }