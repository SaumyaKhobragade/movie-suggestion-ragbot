from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore


DATASET_PATH = Path(__file__).with_name("movies_dataset.csv")
CACHE_DIR = Path(__file__).parent / ".cache"
COLLECTION_NAME = "top_movies"
DEFAULT_ENCODER_NAME = "all-MiniLM-L6-v2"


@dataclass
class MovieHit:
    """Container for a movie search result."""

    title: str
    details: Dict[str, Any]
    score: float


class MovieRAG:
    """Encapsulates dataset loading, embedding, and vector search."""

    def __init__(
        self,
        dataset_path: Path = DATASET_PATH,
        encoder_name: str = DEFAULT_ENCODER_NAME,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.dataset_path = dataset_path
        self.encoder_name = encoder_name
        self.collection_name = collection_name

        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        self.dataframe = pd.read_csv(self.dataset_path)
        self.records = self.dataframe.to_dict("records")

        self.encoder = self._load_encoder()
        self.client = self._create_client()

        self._ensure_collection()

    def _load_encoder(self) -> SentenceTransformer:
        """Load the sentence transformer encoder (cached by transformers)."""
        return SentenceTransformer(self.encoder_name)

    def _create_client(self) -> QdrantClient:
        """Create an in-memory Qdrant client."""
        return QdrantClient(":memory:")

    # region cache helpers
    def _cache_files(self) -> tuple[Path, Path]:
        CACHE_DIR.mkdir(exist_ok=True)
        base_name = f"{self.collection_name}_{self.encoder_name.replace('/', '_')}"
        vectors_file = CACHE_DIR / f"{base_name}.npz"
        meta_file = CACHE_DIR / f"{base_name}.json"
        return vectors_file, meta_file

    def _dataset_signature(self) -> str:
        hash_digest = hashlib.sha256()
        with self.dataset_path.open("rb") as dataset_file:
            for chunk in iter(lambda: dataset_file.read(1 << 20), b""):
                hash_digest.update(chunk)
        return hash_digest.hexdigest()

    def _load_cached_vectors(self) -> Optional[np.ndarray]:
        vectors_file, meta_file = self._cache_files()
        if not (vectors_file.exists() and meta_file.exists()):
            return None

        with meta_file.open("r", encoding="utf-8") as meta_fh:
            metadata = json.load(meta_fh)

        if metadata.get("dataset_signature") != self._dataset_signature():
            return None
        if metadata.get("encoder_name") != self.encoder_name:
            return None

        npz = np.load(vectors_file)
        return npz["vectors"]

    def _persist_vectors(self, vectors: np.ndarray) -> None:
        vectors_file, meta_file = self._cache_files()
        np.savez_compressed(vectors_file, vectors=vectors)
        metadata = {
            "dataset_signature": self._dataset_signature(),
            "encoder_name": self.encoder_name,
            "vector_dim": int(vectors.shape[1]),
        }
        with meta_file.open("w", encoding="utf-8") as meta_fh:
            json.dump(metadata, meta_fh, indent=2)

    # endregion

    def _ensure_collection(self) -> None:
        vectors = self._load_cached_vectors()
        if vectors is None:
            movie_texts = [self._record_to_text(record) for record in self.records]
            vectors = self.encoder.encode(
                movie_texts,
                batch_size=128,
                convert_to_numpy=True,
                show_progress_bar=True,
            )
            self._persist_vectors(vectors)

        vector_dim = vectors.shape[1]

        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_dim,
                distance=models.Distance.COSINE,
            ),
        )

        self.client.upload_points(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=idx,
                    vector=vectors[idx].tolist(),
                    payload=self.records[idx],
                )
                for idx in range(len(self.records))
            ],
        )

    def _record_to_text(self, record: Dict[str, Any]) -> str:
        parts = [str(record.get("Movie Name", ""))]
        genre = record.get("genre")
        if genre:
            parts.append(f"genre: {genre}")
        year = record.get("Release Year")
        if not pd.isna(year):
            parts.append(f"released: {int(year)}")
        profit = record.get("Profit")
        if not pd.isna(profit):
            parts.append(f"profit: {profit}")
        return ". ".join(parts)

    def search(self, prompt: str, top_k: int = 3) -> List[MovieHit]:
        query_vector = self.encoder.encode(prompt).tolist()
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            MovieHit(
                title=hit.payload.get("Movie Name", "<unknown>"),
                details=hit.payload,
                score=float(hit.score),
            )
            for hit in hits
        ]


def summarise_hits(
    hits: Iterable[MovieHit],
    prompt: str,
    llm_model: Optional[str],
    base_url: Optional[str],
    api_key: Optional[str],
) -> Optional[str]:
    if not llm_model:
        return None
    if OpenAI is None:
        raise RuntimeError("openai package not available. Install it or drop --summarize.")

    client_kwargs: Dict[str, Any] = {}
    if base_url:
        client_kwargs["base_url"] = base_url
    if api_key:
        client_kwargs["api_key"] = api_key

    client = OpenAI(**client_kwargs)
    messages = [
        {
            "role": "system",
            "content": "You recommend movies based on provided candidates.",
        },
        {
            "role": "user",
            "content": (
                "Prompt: "
                + prompt
                + "\nCandidates:\n"
                + "\n".join(
                    f"- {hit.title} (score {hit.score:.4f}): {json.dumps(hit.details)}"
                    for hit in hits
                )
            ),
        },
    ]

    response = client.chat.completions.create(model=llm_model, messages=messages)
    return response.choices[0].message.content  # type: ignore[index]


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Movie recommendation CLI powered by SentenceTransformers and Qdrant.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Run a single prompt in batch mode. If omitted, starts an interactive shell.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of movies to retrieve per query (default: 3).",
    )
    parser.add_argument(
        "--encoder",
        type=str,
        default=DEFAULT_ENCODER_NAME,
        help=f"Sentence-Transformer model to use (default: {DEFAULT_ENCODER_NAME}).",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="If provided, ask an OpenAI-compatible model to summarise the results.",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=os.getenv("MOVIE_RAG_LLM_MODEL"),
        help="OpenAI model name for summarisation (defaults to MOVIE_RAG_LLM_MODEL env).",
    )
    parser.add_argument(
        "--llm-base-url",
        type=str,
        default=os.getenv("MOVIE_RAG_LLM_BASE_URL"),
        help="Base URL for the OpenAI-compatible endpoint.",
    )
    parser.add_argument(
        "--llm-api-key",
        type=str,
        default=os.getenv("MOVIE_RAG_LLM_API_KEY", os.getenv("OPENAI_API_KEY")),
        help="API key for the OpenAI-compatible endpoint.",
    )
    return parser.parse_args(argv)


def print_hits(hits: List[MovieHit]) -> None:
    if not hits:
        print("No matches found.")
        return
    for idx, hit in enumerate(hits, start=1):
        details = hit.details
        genre = details.get("genre", "?")
        year = details.get("Release Year", "?")
        print(f"{idx}. {hit.title} (genre: {genre}, year: {year})  score={hit.score:.4f}")


def interactive_loop(rag: MovieRAG, top_k: int, summarise: bool, llm_args: Dict[str, Optional[str]]) -> None:
    print("Type a movie preference prompt (or 'quit' to exit).")
    while True:
        try:
                prompt = input(">> ").strip()
        except EOFError:
            print()
            break
        if not prompt:
            continue
        if prompt.lower() in {"quit", "exit", "q"}:
            break
        hits = rag.search(prompt, top_k=top_k)
        print_hits(hits)
        if summarise:
            summary = summarise_hits(hits, prompt, llm_args.get("llm_model"), llm_args.get("base_url"), llm_args.get("api_key"))
            if summary:
                print("\nSummary:\n" + summary)
        print()


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    rag = MovieRAG(encoder_name=args.encoder)

    llm_args = {
        "llm_model": args.llm_model,
        "base_url": args.llm_base_url,
        "api_key": args.llm_api_key,
    }
    summarise = args.summarize
    if summarise and not args.llm_model:
        print("--summarize requires --llm-model or MOVIE_RAG_LLM_MODEL environment variable.", file=sys.stderr)
        return 2

    if args.prompt:
        hits = rag.search(args.prompt, top_k=args.top_k)
        print_hits(hits)
        if summarise:
            summary = summarise_hits(hits, args.prompt, llm_args["llm_model"], llm_args["base_url"], llm_args["api_key"])
            if summary:
                print("\nSummary:\n" + summary)
        return 0

    interactive_loop(rag, args.top_k, summarise, llm_args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
