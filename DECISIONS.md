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

## 2026-05-16 — evals-harness slice 4 (groundedness + first-call tool)

**Decision:** `python -m evals_harness score --rubric
{groundedness,first_call_tool}` ships as two per-build
rubrics dispatched through the same `score` subcommand
that slice 3 wired. Four pieces of the contract are
locked here:

1. **Eligibility filters are rubric-specific, not
   trace-wide.** Groundedness applies only to
   (label.expected_outcome == "answer") paired with
   rag-app traces (`schema_version == "rag-app.ask.v1"`).
   First-call tool applies only to
   (label.expected_first_tool != null) paired with
   tool-use-agent traces. Labels that don't satisfy the
   rubric's applicability filter are excluded from
   `applicable_labels` so unpaired counts stay honest
   (a refuse-labeled query is not "unpaired" from the
   groundedness rubric — it's outside its scope).
2. **Groundedness match condition is two-pronged.** A row
   matches iff `verification.all_resolved == true` AND
   (when the label carries a non-null
   `expected_citation_source`) at least one *resolved*
   citation has that source. The second prong catches
   "all citations resolved but the model cited a
   different valid corpus chunk than the one the label
   pinned" — a real failure mode that pure
   `all_resolved` would miss.
3. **`no_observation` is excluded from accuracy, mirroring
   slice 3.** A rag-app trace with `verification == null`
   (refused-low-score, dry-run, or otherwise no answer
   to verify) classifies as `no_observation` and is
   counted in the per-build row's `no_observation`
   column, but is excluded from the accuracy denominator.
   Same shape for first-call tool when `tool_calls` is
   empty. A reader can add more dry-runs to the input
   without moving any accuracy percentage.
4. **Per-rubric scored JSONL schemas are distinct but
   share the cross-rubric core (`rubric`, `record_id`,
   `schema_version`, `question`, `label_id`, `match`).**
   Groundedness rows add `citations_total`,
   `citations_resolved`, `all_resolved`,
   `expected_citation_source`, `expected_source_cited`,
   `observed_outcome`. First-call tool rows add
   `expected_first_tool`, `observed_first_tool`,
   `observed_outcome`. The slice-5 report aggregator
   can read all three rubrics' JSONL outputs and group
   by `rubric` without per-rubric special cases on the
   shared columns.

**Rationale (why this shape, not some other):**

- **Two rubrics in one slice, not two iterations.** The
  README's roadmap pre-committed slice 4 as the bundled
  per-build pair. They share the envelope reader, the
  question-string + schema-prefix join key from slice 3,
  the `no_observation` exclusion pattern, and the
  per-record JSONL output shape — splitting them across
  iterations would duplicate four shared design
  decisions for no extra signal. Shipping them together
  keeps the "one complete artifact per iteration" rule
  intact because the artifact is "per-build rubrics."
- **Same `score` subcommand, three rubric choices.** A
  separate `score_per_build` subcommand would have made
  slice-5's aggregate report a sub-flag of yet a third
  subcommand. One `--rubric` dimension covers all
  current and future single-rubric runs; slice 5's
  `report` subcommand reads JSONL files produced by
  any rubric, so the CLI surface stays small.
- **`expected_citation_source` in the match condition
  (vs. only `all_resolved`).** The label set already
  carries the pinned source for 6 of the 9
  answer-expected queries; not using it would leave that
  field as documentation rather than signal. The
  expected-source-cited check is the cheapest possible
  use of that pin and surfaces a real "right form,
  wrong evidence" failure mode.
- **Empty `tool_calls` is `no_observation`, not
  `mismatch`.** A model that refused / answered without
  tools / dry-ran did not *attempt* a tool call — there
  is no first call to be right or wrong about. Counting
  it as `mismatch` would mix "the agent picked the
  wrong tool" with "the agent declined to use any
  tool," and the first-call rubric's purpose is
  unambiguously the first.
- **Sorted JSONL output, same key as slice 3.** Output
  rows are sorted by `(schema_version, record_id,
  label_id)` so two runs over the same envelope produce
  byte-identical scored JSONL — the determinism
  property the harness's reproducibility-without-API
  story rests on.

**Validated against synthetic + real envelope data:** a
7-label / 7-trace synthetic envelope exercises grounded
+ not_grounded (`all_resolved=false`) + not_grounded
(`expected_source` not cited) + no_observation
(refused-low-score) for groundedness; match + mismatch
+ no_observation (empty `tool_calls`) for first-call
tool. Unpaired-trace counter increments on an extra
trace with no matching label. The slice-2/3
REFUSAL_SENTENCE byte-equality and trace-helper
algorithm invariants still pass; the refusal rubric
still produces its iteration-18 confusion matrix
unchanged.

**Out of scope for slice 4** (so slice 5 cannot silently
inherit them): termination-quality scoring over
`refusal_reason` distributions, token/latency
percentiles, `corpus_fingerprint` diversity warnings,
and the aggregate Markdown report that joins all four
rubrics. Each rubric in slice 4 writes its own scored
JSONL; slice 5 reads them and rolls them up.


## 2026-05-16 — evals-harness slice 5a (termination quality scorer)

The fifth and final evals-harness slice is split into two
shipping units. Slice 5a is the **termination quality**
rubric, a per-record scorer that mirrors the slice-3
refusal and slice-4 first-call patterns in shape. Slice
5b will ship the **cost** rubric (an aggregate, not a
per-record match/mismatch) and the **report**
subcommand that rolls every rubric's scored JSONL into a
single Markdown report. Splitting honors the
"one complete artifact per iteration" rule: termination
is a self-contained per-record scorer with its own
locked output schema, while cost + report together are
the cross-rubric aggregate layer.

**Termination rubric contract:**

- **Applies to** `(label.expected_outcome == "answer")`
  paired with `tool-use-agent.ask.v1` traces. Refuse-
  labels stay in the refusal rubric (slice 3); rag-app
  traces have no `refusal_reason` field so they are out
  of scope. Mirrors the eligibility-filter pattern from
  groundedness (rag-app-only) and first-call tool (tua-
  only).
- **Five observed buckets**, with `ended_clean` as the
  only success state:
  - `ended_clean` — `stop_reason=end_turn` AND
    `refusal_reason=null`. The agent answered cleanly
    within the step cap.
  - `model_refused` — `refusal_reason="model_refused"`.
    The model emitted the canonical refusal sentence
    when the label expected an answer; this is a
    refusal-rate-vs-termination crossover and is
    counted here so a PM can read "the agent refused
    when it shouldn't have" as a termination failure
    without also re-bucketing it in the refusal rubric.
  - `max_steps_exhausted` — the agent ran out of steps.
    A cost-bound signal, distinct from the model
    refusing.
  - `repeated_tool_error` — the agent hit the same
    `(tool, input)` error in two consecutive steps and
    bailed (slice-4 contract).
  - `no_observation` — dry-run / non-live traces
    (`mode != "live"`); excluded from the accuracy
    denominator, same shape as slices 3 and 4.
- **Accuracy denominator** = total scored rows minus
  `no_observation`. Reported as `ended_clean / observable`
  with the percent. Matches the slice-3 and slice-4
  shape so the slice-5b report can sum across rubrics
  without per-rubric special cases.
- **`refusal_reason` is authoritative**, not `stop_reason`.
  The slice-4 contract has the two signals agreeing
  deterministically (`refusal_reason` is set iff the
  loop exited via a refusal-bucket path). The scorer
  reads `refusal_reason` first and maps it to the
  bucket; an unknown enum value raises `ScoreError`. A
  live trace with `refusal_reason=null` but a non-
  `end_turn` `stop_reason` is treated as a build
  contract violation and raises — same strict
  cross-check pattern slice 3 used for tool-use-agent
  `final_text` vs `refusal_reason`.
- **Output schema** — per-record JSONL with the cross-
  rubric core columns (`rubric`, `record_id`,
  `schema_version`, `question`, `label_id`, `match`)
  plus the per-rubric extras (`stop_reason`,
  `refusal_reason`, `steps_taken`, `max_steps`,
  `observed_outcome`). The extras let the slice-5b
  report compute the "% of failures at cap vs. retry vs.
  model-refusal" breakdown without re-parsing traces.
- **Sorted by `(schema_version, record_id, label_id)`**,
  the same key slices 3 and 4 use, so two runs over the
  same envelope produce byte-identical scored JSONL.

**Design choices worth naming for the interview leave-behind:**

- **Five buckets, not three.** Collapsing
  `max_steps_exhausted` / `repeated_tool_error` /
  `model_refused` into a single "failed termination"
  bucket would have made the rubric easier to render but
  thrown away the very signals a PM cares about — "the
  agent timed out 12% of the time" vs "the agent
  declined to retry 3% of the time" are different
  product conversations. The slice-4 `refusal_reason`
  enum already paid the cost of distinguishing these;
  the scorer just preserves it.
- **`model_refused` is a termination failure here, not a
  refusal success.** When the label expects `answer`
  and the model emits `REFUSAL_SENTENCE`, the refusal
  rubric records it as `observed=refuse, expected=answer
  → mismatch`, and the termination rubric records it
  as `model_refused` (an `ended_clean=false` bucket).
  These are two correct readings of the same trace, one
  per rubric, and they should be reported in parallel
  rather than merged.
- **Build-contract violations raise, not warn.** A live
  trace with `refusal_reason=null` and a non-`end_turn`
  `stop_reason` is a slice-4 invariant break; treating
  it as a soft warning would let the bug ride into the
  scored JSONL and silently miscount terminations.
  Same posture as slice 3's tool-use-agent
  `final_text`-vs-`refusal_reason` cross-check.

**Validated against synthetic envelope data:** 5
tool-use-agent traces covering each of the five buckets
(ended_clean, model_refused, max_steps_exhausted,
repeated_tool_error, dry-run no_observation) plus one
refuse-label trace that the eligibility filter correctly
excluded; accuracy reported as `1/4 (25.0%)`; non-clean
rows listed individually with `steps_taken/max_steps`.
Two unit-shaped checks exercise the build-contract
raises (null refusal_reason + non-end_turn stop_reason
and an unknown refusal_reason enum value). Slice-3 and
slice-4 rubrics still produce their iteration-18 and
iteration-19 outputs unchanged.

**Out of scope for slice 5a** (so slice 5b cannot
silently inherit them or treat them as already shipped):
the **cost rubric** (`input_tokens + output_tokens`
p50/p95/max per build, plus tool-use-agent
`steps_taken` p50/p95 and summed per-call
`latency_ms`), the **report subcommand**
(`python -m evals_harness report --scored <path>`) that
joins every rubric's scored JSONL into one Markdown
document, and the **`corpus_fingerprint` diversity
warning** that flags when more than one fingerprint
appears for a single build. Slice 5a ships the
per-record scorer; slice 5b ships the cross-rubric
aggregate.

## 2026-05-16 — evals-harness slice 5b (cost rubric)

**Decision:** `python -m evals_harness score --rubric
cost --ingested <path>` ships now as the cross-build
cost rubric. It runs the slice-2 startup invariants,
reads the normalized envelope, joins every trace to the
labels carrying that trace's `question` plus
`schema_version ∈ applies_to` (same key as slices 3–5a),
and emits two surfaces: a per-record JSONL with the
cross-rubric core columns (`rubric`, `record_id`,
`schema_version`, `question`, `label_id`, `match`) plus
six cost extras (`input_tokens`, `output_tokens`,
`total_tokens`, `steps_taken`, `max_steps`,
`tool_latency_ms_sum`), and a per-build Markdown
aggregate of `total_tokens` p50/p95/max for both builds
followed by a tool-use-agent-only second table for
`steps_taken` and `tool_latency_ms_sum` p50/p95/max.
Live traces classify as `observed`; dry-run /
`refused-low-score` / any non-`live` mode classifies as
`no_observation` and is excluded from every stats
denominator. The aggregate `report` subcommand is the
remaining slice and is **deliberately not in 5b**.

**Why split slice 5 into 5a (termination) and 5b
(cost):** the slice-5a iteration-20 learning was that
per-record match/mismatch rubrics (refusal,
groundedness, first-call, termination) and aggregate
stats rubrics (cost) have fundamentally different
output shapes — match rows vs. percentile rows — and
forcing them into one iteration would have either
bloated the slice or quietly skipped the per-build
latency split. Slice 5a kept the per-record shape
clean and slice 5b now adds the aggregate shape
without compromising either.

**Why the cost rubric does not filter by
`expected_outcome`:** the cost rubric scores **what was
spent**, not **whether the answer was correct**. A
live trace that ended in `refusal_reason=model_refused`
still consumed tokens — the model emitted text and
chose to refuse, which has a real cost — so the
`expected_outcome=refuse` labels are eligible. The
refusal rubric is the right home for the
correct/incorrect-refusal signal; the cost rubric
records the dollars-and-cents impact independently.
Confined to live mode, this collapses to "every
billable interaction shows up in the stats."

**Why live tool-use-agent refusals contribute zero to
`steps_taken` and `tool_latency_ms_sum`:** when the
model refuses on turn 1 (no tools called) the
`steps_taken=0` and per-call latency sum is 0 by
definition. Counting these in the p50/p95 calculation
is correct — they are a real cost surface (slow first
turn, no useful work) — and is what makes the stats
table honest about the agent's *actual* per-question
behavior rather than its idealized successful-path
behavior. The alternative (excluding refusals from
the steps/latency stats) would inflate the medians
toward the agent's best case and hide refusal-as-cost
from the PM read.

**Per-record JSONL schema is additive, not a v2 bump:**
the six cost fields are *additional* per-row columns
on the cross-rubric core shape, identical in pattern
to slice 4's `citations_total` / slice 5a's
`stop_reason`. The slice-7 report aggregator can read
every rubric's scored JSONL through the same
cross-rubric core (`rubric`, `record_id`,
`schema_version`, `question`, `label_id`, `match`) and
ignore the per-rubric extras. No rubric requires a
`scored.v2` schema bump.

**Stats convention locked:** the harness computes
percentiles via a small local `_percentile()` helper
(linear interpolation on the sorted values, rounded to
int because all underlying signals — tokens, ms,
steps — are integers and the Markdown table reads
cleaner without trailing `.0`s). `_cost_stats()`
returns `(n, p50, p95, max)`. `statistics.quantiles`
was rejected because its `n=` parameter returns `n-1`
cut points, which is the wrong shape for the
p50/p95/max triple the report needs.

**rag-app rows carry `null` for the three
tool-use-agent-only fields** (`steps_taken`,
`max_steps`, `tool_latency_ms_sum`) rather than
omitting them, mirroring the slice-1 labels-with-
explicit-nulls convention. The cost is roughly +30
bytes per rag-app row; the payoff is that any
downstream pandas/jq reader sees a uniform schema and
can do `df.groupby('schema_version')[
'tool_latency_ms_sum'].quantile(0.5)` cleanly.

**Out of scope for slice 5b** (so slice 7 cannot
silently inherit them): the **`report` subcommand**
(`python -m evals_harness report --scored <path>`)
that joins every rubric's scored JSONL into a single
Markdown report, the **`corpus_fingerprint` diversity
warning** that flags when more than one fingerprint
appears for a single build, and any **cross-rubric
joint aggregations** (e.g. "groundedness conditional
on cost bucket"). Slice 5b ships the cost rubric as
its own scorer; slice 7 will roll up every rubric
including this one.

**Validated against the synthetic envelope built in
this iteration** (7 traces against the real
`queries.jsonl`): rag-app shows `observable=2/4`
(two live answers, one `refused-low-score`, one
dry-run) with `total_tokens` p50=1935, p95=2282,
max=2320; tool-use-agent shows `observable=2/3`
(one live answer, one live `model_refused`, one
dry-run) with `total_tokens` p50=2705, p95=3492,
max=3580 and `steps_taken` p50=2, max=3 and
`tool_latency_ms_sum` p50=18, max=35. Empty-traces
envelope, an unpaired-trace envelope, and the
prior slice-3/4/5a rubrics all continue to run
cleanly against the same envelope. rag-app
`retrieve` and tool-use-agent `catalog` produce
their iteration-20 outputs unchanged.

## 2026-05-16 — evals-harness slice 7 (aggregate `report` subcommand)

**Decision:** `python -m evals_harness report
--scored <path…> [--markdown <path>]` ships now as
the aggregate roll-up across every per-rubric
scored JSONL. It reads one or more
`scored_<rubric>.jsonl` files (in any combination —
all five rubrics or any subset), validates each row
against the cross-rubric core column set
(`rubric`, `record_id`, `schema_version`,
`question`, `label_id`, `match`) and the rubric
enum, and renders a single Markdown document with
two sections: a **quality rubrics table** with
per-(build, rubric) `matched/observable (pct%)`
accuracy for the four match-style rubrics
(refusal, groundedness, first_call_tool,
termination), and a **cost rubric table** with
per-build `total_tokens` p50/p95/max plus a
tool-use-agent-only sub-table for `steps_taken` and
`tool_latency_ms_sum` percentiles. Always prints to
stdout; `--markdown` additionally writes the same
bytes to a file. Unknown rubric, missing core
column, malformed JSON, or a missing file each
exits with code 2 and a named
`REPORT FAILED: file:lineno: …` message.

**Why a single subcommand that takes multiple
`--scored` files** (rather than one report per
scorer call or one mega-file from `score --all`):
each `score --rubric <X>` invocation already writes
one `scored_<X>.jsonl`, and forcing the user to
concatenate them before `report` would be friction
for no payoff. `nargs="+"` on `--scored` lets the
user point at whichever rubrics they have run; the
report sections gracefully omit any rubric absent
from the input. The alternative (a single
combined-rubrics file written by `score`) would
have required a `score --all` umbrella command and
either a bigger one-file output or a side-channel
manifest — both are heavier than `nargs="+"` and
neither buys anything.

**Why aggregate cost stats are recomputed in the
report, not pulled from a pre-aggregated row:** the
slice-5b cost rubric writes one **per-record** row
per (label, trace) pair (six numeric columns plus
the cross-rubric core); the report's per-build
percentile triple has to be derived from those rows
the same way `score --rubric cost` derives the
Markdown table. To guarantee byte-match, the report
imports the locked `_cost_stats` helper from
`score.py` rather than reimplementing percentile
math. Verified end-to-end against a 4-trace
synthetic envelope: both subcommands produce
identical `1935 / 2282 / 2320` and `2705 / 3492 /
3580` triples plus identical `steps_taken
2 / 3 / 3` and `tool_latency_ms_sum 26 / 34 / 35`
sub-table entries.

**Why `match`-rubric accuracy is `matched /
observable` rather than `matched / n_rows`:** the
denominator excludes `no_observation` rows (dry-run
traces, missing verification blocks, empty
`tool_calls`) — same convention slices 3, 4, 5a
use. Mixing observable and no-observation rows
into one denominator would let a re-run with more
dry-runs deflate the accuracy column without any
real quality regression. The report column header
explicitly names `observable` so the denominator
shape is visible at a glance.

**Why the report has two sections (quality + cost)
rather than one big table:** the cost rubric has no
correctness `match` column in the PM-relevant sense
— its `match` field is an observability flag (was
the trace live and were its token fields readable),
not a correctness signal. Putting cost in the same
accuracy table as the four match-rubrics would
either inflate "100% accuracy" reads (cost.match
is True whenever observed) or require a per-rubric
special case in the cell renderer. The two-table
split keeps the quality table's accuracy column
defensible and gives the cost table room for its
own percentile shape (which matches the slice-5b
Markdown).

**Out of scope for slice 7** (deliberate, named
here so a follow-on iteration cannot silently
inherit them as if they were always part of slice 7):

1. **`corpus_fingerprint` diversity warning.**
   Adding "more than one fingerprint seen per
   build → warning row" requires threading
   `corpus_fingerprint` through every per-rubric
   scored row schema first (it lives on the trace
   record, not on any current scored row). That is
   an additive schema bump for **all five** rubric
   writers, which is a separate slice; doing it
   here would silently break the additive-schema
   lock from slices 3–5b. Same DECISIONS pattern
   as slice 5b's deferral of this exact warning
   from the cost rubric.
2. **Per-record drill-down list.** The aggregate
   report only emits the top-level summary; the
   per-record `not-grounded` / `mismatch` /
   `non-clean termination` callouts already live
   inside each `score --rubric <X>` report and are
   not duplicated here. A reader who needs them
   should run the per-rubric `score` command,
   which is the canonical surface for
   per-record-failure narration.
3. **Cross-rubric joint aggregations** (e.g.
   "groundedness accuracy conditional on cost
   bucket" or "termination accuracy among queries
   that resolved every citation"). These require
   joining per-record rows across **different**
   scored.jsonl files by `record_id`, which is a
   bigger data-model step than the slice-7 MVP
   needs. Listed here so a future iteration that
   wants them writes a supersession rather than
   slipping them in additively.

**Validated against five synthetic scored JSONLs**
(one per rubric, 20 rows total spanning both
builds): the report correctly emits a Quality
rubrics table with five (build, rubric)
combinations and a Cost rubric table with two
builds and the tua sub-table; manually-verified
numbers (rag-app refusal 2/3, rag-app groundedness
2/3, tua refusal 3/3, tua first_call_tool 1/2,
tua termination 1/2, cost percentiles matching
slice-5b output) all check out. Error paths
(missing file, unknown rubric, missing `match`
key, malformed JSON) all exit code 2 with named
`REPORT FAILED: …` messages. `--markdown` writes
byte-for-byte the same content as stdout. Empty
file produces a clean `(no scored rows — nothing
to roll up)` document with exit code 0. Prior
subcommands (`ingest`, `score --rubric refusal`,
cross-build startup invariants) all continue to
pass unchanged.

## 2026-05-16 — teardown-prd CANDIDATES.md and the user-pick gate

**Decision:** `teardown-prd/CANDIDATES.md` ships now as the gate before
any teardown drafting. It ranks 3 of the 5 default OBJECTIVE.md
candidates (Cursor, Perplexity, GitHub Copilot — in that order) with
PM-framed rationale per candidate, names the two cuts (Linear AI,
Notion AI) with one-paragraph why-not, lists the five selection
criteria applied uniformly, and closes with a "what pick-one means in
practice" handoff to the next iteration. No teardown is drafted until
the user names the target. The user may override the shortlist with a
product not on the default pool; the override is recorded in the same
DECISIONS pick entry that captures the pick rationale.

**Why a shortlist of 3 (not 5, not 1):** ranking all 5 dilutes the
recommendation into a feature matrix and makes the user weigh
trade-offs the agent already weighed. Picking 1 unilaterally
contradicts the user-gated rule from the iteration-1 DECISIONS entry
(Teardown target selection is user-gated). 3 candidates is the smallest
set that lets the user disagree with the agent's #1 without going
off-pool, and is the same shape OBJECTIVE.md's guardrail prescribes
("ranking 3 options").

**Why the ranking favors AI-native products over AI-add-ons:** the
five selection criteria in CANDIDATES.md were applied uniformly, but
two of them (AI-native vs. AI-add-on, and failure-mode richness) push
hardest in favor of products where AI is the entire surface. Linear AI
and Notion AI failed those two criteria — their AI features sit on top
of strong host products with non-AI design languages, so a teardown
risks drifting into a teardown of the host product and diluting the
AI-PM framing this leave-behind needs. They remain on the bench if the
user is interviewing specifically at one of those companies.

**Why no fabricated metrics in CANDIDATES.md:** every claim in the
shortlist is grounded in publicly observable surface — visible UI, mode
names, pricing tiers, public docs/changelogs, and well-known failure
modes the user can replicate by using the product. No invented user
counts, revenues, internal-roadmap predictions, or "the PM at company
X must have decided …" speculation. The same constraint binds the
teardown itself once a target is picked: all quantitative claims must
trace to a public source cited inline. This restates the
no-fabrication guardrail at the artifact level so a future iteration
cannot import it as a soft suggestion.

**Why a separate top-level `teardown-prd/` directory:** matches the
iteration-1 repo-layout DECISIONS entry, which pre-committed the path.
Keeping the teardown out of `templates/` reflects that the teardown is
a single concrete document for one named product, not a populatable
scaffold like the interview tracker — different artifact category,
different home.

**Out of scope for this iteration** (deliberate, named so a follow-on
iteration cannot silently inherit them):

1. **The teardown PRD itself.** Drafting the teardown before the user
   picks a target violates the iteration-1 user-gate rule. The next
   iteration starts the draft only after the pick is recorded.
2. **A `TEARDOWN_PICK.md` ballot or any other multi-vote artifact.**
   The user names the pick directly to the agent (or in OBJECTIVE.md);
   adding a ballot file is overhead for a single binary decision.
3. **Pre-populating teardown sections for the top-ranked candidate.**
   Even a stub `cursor-teardown.md` would short-circuit the gate by
   biasing the user toward the agent's #1. The skeleton lands in the
   pick-recording iteration, not before.

**Validation:** CANDIDATES.md exists at `teardown-prd/CANDIDATES.md`,
ranks Cursor / Perplexity / GitHub Copilot 1–2–3 with rationale and
"why this user might want a different pick" counter-cases per
candidate, names Linear AI and Notion AI as cuts with rationale, and
closes with a three-step handoff for the next iteration. The new
`teardown-prd/CANDIDATES.md` file is not in the rag-app corpus v1
list (which is locked to OBJECTIVE.md, DECISIONS.md,
templates/INTERVIEW_TRACKER.md, rag-app/README.md), so the file itself
does not perturb the index — but this DECISIONS entry does, by the
same per-iteration drift pattern earlier slices documented.
Expanding the corpus to cover the teardown deliverable belongs to a
deliberate corpus-v2 supersession, not this iteration.


## 2026-05-16 — teardown product locked: Cursor

**Decision:** The Day-20 teardown PRD will be written against **Cursor**.
This resolves the user-pick gate established in the prior entry
("teardown-prd CANDIDATES.md and the user-pick gate") and supersedes the
"Awaiting user pick" status in `teardown-prd/CANDIDATES.md`. Perplexity
and GitHub Copilot, ranked #2 and #3 in the shortlist, are now out of
scope for this milestone.

**Rationale:** User directive on 2026-05-16, no further deliberation
required. The Cursor #1 ranking in CANDIDATES.md already documents the
PM-relevant rationale (AI-native product, fast surface-area expansion,
strong PRD-able tensions around agent autonomy vs. user control, etc.) —
that file remains the canonical justification document. This entry only
records the binding pick.

**Implications for subsequent iterations:**
1. The next iteration begins the actual teardown PRD draft at
   `teardown-prd/cursor-teardown.md`. No more candidate-comparison work.
2. The teardown is a multi-iteration artifact, not a single-iteration
   ship. Expect: outline → "what's working" section → "what's broken"
   section → "what to ship next" section → metrics & instrumentation
   section → polish/leave-behind framing pass.
3. The no-fabrication rule still binds: do not invent Cursor internal
   metrics, employee quotes, or roadmap details. Use only publicly
   observable product behavior, public statements, and stated user
   experience. Where a number is needed and unknown, write a placeholder
   with the source the user would consult to fill it in.
4. CANDIDATES.md is preserved as-is below this entry's effective date —
   it is the record of how the pick was reached, not a live decision
   document anymore. A header note in CANDIDATES.md marks the resolved
   status for human readers.


## 2026-05-16 — Cursor teardown PRD: scope, structure, slicing plan

**Decision:** The Cursor teardown PRD ships as a multi-iteration
artifact at `teardown-prd/cursor-teardown.md`. This iteration delivers
the **outline slice**: masthead (product / author POV / observation
snapshot), an explicit scope decision, and six canonical section
headers (What's working / What's broken / What to ship next / Proposed
metrics / Out of scope / How I'd validate), each carrying a
substantive intent paragraph that names the sub-areas the draft will
narrow to and the evidence-source posture for the section. No section
bodies are drafted in this iteration — the per-section drafts are the
slices that follow.

**Why one document, not a doc-per-section:** the teardown is intended
as a single interview leave-behind, and reviewers will read it
top-to-bottom in a sitting. Splitting it across files would force the
reader to context-switch and would let the proposals in "What to ship
next" drift away from the symptoms in "What's broken" they
respond to. The single-file model also makes the no-fabrication
audit a single grep pass at the polish iteration.

**Why this scope (chat + inline-edit + agent triad, not full product):**
the three triad surfaces share a model-routing layer, a
context-assembly layer, and an edit-application layer, so a teardown
that covers them together can compare PM choices across them rather
than treat each in isolation. A full-product teardown would spread
the draft across surfaces the user does not exercise daily (enterprise
admin, CLI, marketplace) and would dilute the AI-PM framing. A
single-surface teardown (e.g. autocomplete only) would compete
head-to-head with Copilot on one dimension and lose the cross-surface
PM comparison that is the artifact's strongest move. Tab autocomplete
and the Rules system are mentioned as supporting context but not
deep-dove.

**Why six sections, not four:** OBJECTIVE.md names four (what's
working, what's broken, what to ship next, proposed metrics).
CANDIDATES.md added two (out-of-scope, how I'd validate) and that
shape is preserved here. Out-of-scope makes the scope decision
auditable; how-I'd-validate prevents the "what to ship next"
proposals from reading as opinions in a vacuum. Both are PM craft
markers an interviewer expects. The six-section list is locked —
section headers will not be renamed or merged in subsequent slices.

**Per-iteration slicing plan** (each slice is one iteration unless
the iteration plan explicitly says otherwise):

1. **Outline** (this iteration) — masthead, scope decision, six
   section intents. Shipped.
2. **What's working** — narrow the candidate sub-areas to ~3, write
   each as a PM-decision-with-observable-behavior paragraph, cite
   public sources inline.
3. **What's broken** — narrow to ~3, pair each symptom with a
   reproduction note, cite the source category (own observation /
   user-community pattern / Cursor changelog) per claim.
4. **What to ship next** — three proposals, one per top-ranked
   broken sub-area, each shaped as a PM one-pager (problem,
   proposed shape, scope, risks, how to know it worked).
5. **Proposed metrics** — fill the four-quadrant coverage map with
   ~6 metrics; framework-shaped, no fabricated baselines.
6. **Out of scope + How I'd validate** — combine into one iteration
   (both are methodology-shaped, both short).
7. **Polish / leave-behind framing pass** — masthead consistency,
   cross-section references, no-fabrication grep audit, source-list
   reconciliation, final read-aloud pass.

Slices may be re-ordered if a later iteration's user direction
warrants — the slicing plan is not a slip-resistant contract like
the build-roadmap slices were, because the underlying artifact is a
single document a PM revises non-linearly. But each iteration ships
*one* coherent section in *committable* state, not a half-drafted
section across two iterations.

**Source discipline locked** (binds every drafted section):

1. Every quantitative or surface-specific claim cites a public source
   inline. Source categories named in the outline: Cursor docs,
   Cursor changelog (with version), Cursor pricing page (with
   snapshot date), public Anysphere statements (blog / interviews /
   talks, cited by title + date), author's reproduction notes
   (labeled with date / version / OS / tier), and user-community
   reports cited only as patterns ("users report X") with a
   representative link.
2. No internal Cursor information, no fabricated metrics, no invented
   user counts, no revenue numbers, no roadmap claims beyond publicly
   stated direction. This is the OBJECTIVE.md no-fabrication
   guardrail restated at the artifact level so a future iteration
   cannot import it as a soft suggestion.
3. Where a number is needed and unknown, the draft writes a named
   placeholder identifying the source the reader would consult (e.g.
   "(latest figures: Anysphere's public funding announcements)") —
   never an invented value.
4. Observation snapshot pinned to **2026-05-16** in the masthead;
   any later iteration that reproduces a behavior on a different
   date updates the masthead date and re-walks the affected claims,
   not silently overwrites them.

**Out of scope for this iteration** (deliberate, named so the next
iteration cannot silently inherit them):

1. **Any section body content.** Section *intent paragraphs* are in
   scope; section *bodies* are not. A reviewer reading the outline
   should see what the draft will argue, not the argument itself.
   The "What's working" slice is the next iteration's deliverable.
2. **A separate `cursor-teardown-sources.md` sidecar file.** Sources
   are cited inline at draft time, not collected in a sidecar. A
   sidecar would force the reader to flip between two files and
   would let an inline claim drift away from its cited source.
3. **Pre-populating placeholder content with "TBD" filler in section
   bodies.** Empty section bodies (header + intent paragraph) is
   the correct shape for the outline slice; "TBD" filler in the body
   would visually imply the draft is half-done.
4. **A rag-app corpus expansion to include the teardown.** The
   rag-app corpus v1 is locked to four files (OBJECTIVE.md,
   DECISIONS.md, templates/INTERVIEW_TRACKER.md, rag-app/README.md).
   Adding the teardown to the corpus is a deliberate corpus-v2
   supersession, not a side-effect of shipping this artifact.

**Implication for the rag-app corpus_fingerprint:** this iteration
touches DECISIONS.md but not the other three corpus-v1 files; per the
per-iteration drift pattern documented in iterations 16 and 20, the
rag-app corpus_fingerprint will rotate again. The
teardown-prd/cursor-teardown.md file itself is not in the corpus
list, so its existence does not perturb the index — only this
DECISIONS entry does. Tool-use-agent catalog is unchanged so its
fingerprint is unchanged. Both builds and the evals-harness
cross-build invariants still pass.

## 2026-05-16 — Cursor teardown PRD slice 2: "What's working" drafted

**Decision:** The "What's working" section of
`teardown-prd/cursor-teardown.md` ships in drafted state, replacing
the outline slice's four-candidate bullet list with three full
sub-section drafts plus an inline "cut" paragraph naming the
dropped candidate. Sections 2–6 remain in outline / intent-paragraph
state and are picked up in subsequent slices per the slicing plan
locked in the preceding DECISIONS entry.

**Three sub-areas selected:**

1. **§1.1 Edit-application UX: inline-diff-then-accept** — model
   never reaches the working tree without a per-edit human gesture,
   review surface is the default rather than an opt-in, the friction
   cost is dominated by the cost of one missed wrong-direction edit
   ten layers into a refactor.
2. **§1.2 Context as a first-class citizen: the `@` mention system** —
   explicit user-named context vs. silent auto-inclusion, with the
   chip rendering in the prompt and persisting in conversation
   history so the next turn re-shows exactly what context the model
   saw last turn. Predictability vs. cold-start friction trade
   resolved toward predictability.
3. **§1.3 Sequencing autonomy: Background Agent shipped after
   Composer matured** — the autonomy ramp (inline → Composer →
   Background Agent) is also a review-surface ramp, and the staging
   means users arrive at the autonomous mode with a calibrated mental
   model rather than building one against the most autonomous
   surface from cold start.

**Cut from the outline's four: pricing-tier shape.** Defensible as a
product call but lives more on the monetization-positioning axis than
the PM-design axis; defending it concretely requires specific tier
prices and quota numbers that drift week-to-week, and the
no-fabrication posture would force inline placeholders that weaken
the argument. The teardown is stronger with three concrete
PM-design calls than with four where one is positioning. Pricing
surfaces lightly in §4's lagging-business metrics row and in §6's
explicit exclusion of pricing-page A/B as a validation method, so
the topic is not orphaned — it is acknowledged in the methodologies
that touch it without being deep-dove in its own sub-section.

**Canonical sub-section paragraph shape** (locked here as a precedent
binding §2 "What's broken" and §3 "What to ship next" sub-sections,
which will mirror this shape):

1. **The PM decision.** Lead with the choice itself in one or two
   sentences. The reader should be able to summarize the PM call
   without reading further.
2. **Observable behavior.** What a reviewer can reproduce on the
   snapshot date, in concrete UI terms (key bindings, surface names,
   what renders where). Every observable claim cites either the date
   of reproduction or a public source URL.
3. **Why this is the right PM call.** The argument — not feature
   listing. Names the failure mode the decision protects against,
   and the comparative alternative the decision is choosing against.
4. **Tension worth naming.** Every PM decision has a cost; naming the
   tension is what converts the section from advocacy into PM craft.
   The cost may be small (cold-start friction), large (windowed
   competitive disadvantage), or asymmetric; in all cases it is named
   explicitly and the trade is defended on its merits.
5. **Inline source citation** in italics at the close of the
   sub-section, naming source category + accessed date + (where
   relevant) the reproduction conditions (OS, tier). Sources are
   inline at the sub-section, not collected in a sidecar — same
   discipline locked in the outline slice's source-discipline entry.

**Why this shape, not freer-form prose:** the teardown is a
PM-craft artifact, and a reviewer scanning it for PM signal needs to
find decision + behavior + argument + tension in a predictable order.
Freer-form prose would let strong sub-sections shine but would also
let weaker sub-sections hide their thin spots; the locked shape
forces each sub-section to either fill all five slots or explain why
it cannot. §2 and §3 will use the same five-slot shape (with "the
PM failure" and "the PM proposal" substituting for "the PM decision"
respectively); §4's metrics, §5's out-of-scope, and §6's validation
methodology have different natural shapes and are not bound by this
slot list.

**Source-density discipline** carried from the outline's
source-discipline entry, restated here so a future iteration cannot
silently weaken it for §2's drafted sub-sections: every claim about
Cursor's surface behavior cites either (a) "observable behavior on
2026-05-16" with reproduction conditions, (b) a docs URL
(cursor.com/docs) with the accessed date, (c) a changelog reference
(cursor.com/changelog) with the accessed date, or (d) a public
Anysphere statement (cited by post title and date). No
unsourced claims about Cursor's internals, no fabricated version
numbers, no specific dollar amounts unless quoted with a
snapshot citation.

**Header convention:** sub-sections within each canonical section use
`### N.M ...` three-level headers (e.g. `### 1.1 Edit-application UX:
inline-diff-then-accept`). Top-level section headers stay at `## N.
...`. This is consistent with the existing outline's `## Scope
decision` / `## 1. What's working` level choices and gives the
reader a predictable scan hierarchy. §2–§6 sub-sections will follow
the same convention as they are drafted.

**Out of scope for this iteration** (deliberate, named so the next
iteration cannot silently inherit them):

1. **Edits to sections 2–6.** Those sections remain in outline /
   intent-paragraph state; the §2 "What's broken" draft is the next
   iteration's deliverable.
2. **Revisions to the scope decision or the masthead.** The triad
   scope, the observation date (2026-05-16), and the no-fabrication
   posture all stand. The drafted §1 sub-sections must fit within
   the locked scope; if a sub-section would require widening scope,
   it is cut, not drafted.
3. **A "Cuts" sidecar file or a separate cut-rationale doc.** The
   one-paragraph cut explanation lives inline at the end of §1, same
   discipline as keeping sources inline.
4. **Pricing-tier deep-dive in §4 or §6.** Pricing is touched lightly
   in §4's lagging-business metrics row (already in the outline) and
   explicitly excluded as a validation method in §6 (also already in
   the outline). Reopening it as a deep-dive in those sections would
   reintroduce the cut sub-area by side door.
5. **Any change to the rag-app corpus v1 file list.** Corpus v1 stays
   locked to (OBJECTIVE.md, DECISIONS.md, templates/INTERVIEW_TRACKER.md,
   rag-app/README.md). The teardown file itself remains outside the
   corpus.

**Implication for the rag-app corpus_fingerprint:** this iteration
touches DECISIONS.md but not the other three corpus-v1 files; per the
per-iteration drift pattern documented from iteration 16 onward, the
rag-app corpus_fingerprint will rotate again. The
teardown-prd/cursor-teardown.md file's drafted §1 is not in the
corpus, so its drafting does not perturb the index — only this
DECISIONS entry does. Tool-use-agent catalog is unchanged so its
fingerprint is unchanged. Both builds and the evals-harness
cross-build invariants still pass.

---

## 2026-05-16 — Cursor teardown PRD slice 3: "What's broken" drafted

**Decision:** The "What's broken" section of
`teardown-prd/cursor-teardown.md` ships in drafted state, replacing
the outline slice's four-candidate bullet list with three full
sub-section drafts plus an inline "cut" paragraph naming the dropped
candidate. The drafts follow the canonical five-slot shape locked in
the preceding slice-2 entry (PM failure / observable behavior / why-
fixable-UX-gap-not-strategy-mistake / tension / inline source).
Sections 3–6 remain in outline / intent-paragraph state and are
picked up in subsequent slices per the seven-step plan from
iteration 27.

**Three sub-areas selected:**

1. **§2.1 Auto-mode router opacity** — Auto-mode hides the underlying
   model identity, fallback events, and routing rationale from the
   user, breaking the user's ability to learn the product's
   reliability envelope or triage a bad turn. The fix is
   reveal-after-the-fact: per-message model label, optional
   per-thread routing summary. Strategic logic for an Auto default
   is sound; only the post-hoc transparency is missing.
2. **§2.2 Indexer staleness signals** — On larger repos the project
   indexer can serve stale chunks after recent edits, with no
   first-class index-freshness indicator the user can read at a
   glance. The fix borrows the pattern wholesale from IDE search
   panes (last-index timestamp, pending-file count, one-click
   resync). The §1.2 `@`-mention chip system relies on predictable
   model context, and silent indexer staleness directly undercuts
   that contract.
3. **§2.3 Agent stop conditions and overrun** — Composer and
   Background Agent can read ambiguous user acknowledgments as
   license to continue past the intended stopping point, and the
   only mid-execution control is Cancel. The fix is an explicit
   pre-run "I'll stop when X" plan plus a pause-and-amend
   mid-execution control. The default-direction call — stop-
   aggressive vs. stop-permissive — is named here and recommended
   in §3, defending stop-aggressive on overrun-damage asymmetry.

**Cut from the outline's four: free-tier quota surprises.** The
free-tier quota UX gap is real and the fix (a persistent quota meter,
80%-consumed warning, clear upgrade path) is straightforward, but
the sub-area is structurally a monetization-positioning concern
rather than a PM-design call — the same axis that put §1.4's
pricing-tier shape outside the section. Defending it requires
snapshot-pinned quota numbers and conversion data the public surface
does not expose, which collides with the no-fabrication posture.
Free-tier quota surfaces lightly in §3's Proposal B context (a
quota meter and an index-freshness indicator compete for the same
chrome real estate, named explicitly when Proposal B drafts) and in
§4's lagging-adoption metrics row (free-to-paid conversion). The
topic is acknowledged where it touches the PM-design surfaces
without being deep-dove on its own.

**Slot substitution from slice 2's shape:** the canonical first slot
is "the PM decision" in §1 and "the PM failure" in §2 (per the slice-2
entry's "with 'the PM failure' and 'the PM proposal' substituting"
clause). Slot 3 — "why this is the right PM call" in §1 — substitutes
to "why this is a fixable UX gap, not a strategy mistake" in §2, per
iteration 28's learning note that this framing is the load-bearing
slot for §2 ("converts each sub-section from 'Cursor got it wrong'
into a PM-craft critique a Cursor PM could action without rewriting
the product strategy"). Slots 2 (observable behavior), 4 (tension
worth naming), and 5 (inline source citation) carry forward
unchanged. The five-slot list and its rationale (forcing each sub-
section to fill all five or explain why it cannot) remain binding
for §3 as well, with slot 1 substituting to "the PM proposal" there
per the slice-2 entry's pre-commitment.

**Source-density discipline** restated unchanged from slice 2: every
claim about Cursor's surface behavior cites either (a) "observable
behavior on 2026-05-16" with reproduction conditions (OS, tier, and
when relevant repo-size or file-count), (b) a docs URL
(cursor.com/docs) with the accessed date, (c) a changelog reference
(cursor.com/changelog) with the accessed date, or (d) a public
Anysphere statement (cited by post title and date). User-community
reports (forums, social media) are cited only as recurring patterns,
never as authoritative on Cursor internals. No fabricated version
numbers, no invented support-ticket volumes, no specific dollar
amounts.

**Header convention** carries from slice 2 unchanged: `### N.M ...`
three-level headers for sub-sections, `## N. ...` for top-level
canonical sections. The §2 cut paragraph uses a sub-section header
(`### Cut from the outline's four: ...`) parallel to the §1 cut
paragraph, so a reader scanning the document by header sees the
narrowing decision in both sections at the same depth.

**Word-budget discipline** carried from iteration 28's learning note
(~150–250 words per sub-section across five rhetorical slots). The
drafted §2 sub-sections track that budget within ±10% so a reviewer
can scan the three sub-sections at roughly equal cost and notice
which one is structurally weakest. Maintaining a fixed word budget
across sections is what makes the five-slot lock observable rather
than aspirational.

**Out of scope for this iteration** (deliberate, named so the next
iteration cannot silently inherit them):

1. **Edits to sections 3–6.** Those sections remain in outline /
   intent-paragraph state; the §3 "What to ship next" draft is the
   next iteration's deliverable, paired one-to-one with §2's three
   broken sub-areas (Proposal A → §2.1, Proposal B → §2.2,
   Proposal C → §2.3).
2. **Revisions to §1 or to the masthead / scope decision.** §1's
   three drafted sub-sections and the cut paragraph stand. If a §2
   sub-section appears to require restating a §1 decision, the §2
   sub-section is revised, not §1.
3. **A new outline-candidate added to §2 mid-draft.** The §2 cut
   paragraph names exactly one cut (free-tier quota); silently
   adding a fifth or sixth candidate would defeat the
   narrow-to-three discipline established in slice 2.
4. **Promotion of the cut sub-area into a deep-dive elsewhere.**
   Free-tier quota surfaces only as named in §3 Proposal B and §4's
   metrics row, neither of which is a deep-dive. Reopening it as a
   sub-section of §3 or §4 would reintroduce the cut by side door,
   same posture slice 2 took on pricing-tier.
5. **Any change to the rag-app corpus v1 file list.** Corpus v1
   stays locked to (OBJECTIVE.md, DECISIONS.md,
   templates/INTERVIEW_TRACKER.md, rag-app/README.md). The teardown
   file itself remains outside the corpus and its drafted §2 does
   not perturb the rag-app index.

**Implication for the rag-app corpus_fingerprint:** this iteration
touches DECISIONS.md but not the other three corpus-v1 files; per the
per-iteration drift pattern documented from iteration 16 onward, the
rag-app corpus_fingerprint will rotate. The
teardown-prd/cursor-teardown.md file's drafted §2 is not in the
corpus, so its drafting does not perturb the index — only this
DECISIONS entry and the small status-line update at the top of the
teardown file do (and only the DECISIONS entry, because the teardown
file is not in corpus v1). Tool-use-agent catalog is unchanged so its
fingerprint stays at 626af64cb9bf48bf. Both builds and the
evals-harness cross-build invariants still pass.

## 2026-05-16 — Cursor teardown PRD slice 4: "What to ship next" drafted

**Decision:** The "What to ship next" section of
`teardown-prd/cursor-teardown.md` ships in drafted state, replacing
the outline slice's three-bullet "Initial shape" list with three full
sub-section drafts (Proposal A / B / C, one per §2 sub-area). The
drafts follow the canonical five-slot shape locked in the slice-2
entry, with slot 1 substituted to "the PM proposal" and slot 3
substituted to "what could go wrong" — both substitutions
pre-committed by the slice-3 entry's "slot 1 substituting to 'the PM
proposal' there per the slice-2 entry's pre-commitment" clause and by
iteration 29's learning note that "the same substitution pattern
will need a third variant for §3 (slot 3 becomes 'what could go
wrong')." Sections 4–6 remain in outline / intent-paragraph state and
are picked up in subsequent slices per the seven-step plan from
iteration 27.

**Three proposals, one-to-one with §2's broken sub-areas:**

1. **§3.1 Proposal A — Routing transparency for Auto mode**
   (paired with §2.1 Auto-mode router opacity). A per-message
   "served by <model> via Auto" caption plus an opt-in per-thread
   routing summary, plus an opt-in setting that pins the router to
   a specific model from inside Auto. Routing logic itself is not
   changed; only post-hoc transparency is added. Costs typographic
   real estate; pays for itself in user-learning and support-issue
   triage.
2. **§3.2 Proposal B — Index-freshness indicator** (paired with
   §2.2 Indexer staleness signals). A persistent footer chip
   showing "indexed Ns ago, M pending" with hover-to-list,
   one-click resync, and an inherited staleness marker on the
   `@Codebase` mention chip. Borrows the pattern from JetBrains
   and VS Code's footer index affordances. The freshness signal
   claims footer real estate that the cut-from-§1/§2 free-tier
   quota meter would otherwise compete for, named explicitly so a
   later iteration cannot reopen quota via the side door.
3. **§3.3 Proposal C — Agent stop-criteria UI** (paired with §2.3
   Agent stop conditions and overrun). An explicit pre-run "I'll
   stop when X" plan the user confirms, plus a pause-and-amend
   interrupt-by-default during execution. The default direction is
   **stop-aggressive** (mid-execution user messages pause the agent
   by default), with stop-permissive available as a per-task
   opt-in scoped to the current task only. The stop-aggressive
   recommendation discharges the slice-3 entry's pre-commitment
   ("the default-direction call — stop-aggressive vs.
   stop-permissive — is named here and recommended in §3,
   defending stop-aggressive on overrun-damage asymmetry").

**No fourth-candidate cut paragraph in §3.** Unlike §§1 and 2, §3's
proposal count is bound one-to-one to §2's three narrowed sub-areas
rather than to an independent outline-candidate list — there is no
fourth candidate to drop with a parallel cut paragraph. This is named
explicitly in the §3 opening transition paragraph so a reader scanning
for the cut paragraph at parallel depth across the three drafted
sections sees the structural difference and its reason. The
free-tier quota cut from §2 surfaces inside Proposal B's tension
paragraph as documented in the slice-3 entry, fulfilling the "Free-
tier quota surfaces lightly in §3's Proposal B context" pre-
commitment.

**Slot substitution from slice 2's shape:** the canonical first slot
is "the PM decision" in §1, "the PM failure" in §2, and "the PM
proposal" in §3 — three substitutions corresponding to the three
section purposes (decisions worth defending, failures worth fixing,
proposals worth shipping). Slot 3 — "why this is the right PM call"
in §1, "why this is a fixable UX gap, not a strategy mistake" in §2 —
substitutes to "what could go wrong" in §3. The §3 substitution is
the load-bearing slot for a proposal section (parallel to the
load-bearing-slot observation iteration 28 and 29 made for §§1 and 2):
without it, each proposal reads as advocacy and the section as a
whole collapses into a wishlist. The "what could go wrong" framing
forces each proposal to argue not just "ship this" but "ship this
*and* here is how you'd contain the realistic downside." Slots 2
(observable behavior / proposed shape), 4 (tension worth naming),
and 5 (inline source citation) carry forward unchanged. The five-slot
list and its rationale remain binding through the end of the drafted
sections; if §4 ("Proposed metrics") needs a different shape, the
slice-5 entry will name and justify the deviation.

**Stop-aggressive defense, restated:** the §3.3 sub-section names the
default direction as stop-aggressive and defends the call on
asymmetric damage: a wrong-direction agent edit costs the user the
time-to-recover (Cancel + inspect + revert) plus the time-to-rebuild
trust in the agent, while a confirmation prompt costs one click.
Friction amortizes; a single bad overrun can end the day. The
locked stop-permissive opt-in is *scoped to the current task only*
(no persistent setting) — without that scope, users would forget
they had enabled the toggle and re-import the original overrun risk
one session later. This per-task scope is a contract for slice 5's
metrics: any "agent stop-precision" metric that defines success has
to read the per-task scope as a feature of the proposal, not as a
detail to abstract over.

**Source-density discipline** restated unchanged from slices 2 and 3:
every claim in §3 about Cursor's surface grounds in §2's already-
sourced documented behavior or in PM-craft argumentation. Each
proposal's source paragraph names the IDE-pattern precedents (Copilot
Chat / Cody / Claude for §3.1, JetBrains / VS Code for §3.2,
Anysphere public statements for §3.3) and labels them as observable
on the named products' 2026-05-16 surfaces. The §3-level evidence-
sources paragraph adds the no-internal-information guardrail
verbatim from the outline. No internal Cursor information, no
fabricated metrics, no roadmap claims beyond what Anysphere has
stated publicly. A proposal that requires asserting Cursor's
internals to defend ("Cursor's index already supports incremental
refresh") would need a citation or be rewritten as conjecture.

**Header convention** carries from slices 2 and 3 unchanged: `### N.M
…` three-level headers for sub-sections, `## N. …` for top-level
canonical sections. §3 has no cut paragraph (per the no-fourth-
candidate note above), so the symmetric `### Cut from the outline's
four: …` header that §§1 and 2 carry is deliberately absent in §3 —
not an oversight but a structural reflection that §3's three
proposals derive from §2's three failures, not from a four-down-to-
three narrowing.

**Word-budget discipline** carried from iteration 28's learning note
and iteration 29's confirmation: §1 sub-sections ran 357 / 362 / 425
words; §2 sub-sections ran 409 / 417 / 464 words; §3 sub-sections
land in roughly the same band (Proposals A / B / C each at ~430–500
words). The §3 sub-sections trend toward the upper end of the §2
range because the five-slot shape's slot 3 ("what could go wrong" +
two mitigations) carries more argument than §2's slot 3 ("why this
is a fixable UX gap" + the design-vs-strategy split). The asymmetric
slot-budget pattern iteration 29 named ("the load-bearing slot
varies by section purpose") repeats here: slot 3 is the heaviest in
§3 just as it was in §2, and the section-level total accommodates
the slot variance without breaking the rough-equal-scan-cost
property across the three sub-sections.

**Out of scope for this iteration** (deliberate, named so the next
iteration cannot silently inherit them):

1. **Edits to sections 4–6.** Those sections remain in outline /
   intent-paragraph state; the §4 "Proposed metrics" draft is the
   next iteration's deliverable, with the metric framework's
   four-quadrant shape (leading × adoption, leading × quality,
   lagging × adoption, lagging × business) already pre-committed
   in the §4 outline intent paragraph.
2. **Revisions to §§1–2 or to the masthead / scope decision.** The
   drafted §§1–2 sub-sections, the §1 and §2 cut paragraphs, and
   the scope decision stand. If a §3 proposal appears to require
   restating a §1 decision or §2 failure, the §3 proposal is
   revised, not the upstream section.
3. **A fourth proposal added to §3 mid-draft.** §3 has exactly
   three proposals, one per §2 sub-area; silently adding a fourth
   (e.g. a free-tier quota meter, or a pricing-tier rework) would
   reopen by side door the cuts §1 and §2 closed and defeat the
   one-to-one §2-to-§3 binding the slice-3 entry locked.
4. **Promotion of the cut sub-areas (pricing-tier from §1,
   free-tier quota from §2) into deep-dive proposals.** Free-tier
   quota surfaces inside Proposal B's tension paragraph and in §4's
   metrics row as already named; pricing-tier surfaces in §4's
   lagging-business row and in §6's explicit exclusion of pricing
   A/B as a validation method. Neither is a deep-dive in §3.
5. **A new opt-in setting introduced in §3 that requires a
   user-account-shape change.** Per-task and session-scoped toggles
   are in scope; any setting that would require new account-level
   state (a new tier of paid plan, a per-organization policy
   surface) is out of scope because it crosses into the
   enterprise-admin scope explicitly excluded in the outline's
   scope-decision section.
6. **Any change to the rag-app corpus v1 file list.** Corpus v1
   stays locked to (OBJECTIVE.md, DECISIONS.md,
   templates/INTERVIEW_TRACKER.md, rag-app/README.md). The teardown
   file itself remains outside the corpus and its drafted §3 does
   not perturb the rag-app index.

**Implication for the rag-app corpus_fingerprint:** this iteration
touches DECISIONS.md but not the other three corpus-v1 files; per the
per-iteration drift pattern documented from iteration 16 onward, the
rag-app corpus_fingerprint will rotate. The
teardown-prd/cursor-teardown.md file's drafted §3 is not in the
corpus, so its drafting does not perturb the index — only this
DECISIONS entry and the small status-line update at the top of the
teardown file do (and only the DECISIONS entry, because the teardown
file is not in corpus v1). Tool-use-agent catalog is unchanged so its
fingerprint stays at 626af64cb9bf48bf. Both builds and the
evals-harness cross-build invariants still pass.

## 2026-05-16 — Cursor teardown PRD slice 5: "Proposed metrics" drafted

**Decision:** The "Proposed metrics" section of
`teardown-prd/cursor-teardown.md` ships in drafted state, replacing
the outline slice's four-bullet "Coverage map" with six metrics
organized as four sub-sections (4.1 Leading × adoption, 4.2
Leading × quality, 4.3 Lagging × adoption, 4.4 Lagging × business)
following the 2-2-1-1 distribution. Sections 5 and 6 remain in
outline / intent-paragraph state and are picked up in the next
slice per the seven-step plan from iteration 27 (slices 5 + 6 land
together as §§5–6 in the next iteration; final iteration is polish).

**Six metrics, 2-2-1-1 across the 2×2:** the leading-heavy
distribution is deliberate — PM action lives on the leading side,
so the framework is denser there. The lagging side gets the minimum
needed to anchor leading metrics to outcomes Anysphere already
tracks. Concretely:

1. **§4.1.1 `@`-mention adoption rate** (Leading × adoption,
   tied to §1.2): sessions-with-mention ÷ total-sessions over a
   rolling 7-day window, segmented by user-tenure cohort. Caveat:
   `@Codebase`-only usage can mask the deeper context system.
2. **§4.1.2 Auto-mode mix** (Leading × adoption, tied to §2.1
   and Proposal A): share of triad-surface turns served via Auto
   vs. pinned model, weekly. The trend is the actionable signal,
   not the level. Caveat: pinning is not failure; pair with §4.3.1
   retention to read whether the pinned cohort sticks.
3. **§4.2.1 Agent stop-precision** (Leading × quality, tied to
   §2.3 and Proposal C): of agent runs that halted before hitting a
   hard stop, the share that halted at the user's intended
   boundary, measured against an offline labeled eval set whose
   fixture shape matches this repo's evals-harness termination
   rubric. Caveat: report default-mode and opt-in-mode separately;
   the per-task scope of the stop-permissive opt-in (slice-4
   contract) is a feature of the proposal, not a detail to
   abstract over.
4. **§4.2.2 Index-freshness coverage** (Leading × quality, tied
   to §2.2 and Proposal B): share of `@Codebase` and agent turns
   served when the indexer was within a configurable lag threshold
   of the working tree, segmented by repo-size cohort. Caveat:
   large-repo cohorts always run colder; segmenting prevents the
   small-repo majority from making the headline number look
   healthier than the large-repo reality.
5. **§4.3.1 90-day retention by `@`-mention cohort** (Lagging ×
   adoption, tied to §1.2): retention split by week-N
   `@`-mention usage (zero / 1–3 / 4+). Caveat: power users
   self-select into `@` usage; observational gaps are suggestive,
   not causal — any causal claim needs a flag-gated experiment.
6. **§4.4.1 Net revenue retention on the Business tier**
   (Lagging × business, the only business-quadrant metric):
   accounts that crossed into Business in Q, share still on
   Business 12 months later, plus seat-expansion within retained
   accounts. Caveat: 12 months lags too far in a fast-moving
   market; report alongside the quarter-by-quarter trend.

**§4 deviates from the §§1–3 five-slot shape, deliberately.** The
slice-4 entry pre-committed that "if §4 ('Proposed metrics') needs
a different shape, the slice-5 entry will name and justify the
deviation." It does. §§1–3's five-slot shape (PM decision/failure/
proposal — observable behavior or proposed shape — why this is
right / fixable gap / what could go wrong — tension worth naming —
inline source) is sized for *arguments*. §4's metrics are
*computations with decision-implications*, which fit a four-slot
shape: **(1) name + what is computed**, **(2) what PM decision the
metric informs**, **(3) the §1–§3 link this metric measures**, and
**(4) a caveat naming the common way the metric would mislead**.
The inline-source slot is deliberately absent at the per-metric
level because metric categories are PM craft, not fact-claims about
Cursor; the section's evidence-sources paragraph carries the
applicability grounding once. The "tension worth naming" slot is
absorbed into the caveat slot because a metric's tension *is* the
way it can mislead — collapsing the two preserves the
load-bearing-slot property without forcing per-metric prose to do
the same job twice. Carrying the §§1–3 shape mechanically into §4
would have produced metrics-shaped-like-arguments and either
inflated each metric to 200+ words or left two slots underwritten.

**Each §3 proposal has at least one §4 metric pointed at it.**
This is the load-bearing job §4 was supposed to do for §3, locked
explicitly so a future revision cannot quietly drop a §3 proposal
without also revisiting its measuring metric. The pairings:
Proposal A (routing transparency) → §4.1.2 Auto-mode mix; Proposal
B (index-freshness indicator) → §4.2.2 Index-freshness coverage;
Proposal C (stop-criteria UI) → §4.2.1 Agent stop-precision. The
two non-§3-paired leading-quadrant metrics (§4.1.1 `@`-mention
adoption, §4.3.1 retention by cohort) test the §1.1/§1.2 thesis
that the explicit-context model is what earns long-tenure trust —
they are the §§1.1–1.2 monitoring metrics, distinct in purpose
from the §3-proposal evaluation metrics, and the framework labels
both purposes inline so a reader knows whether each metric is for
evaluating a *shipped change* or monitoring an *existing PM
choice*.

**Slice-4 cross-section binding discharged.** Slice 4's DECISIONS
entry asserted "the per-task scope of the stop-permissive opt-in is
itself a contract for slice 5's metrics: any 'agent stop-precision'
metric that defines success has to read the per-task scope as a
feature of the proposal, not as a detail to abstract over." §4.2.1
discharges this contract: the caveat slot names default-mode and
opt-in-mode reporting separately, with the default-mode read as
headline, and explicitly cites the slice-4 per-task scope as
load-bearing for the metric's interpretation. The §6 worked example
('Eval-harness for agent stop-criteria') in the outline also cross-
binds to §4.2.1 — the §6 method is what produces the §4.2.1 number,
so any later §6 polish that changes the worked example must keep
the §4.2.1 link intact or rewrite both together.

**No fabricated baselines, targets, or benchmarks.** Every metric
names what to compute, what decision it informs, and how it can
mislead — none names a target Cursor should hit. Quoting an
internal Cursor number would fabricate it; quoting a public
benchmark would mis-cite a measurement made on a different product
or population. The framework is the artifact, not the dashboard.
This carries the masthead no-fabrication posture into the metrics
section verbatim and matches the §1 pricing-tier and §2 free-tier
quota cut rationale.

**Cross-section linkage table (informational, not in document):**

| Metric | §-link | §3 proposal | Quadrant |
|---|---|---|---|
| 4.1.1 `@`-mention adoption | §1.2 | — | Lead × Adopt |
| 4.1.2 Auto-mode mix | §2.1 | A | Lead × Adopt |
| 4.2.1 Agent stop-precision | §2.3 | C | Lead × Quality |
| 4.2.2 Index-freshness coverage | §2.2 | B | Lead × Quality |
| 4.3.1 90-day retention by `@` cohort | §1.2 | — | Lag × Adopt |
| 4.4.1 NRR on Business tier | §1 pricing | — | Lag × Business |

**Word-budget discipline carried from slices 2–4 with a section-
shape caveat.** §§1–3 sub-sections ran ~360–500 words per slot-5
sub-section. §4's metrics use a four-slot shape and are intended to
be shorter per metric: ~150–250 words per metric × 6 metrics
= ~1100 words total for the section body, comparable to a §§1–3
section total. Per-metric brevity is a feature: the metrics section
should be scan-readable as a framework, not a debate. If a future
polish slice finds a metric ballooning past the per-metric budget,
the right move is to split into "metric + child metric" or to
demote to a follow-up artifact, not to inflate prose.

**Header convention** carries from slices 2–4 unchanged: `## 4.
Proposed metrics` for the top-level section, `### 4.M …` three-
level headers for sub-sections that group metrics by quadrant, and
`**4.M.N <metric name>.**` bold-inline numbered headers for each
metric inside its quadrant sub-section. Bold-inline rather than
`####`-headers because each metric is paragraph-sized; promoting
each to a fourth-level header would over-fragment the section and
defeat the scan-readable framework property.

**Out of scope for this iteration** (deliberate, named so the next
iteration cannot silently inherit them):

1. **Edits to §§5–6.** Those sections remain in outline /
   intent-paragraph state. The next slice drafts §§5–6 together
   (out-of-scope items and how-I'd-validate methodology) per the
   slice-3 entry's "slices 5 + 6 land together" pre-commitment
   from the seven-step plan; the final iteration is polish.
2. **Revisions to §§1–3, the masthead, or the scope decision.**
   The drafted §§1–3, the §1 and §2 cut paragraphs, the §3
   transition paragraph, and the scope decision all stand. If a §4
   metric appears to require restating a §3 proposal's mechanism,
   the §4 metric is revised, not the upstream proposal.
3. **A seventh metric added mid-draft, or a fifth quadrant.** §4
   has exactly six metrics in a 2-2-1-1 distribution across the
   standard PM 2×2. Adding a seventh (e.g. a "Leading × business"
   metric like gross margin per developer-week) would re-open the
   pricing-and-positioning cuts §1 and §2 closed and break the
   no-fabrication posture by requiring per-model unit-cost
   numbers Anysphere does not publish.
4. **Specific targets, baselines, or benchmarks.** Every metric
   names what to compute and how it can mislead — never what
   Cursor should hit. A future iteration that promotes a target
   number is a supersession requiring a citation or a labeled
   conjecture, not an additive edit.
5. **Promotion of the cut sub-areas (pricing-tier from §1,
   free-tier quota from §2) into deep-dive metrics with multiple
   sub-metrics.** Pricing surfaces lightly via §4.4.1 NRR on
   Business tier; free-tier quota does not surface in §4 at all,
   matching the slice-3 entry's "free-tier quota surfaces …
   lightly … in §4's lagging-adoption metrics row (free-to-paid
   conversion)" — which the slice-5 draft chose *against*
   including, replacing it with a Business-tier NRR metric because
   the free-to-paid conversion number would require a quota baseline
   the public surface does not expose. The slice-3 entry's pre-
   commitment is hereby narrowed: free-tier quota does not appear
   in §4. Recording this narrowing here so future polish does not
   reopen it on the strength of the slice-3 hint.
6. **Any change to the rag-app corpus v1 file list.** Corpus v1
   stays locked to (OBJECTIVE.md, DECISIONS.md,
   templates/INTERVIEW_TRACKER.md, rag-app/README.md). The teardown
   file itself remains outside the corpus and its drafted §4 does
   not perturb the rag-app index.

**Implication for the rag-app corpus_fingerprint:** this iteration
touches DECISIONS.md but not the other three corpus-v1 files; per
the per-iteration drift pattern documented from iteration 16 onward,
the rag-app corpus_fingerprint will rotate. The
teardown-prd/cursor-teardown.md file's drafted §4 is not in the
corpus, so its drafting does not perturb the index — only this
DECISIONS entry and the small status-line update at the top of the
teardown file matter, and only the DECISIONS entry actually
contributes to corpus drift. Tool-use-agent catalog is unchanged so
its fingerprint stays at 626af64cb9bf48bf. Evals-harness cross-build
invariants (refusal_sentence_byte_equal, trace_helpers_behavior_
equivalent) still pass.

## 2026-05-16 — Cursor teardown PRD slice 6: "Out of scope" + "How I'd validate" drafted together

**Decision:** §5 ("Out of scope") and §6 ("How I'd validate") of
`teardown-prd/cursor-teardown.md` both ship in drafted state in a
single iteration, replacing the outline-slice intent paragraphs with
substantive prose. This is the "slices 5 + 6 land together" call
pre-committed by iteration 27's seven-step slicing plan and
re-affirmed in slice-5's DECISIONS entry. The masthead Status line
flips from "§§1–4 drafted; §§5–6 in outline state" to "§§1–6
drafted; final iteration is polish." The remaining work is one
polish iteration covering masthead consistency, cross-section
references, a no-fabrication grep audit, source-list reconciliation,
and a final read-aloud pass.

**Two sections, one iteration — rationale.** §5 and §6 are both
methodology-shaped (not argument-shaped like §§1–3 and not
framework-shaped like §4), and each section is short enough on its
own that splitting them into two iterations would have left each
iteration under-loaded. Per the iteration-30/31 word-budget
pattern (drafted sections run 1100–1500 words), §5 at ~830 words and
§6 at ~880 words individually undershoot a normal slice; combined
at ~1700 words they sit cleanly inside one slice's budget. The
seven-step plan from iteration 27 pre-committed this combination
explicitly, so this iteration honors that plan rather than
re-litigating it.

**§5 shape: three-slot per-item, paragraph-sized.** Each of the
seven out-of-scope items follows a (name + one-line definition,
why excluded with rationale category, where if anywhere it surfaces
elsewhere) shape, ~85–130 words per paragraph. This is a *third*
shape variant in the document (§§1–3 use five slots, §4 uses four
slots, §5 uses three) — the shape thins as the content type moves
from argument → framework → scope decision. The bold-inline
**5.N name.** header convention carries from §4 because the items
are paragraph-sized; promoting them to `###` would over-fragment
the section, and using only `## 5.` with no sub-headers would lose
the scan-friendly per-item bookmark a reader uses to jump to a
specific exclusion. The §5 evidence-sources paragraph at the end
deliberately notes that no per-item sources are required because
each entry is a scope decision, not a fact-claim about Cursor — a
distinction that matters for the polish-iteration grep audit (no
out-of-scope paragraph needs a citation).

**Seven items, not five.** The scope-decision paragraph at the top
of the teardown named five out-of-scope categories at outline time.
The §5 draft adds two more (competitive landscape ranking;
founder / company analysis) that became visible during the §§1–3
draft because each kept generating sentences that pulled toward
content the document deliberately excludes. The §5 opener names the
five-plus-two split explicitly so a reader who notices the two
additions in §5 but not in the scope decision sees them documented
rather than as an apparent inconsistency. The §1 pricing-tier and
§2 free-tier-quota cuts are explicitly *not* re-listed in §5
because those are *sub-section-level narrowings*, not *document-
level exclusions* — a different category of cut with different
load-bearing rhetoric, and conflating the two would have weakened
both the §5 list and the §§1–2 cut paragraphs. The slice-5 entry's
"sub-section-level narrowing" framing transfers here verbatim.

**§6 shape: four-slot per-method, with an explicit non-method.**
Each of the four validation methods (§6.1–§6.4) follows a (method
name + how it works, which §3 proposal or §4 metric it ties to,
success threshold, known limit) shape, ~155–220 words per method.
§6.5 is a *non-method* (pricing-page A/B testing) with its own
rationale paragraph, parallel in form to the §1 and §2 cut
paragraphs — listing the deliberately-not-used method is itself a
PM-craft signal. The four-slot per-method shape mirrors §4's
four-slot per-metric shape but with one slot's semantics flexed
(metric-mislead-caveat ↔ method-known-limit; both are the "ways
this can lie to you" slot, the load-bearing-slot-flexes-by-section-
purpose pattern noted in slice-3 and slice-5 entries continues to
hold). Pre-launch / post-launch ordering across the four methods
(§6.1 internal replay → §6.2 flag-gated rollout → §6.3 qual
research → §6.4 offline eval) is named in the section opener so
the section reads as a workflow rather than a menu.

**Per-proposal validation coverage table (informational, not in
document):**

| §3 Proposal | §6 method(s) | §4 metric |
|---|---|---|
| A — Routing transparency | §6.1 (replay) + §6.2 (rollout) | §4.1.2 |
| B — Index-freshness indicator | §6.1 + §6.2 + §6.3 (qual) | §4.2.2 |
| C — Agent stop-criteria UI | §6.1 + §6.4 (offline eval) | §4.2.1 |

Every §3 proposal has at least one §6 method paired to it, and the
opt-in-mode portion of Proposal C explicitly does *not* rely on
§6.2 flag analytics (instead routes through §6.4's separate fixture
sub-set) — discharging the slice-4 / slice-5 per-task-scope contract
end-to-end through validation, not just through the §4 metric. Any
polish iteration that touches §6.4 must preserve the separate-
fixture-sub-set treatment of opt-in mode or rewrite the §3.3 /
§4.2.1 / §6.4 chain together.

**Cross-build cross-binding: §6.4 ↔ evals-harness/.** §6.4 is the
single verifiable cross-reference in §§5–6 — it names this repo's
`evals-harness/` build as a worked example for the offline-eval
method's record shape (per-record JSONL), `stop_reason` enum
semantics (ended_clean vs. cap-exhausted), and rubric output
convention (the slice-20 termination-rubric output). This is the
load-bearing reason the three GitHub builds and the teardown PRD
sit in the same repository: a reader reading §6.4 can `cd
../evals-harness && cat README.md` and see the named conventions
in working code. If a polish iteration tightens the §6.4 prose, it
must keep these three named conventions intact, because a polish
that loosens any of the three would silently break the cross-
artifact link the §6.4 evidence-sources paragraph claims is
inspectable.

**§5 + §6 evidence-sources policy.** Per-paragraph inline citations
are *deliberately absent* from both sections, by section type:
§5 items are scope decisions (not fact-claims), and §6 methods are
methodology arguments (not surface-of-Cursor claims). §6.4 is the
single exception and surfaces its evidence cross-link in the
section-level evidence-sources paragraph rather than inline.
The polish-iteration grep audit for "claims without citations"
should treat §5 and §6 paragraphs as exempt by category — same
exemption §4 metric paragraphs received under the slice-5 rationale.

**Word-budget discipline carried with a documented flex.** §5 sits
at ~830 words, §6 at ~880 words; combined ~1710 words, ~10% under
the §3 / §4 section totals (~1400 each + opener / cuts =
~1500–1600). The under-shoot is acceptable for two reasons:
(1) per-paragraph budgets are honored (§5 items at 85–130 words,
§6 methods at 155–220 words), and (2) §§5–6 are the document's
shortest sections by design — the section opener "name what is
deliberately not done" + the methodology section are each meant to
be scan-readable as a list of decisions, not a debate. A polish
slice that finds either section thin should not pad prose to hit a
section budget; the per-paragraph budgets are the load-bearing
discipline.

**Status-line update.** The masthead Status field now reads "§§1–6
drafted; the final iteration is a polish / leave-behind framing
pass per the seven-step slicing plan locked in DECISIONS.md." This
is the second masthead Status touch (the first was iteration 30
flipping the §3 from outline to drafted). Polish iterations may
touch this line again; intervening slices may not, because the slot
records cumulative draft state.

**Out of scope for this iteration** (deliberate, named so the
polish slice cannot silently inherit them):

1. **Edits to §§1–4 or to the scope decision.** Every §§1–4 word
   that the polish iteration would touch is in *polish* scope, not
   in this iteration. If §6 calls out a §3 proposal or §4 metric
   in a way that suggests the §3 / §4 text could be sharper, the
   §6 reference is rewritten to fit the existing §3 / §4 text, not
   the other way around.
2. **An eighth out-of-scope item added to §5.** §5 has exactly
   seven items (five from scope decision + two added at draft
   time). A future iteration that finds an eighth must either add
   it to the scope decision first (and rev §5 in lockstep) or
   document the addition in a polish-slice DECISIONS amendment.
3. **A fifth validation method or a second non-method.** §6 has
   exactly four methods plus one non-method. The pricing-page A/B
   non-method is the only validation method deliberately excluded
   by name; any other technique not listed (e.g. dogfood-via-
   internal-bug-bash, support-ticket-mining) is *unlisted*, not
   *excluded*, and adding it would shift §6's shape from "four
   methods covering the three §3 proposals" to "open-ended
   methodology grab-bag" — a different rhetorical job.
4. **Promotion of any §5 item into a deep-dive elsewhere.** The
   seven §5 items are scope-bounded paragraphs by design. Lifting
   §5.2 (provider economics) into a §3.4 proposal, for example,
   would re-open the no-fabrication-on-unit-costs cut and turn the
   teardown into a different document.
5. **Pricing-page validation surface migrating into §4.4.1.** §6.5
   already names where a pricing experiment signal *would* belong
   (lagging business-quadrant, §4.4.1 NRR cycle, separate from
   §3). Migrating that surface into a §4.4 sub-metric in this
   iteration would re-open §4's six-metric lock from slice-5.
6. **Any change to the rag-app corpus v1 file list.** Corpus v1
   stays locked to (OBJECTIVE.md, DECISIONS.md, templates/
   INTERVIEW_TRACKER.md, rag-app/README.md). The teardown file
   remains outside the corpus and its drafted §§5–6 do not perturb
   the rag-app index.

**Implication for the rag-app corpus_fingerprint:** this iteration
touches DECISIONS.md plus the teardown file's masthead Status line
and §§5–6 body. Per the per-iteration drift pattern documented
since iteration 16, the rag-app corpus_fingerprint will rotate
because DECISIONS.md is in corpus v1; the teardown file is *not*
in corpus v1 so its 1700-word body change does not perturb the
index. Tool-use-agent catalog is unchanged so its fingerprint
stays at 626af64cb9bf48bf. Evals-harness cross-build invariants
(refusal_sentence_byte_equal, trace_helpers_behavior_equivalent)
still pass.

## 2026-05-16 — Cursor teardown PRD slice 7 (polish): masthead reflects terminal state, source-list reconciled, cross-references cleaned

**Decision:** The seven-step slicing plan locked in iteration 27's
DECISIONS entry has now landed end-to-end. This is the final
polish / leave-behind framing pass. The teardown PRD's body is
unchanged in substance — no edits to §§1–6 prose beyond the four
surgical fixes documented below. Three classes of polish ship:
(1) the masthead Status line flips from "§§1–6 drafted; final
iteration is polish" to terminal state declaring the document
interview-ready, (2) two stale cross-references and one
build-process leakage are corrected, (3) the source-list section
heading and one bullet are reconciled with what the body actually
cites.

**Masthead Status flip.** The Status line is now in a terminal
shape and will not need another flip without a substantive content
revision. The slot is reserved for cumulative draft-state, locked
in iteration 32's slice-6 entry as "polish iterations may touch
this line; intervening slices may not." The terminal-state phrasing
("polish pass complete (2026-05-16) — interview-ready") is
deliberately dated so a reader can map the document's snapshot to
the observation snapshot dated immediately below. A future
substantive revision would write a new Status line whose date
matches its content; mechanically advancing the snapshot date
without changing the body would be a fabrication.

**Three cross-reference fixes (surgical, not stylistic).**

1. **§2 and §2's cut paragraph referenced "§1.4 cut paragraph"
   twice (lines 251, 411 of the pre-polish file).** §1's cut
   paragraph is an unnumbered `### Cut from the outline's four: …`
   header, not a `### 1.4` heading — so "§1.4" pointed nowhere.
   Polish replaces both with "§1's pricing-tier cut paragraph"
   (lossless, more readable, points to a real location). This
   typo class would have surfaced under any careful read-aloud
   pass; logging it here so future multi-section artifacts
   sectioning numbered sub-sections plus unnumbered cut paragraphs
   pre-commit a reference grammar that does not invent slot
   numbers for unnumbered slots.

2. **Build-process leakage in §4.2.1 caveat.** The caveat sentence
   said "the per-task scope from slice-4 DECISIONS is a feature
   of the proposal." `slice-4 DECISIONS` is gnhf-iteration
   scaffolding; a leave-behind PRD reader has no access to that
   reference. Polish replaces with "the per-task scope from §3.3"
   — same load-bearing claim, self-contained inside the document.
   The §6.4 sentence carried the same leak and the same fix.

3. **Scope decision had a "DECISIONS amendment" pointer plus a
   non-sequitur "See the 'How I'd validate' section."** §6
   validates §3 proposals, not the scope choice, so the pointer
   was wrong. Polish rewrites the paragraph to a clean reader-
   redirect frame ("This scope is open to reader feedback…") with
   two named alternative scopes (Tab autocomplete, Cursor CLI)
   drawn from the §5 out-of-scope list. The substantive property
   from iteration-27's notes — that scope is reader-redirectable,
   not pre-gated — is preserved in plain language without exposing
   the iteration scaffolding.

**Source-list reconciliation.** Two reconciliations against actual
inline citation usage:

- Section heading: "Sources & observation snapshot (drafted
  alongside the body)" → "Sources & observation snapshot." The
  parenthetical was outline-era process language; the body is now
  drafted and the qualifier no longer carries meaning. Verb
  tenses in the opening paragraph also shift from future
  ("will cite") to present ("cites").
- User-community-reports bullet: "(Discord, X, Hacker News)" →
  "(Cursor's public forums; Discord, X, and Hacker News threads
  that are public-readable)." Three §2 sub-sections cite "public
  Cursor forum threads" inline; the original bullet omitted that
  surface and named three platforms the body does not directly
  cite. Reconciled to match what the body actually says.
- Pricing-page bullet: added "(cited in §4.4.1 only)" qualifier
  since `cursor.com/pricing` appears in exactly one place in the
  body — §4.4.1's evidence-sources paragraph. This is the
  smallest accuracy gain that preserves the bullet's value as a
  citation-grammar reference.

**No-fabrication grep audit.** Scanned the drafted body for any
specific numeric or surface-specific claim that was not either
sourced inline or labeled as methodology / proposed-default /
sample-size:

- "≥60%", "15%+", "0%", "5%", "≥90%" — all in §6 as method
  thresholds / sample percentages (proposed validation
  shapes, not claimed Cursor metrics).
- "80%" — §2.4 cut paragraph proposing a quota-meter warning
  threshold (a proposed design pattern, not Cursor's current
  threshold).
- "30 seconds", "300ms", "~5k files", "~100k files",
  "~10–15", "~200 turns", "~5%" — all methodology shapes
  (defaults / sample sizes / observable thresholds for
  reproduction), each tied to a method or proposal that names
  the number as proposed, not asserted about Cursor.

No fabricated Cursor metrics, revenue numbers, user counts,
support-ticket volumes, or roadmap claims found in the body.
The no-fabrication guardrail from OBJECTIVE.md is intact and
the audit will not need re-running on subsequent reads unless
new numeric content is added.

**Read-aloud touch-up scope.** Deliberately narrow. The polish
slice changes exactly four prose locations (masthead Status,
scope-decision reader-redirect paragraph, §4.2.1 caveat tail,
§6.4 sentence in the middle of the method) plus the source-list
heading and two bullets. No sentences in §§1–3 body, §4 metric
paragraphs, §5 out-of-scope items, or §6.1–§6.3/§6.5 methods are
touched. The discipline: a polish slice corrects defects (typos,
wrong cross-refs, stale framings), it does not re-edit prose
that is doing its job. This bounds the iteration so a reviewer
diff can be read in five minutes and the substantive arguments
of §§1–6 stand exactly as they were drafted.

**Lessons on what "polish" can and cannot do for multi-iteration
PM documents.** Three rules carry forward to any future polish
slice on a similar multi-iteration artifact:

1. **Polish corrects defects, not arguments.** A sentence the
   polish slice author *would have written differently* but
   that is doing its argumentative job stays as drafted. Polish
   is for typos, stale cross-references, build-process
   leakage, and reconciling lists with body content. Anything
   load-bearing belongs to a substantive-revision slice with
   its own DECISIONS entry naming the change.
2. **Polish surfaces what the drafted slices accumulated as
   technical debt.** §1.4 cross-reference, "slice-4 DECISIONS"
   leakage, the wrong "See §6 for scope checks" pointer — none
   of these were drafting errors at the time, each was correct
   *for the iteration it landed in* and then became incorrect
   as the document grew around it. Naming this dynamic helps
   the next multi-iteration artifact pre-commit a polish slice
   rather than treat each drafted slice as
   already-shipped-clean.
3. **Polish ships the Status line to terminal state.** The
   pre-polish Status line ("final iteration is polish") was
   self-referencing scaffolding. A leave-behind document's
   Status line should describe the *document*, not its
   production process. Future polish slices on similar
   artifacts should plan the final Status-line phrasing as a
   first-class output, same way an engineering release's
   final commit message phrases the user-visible change rather
   than the bisect-recovery surgery.

**Out of scope for this iteration** (deliberate, named so no
future iteration silently inherits them as polish-class):

1. **Any substantive prose revision in §§1–6.** No
   re-argued tensions, no swapped examples, no new tradeoffs
   surfaced. A polish slice that ships a new tradeoff is no
   longer a polish slice — it is an unnumbered slice 8.
2. **A new "Limitations" or "Caveats" section.** Adding a
   chapter would expand the seven-section structure pre-
   committed in iteration 27 and re-affirmed every drafted
   slice since. Limitations are already named per-section
   (§5 out-of-scope, §§1–4 cut paragraphs, evidence-sources
   paragraphs) — duplicating them under a chapter heading
   would dilute the per-section discipline.
3. **Promoting the four §6 methods into a comparison table.**
   §6 reads as a workflow because the methods are pre-launch-
   to-post-launch ordered; promoting them to a side-by-side
   table would lose the workflow framing and re-introduce the
   "open-ended methodology grab-bag" risk slice 6's DECISIONS
   entry explicitly excluded.
4. **A masthead "Read this if you are…" frame for different
   reader audiences.** Adding reader-audience framing would
   bias the document toward a single reader segment (Cursor PM
   vs. interviewer vs. competing-product PM) when the drafted
   §§1–6 deliberately let all three read the same body.
5. **Any change to the rag-app corpus v1 file list.** Corpus
   v1 stays locked to (OBJECTIVE.md, DECISIONS.md, templates/
   INTERVIEW_TRACKER.md, rag-app/README.md). The teardown file
   remains outside corpus v1; its polish edits do not perturb
   the rag-app index.
6. **A regenerated source-citation index at the document
   foot.** The per-section evidence-sources paragraphs plus
   the source-list bullets already enumerate every category;
   a full citation index would be the right addition if this
   document grew a citations-per-paragraph density that
   warranted footnote numbering, which it does not at this
   word count.

**Implication for the rag-app corpus_fingerprint.** This
iteration touches DECISIONS.md (this entry) plus the teardown
file's masthead, scope-decision reader-redirect paragraph, two
mid-body sentences (§4.2.1 caveat tail, §6.4 method body), and
the source-list heading and two bullets. Per the per-iteration
drift pattern documented since iteration 16, the rag-app
corpus_fingerprint will rotate because DECISIONS.md is in corpus
v1; the teardown file is *not* in corpus v1 so its polish edits
do not perturb the rag-app index directly. Tool-use-agent
catalog is unchanged so its fingerprint stays at
626af64cb9bf48bf. Evals-harness cross-build invariants
(refusal_sentence_byte_equal, trace_helpers_behavior_equivalent)
still pass.

**Status of the seven-step slicing plan.** Complete. The plan
locked in iteration 27 mapped exactly to iterations 27→33:
outline (27) → §1 (28) → §2 (29) → §3 (30) → §4 (31) →
§§5–6 combined (32) → polish (33, this entry). Cursor teardown
PRD is the third and final concrete artifact in the AI PM
portfolio scoped by OBJECTIVE.md (alongside rag-app, tool-use-
agent, and evals-harness, all complete). The DECISIONS.md
record of seven iterations on this document plus 21 prior
iterations on the three builds and two on the user-gated pick
gates is intended to read as a portfolio-of-decisions in its
own right — the audit trail an interviewer asking "how did you
get here" can scan in roughly the time it takes to read §§1–6.

## 2026-05-16 — Resume scaffold shape and the deferred cover-letter scaffold

**Decision:** `templates/RESUME.md` ships as a populatable one-page PM
resume scaffold with a locked section order
(`Header → Summary → Experience → Selected AI/PM portfolio →
Skills → Education → optional Writing/Talks → optional
Certifications`) and the same `_<placeholder>_` italic-marker
convention `templates/INTERVIEW_TRACKER.md` uses, so a single regex
(`_<.*>_`) can find unfilled slots across both files. ATS-friendly
rules are baked into the "How to use" section: no tables in
experience, no columns, no images, H2 for section headers and H3 for
role / build sub-headers. The **Selected AI/PM portfolio** section
is pre-stubbed with this repo's three Day-10 builds (rag-app,
tool-use-agent, evals-harness) and the Day-20 Cursor teardown PRD
as named portfolio slots the user can claim once they have actually
demoed each end-to-end. The cover-letter scaffold is explicitly
deferred to the next iteration; this entry locks the resume
contract only.

**Rationale.** (a) **Why a scaffold and not a filled draft.** The
no-fabrication guardrail (OBJECTIVE.md + the 2026-05-16 "No
fabricated employment history" DECISIONS entry) means every concrete
specifier — companies, dates, metrics, project titles — has to come
from the user. The agent's job is to lock the shape so the user does
not have to invent it, and to bake in the PM-craft conventions
(action-verb + metric bullets, three-to-five-role band, one-page
budget, ATS hygiene) that a generic resume template would not carry.
(b) **Why this section order.** Summary first because the recruiter
six-second scan reads top-down and the Bucket-2 targeting line is
the single highest-leverage real estate; Experience second because
that is what every ATS parser expects in slot two; **Selected AI/PM
portfolio** third — promoted ahead of Skills and Education — because
this 90-day plan's whole leave-behind story sits in that section and
burying it after Skills would undersell the three builds and the
teardown PRD. Skills and Education trail as conventional, with
Writing/Talks and Certifications as opt-in sections gated on the
"only include if you have at least two truthful items" rule that
prevents thin or performative sections. (c) **Why share the
placeholder grammar with the tracker.** A single regex (`_<.*>_`)
catches stale placeholders in both files — the resume scaffold's
trailing reminder (`fastest grep is _<`) makes this explicit. If a
future iteration adds the cover-letter scaffold, it inherits the
same marker and the cross-file validator stays one line. (d) **Why
the AI/PM portfolio section is pre-stubbed with this repo's four
artifacts.** The whole point of the Day-10 and Day-20 work is to
have something to point at in interviews. Naming the three builds
and the teardown by their actual repo paths in the scaffold means
the user does not have to remember which artifact lives where, and
the scaffold's "delete only what you cannot demo" rule keeps the
honesty bar visible — a placeholder portfolio bullet is worse than
no portfolio bullet because it advertises an artifact the
interviewer can ask about and the user cannot defend. (e) **Why
defer the cover-letter scaffold to a separate iteration.** The
two artifacts share the no-fabrication guardrail and the
placeholder grammar, but they have different shape constraints:
resumes are one-page structured documents with a fixed section
order; cover letters are 250–400-word prose pieces parameterized
by the target company / role / connection. Shipping both in one
iteration would have either inflated this iteration's surface or
under-served the cover letter. The one-complete-artifact-per-
iteration rule prefers a fully-defended resume scaffold now plus
a fully-defended cover-letter scaffold next iteration over both
landing at half quality together. The cover-letter scaffold should
reuse the `_<placeholder>_` convention and reference back to the
resume's Summary and Selected AI/PM portfolio sections as the
single source of truth for company-agnostic claims, so the user
does not have to keep two drafts of "what I shipped at <Company>"
in sync.

**Out of scope for this iteration.** (1) No cover-letter scaffold
(deferred to the next iteration, as noted above). (2) No
LinkedIn-profile scaffold — the resume's Header section already
points at the LinkedIn URL, and the AI/PM portfolio bullets are the
LinkedIn About-section content in raw form; a separate scaffold
would duplicate the placeholders without adding surface. (3) No
filled-in example resume — every slot is a placeholder, and an
example would invite the user to copy phrasing rather than write
their own. (4) No automated placeholder-validator script — the
trailing-reminder grep guidance is enough at this artifact count;
a `python -m templates lint` command can be added in a future
iteration if a third scaffold lands. (5) No edit to corpus v1 — the
new `templates/RESUME.md` file is NOT in the rag-app corpus list
(corpus v1 is locked to four specific files), so the resume scaffold
does not perturb the rag-app index directly; only this DECISIONS
entry does, by the standard per-iteration drift pattern. (6) No
edit to the three builds or the Cursor teardown PRD — this
iteration is purely a templates/ addition.

## 2026-05-16 — Cover-letter scaffold shape and opener-variant lock

**Decision:** `templates/COVER_LETTER.md` ships as a populatable
cover-letter scaffold paired with `templates/RESUME.md` and
`templates/INTERVIEW_TRACKER.md`, discharging the deferral the prior
DECISIONS entry pre-committed. The scaffold uses the same
`_<placeholder>_` italic-marker grammar the tracker and resume use,
so one regex (`_<.*>_`) now validates all three scaffolds. The body
shape is fixed: **Header → Opening (one of three variants) → Para 2
Track record → Para 3 AI craft proof → Para 4 Why this role and what
you would do first → Closing**, with a target body length of
**250–400 words** (excluding header and sign-off). The opening
section ships three mutually-exclusive variants — **Cold
application**, **Referral**, and **Inbound recruiter response** —
each one a complete paragraph the user picks one of and deletes the
other two before sending. Paragraph 3 deliberately quotes one or two
artifacts from `RESUME.md`'s Selected AI/PM portfolio section in
prose and points at the repo, rather than restating the portfolio
bullet by bullet; this keeps the resume as the single source of
truth for company-agnostic claims so the user maintains them in one
place.

**Rationale.** (a) **Why three opener variants, not one canonical.**
The three sourcing channels (cold direct apply, referral, inbound
recruiter response) require materially different opening rhetoric:
a referral does the warm-intro work so the opener can pivot to the
product observation immediately, a recruiter response has to first
acknowledge their outreach to avoid reading as auto-replied, and a
cold application has to earn attention in the first two sentences
with a specific company-product observation. Shipping one canonical
opener would have forced the user to rewrite it per channel anyway,
silently inviting the bland "I'm passionate about your mission"
default. Locking three variants with explicit "pick one and delete
the other two" guidance puts the choice at the right level. (b)
**Why 250–400 words and not shorter or longer.** Under 250 words
reads as effort-light and gives the hiring manager no surface to
react to; over 400 reads as a second resume and recruiters skim the
middle. The target band lands at roughly four substantive paragraphs
of three to four sentences each, which is the natural rhythm of a
hiring-manager-readable letter and matches the upper bound recruiters
report skimming. The "if you go over, cut from paragraph 3" rule
is specific enough to be enforceable in editing without re-arguing
the structure. (c) **Why paragraph 3 quotes the resume by reference,
not by restatement.** Restating the Selected AI/PM portfolio bullets
verbatim in the letter would force the user to keep two drafts of
"what I shipped at <Company>" in sync, which is a maintenance burden
and an inconsistency hazard (the two drafts will drift the first
time the user edits one and forgets the other). Pointing the reader
at `../templates/RESUME.md`'s portfolio section and quoting at most
one or two artifacts in prose form is the single-source-of-truth
discipline the iteration-34 DECISIONS entry pre-committed.
(d) **Why the company-specific observation slot is named explicitly
and rule-bound.** The single sentence that distinguishes a strong
AI PM cover letter from a generic one is a specific, falsifiable
observation about the company's AI product — a UX choice, a missing
affordance, a metric they probably watch — that proves the user has
actually used the product and thought about it as a PM. The "How to
use" section names this explicitly as "the highest-leverage sentence
in the letter" with an example shape that ties it back to the Cursor
teardown PRD's PM craft pattern (sourced observation → trade-off it
implies), so the user has a concrete model to imitate rather than
inventing the rhetorical move from scratch. The same paragraph
warns against "generic praise" as the easiest signal to discount.
(e) **Why an explicit channel-hygiene rule about plain-text paste.**
A recruiter or hiring manager reads cover letters in their mail
client, not in a Markdown renderer; a docx attachment when the
ATS asked for a paste-in is friction. Naming the channel hygiene
in the "How to use" section rather than leaving it implicit
prevents the most common formatting mistake at zero cost. (f)
**Why no per-target-company example.** The same logic as the
resume scaffold's "no filled-in example" decision applies here
with extra force: an example cover letter would invite the user
to copy phrasing rather than write their own company-specific
observation, which is exactly the sentence that carries the
letter's signal. The scaffold ships shape and rules, not draft
prose.

**Out of scope for this iteration.** (1) No follow-up-email
scaffold — once the recruiter or hiring manager responds, the
exchange is conversational and a templated follow-up would read
as templated. The interview-tracker's "Next action" column carries
the cadence load instead. (2) No LinkedIn-DM scaffold — DMs are
30–60 words, structurally different from a 250–400-word letter,
and trying to share a shape between the two would compromise both.
A separate scaffold can land in a future iteration if outbound
volume justifies it. (3) No automated lint script — the trailing
`_<` grep reminder is enough at three scaffolds; the iteration-34
"add a `python -m templates lint` command if a third scaffold
lands" hint is intentionally not discharged here because three
files do not yet justify a tool over a one-line grep, and the
scaffold's own trailing reminder names the grep explicitly. The
threshold for the lint command remains "fourth scaffold or first
real misuse." (4) No filled-in example letter targeting a specific
company — see rationale (f). (5) No edit to corpus v1 — the new
`templates/COVER_LETTER.md` file is NOT in the rag-app corpus list
(corpus v1 is locked to four specific files), so this scaffold
does not perturb the rag-app index directly; only this DECISIONS
entry does, by the standard per-iteration drift pattern documented
since iteration 16. (6) No edit to the three builds, the Cursor
teardown PRD, the resume scaffold, or the interview tracker — this
iteration is purely a `templates/COVER_LETTER.md` addition plus
this DECISIONS entry.
