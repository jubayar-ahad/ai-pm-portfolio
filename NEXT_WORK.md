# Next Work — Portfolio Hardening Pass

Focused worklist for the next gnhf run. Pick the topmost unchecked item, ship
the next smallest meaningful slice in one commit, and mark sub-items done.
Do NOT add new items here. Do NOT do reconciliation passes between unrelated
artifacts. Do NOT produce a second teardown. If an item requires user input,
ship a single ranked CANDIDATES-style file for that item and move on — do not
block the queue.

When the parent item's sub-checkboxes are all complete, mark the parent done
in the same commit.

---

## 1. Packaging — make all three Python builds `pip install -e .`-able [x]

Ordered first because tests + CI depend on clean packaging.

- [x] `rag-app/pyproject.toml` (build-system, project metadata, entry-point `rag-app = rag_app.__main__:main` if applicable, runtime deps from `requirements.txt`, dev deps slot for pytest/mypy/ruff)
- [x] `tool-use-agent/pyproject.toml` (same shape)
- [x] `evals-harness/pyproject.toml` (same shape)
- [x] Verify each builds with `python -m build --sdist --wheel` (or `pip install -e .` if `build` unavailable) and the existing CLIs still work after install
- [x] DECISIONS.md entry locking the packaging convention (build backend choice, Python version floor, dev-dep names)

## 2. LICENSE — MIT, at repo root + per-build [x]

- [x] `/LICENSE` at repo root (MIT, copyright "Jubayar Ahad <year>")
- [x] `/rag-app/LICENSE` (MIT, identical body, identical copyright line)
- [x] `/tool-use-agent/LICENSE`
- [x] `/evals-harness/LICENSE`
- [x] Reference the license in each `pyproject.toml`'s `license` field and in each build's README

## 3. Tests — `pytest` suites per build [x]

Highest-signal item on this list. Each build gets its own `tests/` directory.
Tests should be runnable with plain `pytest` from inside the build directory,
no fixtures requiring an API key. Use the existing dry-run / key-free paths.

- [x] `rag-app/tests/`: tests for `corpus.py` (chunking shape + determinism),
  `retrieve.py` (BM25 ranking on a fixture corpus), `verify.py` (citation
  parser happy + sad paths, refusal sentence byte-equality), `generate.py`
  (dry-run JSON contract — schema and field types only, no live calls).
  Target: ≥80% line coverage on the package.
- [x] `tool-use-agent/tests/`: tests for the tool catalog (registration + JSON
  schema validity), each registered tool's pure behavior, the agent loop's
  bounded-step contract (default cap, `--max-steps` override, refusal
  classification across the four buckets), trace record schema.
- [x] `evals-harness/tests/`: tests for `ingest` (label + trace schema
  validation, startup invariants), each `score` rubric (refusal, groundedness,
  first-call-tool, termination, cost) with at least one positive + one
  negative fixture per rubric, `report` aggregation against a tiny synthetic
  scored.jsonl set.
- [x] DECISIONS.md entry locking: pytest as the framework, no network in tests,
  fixture directory convention (`tests/fixtures/`), the coverage floor.

## 4. CI — GitHub Actions workflow [x]

- [x] `/.github/workflows/ci.yml` at repo root with one matrix job per build
  (3.9 / 3.11 / 3.12 on ubuntu-latest), running: `pip install -e .[dev]`,
  `pytest`, `python -m mypy <package>` (best-effort), `ruff check`.
- [x] Each build's `pyproject.toml` declares the dev deps used by CI
  (pytest, mypy, ruff) under `[project.optional-dependencies].dev`.
- [x] CI status badge added to each build's README and to the top-level README.
- [x] DECISIONS.md entry locking the matrix shape and the lint/type-check
  policy (`mypy` is non-blocking; `ruff check` is blocking).

## 5. Real corpus for rag-app [x]

Replace the current self-referential corpus with a small, attributable corpus
that signals **AI-PM relevance** to a portfolio reviewer — not just one that
flatters BM25. An interviewer opening the demo should think "smart corpus
choice for this role" rather than wondering why the demo answers questions
about 18th-century political theory. Fair-use-with-attribution for a
non-commercial portfolio demo is acceptable; strict US public domain is not
required and previously over-constrained the choice.

The prior CORPUS_CANDIDATES.md (Federalist Papers / Emerson / Gutenberg
short stories) was written under an over-narrow filter and has been
removed; the prior agent decision entry is to be marked superseded. Write
the new CANDIDATES file from scratch — do **not** re-include the prior
literary candidates.

Revised criteria, all four must clear:

1. **Portfolio fit** — the corpus is something an AI PM hiring manager
   would recognize as relevant to AI product work. Bonus if it ties
   narratively to one of the user's other artifacts (the Cursor teardown,
   the AI PM career objective).
2. **Permissible reuse** — fair use for a non-commercial portfolio demo
   with clear attribution in SOURCES.md, OR explicit permissive licensing
   (CC-BY, MIT, public domain). Avoid CC-BY-NC for prose the reviewer
   might quote back; flag the license per-candidate.
3. **Right size for the chunker** — ~20–80 chunks at the default 400-word
   chunk size with 80-word overlap.
4. **Prose style that lets BM25 work** — short, topical, noun-phrase-dense
   sentences with named entities.

Rank these three shortlist candidates (do not invent new ones):

a. **Cursor's public documentation + changelog** (`cursor.com/docs`,
   `cursor.com/changelog`). Ties directly to the existing Cursor teardown
   so the rag-app demo and the teardown become a paired narrative.
   Recommended default unless the ranking disagrees.
b. **Anthropic's public documentation** (`docs.anthropic.com` — API docs,
   model cards, prompting guide). Directly relevant subject matter for
   any model-lab application.
c. **A 5–10 essay set from Simon Willison's blog** (`simonwillison.net`).
   Explicit permissive reuse, canonical "thoughtful person using LLMs"
   prose. Lower product-fit than (a)/(b) but high AI-fluency signal.

**User pick (2026-05-17): all three.** Skip the re-rank — the candidates
file is not needed for this milestone. Ship all three corpora as separate
subdirectories under `rag-app/corpus/`. The multi-corpus demo is a
deliberate choice: it shows the rag-app handles heterogeneous sources and
makes citation provenance visually meaningful (a chunk path of
`cursor-docs/agent.md` vs. `anthropic-docs/tool_use.md` vs.
`willison/prompt-injection.md` self-explains the system's behavior).

- [x] Acquire and add corpus files under `rag-app/corpus/cursor-docs/`,
  `rag-app/corpus/anthropic-docs/`, and `rag-app/corpus/willison/`. Aim
  for ~10–30 chunks per corpus (so the combined corpus stays in the
  ~30–80 chunk band the chunker is sized for). If full pages are too
  long, pick the most demo-relevant subsections rather than truncating
  mid-paragraph. Use plain markdown, normalize to UTF-8, strip nav/footer
  cruft. **Do not fabricate URLs or content** — every file must trace to
  a real page on the live source, and the SOURCES.md must record exact
  URLs + retrieval date.
- [x] One `rag-app/corpus/SOURCES.md` at the corpus root listing every
  source file, its origin URL, retrieval date, and a per-source
  license/fair-use rationale (Cursor docs and Anthropic docs: fair-use
  for non-commercial portfolio demo with attribution; Willison: explicit
  permissive reuse — link to his stated reuse policy).
- [x] A `make-demo.sh` (or `python -m rag_app demo`) one-shot script
  that loads all three corpora into one index, retrieves on a hand-picked
  cross-corpus demo question, and produces dry-run output suitable for
  pasting into the README. Pick a demo question that *needs* multiple
  corpora to answer well (e.g., contrast a Cursor design choice with the
  Anthropic recommendation it implements, or with the Willison commentary
  on it). One question is enough — don't pad.
- [x] Update `rag-app/README.md` Status section, demo invocation, and a
  one-line note explaining the corpus choice in portfolio terms (so a
  reviewer understands *why* this corpus, not just what it is).
- [x] DECISIONS.md entry locking the corpus pick, the demo-script
  contract, and the fair-use-with-attribution posture — supersedes the
  prior CANDIDATES decision entry.

## 6. Three new agent-y tools for tool-use-agent [x]

Current catalog is six read-only tools. Add three that demonstrate richer
agent-loop behavior. All must be safe (no shell-out, no network), and each
must come with a unit test in item 3's pytest suite (extend that test file
rather than treating this as a separate test deliverable).

- [x] `sql_query` — accepts an in-memory SQLite file (path argument) + a SQL
  string, executes read-only (parametrized rejection of write keywords), and
  returns rows as JSON. Ship with a tiny fixture DB under
  `tool-use-agent/fixtures/`.
- [x] `file_rewrite` — accepts a path + a structured edit operation
  (replace / append / prepend), applies it under a sandboxed root
  (`tool-use-agent/sandbox/`), and returns the diff. Refuses paths outside
  the sandbox.
- [x] `regex_extract` — accepts a path + a regex, returns matches as JSON
  with line numbers. Useful for the agent's own "find places to change"
  reasoning.
- [x] Tool catalog test extended to cover the three new tools.
- [x] DECISIONS.md entry locking the safety guardrails (sandbox root,
  write-keyword denylist for SQL, no path traversal).

## 7. Mock-interview Q&A bank — one per portfolio piece [x]

One markdown file per artifact, anticipating the obvious interviewer
questions and your honest answers. Don't fabricate the user's answers —
write the question, the framing of what a strong answer covers, and a
`<your answer here>` slot. Goal: cut interview prep time and surface
weaknesses in the artifacts themselves.

- [x] `interview-prep/cursor-teardown.md` — 10 likely questions (e.g., "why
  Cursor over Copilot?", "what's your #1 ship-next pick and why?", "how
  would you instrument metric X?", "what would you cut?"). Each question
  followed by the strong-answer rubric and a placeholder for the user's
  draft.
- [x] `interview-prep/rag-app.md` — 8–10 questions covering: BM25 vs.
  dense, evals, when to add a reranker, abstention bar, corpus
  ownership, cost economics, multi-turn extension, failure modes.
- [x] `interview-prep/tool-use-agent.md` — 8–10 questions covering: step
  cap rationale, refusal taxonomy, observability (trace schema), tool
  catalog design, safety guardrails, how you'd productionize it.
- [x] `interview-prep/evals-harness.md` — 8–10 questions covering: rubric
  selection, why these five, cost rubric design, what's missing,
  cross-build invariants, how this scales to a larger eval set.
- [x] `interview-prep/README.md` — index file linking the four Q&A banks,
  the suggested prep order, and a "common cross-artifact questions"
  section (e.g., "walk me through your portfolio").
- [x] DECISIONS.md entry locking the Q&A file shape, the no-fabrication
  rule for the user's answer slots, and the deferral of "behavioral"
  interview prep to a separate (not-this-list) item.

## 8. Hypothetical AI feature PRD — Linear AI weekly retro summarization [x]

A PRD demonstrating PM craft on top of the existing analysis (Cursor
teardown) and code (three Python builds). The portfolio is currently heavy
on "here's how I'd analyze a product" and light on "here's a product I'd
ship." A 4–6 page PRD for a plausible AI feature on a recognized product
fills the gap.

**Selected target (locked 2026-05-17):** **Linear — AI weekly retro
auto-summarization for engineering teams.** Recognized product, Bucket 2
fit (established product adding AI features per OBJECTIVE.md), AI surface
actively expanding so the feature is timely rather than already shipped.
Engineering managers as primary user; ICs as secondary. Do NOT swap to a
different product — if a strong argument exists for swapping, write a
DECISIONS entry flagging it for the user and proceed with Linear anyway.

The PRD must be grounded in publicly observable Linear behavior. **No
fabricated internal metrics, no invented user quotes, no invented
roadmap.** Where a number is needed and unknown, state the source the
user (or interviewer) would consult to fill it in. Source-anchor every
observable Linear behavior claim with an inline footnote or end-list URL.

- [x] `prds/linear-ai-retro-summarization.md` — single PRD with the
  standard sections: problem / users + JTBD / goals / non-goals / proposed
  experience (with two or three sketches in markdown, not images) /
  proposed metrics (leading + lagging) / risks + mitigations / open
  questions / phased rollout plan. Length: 4–6 pages rendered. Cite the
  observable Linear behavior the proposal builds on.
- [x] `prds/README.md` — short index file explaining the prds directory's
  purpose, listing this PRD with a one-line product framing, and noting
  the no-fabrication rule binding any future PRDs.
- [x] DECISIONS.md entry locking the product+feature pick rationale, the
  PRD section structure as a portfolio convention, the no-fabrication
  rule, and three explicit out-of-scope items (most relevantly: no
  second PRD this run).

## 9. Behavioral interview Q&A bank

The existing `interview-prep/` has Q&A banks for each portfolio piece,
but iteration-75 DECISIONS explicitly deferred behavioral / culture-fit /
case-prompt / negotiation prep. Behavioral questions account for the
bulk of PM interview time. Behavioral is the most universal of the four
deferred buckets; the other three remain deferred (out of scope for
this list).

Same shape as the existing per-artifact Q&A files: 12–15 canonical
questions, per-question strong-answer rubric, `_<your draft>_` italic
slot. **Do NOT fabricate the user's stories or experience** — every
answer slot stays empty for the user to fill.

- [x] `interview-prep/behavioral.md` — 12–15 questions covering the
  canonical PM behavioral surface: tell-me-about-a-time prompts (a hard
  decision, a conflict, a failure, a successful launch, an ambiguous
  situation), why-leaving / why-this-role / why-AI-PM, biggest
  strength / biggest weakness, manager-style fit, a question about
  influencing without authority, a question about cross-functional
  conflict, a question about saying no to a stakeholder, a question
  about learning from a wrong call. Each with a strong-answer rubric
  (STAR or PARLA structure named, what a good answer covers) and an
  empty user-draft slot.
- [ ] Update `interview-prep/README.md` to include the behavioral bank
  in the index and the prep order. Note explicitly that culture-fit,
  case-prompt, and negotiation prep remain deferred (out of scope) so a
  reader knows the gap is intentional.
- [ ] DECISIONS.md entry locking the question selection rationale, the
  rubric naming choice (STAR / PARLA / etc), the per-question
  source-anchoring rule (no fabricated stories), and that the three
  remaining deferred buckets stay deferred for this list.

## 10. Personal landing page — single deployable HTML file

There is currently no "front door" for someone Googling the user's name
or clicking a link from a LinkedIn DM. The repo READMEs serve readers
who already clicked into GitHub, but a single-file HTML landing page is
the standard portfolio surface and can be hosted free on GitHub Pages.

Constraints:

1. **One file.** `landing-page/index.html` only — no build tooling, no
   Node, no frameworks, no external image hosts. Inline CSS. The page
   must open in a browser without any setup.
2. **Mobile-responsive** via plain CSS, no JS framework.
3. **No fabricated content.** Use the user's actual name (pull from
   `git config user.name`) and link to actual artifacts in this repo.
   Do NOT invent testimonials, comp expectations, or credentials.
4. Links: the Cursor teardown, each of the three Python builds (via
   their README), the linear-ai PRD (once item 8 ships), the resume
   scaffold (note it's a scaffold), the interview-prep index. Plus a
   one-sentence intro framing the user as transitioning to AI PM. The
   intro must be flagged as user-editable with an HTML comment, so the
   user knows where to make it their own.

- [ ] `landing-page/index.html` — single self-contained file meeting
  the constraints above. Mobile-responsive single column on narrow
  viewports, two-column on wide. Light theme; no dark-mode toggle for
  scope. Include a `<!-- USER: rewrite this intro -->` comment around
  the one-sentence intro so the user can find it.
- [ ] `landing-page/README.md` — one-paragraph deploy instructions
  (point GitHub Pages at this directory, or copy index.html to a
  personal site root). Note the no-fabrication rule.
- [ ] DECISIONS.md entry locking the single-file constraint, the
  no-build-tooling posture, the no-fabrication rule, and the editable
  comment convention.

## 11. Cost / token instrumentation across the three Python builds

Real production AI systems track per-request cost. The three builds
currently track nothing. Adding lightweight instrumentation demonstrates
economic thinking — an AI PM concern most candidates skip. Each build
emits a one-line cost summary on completion (or in `--json` output as a
structured field).

Scope constraint: **no external pricing API calls, no live token-count
calls.** Use locally pinned pricing constants (a single `pricing.py`-style
module per build) updated by hand from a documented source. Token counts
come from either the model response (when live) or a stdlib-only
approximation (4-chars ≈ 1-token heuristic, documented as approximate)
for dry-run paths.

- [ ] `rag-app`: add per-`ask` token-and-cost summary, both human-line
  and structured `--json` field. Document pricing-constants update
  policy in `rag-app/PRICING.md`. Extend `rag-app/tests/` with at least
  one positive + one negative case for the cost calc.
- [ ] `tool-use-agent`: add per-`ask` summary covering all steps,
  human-line + structured. Same `PRICING.md` sibling. Extend
  `tool-use-agent/tests/` with the same coverage shape.
- [ ] `evals-harness`: cost rubric already exists; extend the `report`
  subcommand to surface per-record total cost in the aggregated
  markdown report. Document pricing constants in
  `evals-harness/PRICING.md`. Extend `evals-harness/tests/` accordingly.
- [ ] DECISIONS.md entry locking: the per-build `PRICING.md` convention,
  the 4-chars-per-token heuristic for dry-run paths (explicitly named
  as approximate), the pricing constants update policy (manual, dated,
  sourced), and six explicit out-of-scope items (most relevantly: no
  live token-count API calls, no external pricing fetch, no
  cost-budget enforcement, no retroactive cost re-pricing).

---

## Done criteria for the whole list

- All eleven top-level checkboxes ticked.
- DECISIONS.md has one entry per top-level item plus a final entry marking
  the list complete and pointing to potential future work (which is the
  user's call, not the agent's).
- `pytest` passes locally inside each of the three build directories with no
  network access, and the GitHub Actions matrix is green on the next push.
