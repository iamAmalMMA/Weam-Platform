# Weam architecture baseline

## Product principle
The system supports multiple child conditions and support needs. It must not hard-code the product around hearing impairment or any single diagnosis.

## Layers
1. Responsive React client
2. FastAPI application API
3. PostgreSQL structured data
4. Object storage for reports/audio/images
5. Realtime communication layer
6. AI Gateway
7. RAG retrieval layer
8. Audit and permission enforcement

## Core permission rule
Access is evaluated using:

`role + child + guardian consent + resource permission + expiration`

AI features must use the same permission boundary as the UI/API.

## AI principle
AI may summarize, extract, retrieve, compare, and suggest. Sensitive actions require explicit human approval.

## Center matching boundary
Center matching is child-scoped and permission-aware. It uses only the care profile and the approved reports and active goals visible to the requesting user. A deterministic, explainable scorer ranks compatible active centers by recorded needs, age, optional city, and delivery preference. The existing Gemini layer may phrase the short grounded summary, but it cannot change the ranking or invent reasons; local fallback keeps the feature available. Matching runs are stored per requesting user for traceability and never claim that a center is medically “best.”

## Communication boundary
Conversations remain child-scoped and require an active care-team membership with messaging permission. Read receipts are per user. Attachments are signature-validated, stored privately, and downloaded only after conversation and child-access checks. Sharing a report, goal, or follow-up does not bypass that resource's own view permission.

## Center account boundary
A center account owns a directory profile through `CenterAccountMembership` and may manage its services and specialists. It receives no child access from that ownership. A child appears to a center only after a guardian invitation is accepted, with explicit permissions and an optional expiration.

## Administration boundary
Admin accounts are provisioned through a server-side command, never public registration. The admin API manages account/center review, activation, aggregate counts, and a dedicated administrative audit trail. It intentionally exposes no report contents, diagnoses, goals, voice notes, conversations, or other clinical records.

## Demo principle
Competition/demo environments use synthetic data only.
