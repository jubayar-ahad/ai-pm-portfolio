# DECISIONS

A log of choices made while executing OBJECTIVE.md. Each entry has an ISO date,
a Decision line, and a Rationale. Decisions are reversible — if a later
iteration finds a better path, append a new entry that overrides the old one
rather than rewriting history, so the change of mind stays auditable.

This file is the agent's contract with the user. Edit it anytime to redirect.

---

## 2026-05-16 — Build order for the Day-10 portfolio

**Decision:** Ship the three Day-10 builds in this order:
1. RAG application (`rag-app/`)
2. Tool-use agent (`tool-use-agent/`)
3. Evals harness (`evals-harness/`)

**Rationale:** RAG is the most concrete thing to point at in an interview and
has the lowest bar to a working end-to-end loop, so it produces a
LinkedIn-shareable artifact fastest. The tool-use agent reuses the same
provider/SDK setup, lowering incremental cost. The evals harness goes last on
purpose: evals built against a hypothetical system tend to be toy benchmarks,
but evals built against two real artifacts you already shipped are credible.

## 2026-05-16 — Repo layout

**Decision:** Each Day-10 build is a top-level subdirectory: `rag-app/`,
`tool-use-agent/`, `evals-harness/`. The Day-20 teardown PRD lives in
`teardown-prd/`. Fillable interview tracker and resume/cover-letter scaffolds
live in `templates/`.

**Rationale:** Top-level subdirectories keep each artifact one click from the
repo README, which keeps recruiter and interviewer eyes one click from a
working demo. Avoids a nested `src/` or `projects/` layer that adds no value.

## 2026-05-16 — Tech-stack choices are deferred per build

**Decision:** Language, LLM provider, and framework for each build are chosen
in the iteration that starts that build, not pre-committed here.

**Rationale:** The right stack for a RAG demo (e.g. a vector store and a
retrieval loop) is not necessarily the right stack for an evals harness (which
favors a thin test-runner pattern). Pre-committing now locks in choices before
the work informs them, with no upside.

## 2026-05-16 — Teardown target selection is user-gated

**Decision:** The first Day-20 iteration writes `teardown-prd/CANDIDATES.md`
ranking 3 real products from the default pool (Cursor, Linear AI, Notion AI,
Perplexity, GitHub Copilot) with rationale, then pauses for the user to pick.
The teardown PRD itself is drafted only after the user names the target.

**Rationale:** The teardown is the single highest-leverage interview
leave-behind. Its quality depends on the user being able to speak
authentically to the product, which means they need to actually use it. The
agent guessing wrong here wastes a full iteration.

## 2026-05-16 — No fabricated employment history or interview pipeline

**Decision:** Resume, cover-letter, and tracker artifacts are scaffolds with
clearly marked placeholders. The agent does not invent companies the user is
interviewing with, prior roles, projects, or credentials.

**Rationale:** Restated here from OBJECTIVE.md guardrails so it's
unmistakable. Fabricated specifics in a job-search artifact are worse than
useless — they break trust the moment the user reads them and risk leaking
into an external-facing document.

## 2026-05-16 — One complete artifact per iteration

**Decision:** Each iteration ships one complete thing rather than partially
advancing several. "Complete" means: the artifact stands on its own, a future
iteration can extend it without first cleaning it up, and it could be linked
to from the repo README today.

**Rationale:** Half-finished scaffolds across three builds leave nothing to
point at in an interview. One shipped artifact does.
