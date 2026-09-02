# Poster status

`WEAM_POSTER_DRAFT.pptx` in this folder — built from the official
`Poster-Template.pptx` you supplied. Same working-draft caveat as the main
deck: it's not final, since it's still missing facts only the team has.

## Deadline conflict — please resolve this first

Your forwarded email says the deadline is **5 September 2026**. The
**Poster_Guidelines.pdf itself says 4 September 2026**. Today is 2 September
2026, so this is a one-day difference with almost no slack either way —
worth confirming with `kscdr.hackathon@gmail.com` directly rather than
guessing which is authoritative.

## Confirmed done

- **Track · Category**: filled in as "Everyday Life · Individuals" (per your
  earlier decision for the main deck — reused here for consistency).
- **Logo box**: left empty per the guideline's own instruction ("if you have
  no logo, delete the placeholder text and leave the box empty") — no logo
  file was supplied.
- **All six content boxes** filled with short bullets, person-first language,
  no invented statistics — Introduction & problem statement, Objectives &
  target users, Proposed solution, Methodology & system design, Results &
  evaluation, Discussion/impact/ethics. The Results box reuses the same real,
  verified numbers as the main deck (111/111 tests, 18/18 migrations on real
  Postgres, 0 viewport-overflow issues, 5.18:1 worst-case contrast) and
  explicitly labels them as engineering/QA evidence, not a user study.
- Left plain (non-bracketed) "To insert:" notes for the three visuals the
  guidelines prefer but don't require (a screenshot in Proposed Solution, an
  architecture diagram in Methodology, a chart in Results) — no actual image
  was generated or embedded.

## Still blocked on facts (same list as the main deck)

- Team number (`KSCDR_Hackathon_000` → your real number)
- Project title (and the same "Weam vs. وئام vs. both" formatting question
  from the main deck applies here too — I have not filled this in on the
  poster either, unlike the main deck where I made a judgment call; here I
  left the bracket as-is since the poster's title is the single largest,
  most prominent element on the page and getting the formatting wrong would
  be more visible)
- Team members (up to 5 names) and affiliation
- Contact person: name, email, mobile
- QR code target (repo / demo video / live build link) — and the guidelines
  want an *actual scannable QR image* generated from that link and embedded,
  not just a URL typed as text; that's a follow-up step once you give me the
  link.

## Same verification gap as the main deck

LibreOffice isn't installed in this environment, so this could not be
rendered to images either. Validated structurally (`validate.py --original`
passed) and confirmed bracket-free everywhere except the four fields above.
**Please open the real file and check the six content boxes for text
overflow before submitting** — at 24pt Calibri in these box sizes there was
generous room in my calculations, but "calculated" is not "observed."

## One thing to double-check yourself
The guidelines say `Section headings — Cambria Bold, 36 pt (do not change)`
and I didn't touch them. I also didn't touch box positions/sizes, per "You
may resize the boxes... but keep them aligned." My new body text boxes were
placed to fit inside the existing card boundaries without resizing anything.
