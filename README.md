# Weam | وئام

## Overview

Weam (وئام) is an Arabic-first web platform that coordinates the care journey of a child with a disability. It brings the guardian, the care team (specialists, teachers), and specialized centers into one shared record — with fine-grained, permission-based access and an AI assistant grounded in the child's own data.

The system combines a React/TypeScript frontend with a FastAPI backend and a PostgreSQL database. AI features (report analysis, the grounded child assistant, and voice-note transcription) run through a replaceable AI gateway, with a free local fallback so the app stays fully usable without any paid API key.

The platform supports multiple guardians per child, multiple children per guardian, and any combination of conditions and support needs — it is not hard-coded around a single diagnosis.

---

## Main Features

- Email/password authentication (Argon2 + JWT) with optional Google Sign-In
- Roles: guardian, care provider, center, admin
- Multiple child profiles per guardian, with identity and care-profile data kept separate
- Care team invitations with per-member, time-limited or ongoing permissions
- Reports with versioning, upload, and permission-scoped visibility
- Goals with progress updates and an attributed history
- Timeline / follow-ups and notifications
- Voice notes: record or upload, transcribe locally, human review before the transcript is shared
- Realtime team conversations with unread state, read receipts, and shared reports/goals/follow-ups
- Centers directory with search, filters, and an explainable child-to-center matching score
- Center/provider workspace for managing a center's own profile, services, and specialists
- Admin dashboard for account/center verification and audit, with no access to clinical content
- Dark mode, adjustable text size, and an English/Arabic language toggle
- Synthetic demo data: four complete child profiles with full care teams, goals, reports, and voice notes

---

## System Architecture

```text
                              User (guardian / specialist / center)
                                        |
                                        v
                              React + TypeScript UI
                               (Vite, responsive PWA)
                                        |
                                        v
                                 FastAPI backend
                                        |
                +------------+----------+----------+------------+
                |            |                     |            |
                v            v                     v            v
          PostgreSQL   Local file storage    Realtime (WS)   AI Gateway
          (SQLAlchemy    (reports, voice      conversations       |
           + Alembic)      notes, images)                +--------+--------+
                                                           |                 |
                                                           v                 v
                                                   Gemini (free tier)  Local fallback
                                                   report analysis /   (no API key
                                                   grounded assistant   required)
                                                           
                                        Voice notes also route through:
                                        Local Whisper (faster-whisper) — fully free,
                                        no external API required
```

Every access path — UI, API, and AI — is evaluated against the same permission rule: **role + child + guardian consent + resource permission + expiration**. AI features never bypass this boundary, and center matching never claims a center is medically "best" — it returns a deterministic, explainable score over the data the requesting user is already authorized to see.

---

## Project Structure

```text
weam-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI routers (auth, children, care-team, reports, goals, ...)
│   │   ├── core/             # settings, constants, security helpers
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # AI gateway, STT, security, business logic
│   │   └── scripts/          # create_admin.py (server-side only)
│   ├── alembic/               # database migrations
│   ├── scripts/
│   │   ├── seed_demo.py       # synthetic four-child demo dataset
│   │   ├── seed_real_centers.py
│   │   └── demo_data/         # per-child seed builders
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/             # one file per route/screen
│   │   ├── components/        # shared UI components
│   │   ├── contexts/          # auth + settings (theme/text-size/language)
│   │   ├── i18n/              # translation dictionary
│   │   ├── api/                # typed API client
│   │   └── styles/             # per-page/per-milestone CSS
│   ├── public/
│   ├── package.json
│   └── .env.example
│
├── docs/
│   ├── ARCHITECTURE.md         # permission model and system boundaries
│   ├── DESIGN_SYSTEM.md        # visual design tokens and components
│   ├── LOCAL_SETUP.md          # step-by-step local setup (Windows/PowerShell)
│   ├── SEED_DATA_ARCHITECTURE.md
│   └── presentation/           # poster, submission deck, demo/judge scripts
│
├── docker-compose.yml           # local PostgreSQL
└── README.md
```

---

## Requirements

### Backend
- Python 3.12+
- PostgreSQL (via Docker Desktop, recommended) — tests fall back to SQLite automatically if Docker is unavailable
- See `backend/requirements.txt` for exact package versions (FastAPI, SQLAlchemy, Alembic, Argon2, PyJWT, faster-whisper, pytest, ...)

### Frontend
- Node.js 20+
- React 19 + TypeScript + Vite (see `frontend/package.json`)

### AI (optional, free tier)
- A free Gemini API key enables report analysis and the grounded child assistant. Without one, the app automatically uses a local, non-AI fallback — no feature is blocked.
- Voice-note transcription uses a local Whisper model (`faster-whisper`) that downloads once on first use and then runs fully offline — no API key needed.

---

## Setup

### 1. Copy environment files

From the repository root:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Before any deployment, replace `WEAM_JWT_SECRET` in `backend/.env` with a long random secret — the app refuses to start in production with the placeholder value.

### 2. Start PostgreSQL

```powershell
docker compose up -d postgres
```

### 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

### 4. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### 5. Demo data (optional but recommended)

From `backend/`, with the virtual environment active:

```powershell
python -m scripts.seed_demo              # four-child synthetic demo (safe to rerun)
python -m scripts.seed_real_centers       # real, publicly-sourced Riyadh/Jeddah centers
```

This refuses to run against `WEAM_ENVIRONMENT=production` unless `WEAM_ALLOW_DEMO_SEED=true` is set explicitly, and refuses to run unless the database is already at the latest Alembic revision. See [`docs/SEED_DATA_ARCHITECTURE.md`](docs/SEED_DATA_ARCHITECTURE.md) for the full design.

### 6. Tests

```powershell
cd backend
pytest -q
```

```powershell
cd frontend
npm run typecheck
npm run build
```

---

## Login / Demo Accounts

There is no admin sign-up — every other role can self-register from the app, or you can log in directly with the seeded demo accounts below.

**Password for every demo account:** `WeamDemo123!`

| Role | Email | Notes |
|---|---|---|
| Guardian (primary) | `guardian@weam.demo` | Parent of all four demo children |
| Guardian (secondary) | `guardian2@weam.demo` | Co-guardian |
| Speech & language specialist | `slp@weam.demo` | |
| Physical therapist | `pt@weam.demo` | |
| Special education specialist | `edu@weam.demo` | |
| Occupational therapist | `ot@weam.demo` | |
| Audiologist | `audiologist@weam.demo` | |
| Behavioral specialist | `behavioral@weam.demo` | |
| Psycho-educational specialist | `psych.edu@weam.demo` | |
| Teacher (per demo child) | `teacher.lama@weam.demo`, `teacher.youssef@weam.demo`, `teacher.rawan@weam.demo`, `teacher.omar@weam.demo` | |
| Center representative | `center@weam.demo` | |

Start with `guardian@weam.demo` to see the parent side (dashboard, all four children, reports/goals/voice notes, care team, centers), then log in as a specialist to see the same shared child from the care-team side.

### Create the first admin account

Admin accounts are never created through public registration. After applying migrations, run from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.create_admin --email admin@example.com --name "إدارة وئام"
```

The password is requested privately in the terminal and is never written to the repository. If the account already exists, its password is left unchanged unless you add `--reset-password`.

### Google Sign-In (optional)

Email/password works without any Google configuration. To enable Google Sign-In, put the same web Client ID in `backend/.env` (`WEAM_GOOGLE_CLIENT_ID`) and `frontend/.env` (`VITE_GOOGLE_CLIENT_ID`), and make sure the Google Cloud OAuth origin includes `http://localhost:5173`.

---

## Troubleshooting

**Backend won't start / crashes on startup in production mode**
Check `WEAM_JWT_SECRET` (must be 32+ random characters, not the placeholder), `WEAM_CREATE_TABLES_ON_STARTUP` (must be `false` in production — schema changes go through Alembic only), and that `WEAM_DATABASE_URL` points to PostgreSQL.

**Frontend can't reach the API**
Check `frontend/.env` → `VITE_API_URL` matches where the backend is actually running (default `http://localhost:8000/api/v1`), and that `backend/.env` → `WEAM_FRONTEND_ORIGINS` includes the frontend's origin.

**Demo seed script refuses to run**
It requires migrations to be at head (`alembic upgrade head` first) and, outside development, an explicit `WEAM_ALLOW_DEMO_SEED=true`.

**AI features return the fallback / non-AI response**
This is expected without an API key — set `WEAM_AI_API_KEY` / `WEAM_ASSISTANT_API_KEY` in `backend/.env` to enable Gemini-backed responses. The app remains fully functional either way.

**Voice-note transcription is slow on first use**
The local Whisper model downloads once on first run; subsequent runs are local and much faster.

---

## Product rules

- Supports multiple conditions and support needs from the start — no single diagnosis is hard-coded into the product.
- Guardian consent and least-privilege access apply to AI features exactly as they do to the rest of the UI/API.
- Competition/demo environments use synthetic data only — no real child, medical, identity, credential, or API-key data.
