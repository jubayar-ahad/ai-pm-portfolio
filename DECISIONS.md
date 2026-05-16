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

## 2026-05-16 — evals-harness stack, CLI shape, and slice plan (README first)

**Decision:** The `evals-harness/` build is Python 3.9+ (matching the
other two builds) and **stdlib-only** — no third-party dependencies,
no `requirements.txt`, no `ANTHROPIC_API_KEY` needed at any point.
The harness scores trace records that the two prior builds already
emit via their `ask --json` outputs (`rag-app.ask.v1` and
`tool-use-agent.ask.v1`); it deliberately performs **no model calls
of its own**. The CLI is a three-subcommand entry point:
`python -m evals_harness {ingest,score,report}`. Inputs are
JSONL trace files and a single labeled-query JSONL file
(`evals-harness/queries.jsonl`, hand-authored — the agent does not
generate ground-truth labels). Outputs are a normalized
`ingested.jsonl`, a per-record `scored.jsonl` (one row per
`(record_id, rubric)`), and a Markdown aggregate report. Trace
routing is by `schema_version` prefix; unknown versions raise
rather than fall back to the closest known version.

The build is shipped README-first, mirroring the `rag-app/` and
`tool-use-agent/` patterns. Subsequent iterations land:
1. **Labeled query set scaffold** (`queries.jsonl`) — ~10–20 hand-
   authored labeled queries spanning four shapes (in-corpus /
   answerable, out-of-corpus / refuse-expected, tracker-rollup,
   adversarial-stopword-overlap). Per-query schema locked in
   DECISIONS the iteration it ships.
2. **Ingester + startup invariant checks** — parses every JSONL
   line, validates `schema_version`, asserts the two cross-build
   invariants below, emits `ingested.jsonl` + counts summary.
3. **Refusal-bucket scorer (cross-build)** — single equality check
   on `REFUSAL_SENTENCE` (plus `reason: low_retrieval_score` for
   the rag-app short-circuit path); emits a confusion matrix per
   build and per-record scored rows.
4. **Groundedness + first-call-tool scorers (per-build)** —
   rag-app groundedness reads the trace's `verification` block;
   tool-use first-call accuracy reads `tool_calls[0].tool` against
   the label's `expected_first_tool`. Each emits scored rows
   tagged with their rubric name.
5. **Termination + cost scorers, aggregate Markdown report** —
   rolls up `refusal_reason` distribution and token/cost p50/p95
   per build into a single Markdown table; flags
   `corpus_fingerprint` diversity per build as an explicit
   warning row rather than silently averaging across mismatched
   corpora.

**Two cross-build invariants asserted at startup, not at score
time, by the harness:**
1. `rag-app/rag_app/verify.py::REFUSAL_SENTENCE` is byte-equal
   to `tool-use-agent/tool_use_agent/verify.py::REFUSAL_SENTENCE`.
2. Trace-helper behavior equivalence: hashing a fixed sample
   payload through each build's `compute_record_id` /
   `compute_corpus_fingerprint` produces the truncated-16-hex
   digest the harness has pre-computed against the agreed
   algorithm (canonical-JSON-with-`sort_keys=True` → SHA-256 →
   first 16 hex chars). This is the equivalent contract to the
   prior REFUSAL_SENTENCE equality, applied to the helpers
   instead of the string.

**Rationale.** Five reinforcing properties.

- **No model calls means deterministic re-runs.** Every rubric
  is a function of trace fields already emitted by the builds.
  Re-running the harness against the same trace + label inputs
  always produces byte-identical scored output, which is the
  property that makes "did this iteration regress?" a one-diff
  question. Model-graded scoring (an LLM evaluating the LLM)
  is a real next quality knob and a real cost — it
  re-introduces the API-key dependency, the judge-variance
  question, and the judge-prompt-drift question — and is
  deliberately deferred. The v1 harness establishes the
  baseline; model-graded scoring is the iteration that improves
  on it, not the iteration that defines it.
- **Stdlib-only matches the rest of the repo.** The two builds
  each have exactly one third-party dep (the Anthropic SDK,
  needed only for live `ask`). The harness needs none. Keeping
  the dependency surface flat across all three builds is what
  makes the "interviewer clones the repo, runs each demo
  end-to-end" path realistic without a setup readme that grows
  per build.
- **Single labeled file is the property that makes cross-build
  comparison legible.** If the rag-app and the tool-use agent
  each had their own labeled set, "which one is more grounded?"
  would always carry an asterisk. Forcing one
  `queries.jsonl` with per-build expectation fields keeps the
  comparison honest at the cost of slightly more verbose
  labels — the right tradeoff for an interview leave-behind
  whose whole purpose is the comparison.
- **Schema-version routing prevents silent miscompare.** A
  trace from a hypothetical future `rag-app.ask.v2` should not
  be scored by the v1 rubric — fields may have moved, semantics
  may have changed. Matching `schema_version` exactly and
  raising on unknown versions is the cheapest possible
  forward-compat insurance and a direct application of the
  additive-fields-keep-version policy locked in both builds'
  slice-5 entries.
- **Startup invariants are the smallest harness-side defense
  against cross-build drift.** Both prior builds were
  deliberately designed to define `REFUSAL_SENTENCE` and the
  trace helpers *independently* — each build is self-contained
  — and to rely on a startup-asserted byte/behavior equivalence
  for the cross-build guarantee. The harness is the natural
  place to assert it: it is the only artifact that reads
  records from both builds, and it is the artifact whose
  metrics would silently skew if either drifted. Two ~3-line
  fixtures and one string-equality check are enough; a full
  helper test suite inside the harness would duplicate work
  each build's own unit tests already cover.

**Out of scope for this build** (named here so the next four
iterations don't drift): model-graded scoring (re-introduces
key dependency and judge variance), labeled-set authoring tools
(`queries.jsonl` is hand-edited at the start, with a future
`seed` subcommand left as a candidate), regression dashboards
or run-history persistence (Markdown snapshot is the artifact),
latency benchmarking (the harness reads the `latency_ms` the
agent already emits and does not re-time anything), and fine-
tuning loops (eval scoring describes behavior; it does not
change weights or prompts). Each of these would be a separate
build, not a slice of this one.

## 2026-05-16 — evals-harness slice 1: `queries.jsonl` schema and labeled set

Slice 1 of the evals-harness build ships
`evals-harness/queries.jsonl` — a single, hand-authored,
uniform-shape JSONL file containing 16 labeled queries. The
schema is locked here so subsequent slices (ingester, per-rubric
scorers, report) can rely on the fields without re-litigating
shape or vocabulary.

**Record shape (every line, all keys present, optional values
nullable):**

- `id` (string, required) — stable identifier `q-NNN`. Used by
  the harness for cross-run identity and for naming records in
  the report.
- `question` (string, required) — the prompt fed to both
  builds' `ask` subcommand.
- `shape` (enum, required) — one of `in_corpus`,
  `out_of_corpus`, `tracker_rollup`, `adversarial_in_corpus`.
  Mirrors the four-shape spread named in the evals-harness
  README slice-1 roadmap and gives the report a stable
  grouping axis.
- `expected_outcome` (enum, required) — `answer` | `refuse`.
  This is what the refusal-bucket scorer (slice 3) joins
  against the trace.
- `applies_to` (array of schema_version strings, required) —
  subset of `{"rag-app.ask.v1", "tool-use-agent.ask.v1"}`. A
  query that exercises tool-side rollups lists only
  `tool-use-agent.ask.v1`; a query that exercises retrieval
  groundedness can list both. The harness's per-build router
  intersects this list with each trace's `schema_version`.
- `expected_citation_source` (string | null, optional) —
  set only when `applies_to` includes `rag-app.ask.v1` and a
  specific in-corpus file should appear in at least one
  citation of an answered response. Consumed by the
  groundedness scorer.
- `expected_first_tool` (string | null, optional) — set only
  when `applies_to` includes `tool-use-agent.ask.v1` and the
  first tool call has an obvious right answer. Consumed by
  the first-call-tool scorer.
- `corpus_fingerprint_at_label` (object, required, possibly
  empty) — map keyed by each `applies_to` schema string, with
  the 16-hex-char fingerprint that was current when the label
  was authored. Surfaces stale labels as per-record warnings
  rather than silent miscount when the corpus or catalog
  evolves under the labeled file.
- `notes` (string | null, optional) — author-only rationale
  for the expected outcome; never read by any scorer.

**Slice-1 counts** (this iteration ships exactly these): 6
`in_corpus`, 4 `out_of_corpus`, 3 `tracker_rollup`, 3
`adversarial_in_corpus`. 9 records with `expected_outcome:
answer`, 7 with `expected_outcome: refuse`. The mix is
deliberately weighted toward `answer` so the groundedness
rubric has a non-trivial denominator while still giving the
refusal scorer enough negative examples to detect a build
that over-refuses.

**Rationale (why each property is locked here):**

- **Uniform record shape with explicit nulls** beats
  "optional fields may be omitted." With nullable keys
  always present, the ingester's per-record validation is a
  single key-set equality check and an interviewer reading
  the file can see at a glance which expectations a query
  carries and which it deliberately doesn't. The cost
  (slightly bigger lines) is paid back the first time a
  reviewer needs to scan the file by eye.
- **`shape` is a label, not a derived field.** The harness
  could infer shape from `expected_outcome` and the presence
  of `expected_first_tool`, but doing so would couple the
  classification to the per-build expectation fields, which
  is exactly the coupling the four-shape framing exists to
  break. Tagging shape at authoring time also gives the
  report a stable grouping axis even if the per-build
  expectation policy evolves.
- **`applies_to` is required and explicit, not derived.**
  A `tracker_rollup` query is meaningless to score against
  rag-app; a corpus-citation query is meaningless to score
  against tool-use-agent. Encoding this as an explicit list
  (rather than inferring "if the expected_first_tool is set,
  it's a tool-use query") means the harness can refuse to
  score a trace whose schema is not in `applies_to`, which is
  a cleaner failure mode than producing a meaningless score.
- **`corpus_fingerprint_at_label` keys by schema_version**
  because each build has its own analog of "corpus": rag-app
  hashes its chunks file, tool-use-agent hashes its catalog.
  The harness checks each trace's fingerprint against the
  matching key — mismatch is a warning, not a hard fail, so
  label drift is visible in the report without breaking the
  run. Concrete fingerprint values are not quoted in this
  entry because DECISIONS.md is itself part of the rag-app
  corpus: writing the rag-app fingerprint here would mutate
  the corpus and immediately invalidate the quoted value
  (self-reference). The current values live in
  `evals-harness/queries.jsonl`, which is *not* part of any
  build's corpus or catalog, so it can hold the literal
  hashes without recursion.
- **JSONL not JSON-array** so the ingester can stream
  records and so a future `evals_harness seed` subcommand can
  append candidate labels without rewriting the whole file.
  Matches the JSONL shape both builds already use for their
  trace records and `chunks.jsonl` — one fewer format to
  introduce.
- **Adversarial-in-corpus queries are required to have
  `expected_outcome: refuse`** but are recorded as a separate
  shape from plain `out_of_corpus` because they share corpus
  tokens with the real answer set. The refusal-bucket scorer
  treats both as the same expected outcome, but the report
  groups them separately so a PM can read "the rag-app
  refused 4/4 out-of-corpus but only 1/3 adversarial" — that
  distinction is the calibration signal the iteration-7
  notes named when MIN_RETRIEVAL_SCORE was first locked.
- **In-corpus / answerable queries cite the source file by
  path string** (e.g. `"OBJECTIVE.md"`), not by `record_id`
  of a specific chunk. The chunker may re-pack the corpus on
  any iteration that edits a corpus file, which would
  invalidate any chunk-id-level expectation; the source path
  is stable across re-chunking. The groundedness scorer
  reads `verification.citations[*].source` and checks for
  string membership.
- **`notes` is for the author, not the harness.** Lock it as
  never-read so the harness has no incentive to start parsing
  prose. The same property holds today for the rag-app's
  trace records (the `prompt` field is preserved but no
  scorer keys on its contents).

**Forward link to slice 2:** the ingester (slice 2) loads
this file by streaming `json.loads` per line, validates the
key set and enum values against this lock, and pairs each
labeled record with traces by `question`. The slice-2
DECISIONS entry will lock the pairing key (question-string
equality vs. record_id resolution); slice 1 does not commit
to that decision because the cross-build pairing requires
two different `record_id` schemas and is properly the
ingester's concern.

## 2026-05-16 — evals-harness slice 2: ingester contract + startup invariants

Slice 2 ships `python -m evals_harness ingest` plus the two
cross-build startup invariants the README pre-committed to.
Four contract pieces locked here so the slice-3 refusal
scorer (and every subsequent rubric) can rely on them.

**1. Ingester I/O contract.**

- `--labels <path>` (required, exactly one JSONL file) loads
  records from the slice-1 schema. Validation rejects any
  record whose key set is not exactly the locked 9-key set,
  whose `shape` is not in
  `{in_corpus, out_of_corpus, tracker_rollup, adversarial_in_corpus}`,
  whose `expected_outcome` is not in `{answer, refuse}`,
  whose `applies_to` is empty / contains an unknown schema,
  or whose `corpus_fingerprint_at_label` key set does not
  equal `applies_to`. Each failure raises `IngestError`
  pointing at `<path>:<lineno>` and exits with code 2.
- `--traces <path...>` (zero or more JSONL files) loads ask
  --json records. Each record must carry a `schema_version`
  in `{rag-app.ask.v1, tool-use-agent.ask.v1}` and the three
  cross-cuttable fields `{record_id, corpus_fingerprint,
  question}`. Per-build fields (`verification` on rag-app,
  `refusal_reason` / `tool_calls` on tool-use-agent) are
  *not* required at ingest because each future scorer routes
  by `schema_version` and validates its own per-build
  surface. Unknown schemas raise rather than being treated
  as the closest known version.
- `--out <path>` (optional) emits a normalized
  `ingested.jsonl` wrapping each input line in a
  `{"kind": "label"|"trace", ...envelope, "record": <orig>}`
  envelope. The slice-3 scorer reads this rather than
  re-validating, so re-running scoring without re-ingesting
  is well-defined.
- Zero traces is explicitly allowed (`--traces` defaults to
  `[]`) so a user can iterate on labels before any traces
  exist. The invariants still run and the counts summary
  still prints, which keeps the harness usable from day one.

**2. Startup invariants.**

Two checks run before any record is validated, so a schema
bug cannot mask a cross-build drift:

- **`REFUSAL_SENTENCE` byte-equality.** Imports
  `rag_app.verify.REFUSAL_SENTENCE` and
  `tool_use_agent.verify.REFUSAL_SENTENCE`, asserts string
  equality. Drift raises `InvariantError` naming both
  string repr()s. This is the single line that protects the
  slice-3 refusal-bucket scorer from splitting one logical
  bucket into two when one build's canonical refusal text
  silently changes.
- **Trace-helper algorithm equivalence.** For each build,
  the harness computes the *expected* digest independently
  in `evals_harness/invariants.py` (SHA-256 of canonical
  JSON bytes / raw bytes, truncated to 16 hex chars) over
  a fixture, then asserts each build's
  `compute_corpus_fingerprint` and `compute_record_id`
  reproduce it. Signatures differ across the two builds
  (rag-app takes a chunks file path; tool-use takes a
  catalog list) so this asserts *algorithm* equivalence,
  not signature equivalence, matching the iteration-15
  rationale. A drift in hash algorithm, truncation length,
  or canonical-JSON ordering in either build raises with
  the build name and the diverged digests.

Both invariants run in milliseconds, never hit the network,
and never load corpus data. The output of `ingest --verbose`
prints one `ok: <name> (<detail>)` line per passed check.

**3. Sibling-build import policy.**

The harness imports
`{rag_app,tool_use_agent}.{verify,trace}` by adding
`<repo>/rag-app/` and `<repo>/tool-use-agent/` to
`sys.path` at module load time (`evals_harness/_repo.py`).
This is the *harness's* responsibility, not the builds'.
The iteration-14 lock that each build remains
self-contained (no cross-imports between rag-app and
tool-use-agent) is unchanged — the harness is the third
party that imports both. Repo root is auto-discovered by
walking up from `_repo.py` until `OBJECTIVE.md` is found,
mirroring the rag-app loader's pattern so `cd evals-harness
&& python3 -m evals_harness` works without
`PYTHONPATH` munging.

**4. Normalized `ingested.jsonl` envelope.**

Each output line is one of:

```jsonl
{"kind":"label","id":"q-NNN","applies_to":[...],"record":{...orig label...}}
{"kind":"trace","schema_version":"rag-app.ask.v1","record_id":"...","trace":{...orig trace...}}
```

The envelope pulls the routing fields to the top level so
the slice-3 scorer can route on `kind` and
`schema_version` without parsing each `record` body, while
preserving the original record verbatim under `record` so
no information is lost between ingest and scoring. The
ordering inside the file is `labels first, then traces, in
input order` — deterministic given the inputs, which is
the property the README's deterministic-output guarantee
already promised.

**Rationale (why this shape, not some other):**

- **Invariants before validation, not after.** If we
  validated record schemas first, a schema bug in
  `queries.jsonl` would short-circuit the invariant
  checks, and a silent cross-build drift could persist
  through several iterations of label edits before being
  caught. Putting the invariants first means the
  one-line summary "2 invariant checks passed" is the
  first signal a developer sees on every run, so drift is
  caught the iteration it lands.
- **Fail-fast with exit code 2, not a warning.** The
  rag-app and tool-use-agent CLIs both use exit code 2
  for unrecoverable errors; matching that here means a CI
  caller can treat any non-zero exit as "stop the
  pipeline" without parsing stderr. A warnings-only mode
  is not in v1: a drifted refusal sentence or unknown
  schema is a category of bug worth blocking on, not a
  category of bug worth proceeding past.
- **Pairing key deferred to slice 3, not locked here.**
  Slice 1's DECISIONS entry forward-linked this slice's
  decision on the label↔trace pairing key. Slice 2's
  ingester does *not* commit to it because pairing is
  the refusal scorer's job: it knows whether to join by
  question-string equality (cross-build) or by an
  `(applies_to, question)` tuple (per-build). Slice 2
  preserves both `question` and `record_id` in the
  envelope so slice 3 has full optionality.
- **Importing each build's `verify`/`trace` modules is
  the only way to assert byte/algorithm equivalence.**
  Re-implementing the constants and helpers inside the
  harness would let the harness drift while the builds
  stay aligned, which is the opposite of the property
  the invariants exist to assert. The sys.path nudge in
  `_repo.py` is the cheap way to keep the harness
  stdlib-only (no `pip install -e .`) while still
  importing the real source of truth from each build.

**Out of scope for slice 2** (explicit, so slice 3 cannot
silently inherit them): scoring of any kind, refusal
bucketing, fingerprint-mismatch warnings (those land in
the report slice), per-record validation of per-build
fields like `verification.citations` or `tool_calls`,
and any kind of LLM call. The harness remains stdlib-only.

## 2026-05-16 — evals-harness slice 3: refusal-bucket scorer

Slice 3 ships `python -m evals_harness score --rubric
refusal` — the smallest cross-build comparison the harness
can produce, and the one that directly exercises the
canonical-refusal-string invariant locked in the prior
builds' slice 4. Five contract pieces locked here so
slices 4 and 5 can build on them without re-litigation.

**1. Input: normalized envelope only.**

The scorer takes `--ingested <path>` (the
`ingested.jsonl` produced by `ingest --out`). It does not
re-accept `--labels` and `--traces` directly; the slice-2
DECISIONS entry already named the envelope as the
canonical scorer input, and supporting two input paths
would silently bifurcate the validation surface (label
schema checks live in `ingest`, not `score`). A user who
hasn't run `ingest --out` first gets a clear "file not
found" rather than a different validation error.

**2. Startup invariants re-run before scoring.**

`cmd_score` calls `run_startup_invariants()` before
opening the envelope. Slice 2 already ran them at ingest
time, but a `REFUSAL_SENTENCE` drift introduced between
the ingest and score commands (e.g. an editor save in
either build's `verify.py` between the two CLI calls)
would silently split one refusal bucket into two. Running
the invariants again is cheap (milliseconds) and is the
single line that protects this rubric from drift.

**3. Pairing key: (question, schema_version ∈ applies_to).**

The label↔trace pairing slice 2 deferred lands here:
the natural cross-build identity is the question string,
because labels carry one question that may apply to one
or both builds via `applies_to`. The scorer joins by
exact `trace.question == label.question` AND
`trace.schema_version ∈ label.applies_to`. A trace whose
question never appears in any label counts as
`unpaired_trace`; a label whose question never appears in
any trace counts as `unpaired_label`. Counts appear in
the report header as diagnostic signal; neither path
raises.

`record_id` was the alternative pairing key. Rejected:
each build computes `record_id` from a per-build logical
tuple that includes that build's own corpus_fingerprint,
so two builds running the same labeled question produce
two different `record_id`s. Joining by question lets the
same label compare both builds' behavior in one row of
the confusion matrix, which is the property that
motivated the harness in the first place.

**4. Build-specific observed-outcome classifiers.**

The README claims `final_text == REFUSAL_SENTENCE` as
the cross-build refusal detector. In practice the two
builds expose the signal slightly differently:

- **rag-app.** Observed = `refuse` iff
  `mode == "refused-low-score"` (threshold-bypass; no
  model call) OR `mode == "live"` AND
  `answer.text.strip() == REFUSAL_SENTENCE`. Observed =
  `answer` iff `mode == "live"` AND
  `answer.text.strip() != REFUSAL_SENTENCE`. Observed =
  `no_observation` for every other mode (notably
  `dry-run`, where `answer` is None).
- **tool-use-agent.** Observed = `refuse` iff
  `mode == "live"` AND
  `final_text.strip() == REFUSAL_SENTENCE`. The
  classifier additionally cross-checks
  `refusal_reason is not None`; a divergence between the
  text-equality and the reason-set signals raises
  `ScoreError` because it would indicate a build bug the
  slice-2 invariants did not anticipate. Observed =
  `no_observation` for `dry-run` (where `final_text` is
  empty).

The two detectors are not symmetrical because the trace
shapes are not symmetrical: rag-app carries refusal as a
`{text, reason}` block while tool-use-agent carries it
as `final_text` plus an enum `refusal_reason`. The
strict-strip byte-equality with `REFUSAL_SENTENCE`
imported from each build's own `verify.py` is the
property that lets the same scorer treat all five
canonical-refusal paths (rag-app threshold-bypass, rag-app
model-refused, tua model-refused, tua max_steps_exhausted,
tua repeated_tool_error) as one logical bucket.

**5. Output shapes.**

- **Per-record JSONL** (`--out <path>`, optional). Each
  line is one (record_id, rubric) row with keys
  `{rubric, record_id, schema_version, question,
  label_id, expected_outcome, observed_outcome, mode,
  match}`. Rows are sorted by
  `(schema_version, record_id, label_id)` so the file
  diffs cleanly across re-runs.
- **Markdown table** (always to stdout, optionally
  duplicated to `--markdown <path>`). One row per
  `(build, expected_outcome)` cell plus an
  `**overall**` row per build with
  `correct/observable (pct%)` accuracy. The header line
  carries `labels=N  traces=N  scored_rows=N
  unpaired_traces=N  unpaired_labels=N` so the diagnostic
  counts cannot get lost when the table is pasted into a
  recruiter email.

`no_observation` rows (currently: dry-run traces) are
counted in the matrix but excluded from the
`correct/observable` accuracy denominator. This is the
single decision that keeps the accuracy column
reproducible regardless of how many dry-run records
happen to appear in the input — dry-runs are a
diagnostic artifact, not a behavioral signal.

**Rationale (why this shape, not some other):**

- **One row per (label, trace) pair, not one row per
  label.** A single labeled question can have multiple
  traces in the envelope (e.g. one rag-app live run plus
  one rag-app dry-run plus one tool-use-agent live run);
  each trace is its own behavioral observation and earns
  its own row. Collapsing to one-per-label would force
  the scorer to vote across runs, which would (a) hide
  variance and (b) be ambiguous when traces disagree.
- **Disagreement is an error, not a warning.** The
  text-equality vs. refusal_reason cross-check on
  tool-use-agent could have been a soft warning, but a
  divergence means one of the two signals is lying about
  what happened — there is no safe interpretation. The
  strict raise forces the bug to surface in the iteration
  that introduced it, with the offending `record_id` in
  the error message.
- **Cross-build alignment uses each build's own
  REFUSAL_SENTENCE, not a harness copy.** The classifier
  imports `REFUSAL_SENTENCE` directly from
  `rag_app.verify` and `tool_use_agent.verify`. If the
  harness owned a copy, a drift could land that left both
  builds aligned with each other and out of sync with the
  harness — silently miscounting every refusal. Importing
  the actual constants is the only way to make the
  startup-invariants assertion load-bearing rather than
  ceremonial.

**Out of scope for slice 3** (explicit, so slice 4 and 5
cannot silently inherit them): groundedness scoring
(citations resolved/unresolved — slice 4 reads the
`verification` block), first-call tool accuracy (slice 4
reads `tool_calls[0]`), termination-quality buckets and
token/cost percentiles (slice 5), `corpus_fingerprint`
diversity warnings (slice 5), and report aggregation
across rubrics (slice 5 reads the scored JSONL). The
harness remains stdlib-only, performs no LLM calls, and
holds no state across runs.
