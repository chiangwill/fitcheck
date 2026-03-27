# Tobira 扉

> Your door to Japan's job market.

A full-stack AI job search assistant built for Japan-focused engineers. Paste a job URL, get an instant resume match score, and track your pipeline — all in a dark, minimal UI powered by Gemini.

![Pipeline](docs/screenshots/kanban.png)

---

## Features

**Pipeline (Kanban)**
Drag jobs across four stages — Unsorted, Interested, Applied, Pass. Each card shows an AI fit score as an animated ring. Bulk-score all unscored jobs with one click; a 4-second rate-limit delay prevents Gemini quota burn.

**Resume Management**
Upload multiple PDF versions (e.g. "Backend v2", "Full-stack"). Each is parsed by Gemini into structured JSON: skills, years of experience, work history. Set one as active — it becomes the baseline for all scoring.

![Resume](docs/screenshots/resume.png)

**Job Parsing**
Paste any public job listing URL (104, CakeResume, Japan Dev, Tokyo Dev, etc.). Gemini fetches and extracts title, company, required skills, salary, location, and remote policy.

![Jobs](docs/screenshots/jobs.png)

**Match Analysis**
Semantic comparison between your active resume and any parsed job. Returns a score 1–10, matched skills, missing skills, and concrete suggestions. Cover letter generation (Traditional Chinese + English) with adjustable tone.

![Analysis](docs/screenshots/match.png)

**Application Tracking**
Track every application through `pending → applied → interviewing → offer / rejected` with free-text notes per stage.

![Applications](docs/screenshots/apps.png)

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js · TypeScript · Tailwind CSS · Framer Motion |
| Drag & Drop | @dnd-kit/core |
| Backend | FastAPI · SQLAlchemy 2.0 (async) |
| Database | PostgreSQL |
| Vector DB | ChromaDB |
| LLM | Gemini API (free tier) |
| PDF Parsing | pdfplumber |
| Package Manager | uv (backend) · npm (frontend) |
| Deployment | Docker Compose |

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Node.js](https://nodejs.org/) 18+ (for the frontend)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier works)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/tobira.git
cd tobira
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql+asyncpg://fitcheck:fitcheck@localhost:5432/fitcheck
CHROMA_HOST=localhost
CHROMA_PORT=8001
GEMINI_API_KEY=your_key_here

# Optional: Crawler Jobs page (Japan Dev + Tokyo Dev daily listings)
# Get these from your Supabase project → Settings → API
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

### 2. Start the backend

```bash
docker compose up --build
```

This starts PostgreSQL, ChromaDB, and the FastAPI backend with hot-reload on port `8000`.

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

| URL | Description |
|---|---|
| `http://localhost:3000` | Tobira UI |
| `http://localhost:8000/docs` | FastAPI Swagger docs |

---

## Project Structure

```
tobira/
├── docker-compose.yml
├── .env.example
├── frontend/                    # Next.js app (App Router)
│   └── src/
│       ├── app/                 # Pages: /, /resume, /jobs, /match, /apps
│       ├── components/
│       │   ├── kanban/          # Board, JobCard, ScoreRing
│       │   └── layout/          # Sidebar
│       └── lib/
│           ├── api.ts           # Typed API client
│           └── types.ts         # Shared TypeScript interfaces
└── backend/
    ├── Dockerfile
    ├── pyproject.toml
    ├── tests/                   # pytest suite (100% coverage on core modules)
    └── app/
        ├── main.py              # FastAPI app + CORS
        ├── core/
        │   ├── gemini.py        # Gemini API client
        │   ├── vector_db.py     # ChromaDB client
        │   └── supabase_db.py   # Supabase PostgREST client
        ├── routers/             # API endpoints
        ├── services/
        │   ├── parser.py        # PDF + resume parsing
        │   ├── scraper.py       # Job URL fetching via Gemini
        │   ├── embedder.py      # Embedding generation + storage
        │   ├── matcher.py       # Resume ↔ job analysis
        │   └── generator.py     # Cover letter generation
        └── models/ · schemas/
```

---

## Notes

- LinkedIn is not supported (requires authentication)
- Gemini free tier: ~20 generation requests/day, 1000 embedding requests/day
- Resume and job data is sent to the Gemini API (Google's terms apply)
- The Pipeline page's crawler jobs require a running [jp_job_crawler](https://github.com/chiangwill/jp_job_crawler) Supabase project — scores are cached locally so each job only consumes one Gemini call
