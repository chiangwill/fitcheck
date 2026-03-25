# FitCheck

A personal AI-powered job search assistant. Paste a job URL, get an instant match analysis against your resume, and generate a tailored cover letter — in both Chinese and English.

## Features

- **Resume Management** — Upload a PDF or paste text directly. Supports multiple versions (e.g. "Backend", "Full-stack") with active version switching.
- **Job Parsing** — Paste any public job listing URL (104, CakeResume, etc.). Gemini fetches and extracts structured data: required skills, salary, location, remote policy, and culture keywords.
- **Match Analysis** — Semantic comparison between your resume and the job. Outputs a score (1–10), matched skills, missing skills, and concrete improvement suggestions.
- **Cover Letter Generation** — AI-generated cover letter in both Traditional Chinese and English, with adjustable tone (formal / friendly). One-click copy.
- **Application Tracking** — Track every application through `pending → applied → interviewing → offer / rejected` with notes.
- **Crawler Jobs** — Browse daily job listings scraped from Japan Dev & Tokyo Dev (via [jp_job_crawler](https://github.com/chiangwill/jp_job_crawler)). One-click Gemini scoring against your active resume, with results cached so you never burn quota twice on the same job.

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| Frontend | NiceGUI (Python-based UI) |
| Database | PostgreSQL |
| Vector DB | ChromaDB |
| LLM + Embedding | Gemini API (free tier) |
| PDF Parsing | pdfplumber |
| Web Scraping | Gemini URL context tool |
| Package Manager | uv |
| Deployment | Docker Compose |

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) — for PostgreSQL and ChromaDB
- [uv](https://docs.astral.sh/uv/) — Python package manager
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier works)

### Setup

1. **Clone the repo**

```bash
git clone https://github.com/your-username/fitcheck.git
cd fitcheck
```

2. **Configure environment**

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
DATABASE_URL=postgresql+asyncpg://fitcheck:fitcheck@localhost:5432/fitcheck
CHROMA_HOST=localhost
CHROMA_PORT=8001
GEMINI_API_KEY=your_key_here

# Optional: enable the Crawler Jobs page (Japan Dev + Tokyo Dev listings)
# Get these from your Supabase project → Settings → API
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

3. **Start the app**

```bash
docker compose up --build
```

This starts PostgreSQL, ChromaDB, and the FastAPI backend with hot-reload. Or to run the backend locally instead:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

5. **Open the app**

| URL | Description |
|---|---|
| `http://localhost:8000/ui` | Main UI |
| `http://localhost:8000/docs` | API docs (Swagger) |

## Project Structure

```
fitcheck/
├── docker-compose.yml
├── .env.example
└── backend/
    ├── Dockerfile
    ├── pyproject.toml
    ├── tests/                   # pytest test suite (100% coverage on core modules)
    └── app/
        ├── main.py
        ├── config.py
        ├── database.py
        ├── core/
        │   ├── gemini.py        # Gemini API client
        │   ├── vector_db.py     # ChromaDB client
        │   └── supabase_db.py   # Supabase PostgREST client (crawler jobs)
        ├── models/              # SQLAlchemy models
        ├── schemas/             # Pydantic schemas
        ├── routers/             # API endpoints
        │   └── crawler_jobs.py  # /crawler-jobs — list + score endpoints
        ├── services/
        │   ├── parser.py        # PDF + resume parsing
        │   ├── scraper.py       # Job URL fetching via Gemini
        │   ├── embedder.py      # Embedding generation + storage
        │   ├── matcher.py       # Resume ↔ job analysis
        │   └── generator.py     # Cover letter generation
        └── ui/                  # NiceGUI pages
            └── crawler_jobs_page.py  # 爬蟲職缺 — daily job listings
```

## Notes

- LinkedIn is not supported (requires authentication)
- Gemini free tier limits: ~20 requests/day for generation, 1000/day for embedding
- Resume and job data is processed by the Gemini API (Google's terms apply)
- The Crawler Jobs page requires a running [jp_job_crawler](https://github.com/chiangwill/jp_job_crawler) Supabase project — scores are cached locally so each job only consumes one Gemini request
