from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analysis_data import MovieAnalytics
from rag_cli import MovieRAG

APP_TITLE = "Movie Suggestion Bot"
APP_DESCRIPTION = "Discover movies with fast semantic search."
FRONTEND_DIR = Path(__file__).parent / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"
ANALYSIS_FILE = FRONTEND_DIR / "analysis.html"

app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

rag = MovieRAG()
analytics = MovieAnalytics.from_dataset()


class SearchRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Natural language query")
    top_k: int = Field(3, ge=1, le=20, description="Number of matches to return")
    summarize: bool = Field(False, description="Deprecated flag retained for backwards compatibility.")


class MovieResult(BaseModel):
    title: str
    genre: Optional[str]
    release_year: Optional[int]
    score: float
    payload: Dict[str, Any]


class SearchResponse(BaseModel):
    results: List[MovieResult]


@app.get("/", response_class=HTMLResponse)
def serve_index() -> str:
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return INDEX_FILE.read_text(encoding="utf-8")


@app.get("/analysis", response_class=HTMLResponse)
def serve_analysis() -> str:
    if not ANALYSIS_FILE.exists():
        raise HTTPException(status_code=404, detail="Analysis frontend not found")
    return ANALYSIS_FILE.read_text(encoding="utf-8")


@app.post("/api/search", response_model=SearchResponse)
def search_movies(request: SearchRequest) -> SearchResponse:
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt must not be empty")

    hits = rag.search(prompt, top_k=request.top_k)
    results = [
        MovieResult(
            title=hit.title,
            genre=_safe_str(hit.details.get("genre")),
            release_year=_safe_int(hit.details.get("Release Year")),
            score=hit.score,
            payload=hit.details,
        )
        for hit in hits
    ]

    return SearchResponse(results=results)


@app.get("/api/analysis")
def get_analysis_summary() -> Dict[str, Any]:
    return analytics.summary_payload()


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or (isinstance(value, float) and (value != value)):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "app",
    "SearchRequest",
    "SearchResponse",
]
