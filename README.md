# ai-pm-role-90days

An AI Product Manager job-search portfolio, built incrementally to back the
90-day plan in [OBJECTIVE.md](OBJECTIVE.md). Every artifact in this repo is a
deliberate, PM-framed deliverable an interviewer can poke at — three working
LLM builds, a single high-quality teardown PRD, and a fill-in template kit for
the search itself.

This top-level README is the index. Each subdirectory has its own README with
its design contract; this file is the map from the
[OBJECTIVE.md](OBJECTIVE.md) milestones to the actual files. The full
chronological design log lives in [DECISIONS.md](DECISIONS.md).

---

## What this repo is, in one sentence

A real (not aspirational) AI PM portfolio: three runnable demos that share
cross-build conventions on purpose, plus a teardown of a live AI product, plus
a five-scaffold hiring-funnel kit (sourcing → outreach → cover letter →
resume → tracker) the user populates against the actual search.

## Milestone map

| Milestone | Artifact | State |
| --- | --- | --- |
| Day 10 — Build 1 (RAG app) | [`rag-app/`](rag-app/) | Shipped |
| Day 10 — Build 2 (Tool-use agent) | [`tool-use-agent/`](tool-use-agent/) | Shipped |
| Day 10 — Build 3 (Evals harness) | [`evals-harness/`](evals-harness/) | Shipped |
| Day 20 — Teardown PRD (Cursor) | [`teardown-prd/cursor-teardown.md`](teardown-prd/cursor-teardown.md) | Shipped (interview-ready, 2026-05-16) |
| Day 30 — Five funnel scaffolds (sourcing → outreach → cover letter → resume → tracker) | [`templates/`](templates/) | Shipped (scaffolds; user-populated) |

The three Day-10 builds are real coding work in their own subdirectories with
working demos and PM-framed READMEs, per the operating guardrails in
[OBJECTIVE.md](OBJECTIVE.md). The teardown PRD is a single document, not five
mediocre ones. The Day-30 templates are scaffolds the user fills against
actual companies — no fabricated employment, no invented pipeline rows.

## The three Day-10 builds

Each build shares two contracts the [`evals-harness/`](evals-harness/) asserts
at startup: a byte-identical `REFUSAL_SENTENCE` across both LLM builds, and an
algorithm-equivalent `compute_record_id` / `compute_corpus_fingerprint` pair
so the same logical query produces the same `record_id` from either side.
That cross-build property is what lets the harness say something interesting
*across* the two builds rather than benchmarking them in isolation.

### [`rag-app/`](rag-app/) — Retrieval-Augmented Generation demo

A CLI that retrieves chunks from this repo's own markdown corpus (BM25, no
embeddings, no API key needed for retrieval) and asks Claude to answer using
only those chunks, with `[source#start-end]` citations the build verifies
against the retrieved set. Refuses below a configurable BM25 score
threshold. Runs live with `ANTHROPIC_API_KEY`, dry-runs without.

Three subcommands: `load` (build the index), `retrieve` (BM25 only),
`ask` (full RAG, live or dry-run). `ask --json` emits a
`rag-app.ask.v1` trace record the evals harness consumes.

### [`tool-use-agent/`](tool-use-agent/) — Bounded tool-using Claude agent

A CLI that answers PM-style questions about this repo and the
interview-pipeline tracker by deciding for itself which of six read-only,
typed, stdlib-only tools to call. The loop is bounded by
`--max-steps` (default 6) and terminates in one of three deterministic
states surfaced as a `refusal_reason` discriminator in the JSON trace:
`end_turn`, `max_steps_exhausted`, or `repeated_tool_error`.

Three subcommands: `catalog` (print the tool surface as
Anthropic-tools-compatible JSON), `tool` (invoke a tool directly, no LLM),
`ask` (full agent, live or dry-run). `ask --json` emits a
`tool-use-agent.ask.v1` trace record the evals harness consumes.

### [`evals-harness/`](evals-harness/) — Cross-build evals harness

A stdlib-only Python CLI that reads `ask --json` trace records from the two
LLM builds, scores them against a labeled query set
([`evals-harness/queries.jsonl`](evals-harness/queries.jsonl)), and produces
a per-build, per-rubric Markdown report fit for an interview leave-behind.
**Performs no model calls of its own**, so it runs without
`ANTHROPIC_API_KEY` and re-runs are deterministic.

Three subcommands: `ingest` (validate labels + traces, normalize into an
envelope), `score --rubric {refusal,groundedness,first_call_tool,termination,cost}`
(per-rubric scoring), `report --scored …` (aggregate one Markdown report).

## The Day-20 teardown PRD

[`teardown-prd/cursor-teardown.md`](teardown-prd/cursor-teardown.md) is the
single, high-quality leave-behind: a six-section teardown of Cursor (AI-native
code editor) covering what's working, what's broken, what to ship next,
proposed metrics, out of scope, and how I'd validate. All claims about
Cursor are grounded in publicly observable product surface as of the
2026-05-16 observation snapshot — no fabricated metrics, no invented
internal context. §6.4 cross-references this repo's
[`evals-harness/`](evals-harness/) build as the concrete offline-eval pattern,
which is the load-bearing reason the teardown sits in the same repo as the
three builds rather than a separate doc.

The pick is recorded in [DECISIONS.md](DECISIONS.md); the shortlist that
preceded it is preserved at
[`teardown-prd/CANDIDATES.md`](teardown-prd/CANDIDATES.md) as the record of
how the choice was reached.

## The Day-30 scaffolds

Five fill-in templates that share a single placeholder grammar
(`_<placeholder>_`) so one regex (`_<.*>_`) validates all five. They are
ordered along the hiring funnel — sourcing feeds outreach, outreach feeds
applications, applications feed the tracker — so each downstream artifact
is honestly populatable only after the upstream one is:

- [`templates/TARGET_COMPANIES.md`](templates/TARGET_COMPANIES.md) —
  pre-engagement sourcing inventory upstream of `OUTREACH.md`: a 30–50-row
  target list with a four-state status workflow
  (`not-researched` → `researched` → `outreached` → `promoted-to-tracker`
  as a delete-from-this-file transition), discovery-source categories,
  brainstorm prompts, and a list-health rollup distinct from the tracker's
  authoritative Day-30 milestone rollup.
- [`templates/OUTREACH.md`](templates/OUTREACH.md) — 30–80-word cold-DM /
  referral-ask / dormant-re-engagement scaffold with three mutually-exclusive
  variants keyed to relationship state, a forwardable-blurb sub-section under
  the referral variant, and a one-explicit-ask-per-DM rule.
- [`templates/COVER_LETTER.md`](templates/COVER_LETTER.md) — 250–400-word
  letter scaffold with three mutually-exclusive opener variants
  (cold / referral / inbound-recruiter-response) and a paragraph 3 that
  quotes `RESUME.md`'s portfolio section by reference rather than restating
  it (single source of truth for company-agnostic claims).
- [`templates/RESUME.md`](templates/RESUME.md) — one-page PM resume scaffold
  with the three Day-10 builds and the Day-20 Cursor teardown pre-stubbed as
  named portfolio slots the user fills once they can demo each end-to-end.
- [`templates/INTERVIEW_TRACKER.md`](templates/INTERVIEW_TRACKER.md) — active
  pipeline + closed/off-ramp table + outreach log + Day-30 milestone rollup,
  with a fixed stage vocabulary and B1/B2/B3 bucket shorthand encoding the
  Bucket-2 priority from [OBJECTIVE.md](OBJECTIVE.md).

The trailing `_<` grep self-check is the same across all five: if any
italic placeholder marker still appears, the artifact is not ready to send.

## How to run the demos

```bash
# Build 1: RAG app
cd rag-app
python -m rag_app load                              # build chunks.jsonl from repo markdown
python -m rag_app retrieve "<a question>"           # BM25 only, no API key needed
python -m rag_app ask "<a question>" --dry-run      # prompt assembly only, no API key needed
ANTHROPIC_API_KEY=... python -m rag_app ask "<a question>"   # live with Claude
cd ..

# Build 2: Tool-use agent
cd tool-use-agent
python -m tool_use_agent catalog                    # print the six-tool surface
python -m tool_use_agent tool list_repo_files       # invoke a tool directly, no LLM
python -m tool_use_agent ask "<a question>" --dry-run        # first-turn prompt, no API key needed
ANTHROPIC_API_KEY=... python -m tool_use_agent ask "<a question>"   # live
cd ..

# Build 3: Evals harness (no API key, no model calls)
cd evals-harness
python -m evals_harness ingest --labels queries.jsonl --traces <path-to-asks.jsonl> --out ingested.jsonl
python -m evals_harness score --rubric refusal --ingested ingested.jsonl --out scored_refusal.jsonl
python -m evals_harness report --scored scored_refusal.jsonl --markdown report.md
cd ..
```

`anthropic>=0.40` is the only runtime dep, and only the live `ask` paths
need it; each build's `requirements.txt` documents this. The harness and
all dry-run / non-LLM subcommands are stdlib-only.

## Layout

```
.
├── OBJECTIVE.md           # the 90-day plan and operating guardrails
├── DECISIONS.md           # full chronological design log
├── rag-app/               # Day-10 Build 1: RAG demo
├── tool-use-agent/        # Day-10 Build 2: tool-using agent
├── evals-harness/         # Day-10 Build 3: cross-build evals
├── teardown-prd/          # Day-20: Cursor teardown + the shortlist that preceded it
└── templates/             # Day-30: sourcing, outreach, cover-letter, resume, tracker scaffolds
```

## On scope and honesty

Per the operating guardrails in [OBJECTIVE.md](OBJECTIVE.md), the templates
ship as fill-in scaffolds — there are **no fabricated companies, pipeline
rows, employment history, projects, or credentials** anywhere in this repo.
Every observation in the Cursor teardown is grounded in publicly observable
product surface. Every numeric example in the rag-app / tool-use-agent /
evals-harness READMEs is placeholder-shaped or reproduced from the same
build's actual output. The single chronological design log
([DECISIONS.md](DECISIONS.md)) records the contracts each iteration locked
in, so a reader can see what was decided when and why.
