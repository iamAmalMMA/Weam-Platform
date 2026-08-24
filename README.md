# Weam Platform | وئام

وئام منصة ذكية لتنسيق رحلة رعاية الأطفال ذوي الإعاقة والاحتياجات المختلفة، تجمع ولي الأمر وفريق الرعاية والمراكز في منظومة واحدة مع سجل رعاية موحد وصلاحيات دقيقة وذكاء اصطناعي مساند.

## Current implementation
**M1–M4 complete; M5 AI Center Matching implemented and pending final verification**

Implemented now:
- Responsive React + TypeScript UI
- FastAPI backend
- PostgreSQL-ready data layer + Alembic
- Email/password authentication
- JWT access + refresh
- Google Sign-In integration path (requires client ID configuration)
- Roles: guardian / care provider / center / admin
- Multiple child profiles under one guardian
- Separated `ChildIdentity` and `CareProfile`
- Condition-agnostic care model: conditions, needs, support requirements, services
- Protected child access
- Care team permissions, reports, goals, timeline, follow-ups, notifications, chat, voice notes, and grounded assistant
- Centers directory with search, filters, details, and user favorites
- Explainable child-to-center matching using the authorized profile, approved report analyses, active goals, age, city, and delivery preference
- Persisted per-user matching runs with permission-aware sources and audit records
- Synthetic demo seed
- PWA baseline

## Stack
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + Python
- Database: PostgreSQL
- Migrations: Alembic
- Authentication: Argon2 + JWT; optional Google Identity
- File storage: Object storage planned for reports/audio
- AI: Gemini-backed generation with grounded local fallbacks
- Realtime: WebSocket-compatible layer planned

## Repository layout
- `frontend/` — responsive web/PWA
- `backend/` — API, models, auth, migrations, tests
- `docs/` — architecture, local setup, branching, implementation status
- `.github/workflows/` — CI

## Local setup
See [`docs/LOCAL_SETUP.md`](docs/LOCAL_SETUP.md).

## MVP order
1. ✅ M1 — Core Care Record
2. ✅ M2 — AI & Communication Core
3. ✅ M3 — Follow-ups & Notifications
4. ✅ M4 — Centers Directory
5. 🧪 M5 — AI Center Matching (pending migration, test, build, and UX verification)
6. M6 — Communication Upgrade
7. M7 — Center Accounts / Provider Experience
8. M8 — Admin Dashboard
9. M9 — Final Product Polish
10. M10 — Demo / Competition Ready

## Product rules
- Supports multiple conditions and support needs from the start.
- Hearing impairment is a demo/use-case, not a product limitation.
- Guardian consent and least-privilege access apply to AI features too.
- Competition/demo environments use synthetic data only.
