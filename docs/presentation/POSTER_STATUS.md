# Poster status — final pass (2026-09-04)

`KSCDR_Hackathon_114_Weam.pptx` in this folder — built on top of your own working
draft (all header/footer facts you and the team had already filled in were kept
untouched). Named per the submission convention:
`KSCDR_Hackathon_000_TeamName.pptx` → `KSCDR_Hackathon_114_Weam.pptx`.

## What changed in this pass

The six content boxes were dull — three of them still ended in a plain
"To insert: ..." text line instead of an actual visual. Guidelines *prefer* a
diagram in Methodology, a chart/table in Results, and a screenshot in Proposed
solution, so all three were built and inserted:

- **Methodology** — a real architecture diagram (guardian/specialist/center →
  Weam platform → AI assistant + versioned migrations), built as native
  PowerPoint shapes so it stays crisp at any print size (no DPI concerns —
  vector, not a raster image).
- **Results** — a native PowerPoint bar chart (Backend tests 111/111, DB
  migrations 18/18, Screen sizes 5/5 — all real numbers already in the deck)
  plus a stat callout for the contrast ratio (5.18:1 vs the 4.5:1 AA minimum),
  since it's a different unit and doesn't belong on the same bar chart.
- **Proposed solution** — a real screenshot of the running app's AI
  report-analysis screen, captured at 4800×3000px via a headless browser
  (device-scale-factor 3) so it clears the guideline's 600 DPI minimum even
  placed at 6 inches wide (works out to ~637 DPI). It was deliberately chosen
  because it visually proves the poster's own claim right next to it — "every
  AI-generated output stays a labeled draft until a human reviews it" — the
  screenshot shows the actual "مراجعة بشرية قبل الاعتماد" (human review before
  approval) badge and "معتمد بشريًا" (human-approved) status tag live in the UI.

Each of the three boxes had its bullet list trimmed and tightened to make
room — content moved into the visual instead of being duplicated as words next
to it (e.g. the architecture diagram already shows "FastAPI + PostgreSQL" and
"18 versioned migrations," so the bullets don't repeat those facts).

The project title was also filled in: `[ Project title ]` → **Weam** (Cambria
Bold 112pt, matching the guideline's recommended size — already set on the
box). This is the one call made without asking first, since the deadline was
today — English "Weam," matching the language of the rest of the poster and
your own logo asset already embedded in the file, in the box's existing
formatting.

## Confirmed already done (by you/the team, before this pass)

- Team number **114**, all 4 team members, affiliation, contact person,
  track/category — all real, all filled in.
- **QR code** — already embedded and decodes correctly (verified by actually
  decoding it, not assumed): it redirects to a Google Drive folder, matching
  "video, demo, repository, or additional files" from the guidelines.
- Team/institution logo placed in the header box.

## Still worth doing yourself before submitting

- **Open the real file in PowerPoint and check for text overflow.** LibreOffice
  isn't installed in this environment, so none of this could be rendered to
  images for pixel-level visual QA — every measurement above is arithmetic
  (font size × line count × box height), not something I looked at. I did the
  math conservatively and kept every bullet short enough that it's very
  unlikely to wrap to an extra line, but "calculated" is not "observed."
- **Scan the QR code with an actual phone** before sending, per the
  guideline's own instruction — I only confirmed it decodes correctly and
  redirects somewhere real, not that the Drive folder's sharing permissions
  are set to public.
- **Deadline**: the guidelines PDF says 4 September 2026, which is today. If
  that's genuinely different from what your team was told, this is the moment
  to double check with kscdr.hackathon@gmail.com.
