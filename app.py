from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_cli import MovieHit, MovieRAG, summarise_hits

APP_TITLE = "Movie RAG"
APP_DESCRIPTION = "Query the movie dataset with semantic search and optional summarisation."
FRONTEND_DIR = Path(__file__).parent / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"

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

LLM_MODEL = os.getenv("MOVIE_RAG_LLM_MODEL")
LLM_BASE_URL = os.getenv("MOVIE_RAG_LLM_BASE_URL")
LLM_API_KEY = os.getenv("MOVIE_RAG_LLM_API_KEY", os.getenv("OPENAI_API_KEY"))


class SearchRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Natural language query")
    top_k: int = Field(3, ge=1, le=20, description="Number of matches to return")
    summarize: bool = Field(False, description="Return an LLM-crafted summary when available")


class MovieResult(BaseModel):
    title: str
    genre: Optional[str]
    release_year: Optional[int]
    score: float
    payload: Dict[str, Any]


class SearchResponse(BaseModel):
    results: List[MovieResult]
    summary: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
def serve_index() -> str:
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return INDEX_FILE.read_text(encoding="utf-8")


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

    summary: Optional[str] = None
    if request.summarize and LLM_MODEL:
        try:
            summary = summarise_hits(
                hits,
                prompt,
                llm_model=LLM_MODEL,
                base_url=LLM_BASE_URL,
                api_key=LLM_API_KEY,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"LLM summarisation failed: {exc}") from exc

    return SearchResponse(results=results, summary=summary)


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
