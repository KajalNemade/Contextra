# DCRS — Developer Context Recovery System

> Understand any codebase in 10 minutes. Local-first, AI-powered. No cloud required.

---

## What is DCRS?

DCRS helps developers quickly understand unfamiliar codebases by:

- **Asking questions** in plain English — answers grounded in actual code
- **Visualizing** dependency graphs with import relationships
- **Searching** semantically across all functions and files
- **Summarizing** files and projects automatically using local AI
- **Detecting secrets** — API keys are redacted before any AI sees your code

Everything runs on your machine. Your code never leaves.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| Embeddings | Ollama (nomic-embed-text) |
| LLM | Ollama (llama3) + Gemini fallback |
| Parser | Tree-sitter |
| Graph | NetworkX |
| Frontend | React + Vite + TypeScript + Tailwind |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Node.js 20+](https://nodejs.org/) — only needed for frontend dev mode

---

## Quick Start

**Step 1 — Start all services**
```bash
docker-compose up --build
```

**Step 2 — Pull AI models** (first time only, in a second terminal)
```bash
docker exec -it dcrs_ollama ollama pull llama3
docker exec -it dcrs_ollama ollama pull nomic-embed-text
```

`llama3` is ~4 GB — wait for both to finish before using the app.

**Step 3 — Open the app**

| URL | What |
|---|---|
| `http://localhost` | App UI |
| `http://localhost:8000/docs` | API documentation |
| `http://localhost:6333/dashboard` | Vector DB dashboard |

---

## Environment Variables

Copy `.env.example` to `.env` in the `backend/` folder:

```env
DATABASE_URL=postgresql+psycopg://dcrs:dcrspass@postgres:5432/dcrs_db
QDRANT_URL=http://qdrant:6333
OLLAMA_URL=http://ollama:11434
GEMINI_API_KEY=          # Optional — leave blank to use Ollama only
REPOS_PATH=/tmp/dcrs_repos
MAX_FILES=500
MAX_LOC=100000
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/repo` | Submit GitHub URL for indexing |
| `POST` | `/repo/upload` | Upload a ZIP file |
| `GET` | `/repo/{id}` | Get repo status |
| `DELETE` | `/repo/{id}` | Delete repo and all data |
| `GET` | `/graph/{repo_id}` | Dependency graph |
| `POST` | `/ask` | Ask a question about the repo |
| `GET` | `/summary/{repo_id}` | AI-generated summaries |
| `GET` | `/search/{repo_id}?q=` | Semantic code search |
| `GET` | `/jobs/{repo_id}` | Indexing job status |
| `GET` | `/health` | Backend health check |

---

## Supported Languages

- Python (`.py`)
- JavaScript (`.js`, `.jsx`)
- TypeScript (`.ts`, `.tsx`)

---

## Limits

| Limit | Value |
|---|---|
| Max files per repo | 500 |
| Max lines of code | 100,000 |
| Ollama response timeout | 300 seconds |

---

## Daily Commands

```bash
# Start
docker-compose up

# Stop
docker-compose down

# Restart backend after a code change
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Full reset (deletes all data)
docker-compose down -v
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Ollama timeout on `/ask` | Model is loading into memory — wait and retry |
| Repo stuck in `PARSING` | Check `docker-compose logs -f backend` |
| Port 80 already in use | Change `80:80` to `3000:80` in `docker-compose.yml` |
| Port 8000 already in use | Change `8000:8000` to `8001:8000` |
| Database error on startup | Run `docker-compose down -v` then `docker-compose up --build` |

---

## License

MIT