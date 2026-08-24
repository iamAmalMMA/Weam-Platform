# Weam implementation status

## Implemented — M5: AI Center Matching (verification pending)

### Backend
- Child-scoped matching endpoint and latest-result endpoint
- Matching over authorized profile data, approved report analyses, and active goals
- Age, city, and in-person/remote constraints
- Explainable top-three ranking with source attribution
- Stored per-user matching runs and access audit records
- Gemini summary through the existing AI layer with a grounded local fallback
- Migration `0011_ai_center_matching`

### Frontend
- Arabic RTL center-matching page under each child profile
- Optional city and delivery preferences
- Clear reasons, authorized source labels, limitations, loading, empty, and error states
- Responsive cards and direct navigation to center details
- Safety wording that avoids medical endorsement or “best center” claims

### Verification
- Automated M5 backend tests cover ranking, permissions, source approval, age/city/mode constraints, latest results, and insufficient data.
- Run Backend tests, TypeScript typecheck, Frontend build, and responsive manual review before closing the milestone.

---

## Completed — Feature 01: Authentication + Child Profile

### Backend
- Email/password registration and login
- JWT access + refresh tokens
- `GET /auth/me`
- Google Sign-In backend path (activates when a Google Client ID is configured)
- Roles: guardian, care provider, center, admin
- Care providers and centers start unverified
- PostgreSQL-ready SQLAlchemy models
- Alembic baseline migration
- Identity data separated from care-profile data
- Multiple children per guardian
- Multi-condition / multi-need child profile
- Guardian isolation: another guardian receives 404 for a child they do not own
- Synthetic demo seed script

### Frontend
- Arabic responsive landing page
- Register / login
- Role selection
- Google Sign-In UI path when configured
- Protected routes
- Guardian dashboard with multiple children
- New child flow
- Child profile detail page
- PWA baseline manifest/service worker

### Verification
- Backend automated tests: 9 passing
- Python compile check: passing
- Frontend build must be run on a machine where npm dependencies can be installed (package network access is unavailable in the build sandbox used to prepare this package).

