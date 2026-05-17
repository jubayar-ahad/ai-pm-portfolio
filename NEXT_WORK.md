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

## 5. Real corpus for rag-app

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

- [ ] `rag-app/corpus/CORPUS_CANDIDATES.md` — rewrite from scratch against
  the revised criteria, ranking the three shortlist candidates a/b/c
  above with per-candidate license note, sample demo question, and
  concerns. Same `Pick:` line convention at the bottom. Do not re-include
  the prior public-domain literary candidates.
- [ ] Once the user picks (or by default the top-ranked candidate after a
  second iteration): add the chosen corpus files under
  `rag-app/corpus/<name>/` with a `SOURCES.md` listing exact URLs,
  retrieval date, and license/fair-use rationale, and a `make-demo.sh`
  (or `python -m rag_app demo`) one-shot script that loads, retrieves,
  and asks a hand-picked question with dry-run output for the README.
- [ ] Update `rag-app/README.md` Status section, demo invocation, and a
  one-line note explaining the corpus choice in portfolio terms (so a
  reviewer understands *why* this corpus, not just what it is).
- [ ] DECISIONS.md entry locking the corpus pick, the demo-script
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

---

## Done criteria for the whole list

- All seven top-level checkboxes ticked.
- DECISIONS.md has one entry per top-level item plus a final entry marking
  the list complete and pointing to potential future work (which is the
  user's call, not the agent's).
- `pytest` passes locally inside each of the three build directories with no
  network access, and the GitHub Actions matrix is green on the next push.
