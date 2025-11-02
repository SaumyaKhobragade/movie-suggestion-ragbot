# 🎬 Movie Suggestion Bot

Fast, local-friendly RAG pipeline for movie discovery. The project ships with:

- `rag_cli.py` — command-line entrypoint for one-off prompts or an interactive loop.
- `app.py` — FastAPI service that powers a browser UI under `frontend/`.
- `movies_dataset.csv` — curated dataset used to build the vector store.

All embeddings are stored in-memory via Qdrant’s Python client; no external vector DB is required.

---

## 🚀 Quick start

```powershell
pip install -r requirements.txt
```

### Run the CLI once-off
```powershell
python rag_cli.py --prompt "space adventure movies" --top-k 3
```

### Interactive CLI loop
```powershell
python rag_cli.py
```

### Launch the web experience
```powershell
uvicorn app:app --reload --port 8000
```
Then open `http://127.0.0.1:8000` to explore the frontend.

---

## 🌐 Frontend structure

```
frontend/
  index.html      # Root HTML served at /
  css/style.css   # Styling
  js/app.js       # Fetch logic + rendering
```

Static assets are mounted at `/static`, so the HTML references `/static/css/style.css` and `/static/js/app.js`.

---

## 🗂️ Project layout

```
movies_dataset.csv   # Source data
rag_cli.py           # CLI wrapper + MovieRAG core class
app.py               # FastAPI service
frontend/            # Separated HTML, CSS, JS assets
requirements.txt     # Runtime dependencies
README.md            # This guide
```

---

## 🧪 Development tips

- The first run embeds every movie title; reruns reuse cached vectors in `.cache/`.
- Use `python -m fastapi dev app:app` (FastAPI CLI) for hot reloads if installed.
- Dataset changes automatically trigger re-embedding thanks to the cache fingerprinting in `MovieRAG`.

---

## 🧑‍💻 License
MIT License
