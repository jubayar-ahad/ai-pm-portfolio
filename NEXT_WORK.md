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

## 1. Packaging — make all three Python builds `pip install -e .`-able

Ordered first because tests + CI depend on clean packaging.

- [x] `rag-app/pyproject.toml` (build-system, project metadata, entry-point `rag-app = rag_app.__main__:main` if applicable, runtime deps from `requirements.txt`, dev deps slot for pytest/mypy/ruff)
- [x] `tool-use-agent/pyproject.toml` (same shape)
- [x] `evals-harness/pyproject.toml` (same shape)
- [ ] Verify each builds with `python -m build --sdist --wheel` (or `pip install -e .` if `build` unavailable) and the existing CLIs still work after install
- [ ] DECISIONS.md entry locking the packaging convention (build backend choice, Python version floor, dev-dep names)

## 2. LICENSE — MIT, at repo root + per-build

- [ ] `/LICENSE` at repo root (MIT, copyright "Jubayar Ahad <year>")
- [ ] `/rag-app/LICENSE` (MIT, identical body, identical copyright line)
- [ ] `/tool-use-agent/LICENSE`
- [ ] `/evals-harness/LICENSE`
- [ ] Reference the license in each `pyproject.toml`'s `license` field and in each build's README

## 3. Tests — `pytest` suites per build

Highest-signal item on this list. Each build gets its own `tests/` directory.
Tests should be runnable with plain `pytest` from inside the build directory,
no fixtures requiring an API key. Use the existing dry-run / key-free paths.

- [ ] `rag-app/tests/`: tests for `corpus.py` (chunking shape + determinism),
  `retrieve.py` (BM25 ranking on a fixture corpus), `verify.py` (citation
  parser happy + sad paths, refusal sentence byte-equality), `generate.py`
  (dry-run JSON contract — schema and field types only, no live calls).
  Target: ≥80% line coverage on the package.
- [ ] `tool-use-agent/tests/`: tests for the tool catalog (registration + JSON
  schema validity), each registered tool's pure behavior, the agent loop's
  bounded-step contract (default cap, `--max-steps` override, refusal
  classification across the four buckets), trace record schema.
- [ ] `evals-harness/tests/`: tests for `ingest` (label + trace schema
  validation, startup invariants), each `score` rubric (refusal, groundedness,
  first-call-tool, termination, cost) with at least one positive + one
  negative fixture per rubric, `report` aggregation against a tiny synthetic
  scored.jsonl set.
- [ ] DECISIONS.md entry locking: pytest as the framework, no network in tests,
  fixture directory convention (`tests/fixtures/`), the coverage floor.

## 4. CI — GitHub Actions workflow

- [ ] `/.github/workflows/ci.yml` at repo root with one matrix job per build
  (3.9 / 3.11 / 3.12 on ubuntu-latest), running: `pip install -e .[dev]`,
  `pytest`, `python -m mypy <package>` (best-effort), `ruff check`.
- [ ] Each build's `pyproject.toml` declares the dev deps used by CI
  (pytest, mypy, ruff) under `[project.optional-dependencies].dev`.
- [ ] CI status badge added to each build's README and to the top-level README.
- [ ] DECISIONS.md entry locking the matrix shape and the lint/type-check
  policy (`mypy` is non-blocking; `ruff check` is blocking).

## 5. Real corpus for rag-app

The current corpus is the repo's own markdown — coherent but a bit ouroboros
for a demo. Replace with a small, attributable, public-domain text set so the
retrieval + citation behavior is provable on unfamiliar content.

- [ ] `rag-app/corpus/CORPUS_CANDIDATES.md` — rank 3 candidate public-domain
  sources (suggested defaults: selected Federalist Papers, selected Emerson
  essays, selected Project Gutenberg short stories) with per-candidate
  rationale: licensing certainty, length, prose style suitability for a Q&A
  demo, and any concerns. The user picks; subsequent iterations stop the
  corpus item if no pick is recorded after 1 iteration of waiting.
- [ ] Once the user picks (or by default the top-ranked candidate after a
  second iteration): add the chosen corpus files under
  `rag-app/corpus/<name>/` with a `SOURCES.md` listing exact URLs and
  retrieval date, and a `make-demo.sh` (or `python -m rag_app demo`)
  one-shot script that loads, retrieves, and asks a hand-picked question
  with dry-run output for the README.
- [ ] Update `rag-app/README.md` Status section and demo invocation.
- [ ] DECISIONS.md entry locking the corpus pick and the demo-script contract.

## 6. Three new agent-y tools for tool-use-agent

Current catalog is six read-only tools. Add three that demonstrate richer
agent-loop behavior. All must be safe (no shell-out, no network), and each
must come with a unit test in item 3's pytest suite (extend that test file
rather than treating this as a separate test deliverable).

- [ ] `sql_query` — accepts an in-memory SQLite file (path argument) + a SQL
  string, executes read-only (parametrized rejection of write keywords), and
  returns rows as JSON. Ship with a tiny fixture DB under
  `tool-use-agent/fixtures/`.
- [ ] `file_rewrite` — accepts a path + a structured edit operation
  (replace / append / prepend), applies it under a sandboxed root
  (`tool-use-agent/sandbox/`), and returns the diff. Refuses paths outside
  the sandbox.
- [ ] `regex_extract` — accepts a path + a regex, returns matches as JSON
  with line numbers. Useful for the agent's own "find places to change"
  reasoning.
- [ ] Tool catalog test extended to cover the three new tools.
- [ ] DECISIONS.md entry locking the safety guardrails (sandbox root,
  write-keyword denylist for SQL, no path traversal).

## 7. Mock-interview Q&A bank — one per portfolio piece

One markdown file per artifact, anticipating the obvious interviewer
questions and your honest answers. Don't fabricate the user's answers —
write the question, the framing of what a strong answer covers, and a
`<your answer here>` slot. Goal: cut interview prep time and surface
weaknesses in the artifacts themselves.

- [ ] `interview-prep/cursor-teardown.md` — 10 likely questions (e.g., "why
  Cursor over Copilot?", "what's your #1 ship-next pick and why?", "how
  would you instrument metric X?", "what would you cut?"). Each question
  followed by the strong-answer rubric and a placeholder for the user's
  draft.
- [ ] `interview-prep/rag-app.md` — 8–10 questions covering: BM25 vs.
  dense, evals, when to add a reranker, abstention bar, corpus
  ownership, cost economics, multi-turn extension, failure modes.
- [ ] `interview-prep/tool-use-agent.md` — 8–10 questions covering: step
  cap rationale, refusal taxonomy, observability (trace schema), tool
  catalog design, safety guardrails, how you'd productionize it.
- [ ] `interview-prep/evals-harness.md` — 8–10 questions covering: rubric
  selection, why these five, cost rubric design, what's missing,
  cross-build invariants, how this scales to a larger eval set.
- [ ] `interview-prep/README.md` — index file linking the four Q&A banks,
  the suggested prep order, and a "common cross-artifact questions"
  section (e.g., "walk me through your portfolio").
- [ ] DECISIONS.md entry locking the Q&A file shape, the no-fabrication
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
