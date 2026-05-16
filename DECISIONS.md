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

## 2026-05-16 — Tracker vocabulary: stage strings and bucket shorthand

**Decision:** `templates/INTERVIEW_TRACKER.md` uses a fixed stage vocabulary
(`sourced` → `applied` → `recruiter-screen` → `hiring-manager` → `panel` →
`final` → `offer-verbal` → `offer-written` → `accepted`, plus terminal
`rejected` / `withdrew` / `ghosted-30d`) and a `B1` / `B2` / `B3` bucket
shorthand mapping to the scope section of OBJECTIVE.md. Future artifacts
(resume scaffold, cover-letter scaffold, any rollup tooling) reuse these
exact strings.

**Rationale:** A controlled vocabulary lets a future iteration add a rollup
or status command without re-parsing free text, and keeps the user's mental
model consistent across artifacts. Encoding the Bucket 2 priority in the
shorthand (rather than a free-text "AI scope" column) makes the
objective-aligned filter trivial.

## 2026-05-16 — rag-app stack and corpus

**Decision:** The `rag-app/` build is Python 3.11+, generation via the
Anthropic SDK (default model `claude-haiku-4-5-20251001`, configurable),
embeddings via local `sentence-transformers/all-MiniLM-L6-v2`, an in-memory
NumPy cosine-similarity index, and a single-command CLI
(`python -m rag_app ask "<question>"`). Corpus v1 is the repo's own
markdown (`OBJECTIVE.md`, `DECISIONS.md`, `templates/INTERVIEW_TRACKER.md`,
`rag-app/README.md`). Corpus v2 (a small set of public AI-PM documents) is
deferred to a later iteration.

**Rationale:** This stack needs exactly one API key (`ANTHROPIC_API_KEY`) to
run end-to-end — no vector DB to provision, no second account for hosted
embeddings, no model fine-tuning. Local embeddings cost some retrieval
quality but remove a setup step, which matters more for a demo a recruiter
might watch on a screen share. NumPy beats a vector DB at this scale and
reads cleanly in interviews. Eating the repo's own dog food for corpus v1
sidesteps dataset licensing and lets the demo answer questions about its
own design decisions, which is itself a useful interview moment. The default
Haiku model keeps the per-query cost low enough that the demo can be run
liberally during interviews without budget anxiety.

## 2026-05-16 — rag-app ships incrementally, README first

**Decision:** The `rag-app/` README is shipped before any code. Subsequent
iterations implement: (1) corpus loader + chunker, (2) embedding index,
(3) retrieval CLI, (4) generation with citations, (5) refusal hardening,
(6) eval hooks for `evals-harness/`. Each lands in its own iteration. The
repo root README will only mark `rag-app/` as "demo-ready" once the
end-to-end `ask` slice runs against a real model.

**Rationale:** Locking the design contract in a README before code prevents
re-litigating stack and scope mid-build, which is the single biggest waste
mode for one-iteration-at-a-time work. The README is also a complete
standalone artifact today: it is the PM-framed writeup the objective asks
for, regardless of how much code has landed. The honesty cost — explicitly
labeling the build as "in progress" rather than claiming a working demo —
is paid up front in the README's Status table so the user is never
surprised.

## 2026-05-16 — rag-app chunker: word-based, paragraph-aware, 400/80

**Decision:** The `rag-app/` corpus loader (`python -m rag_app load`)
measures chunk size in **words**, not tokens, with defaults `chunk_words=400`
and `overlap_words=80`. Chunking is paragraph-aware: paragraphs are packed
greedily, never split mid-paragraph, and overlap is carried as whole
trailing paragraphs (not arbitrary word slices). A paragraph longer than
`chunk_words` is emitted as its own oversized chunk rather than mid-split.
Each chunk record carries an `id` (`source::index`), `source` (repo-relative
path), `span` (`[start_char, end_char]` in the source file), `word_count`,
and `text`.

**Rationale:** Token-accurate chunking would require pulling in `tiktoken`
or a model-specific tokenizer, which adds a dependency the loader does not
otherwise need. Word counts are a stable, deterministic, stdlib-only proxy
that is close enough for English markdown of this size; the embedding step
can re-measure in tokens if it ever matters for a model context budget.
Paragraph-level overlap preserves semantic coherence in the carried text
better than arbitrary word-window overlap, which can split mid-sentence.
Emitting char spans (rather than just text) lets the future generation step
resolve citations back to exact source positions for verification.

## 2026-05-16 — rag-app retriever: BM25 first, dense embedding deferred

**Decision:** The retrieval slice (`python -m rag_app retrieve`) uses a
stdlib BM25 (Okapi, k1=1.5, b=0.75) over the chunks produced by `load`,
not the previously pinned `sentence-transformers/all-MiniLM-L6-v2` dense
index. Dense retrieval is reframed as an optional later quality lift
that would act as a **reranker** over BM25's top-N, not as the primary
index. This supersedes the embedding choice in the 2026-05-16 "rag-app
stack and corpus" decision (which remains unchanged for Python version,
generation provider/model, CLI shape, and corpus v1 selection).

**Rationale:** Three reinforcing reasons. (1) MiniLM via `sentence-
transformers` requires PyTorch (~500 MB) and a one-time model download
(~80 MB), which is real friction for a demo intended to be run on an
interviewer's machine or in a sandbox. (2) BM25 is the established sparse
baseline; for a corpus of tens of chunks it is competitive with dense
embeddings, and the resulting retriever is fully explainable on a screen
share (term frequency, IDF, length normalization — no opaque embedding
space). (3) The modern production pattern is hybrid (BM25 + dense
reranker), so framing dense as a *quality lift on the lexical baseline*
matches what an AI PM would actually argue for in a real product, rather
than the older "swap BM25 for dense" framing. The "exactly one API key"
property of the original stack is preserved — in fact strengthened, since
no key is needed for retrieval at all and the only key remains
`ANTHROPIC_API_KEY` for generation. The hardcoded BM25 hyperparameters
(k1=1.5, b=0.75) are the standard defaults and do not need to live in
this log; if a future iteration tunes them against the evals harness,
that tuning result is what would be locked here.

## 2026-05-16 — rag-app generation: prompt contract, citation format, dry-run fallback

**Decision:** The generation slice (`python -m rag_app ask`) builds a
single-turn prompt with three load-bearing pieces locked here:

1. **System prompt rules, in priority order.** (a) Refuse with the exact
   string `"I don't have enough information in the provided context to
   answer this."` if the context is insufficient. (b) Every factual claim
   in the answer carries a citation `[<source>#<start>-<end>]`. (c) Do
   not draw on outside knowledge — context wins on conflict. (d) Be
   concise. The full system prompt text lives in `rag_app/generate.py`
   (`SYSTEM_PROMPT`); changes to it should land in a new DECISIONS entry.
2. **Citation format `[<source>#<start>-<end>]`** using the chunker's
   char span (not chunk-id index). `#` was chosen because it does not
   collide with the `::` separator inside chunk IDs and is regex-clean
   (`\[([^#\]]+)#(\d+)-(\d+)\]`), so the upcoming citation-verifier
   slice can parse it and re-read the cited bytes from disk to confirm
   the answer is genuinely grounded.
3. **Dry-run fallback.** `ask` auto-runs in dry-run (prints the assembled
   prompt instead of calling Claude) when `ANTHROPIC_API_KEY` is unset,
   and there is an explicit `--dry-run` flag for forcing the same path
   when a key *is* present. The `anthropic` SDK is imported lazily inside
   `call_claude`, so a fresh checkout without `pip install` can still
   run `load`, `retrieve`, and `ask --dry-run` without error.

**Rationale:** Locking the prompt rules in DECISIONS (not just the code)
makes the next-slice contract explicit: refusal hardening only needs to
enforce rule 1 mechanically (BM25 top-score threshold → bypass the
model and emit the canonical refusal string), and the citation verifier
only needs to enforce rule 2 (regex-parse the answer, look each span up
in `chunks.jsonl`). The `#` separator in the citation format is the
smallest reversible choice that keeps citations both human-skimmable
and machine-parseable. The dry-run fallback is the property that
makes this build demo-able in any environment — interview machines,
recruiter screen shares, CI — without requiring the interviewer to
provision a key first. It also gives the evals harness a no-network
code path that exercises retrieval and prompt construction, which is
the right unit to test deterministically. Default model remains
`claude-haiku-4-5-20251001` from the original stack decision; the
`--model` flag exists for the moment an interviewer asks "what about
Sonnet?", which is a useful PM-conversation moment, not a config
crisis.

## 2026-05-16 — rag-app refusal threshold and citation verification

**Decision:** The `ask` slice enforces two mechanical guardrails on top
of the prompt rules locked in the prior entry:

1. **BM25 top-score refusal threshold.** Default `MIN_RETRIEVAL_SCORE =
   1.5` (overridable per call with `--min-score`). When the BM25 top
   score is below the threshold (or retrieval returns no chunks), `ask`
   short-circuits before the model call and emits the canonical refusal
   sentence with `reason: low_retrieval_score` in the JSON trace and a
   `Mode: refused-low-score` line in the human-readable output. No
   tokens are spent.
2. **Citation verification on live answers.** `rag_app/verify.py`
   regex-parses every `[<source>#<start>-<end>]` citation in the
   model's answer (grammar: `\[([^#\]]+)#(\d+)-(\d+)\]`) and marks each
   `resolved` iff its `(source, start, end)` exactly matches the source
   and span of a chunk that was retrieved for this query. The CLI
   prints a one-line `citations: N/M resolved — OK|MISMATCH` summary
   and lists every unresolved citation; `--json` emits a structured
   `verification` block.

The canonical refusal sentence — `"I don't have enough information in
the provided context to answer this."` — is defined exactly once in
`rag_app/verify.py` as `REFUSAL_SENTENCE` and interpolated into
`generate.py`'s `SYSTEM_PROMPT` and the CLI's refusal short-circuit, so
the model-following-the-prompt path and the threshold-bypass path emit
byte-identical strings.

**Rationale:** Three properties earned by this slice.

- **Refusal is testable without an API key.** The threshold path is
  pure-Python and deterministic, so the evals harness can score
  refusal-when-uncertain accuracy by replaying retrieval traces — no
  network, no key, no nondeterminism. The threshold value (1.5) is
  honest-to-v1 only: queries with zero corpus-token overlap score 0.0
  and refuse cleanly, but BM25 over an English markdown corpus does
  not perfectly separate in-corpus from out-of-corpus questions when
  they share high-frequency stopwords ("what", "the", "is"). The
  evals harness will retune this against a labeled set, and a future
  iteration can swap in a query classifier or stopword-stripped index
  if the gap proves load-bearing.
- **Groundedness is mechanically auditable.** Verifying citations
  against the *retrieved* set (not the full corpus) directly enforces
  the system-prompt rule that the model must not cite context it was
  not given; a citation pointing to a real corpus chunk that wasn't in
  this query's top-k still flags as unresolved. Span equality (not
  containment) is required so the model cannot invent sub-spans the
  chunker did not emit.
- **One refusal string, one definition.** Drifting the refusal
  sentence between the system prompt and the threshold-bypass output
  would split the eval bucket and force the harness to maintain a
  fuzzy-match. Centralizing it in `verify.py` is the smallest possible
  guarantee against that drift.

The `1.5` threshold is the only tunable parameter in this slice and is
intentionally an ordinary constant (not a config file) until the evals
harness produces a reason to move it.

## 2026-05-16 — rag-app eval trace schema (`rag-app.ask.v1`)

**Decision:** Every `python -m rag_app ask --json` record carries four
trace fields, defined in `rag_app/trace.py`:

1. **`schema_version`** — constant string `"rag-app.ask.v1"`. The
   future `evals-harness/` version-gates on this. Additive fields keep
   the version; renames, removed fields, or changed semantics of
   existing fields require a bump (`v2`, etc.).
2. **`corpus_fingerprint`** — SHA-256 of `chunks.jsonl` bytes,
   truncated to 16 hex chars. Lets the harness detect corpus drift
   between two records that otherwise look identical.
3. **`record_id`** — SHA-256 over a canonical JSON of
   `{schema, question, top_k, model, min_score, corpus_fingerprint,
   mode}`, truncated to 16 hex chars. Deterministic given those
   inputs; `generated_at` is deliberately excluded so two runs of the
   same logical query on different days share an id.
4. **`generated_at`** — ISO-8601 UTC with second precision and a `Z`
   suffix. Lets the harness sort records chronologically without
   parsing filenames.

All four are populated only on `--json`; the human-readable `ask`
output is unchanged.

**Rationale:** These are the minimum-viable hooks for an eval harness
that hasn't been built yet, deliberately constrained to what the
harness genuinely needs rather than what it might want. `record_id`
gives the harness a content-addressable key for cross-run grouping
("did the answer to this exact logical query change between iteration
5 and iteration 10?"); `corpus_fingerprint` keeps the comparison
honest by surfacing a corpus change that would otherwise look like an
answer regression; `schema_version` is the cheapest possible insurance
against silent breakage when the schema does evolve. Truncating both
hashes to 16 hex chars (64 bits) trades cryptographic collision
resistance for skim-friendliness in diffs — well-suited to a corpus of
tens of records, and trivially expandable to the full digest if a
later iteration ever needs it. The trace lives in its own module
(`trace.py`) rather than being inlined in `__main__.py` so the future
harness can import the same helpers and produce records that are
byte-identical to ones the CLI emits — no duplicated hashing logic to
drift.

## 2026-05-16 — tool-use-agent stack and tool catalog (v1)

**Decision:** The `tool-use-agent/` build is Python 3.9+ (matching the
`rag-app/` runtime), generation via the Anthropic SDK using the SDK's
native tool-use API (`tools=[…]`, `tool_choice="auto"`, `tool_use` /
`tool_result` blocks; default model `claude-haiku-4-5-20251001`,
configurable), tools implemented as pure-Python stdlib-only functions
with explicit JSON schemas, dispatched through a single mutable
catalog. The CLI is a three-subcommand entry point
(`python -m tool_use_agent {tool,ask,catalog}`): `tool` invokes a
registered tool directly for testing without an API key, `catalog`
prints the JSON schemas, `ask` runs the LLM-driven agent loop. The
agent loop is bounded (`max_steps=6` default). The dry-run fallback
(`ask` auto-runs without an API key) is preserved from the `rag-app/`
pattern. The v1 tool catalog is exactly six read-only tools:
`list_repo_files`, `read_repo_file`, `grep_repo`, `list_pipeline_rows`,
`count_by_stage`, `count_by_bucket`. No write tools, no network tools,
no tool composition / planning, no cross-query persistence. Refusal
emits the same canonical sentence shape as `rag-app/` (a single
string defined once in the build, referenced from every refusal
path) so the future evals harness can bucket refusals across both
builds the same way.

**Rationale:** The stack reuses every load-bearing choice from
`rag-app/` (Python version, provider, model default, lazy SDK
import, dry-run fallback, exactly-one-API-key property) so an
interviewer who has already seen the rag-app demo does not pay
context-switch cost. The SDK's native tool-use API is the right
dispatch layer because it enforces the JSON schema and emits
structured `tool_use` / `tool_result` blocks — re-implementing tool
parsing over plain text would reproduce a known failure mode
(parameter hallucination) for no upside. The six-tool v1 catalog is
chosen for three reinforcing reasons: (a) it covers the two access
patterns a PM-relevant agent demo needs (read repo content; compute
structured rollups over the interview tracker), (b) it stays stdlib-
only so the dependency surface matches `rag-app/`, and (c) it
deliberately overlaps the data surface with the rag-app build so the
RAG-vs-tool-use tradeoff has a concrete in-repo answer to point at
during interviews. The bounded `max_steps=6` cap matches the
expected worst-case demo (one list-files, one read, one grep, one
rollup, one re-read, one summary) and turns "infinite loop" from a
silent failure into a structured `max_steps_exhausted` outcome the
evals harness can score. Read-only is a deliberate scope cap: write
tools open a separate product surface (confirmation UX, undo,
scoping) that belongs in its own iteration, not this one.

## 2026-05-16 — tool-use-agent ships incrementally, README first

**Decision:** The `tool-use-agent/` README is shipped before any code,
mirroring the `rag-app/` pattern. Subsequent iterations implement:
(1) tool catalog as pure-Python functions with `python -m
tool_use_agent tool <name>` direct-invocation and `… catalog` schema
printer, (2) single-step agent loop with one tool call then answer,
(3) multi-step bounded loop with inline tool trace, (4) refusal +
bounded-step termination (canonical refusal sentence single-source-
of-truth, emitted on no-useful-tool-result / `max_steps_exhausted` /
two-consecutive-errors), (5) eval-trace records (`tool-use-
agent.ask.v1`) reusing `rag-app/rag_app/trace.py` helpers via
import so `record_id` and `corpus_fingerprint` are byte-identical
across builds. The repo root README will only mark `tool-use-agent/`
as "demo-ready" once the multi-step loop slice runs against a real
model.

**Rationale:** The README-first sequencing earned its keep on the
`rag-app/` build (six implementation iterations all landed without
re-litigating scope, stack, or interface). The same property is
worth more here, not less: an agent-loop build has more places for
scope creep (every "what if it could also …" is a new tool), and a
locked v1 catalog in the README is the smallest possible commitment
device against catalog drift. Importing `trace.py` from the
`rag-app/` build rather than copying the helpers is the only way to
keep `record_id` hashes byte-identical across the two builds, which
is the property the evals harness will lean on to compare refusal
and groundedness behavior across them; copying the helpers would
silently drift the first time someone tweaked the canonical-JSON
ordering or the truncation length. The slice list is deliberately
five (not six like `rag-app/`) because there is no separate
"retrieval CLI before generation" slice analog — the tools *are*
the retrieval surface, and they are exercised directly by the
`tool` subcommand from slice 1, so slice 2 can land the LLM loop
without an intermediate step.

## 2026-05-16 — tool-use-agent slice 1: catalog shape, dispatcher, repo-meta exclusions

**Decision:** The tool-use-agent v1 catalog is implemented as a single
frozen `dict[str, Tool]` built once at import time by `build_catalog()`
in `tool_use_agent/catalog.py`. Each `Tool` is a frozen dataclass of
`{name, description, input_schema, impl}` where `impl` is a Python
callable with signature `(repo_root: Path, **kwargs) -> Any`. Tool
dispatch goes through `call_tool(name, repo_root, **kwargs)`, which
also normalizes return values for JSON serialization (dataclasses
become dicts, lists/dicts recurse). The Anthropic-tools-compatible
view (`{name, description, input_schema}` only — `impl` stripped) is
produced by `catalog_as_anthropic_tools()` so slice 2 can pass it
directly to `client.messages.create(tools=...)` with no further
shaping. Repo-meta directories excluded from `list_repo_files` /
`grep_repo` enumeration are: `.git`, `.gnhf`, `.cache`,
`__pycache__`, `.venv`, `node_modules`, `.DS_Store`. The grep tool
restricts itself to a small text-suffix allowlist
(`.md/.py/.txt/.json/.yml/.yaml/.toml/.cfg/.ini/.jsonl/.gitignore`)
plus a 1 MB per-file cap. Path arguments to `read_repo_file` /
`grep_repo` / `list_repo_files` resolve through `_resolve_inside_repo`,
which `Path.resolve()`s against the repo root and refuses any result
that escapes — refusal returns `None` (or an `ERROR: ...` string from
`read_repo_file`) so the agent receives a structured tool_result
rather than an exception.

**Rationale:** A single frozen catalog with one shared dispatcher is
the minimum surface area that lets slice 2's agent loop, the
`catalog` printer, and the per-tool argparse subparsers all discover
tools through the same registry — adding or removing a tool means
editing one list inside `build_catalog()` and nothing else. Splitting
the `Tool` shape into `description` (one line, ships to the LLM) and
`input_schema` (full JSON Schema, ships to the LLM) keeps the prompt
surface tight while preserving everything the model needs to call the
tool correctly. The exclusion list bundles three categories of
non-source content: VCS metadata (`.git`), orchestrator state
(`.gnhf` — the gnhf run log already includes the full chat history
and tool results, so leaving it in would make every grep hit
massively redundant), and build artifacts (`__pycache__`, `.venv`,
`node_modules`, `.cache`). The text-suffix allowlist and 1 MB cap are
defensive but cheap: an agent that points `grep_repo` at a binary
asset or a huge log file should not stall the demo. Returning
`ERROR: ...` strings (not raising) from `read_repo_file` is the same
pattern slice 4's refusal handling will rely on — every recoverable
error becomes a tool_result the model can read and react to,
matching the behavior the Anthropic tool-use API expects.

**Tracker parser specifics:** `list_pipeline_rows` parses the
`## Active pipeline` section of `templates/INTERVIEW_TRACKER.md` by
slicing out lines between that heading and the next `## ` heading,
then walking the markdown-table rows. Placeholder rows are detected
by the regex `^_<.*>_$` matching the Company cell, plus empty
Company cells; both are excluded. Unknown stage/bucket filter values
return an empty list (not an error). `count_by_stage` and
`count_by_bucket` always return histograms keyed by the full locked
vocabulary from the iteration-2 stage/bucket decision, so an empty
tracker still produces a stable-shaped output and the LLM's
downstream summarization does not have to guess at missing keys.
This is the property that lets future eval traces compare the same
tool call across iterations without per-run schema reconciliation.

## 2026-05-16 — tool-use-agent slice 2: single-step loop, prompt contract, dry-run inheritance

**Decision:** The tool-use-agent's `ask` subcommand is a single
**tool-call cycle** in this slice — the model is called once with
`tools=[…]`, every `tool_use` block it emits in turn 1 is executed
locally via `call_tool(...)`, the results are sent back as
`tool_result` content blocks, and turn 2's text is the final answer.
A second cycle of tool calls (the model asking for more tools after
seeing the first batch of results) is **not** honored in slice 2 —
`stop_reason` is set to `single_step_cap_reached` and the cap is
named explicitly in the CLI output. Slice 3 will lift this to a
bounded `max_steps=6` loop. The slice-2 contract is implemented in
`tool_use_agent/agent.py` and locks four pieces:

1. **System prompt rules, in priority order.** (a) Refuse with the
   exact sentence `"I don't have enough information in the provided
   context to answer this."` when no tool can produce supporting
   evidence. (b) Prefer the smallest, most targeted tool call
   (specific line ranges, filtered tracker queries). (c) Be concise;
   never paste long file contents back to the user. (d) Tool results
   are the only evidence; outside knowledge is disallowed. The full
   text lives in `agent.py::SYSTEM_PROMPT`; future edits land in a
   new DECISIONS entry.
2. **`REFUSAL_SENTENCE` constant defined in this build.** Same literal
   string as `rag-app/rag_app/verify.py::REFUSAL_SENTENCE`. Both
   builds define this independently rather than cross-importing, so
   each build remains self-contained, but the string is *byte-
   identical* so the future evals harness can bucket refusals from
   both builds with a single equality check (no fuzzy match). Slice 4
   will centralize this in a `verify.py`-style module for this build
   and add the programmatic threshold-bypass enforcement.
3. **Tool-result content shape.** Tool outputs are JSON-encoded with
   `json.dumps(..., default=str)` and passed as `tool_result.content`
   (string form, which the Anthropic API accepts). Recoverable
   dispatch errors (unknown tool name → `KeyError`, bad kwargs →
   `TypeError`, schema-rejected values → `ValueError`) are caught at
   the dispatch boundary and become `{"type": "tool_result",
   "tool_use_id": ..., "content": "ERROR: <type>: <msg>",
   "is_error": true}` so the model receives them as data and can
   react. Unrecoverable errors (programmer bugs) still raise.
4. **Dry-run fallback inherited from the rag-app pattern.** `ask`
   auto-runs in dry-run (prints the assembled system prompt, user
   message, and the tool catalog the model would see) when
   `ANTHROPIC_API_KEY` is unset, and there is an explicit `--dry-run`
   flag for forcing the same path when a key is present. The
   `anthropic` SDK is imported lazily inside `run_single_step`, so a
   fresh checkout without `pip install -r tool-use-agent/
   requirements.txt` can still run `catalog`, `tool`, and `ask
   --dry-run`. `--json` emits a slice-2 baseline shape (`mode`,
   `question`, `prompt`, `tool_calls[]`, `stop_reason`, `model`,
   token usage, `final_text`) — slice 5 will add
   `schema_version`/`record_id`/`corpus_fingerprint`/`generated_at`
   to this shape by importing the helpers from
   `rag-app/rag_app/trace.py`.

**Rationale:** A single-step cap is the smallest implementation that
exercises the full tool-use surface (catalog → tool_use → dispatch →
tool_result → final answer) end-to-end, so slice 3's multi-step
upgrade becomes a loop counter and a termination check rather than a
re-architecture. Surfacing the cap as a named `stop_reason` (instead
of silently truncating) means an interviewer who runs the demo today
sees the planned boundary, not a mysterious half-answer — and slice
3's "what changed?" diff will be tightly scoped. Inheriting the
dry-run fallback from `rag-app/` keeps the **exactly one API key
across both builds** property and makes the slice verifiable in a
sandbox where no key is present (which is the same property the
evals harness will need). Catching `KeyError`/`TypeError`/`ValueError`
at the dispatch boundary and surfacing them as `is_error=true`
tool_result blocks is the same recoverable-error-as-data pattern
the slice-1 DECISIONS entry locked for `read_repo_file` — slice 4's
refusal handling will treat these as one bucket. Defining
`REFUSAL_SENTENCE` independently in both builds (rather than
cross-importing across top-level directories) keeps each build
runnable on its own; the alignment guarantee is a string-equality
test the evals harness can assert at startup.

## 2026-05-16 — tool-use-agent slice 3: bounded multi-step loop, max_steps semantics, cap surface

Slice 3 lifts the slice-2 single-step cap and ships the bounded
multi-step agent loop in `tool_use_agent/agent.py::run_agent`. The
following contract is locked so slice 4 (refusal canonicalization)
and slice 5 (eval-trace records) can layer on without re-litigating
loop semantics:

1. **`max_steps` semantics: cost-bound, not call-count.** `max_steps`
   (default 6, configurable via `--max-steps`) caps the number of
   *tool-execution rounds*, where one round = one model call whose
   response contained at least one `tool_use` block + the local
   execution of every `tool_use` in that response. A model turn that
   emits *no* `tool_use` blocks terminates the loop immediately and
   does not consume a step. With `max_steps=6` the worst case is up
   to 6 model calls that each request tools, plus their local
   executions; there is no implicit "final summarization" call after
   the cap. This is the cost-bound semantics the `calls-per-answered-
   query` AI-PM-lens metric measures.

2. **Termination conditions and `stop_reason` discriminator.** The
   loop ends in exactly one of two states: `stop_reason=end_turn`
   when the model emits no `tool_use` blocks in some turn (the
   final answer is the accumulated `text` blocks from that turn,
   `steps_taken < max_steps` is possible), or
   `stop_reason=max_steps_exhausted` when the cap is reached
   (`steps_taken == max_steps`, `final_text` is a deterministic cap
   note for now). Slice 4 will replace the cap note with
   `REFUSAL_SENTENCE` so the evals harness can bucket the
   `max_steps_exhausted` path with other refusals via a single
   equality check; slice 3 deliberately keeps the cap note distinct
   so an interviewer running the demo today sees the planned
   boundary instead of a refusal pretending to be a model decision.

3. **Per-step trace granularity.** `ToolCallTrace` gains a
   1-indexed `step: int` field denoting the bounded-loop round in
   which the call was issued. Parallel `tool_use` blocks in one
   model turn share a `step` value, so the trace distinguishes
   "two tools in one round" (1 step) from "two tools in two rounds"
   (2 steps). This is the granularity slice 5's trace records will
   serialize, and the `--max-steps` cap is checked against
   `steps_taken` (not `len(tool_calls)`).

4. **AgentResult shape additions.** `AgentResult` gains two new
   fields surfaced in both the human-readable view and the
   `--json` payload: `max_steps: int` (the configured cap, default
   6) and `steps_taken: int` (the rounds actually executed). Token
   usage continues to accumulate across all turns. The slice-2 JSON
   schema is otherwise unchanged — same `mode`/`question`/`prompt`/
   `tool_calls[]`/`stop_reason`/`model`/`input_tokens`/
   `output_tokens`/`final_text` keys — so this is an additive-fields
   change and does not require a `tool-use-agent.ask.v1` schema
   version bump when slice 5 lands.

**Rationale.** Making `max_steps` mean "tool-execution rounds" (not
"model calls") is the framing that survives both demo and
production: a PM saying "the agent loops at most six times" matches
the user-visible cost they would budget. Distinguishing
`end_turn` from `max_steps_exhausted` at the `stop_reason` level
gives the eval harness a clean discriminator without needing to
parse `final_text`, which matters because the harness's per-question
correctness rubric and its per-question termination-quality rubric
are different metrics and would otherwise have to share a signal.
Surfacing `steps_taken` alongside `max_steps` is the smallest
disclosure that lets a viewer reason about "did the cap matter for
this answer?" — a cap that was never hit is a free-disposal upper
bound; a cap that was hit is the cost the agent paid. Adding
`step` to `ToolCallTrace` rather than relying on positional
enumeration matters because parallel `tool_use` blocks would
otherwise inflate the apparent step count by 2x in a multi-tool
turn, which would make any "% of queries answered in ≤2 steps"
eval metric quietly wrong. The deterministic cap-note final-text
(deferring `REFUSAL_SENTENCE` to slice 4) keeps each slice's
contract minimal: slice 3 owns "what does the loop do," slice 4
owns "what string represents a refusal," and the diff between them
is a one-line swap, not a re-architecture.

## 2026-05-16 — tool-use-agent slice 4: canonical refusal surface and termination discriminator

Slice 4 closes out the agent loop's termination semantics by routing
every non-`end_turn` exit through a single canonical refusal string
and adding a `refusal_reason` discriminator that the future evals
harness can group on without parsing `final_text`. The contract is
implemented in `tool_use_agent/verify.py` and consumed by
`tool_use_agent/agent.py::run_agent`. Four pieces are locked here:

1. **`REFUSAL_SENTENCE` lives in `tool_use_agent/verify.py`, defined
   exactly once in this build.** Imported into `agent.py` (replacing
   the slice-2 local constant). The string is byte-identical with
   `rag-app/rag_app/verify.py::REFUSAL_SENTENCE`. The two builds
   continue to define the string independently — neither imports
   from the other top-level directory — so each build remains
   self-contained; the alignment guarantee is a string-equality
   check the future evals harness will assert at startup. Drifting
   the sentence in either build is the single failure mode this
   slice trades off against, and the harness's startup assertion is
   the smallest possible canary.

2. **Three termination states, one canonical `final_text` shape.**
   `run_agent` now exits in exactly one of:
   (a) `stop_reason="end_turn"` — the model emitted no `tool_use`
   block. `final_text` is the model's text, stripped.
   `refusal_reason` is `null` unless the text is byte-equal to
   `REFUSAL_SENTENCE` per system-prompt rule 1, in which case
   `refusal_reason="model_refused"`.
   (b) `stop_reason="max_steps_exhausted"` — the bounded loop hit
   `--max-steps` without an `end_turn`. `final_text` is
   `REFUSAL_SENTENCE` (the slice-3 placeholder cap note is removed).
   `refusal_reason="max_steps_exhausted"`.
   (c) `stop_reason="repeated_tool_error"` (new in slice 4) — the
   same `(tool, input)` canonical key, computed by
   `verify.canonical_call_key`, errored in two consecutive steps.
   `final_text` is `REFUSAL_SENTENCE`.
   `refusal_reason="repeated_tool_error"`. A single error followed
   by a successful retry, or two errors with different inputs in
   consecutive steps, do **not** trigger the refusal — the loop
   continues so the model can recover, mirroring the existing
   recoverable-error-as-`tool_result.is_error=true` pattern from
   slice 1/2.

3. **`canonical_call_key` is the equality grammar for the
   repeated-error detector.** Keys are
   `json.dumps({"tool": ..., "input": ...}, sort_keys=True,
   ensure_ascii=False)`. Sorted keys means parallel `tool_use`
   blocks in one turn that emit identical `(tool, input)` pairs
   collapse to one key (correct: they were emitted in the *same*
   step, so they cannot be consecutive across steps). The detector
   (`verify.detect_repeated_error`) takes the prior step's error-
   key set and the current step's error-key set and returns the
   first intersecting key, or `None`. Locking the key grammar in
   `verify.py` (not inline in `agent.py`) is what lets the future
   evals harness recompute the same key from a trace record if it
   needs to score termination-quality per error type.

4. **`AgentResult.refusal_reason` is an additive JSON field.**
   Surfaced in the `ask --json` payload and the human-readable
   trace footer. Slice-3's `tool-use-agent.ask.v1` baseline shape
   is otherwise unchanged (same `mode`/`question`/`prompt`/
   `tool_calls[]`/`stop_reason`/`model`/`max_steps`/`steps_taken`/
   token usage/`final_text` keys), so this remains an additive
   change and does not require a schema-version bump when slice 5
   serializes trace records.

**Rationale.** Three properties earned by this slice.

- **One canonical string, three deterministic paths.** The future
  evals harness's "refusal-when-uncertain rate" metric needs every
  refusal path to collapse to one bucket without fuzzy matching.
  With slice 3's placeholder cap note still in place, the harness
  would have had to maintain a per-build refusal regex and re-tune
  it every time the cap note's wording drifted. Replacing the cap
  note with `REFUSAL_SENTENCE` is the smallest possible change
  that makes the metric a one-line equality check.

- **`refusal_reason` discriminator separates "why" from "what."**
  The `final_text` becoming uniform across refusal paths is the
  property that makes refusal a single bucket; the
  `refusal_reason` field is the property that lets the harness
  *also* score termination quality per cause — "% of refusals that
  were cap-driven vs. error-driven vs. model-self-driven." Without
  it, the harness would have to reconstruct cause from the trace,
  which is exactly the dishonest signal slice 3's `stop_reason`
  discriminator avoided. Three reasons (`model_refused`,
  `max_steps_exhausted`, `repeated_tool_error`) is the smallest set
  that covers the three deterministic refusal paths the loop can
  produce, and the field is `null` on the happy path so a single
  `is None` check answers "did this run succeed."

- **Repeated-error refusal is consecutive-across-steps, not
  total-across-loop.** A model that errors once, sees the
  `is_error=true` tool_result, and retries with a corrected input
  is the *intended* recovery path and must not refuse. Checking
  for the same canonical key in *consecutive* steps (not across
  the whole trace) is the smallest detector that fires only on
  genuine retry-loops while leaving recovery semantics intact.
  Parallel `tool_use` blocks within one turn share a `step`
  number (locked in slice 3), so two identical bad calls emitted
  in parallel collapse to one canonical key in `this_step_error_keys`
  and do not self-trigger the refusal — which is the correct
  semantics, because they are not "consecutive errors" but "one
  bad turn."

The detector intentionally does *not* try to detect "model is
spinning but each call succeeds" (e.g. reading the same file ten
times). That is a cost-bound, not a refusal-bound, and the
existing `--max-steps` cap is the right tool for it. Conflating
the two would create a fuzzy "stuck-detector" with parameters
the evals harness would have to tune, instead of the two clean,
independent signals (`max_steps_exhausted` and
`repeated_tool_error`) the harness has today.

## 2026-05-16 — tool-use-agent slice 5: eval trace schema (`tool-use-agent.ask.v1`)

**Decision:** Every `python -m tool_use_agent ask --json` record
carries the same four trace fields shipped by `rag-app/`'s slice 5,
defined in a new module `tool_use_agent/trace.py`:

1. **`schema_version`** — constant `"tool-use-agent.ask.v1"`. The
   future `evals-harness/` version-gates on the prefix
   (`rag-app.ask.v1` vs `tool-use-agent.ask.v1`) to route to the
   right scorer. Additive top-level or per-call fields keep the
   version; renames, removed fields, or changed semantics of
   existing fields require a bump.
2. **`corpus_fingerprint`** — SHA-256 of the canonical-JSON
   serialization (`sort_keys=True, ensure_ascii=False`) of
   `catalog_as_anthropic_tools()`, truncated to 16 hex chars. The
   tool-use agent has no chunks file; its analog of a corpus is
   the catalog the model perceives. Fingerprinting the
   Anthropic-tools view (not the Python `impl` callables) means a
   behavior-preserving refactor of a tool implementation does
   *not* invalidate cross-iteration record comparison, while
   adding/removing/re-describing a tool does.
3. **`record_id`** — SHA-256 over the canonical JSON of
   `{schema, question, model, max_steps, mode,
   corpus_fingerprint}`, truncated to 16 hex chars. The `model`
   used here is the CLI's `--model` argument (the *requested*
   model), not the SDK response's `model` (which may carry a
   more specific version pin); this matches `rag-app/`'s pattern
   and means the same logical query against the same catalog
   produces the same id on different days, including for the
   dry-run path. `top_k`/`min_score` from the rag-app shape are
   replaced by `max_steps` because the tool-use loop's bound is
   the relevant cost knob (and changing it materially changes
   behavior). `generated_at` is excluded for the same reason as
   in rag-app: wall-clock time is not part of the query.
4. **`generated_at`** — ISO-8601 UTC with second precision and a
   `Z` suffix. Same shape as `rag-app/`.

The `tool_calls[]` array gains two additive per-call fields:
`latency_ms` (wall-clock duration of the local tool execution,
measured with `time.perf_counter` and rounded to int
milliseconds) and `output_len` (byte length of the UTF-8 encoded
JSON serialization of the tool output, which is the cost signal
the harness reads without re-running tools). The slice-3/4 inner
keys (`tool`, `input`, `output`, `is_error`, `step`) are
unchanged, so this remains additive and does not require a
schema-version bump.

**Cross-build helper alignment.** `tool_use_agent/trace.py`
mirrors `rag-app/rag_app/trace.py` *structurally* — same hashing
algorithm (canonical JSON with sorted keys → SHA-256 → 16-hex-
char truncation), same `_HEX_LEN = 16` truncation, same
`now_iso()` timestamp shape — but the two modules deliberately
do **not** cross-import. Each top-level build remains self-
contained; the alignment guarantee is a startup assertion the
future evals harness will own (parallel to slice 4's
`REFUSAL_SENTENCE` byte-equality contract). The earlier "import
trace.py from rag-app" plan locked in the iteration-9 stack
entry is superseded by the same iteration-11 pattern that
walked back cross-import of `REFUSAL_SENTENCE`: per-build self-
containment beats a cross-directory `sys.path` hack, and the
harness can assert behavior equivalence with two ~3-line
fixtures (hash a known catalog twice, one per build) at startup.

**Rationale.** Three properties earned by this slice.

- **Cross-day record diffability for the same logical query.**
  Excluding `generated_at` from `record_id` and pinning the
  `model` to the user-facing `--model` argument means three
  consecutive runs of the same `ask` invocation share an id, and
  three runs across iterations 13 → 14 → 20 also share one — as
  long as the catalog surface and the requested-model string
  don't change. This is the property the harness needs to ask
  "did the answer to this exact logical query change between
  two runs?"
- **Fingerprint on the model-facing surface, not the impl.**
  Hashing `catalog_as_anthropic_tools()` rather than the
  Python `impl` callables means a behavior-preserving refactor
  (e.g. rewriting `grep_repo` for performance with no surface
  change) does not invalidate every prior record. The
  conservative alternative — hashing every `impl` callable's
  bytecode — would silently bust id stability on every
  refactor, hiding genuine answer-regression signal under
  spurious id churn. If a future iteration finds the
  surface-only fingerprint too lax (e.g. a buggy `impl`
  produces wrong answers without changing its surface), the
  evals harness's correctness rubric will catch it; that is
  the right separation of concerns between trace identity and
  trace correctness.
- **Per-call cost signals are additive.** Surfacing
  `latency_ms` and `output_len` per `ToolCallTrace` rather than
  computing them at harness scoring time means the harness
  doesn't need to re-execute tools or hash outputs to know
  "which tool dominated this query's cost." Keeping the
  existing `output` field alongside (rather than dropping it
  for `output_len` only) costs trace-size bytes but pays back
  on every debugging session — at this build's record volume
  (tens per eval run) the full output is genuinely useful for
  spot-checking, and the additive policy lets a future
  iteration drop `output` (which would be a v2 bump) without
  rewriting the slice-5 shape today.

The `requested_model` field also appears at the top level of
the payload, separate from `model` (which is the SDK response's
model id, `null` on dry-run). The harness can read either; the
record_id is computed against `requested_model` so it stays
stable across SDK version-pin changes.
