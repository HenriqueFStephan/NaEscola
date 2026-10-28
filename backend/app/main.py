from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.persistence.catalog import CurriculumCatalog, LessonStore, TaskStore
from app.settings import load_settings

settings = load_settings()
app = FastAPI(
    title="NaEscola API",
    version="0.1.0",
    summary="Curriculum, lessons, validation, and generation for NaEscola.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)
app.state.settings = settings
app.state.catalog = CurriculumCatalog(settings.curriculum_dir)
app.state.lessons = LessonStore(settings.lessons_dir)
app.state.tasks = TaskStore(settings.runtime_dir)


@app.get("/")
def root() -> dict:
    return {"service": "naescola-api", "docs": "/docs"}
