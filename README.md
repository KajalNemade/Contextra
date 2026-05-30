 # DCRS — Developer Context Recovery System

Understand any codebase in 10 minutes. Local-first, AI-powered repository intelligence.

## What it does

- Indexes Python, JavaScript, TypeScript repositories
- Builds dependency graphs with NetworkX
- Generates semantic embeddings with Ollama (nomic-embed-text)
- Answers questions about your codebase using RAG (Retrieval-Augmented Generation)
- Runs 100% locally — no cloud required

## Stack

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

## Quick Start

```bash
# 1. Start all services
docker-compose up --build

# 2. Open frontend
http://localhost:3000

# 3. Open API docs
http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /repo | Submit GitHub URL for indexing |
| POST | /repo/upload | Upload ZIP file |
| GET | /repo/{id} | Get repo status |
| GET | /graph/{repo_id} | Dependency graph |
| POST | /ask | Ask a question about the repo |
| GET | /summary/{repo_id} | Get AI summaries |
| GET | /search/{repo_id}?q= | Semantic search |
| GET | /jobs/{repo_id} | Pipeline job status |

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in values.

```env
DATABASE_URL=postgresql+psycopg://dcrs:dcrspass@postgres:5432/dcrs_db
QDRANT_URL=http://qdrant:6333
OLLAMA_URL=http://ollama:11434
GEMINI_API_KEY=        # optional fallback
REPOS_PATH=./repos
MAX_FILES=500
MAX_LOC=100000
```

## Limits (V1)

- Max 500 files per repository
- Max 100,000 lines of code
- Supported languages: Python, JavaScript, TypeScript




CONTEXTRA/
│
├── .gitignore                          
├── README.md                           
├── docker-compose.yml                  
│
├── backend/                             38 files
│   ├── .env
│   ├── .env.example
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── api/         __init__ ask graph jobs repo search summary
│   ├── config/      __init__ settings
│   ├── embeddings/  __init__ engine
│   ├── graph/       __init__ builder
│   ├── jobs/        __init__ indexing
│   ├── migrations/  __init__ env + versions/001 + versions/__init__
│   ├── models/      __init__ db
│   ├── parser/      __init__ tree_parser
│   ├── services/    __init__ llm_provider sanitizer scanner
│   ├── storage/     __init__ database
│   └── utils/       __init__ helpers
│
└── frontend/                            30 files
    ├── .gitignore
    ├── Dockerfile
    ├── index.html
    ├── nginx.conf
    ├── package.json
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx  App.css  main.tsx  index.css  vite-env.d.ts
        ├── components/  GraphCanvas Layout ProgressBar RepoCard SearchBar StatusBadge
        ├── hooks/       useRepo
        ├── pages/       AskPage DashboardPage GraphView HomePage RepoView UploadPage
        ├── services/    api
        ├── types/       api
        └── utils/       constants



DCRS-V1/
├── .gitignore
├── README.md
├── docker-compose.yml
├── backend/          ← 14 folders, 38 files, 
└── frontend/         ← 8 folders, 30 files





Step 1 — Start the entire project
cmd cd D:\Contextra
docker-compose up --build

http://localhost:8000/docs


Step 6 — Open everything in browser
Frontend UI       http://localhost
Backend API docs   http://localhost:8000/docs
Backend health    http://localhost:8000
Qdrant dashboard   http://localhost:6333/







Daily workflow — how to start and stop:


Start every day:  cmd  cd D:\Contextra --> docker-compose up

Stop: cmd docker-compose down

Stop and delete all data (fresh start):
cmd  docker-compose down -v

Restart just the backend after code change:
cmd docker-compose restart backend

See backend logs:
cmd docker-compose logs -f backend

See all logs:
cmd docker-compose logs -f













repos
  id, name, url, status, file_count, total_loc, languages
    │
    ├── files (repo_id)
    │     id, path, language, loc, size_bytes, is_entry_point
    │       │
    │       ├── functions (file_id, repo_id)
    │       │     id, name, class_name, start_line, end_line, body
    │       │
    │       └── imports (file_id, repo_id)
    │             id, module, names, is_relative
    │
    ├── summaries (repo_id)
    │     id, scope, path, content, provider, model
    │
    ├── jobs (repo_id)
    │     id, job_type, status, stage, progress, error_message
    │
    └── events (repo_id)
          id, event_type, data, created_at




MyPgAdmin123! - pgAdmin password


Host name/address: localhost
Port: 5432

Maintenance database: dcrs_db

Username: dcrs
Password: dcrspass
