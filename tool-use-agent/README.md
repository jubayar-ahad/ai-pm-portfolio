# tool-use-agent

[![CI](https://github.com/jubayar-ahad/ai-pm-role-90days/actions/workflows/ci.yml/badge.svg)](https://github.com/jubayar-ahad/ai-pm-role-90days/actions/workflows/ci.yml)

A small tool-using Claude agent, framed for an AI PM portfolio.

This README is the design contract for the build. It locks scope, stack, and
the PM-relevant decisions so subsequent iterations can land code without
re-litigating choices. Code lives alongside this README and lands
incrementally — see [Status](#status) for what currently runs.

---

## Status

| Slice | State |
| --- | --- |
| Design doc (this README) | Shipped |
| Tool catalog (pure-Python, no LLM) | Shipped |
| Single-step agent loop (one tool call, then answer) | Shipped |
| Multi-step agent loop (chained tool calls, bounded) | Shipped |
| Refusal + bounded-step termination | Shipped |
| Eval-trace records (`tool-use-agent.ask.v1`) | Shipped |

The `ask` subcommand runs in two modes, matching the `rag-app/` build.
With `ANTHROPIC_API_KEY` set it calls Claude with `tools=[…]`, runs whichever
tool(s) the model requests, returns the results, loops up to
`--max-steps` (default 6) until the model returns an `end_turn` without a
new tool call, and prints Claude's final answer plus a per-step trace.
The loop terminates in one of three deterministic states surfaced as a
`refusal_reason` discriminator in the JSON trace: `end_turn` (clean
finish, `refusal_reason=null` unless the model itself returned the
canonical refusal sentence, in which case `refusal_reason="model_refused"`),
`max_steps_exhausted` (cap reached — `final_text` becomes the canonical
`REFUSAL_SENTENCE`, byte-identical to `rag-app/`'s), or
`repeated_tool_error` (same `(tool, input)` errored in two consecutive
steps — the loop refuses rather than letting the model spin). Without a
key (or with explicit `--dry-run`) the command prints the assembled
first-turn prompt and the tool catalog the model would see — enough to
validate the tool schema and prompt construction in a sandbox or CI
environment.

## What this demo is, in one sentence

A command-line agent that answers PM-style questions about this repo and the
interview-pipeline tracker by deciding for itself which of a small set of
typed tools to call, calling them, and citing the tool results in its answer.

## Why an agent and not RAG

This build deliberately overlaps with `rag-app/` on its data surface (it can
read the same repo markdown) and deliberately diverges on its retrieval
strategy: there is no pre-built index. The agent decides at query time which
file to read, which directory to list, or which tracker rollup to compute.
That is the production tradeoff worth showing on a portfolio:

- **RAG** is faster, cheaper, and more deterministic when the question shape
  is "find me the passage that answers this."
- **Tool use** is the right pattern when the question requires *structured
  computation* over the data ("how many Bucket 2 loops are still in
  recruiter-screen?"), or when the right document to read is itself a
  function of the question.

Locking both patterns side-by-side in this repo means an interviewer can
ask the obvious follow-up — *"when would you reach for one vs the other?"* —
and there is a concrete answer that points at the code.

## Tool catalog (v1)

Six read-only tools, all stdlib-only, all deterministic, all safe to call
multiple times with the same inputs:

| Tool | Signature | What it does |
| --- | --- | --- |
| `list_repo_files` | `(directory: str = ".", pattern: str = "*.md") -> list[str]` | Enumerate repo-relative paths matching a glob pattern under `directory`. Read-only, never escapes the repo root. |
| `read_repo_file` | `(path: str, start_line: int = 1, end_line: int \| None = None) -> str` | Return the named slice of a repo file. Bounded by file length; returns an error message (not a raise) if the path is outside the repo. |
| `grep_repo` | `(query: str, path: str = ".", max_matches: int = 20) -> list[Match]` | Case-insensitive substring search over text files. Returns `(path, line_number, line)` records, capped at `max_matches`. |
| `list_pipeline_rows` | `(stage: str \| None = None, bucket: str \| None = None) -> list[Row]` | Parse `templates/INTERVIEW_TRACKER.md` and return rows, optionally filtered by stage (`sourced`/`applied`/…) and/or bucket (`B1`/`B2`/`B3`). Honors the controlled vocabulary locked in DECISIONS.md. |
| `count_by_stage` | `() -> dict[str, int]` | Histogram of pipeline rows by stage. Useful for "how close am I to the Day-30 milestones?" |
| `count_by_bucket` | `() -> dict[str, int]` | Histogram of pipeline rows by bucket. Surfaces the Bucket-2 priority quickly. |

Tools are pure Python functions with explicit JSON schemas, registered in a
single catalog. The catalog is the only mutable surface — adding a tool means
appending to the catalog, not changing the agent loop. Read-only enforcement
is structural (no write tools exist) rather than policy-based.

`list_pipeline_rows`, `count_by_stage`, and `count_by_bucket` operate on the
tracker template's placeholder rows today; they will be useful immediately
once the user fills in real pipeline state, with zero code changes required.

## Stack choices

| Concern | Choice | Why |
| --- | --- | --- |
| Language | Python 3.9+ (matches `rag-app/`) | Same audience, same import path, no new toolchain. |
| Generation | Anthropic Claude (`claude-haiku-4-5-20251001` default, configurable) | Reuses the `rag-app/` provider/model decision; same `ANTHROPIC_API_KEY`. |
| Tool implementation | Stdlib only (`pathlib`, `re`, `glob`, `csv`/regex for the tracker parser) | No third-party deps for the tools themselves. Demo runs on any Python. |
| Tool dispatch | Anthropic SDK's native tool-use API (`tools=[…]`, `tool_choice="auto"`, `tool_use` / `tool_result` blocks) | Avoids re-implementing tool-call parsing on top of plain text — the SDK already does it correctly. |
| Agent loop | Bounded multi-step (`max_steps=6` default, configurable) | Caps cost in the worst case (model loops asking for the same file). Six is enough for the planned demos and a clear cliff if exceeded. |
| CLI | Three subcommands of one entry point: `python -m tool_use_agent {tool,ask,catalog}` | `tool` invokes any registered tool directly for testing; `ask` runs the LLM loop; `catalog` prints the tool schemas. |
| Refusal contract | Canonical sentence emitted when no tool returns useful info, or `max_steps` is exhausted without a grounded answer | Mirrors the `rag-app/` refusal pattern so the future evals harness can bucket refusals from both builds the same way. |
| Dry-run fallback | `ask` auto-falls back to printing the catalog + first-turn prompt if `ANTHROPIC_API_KEY` is unset | Same property as `rag-app/`: demoable in any environment. |
| Eval trace | `ask --json` will emit a `tool-use-agent.ask.v1` record (`schema_version`, `record_id`, `corpus_fingerprint`, `generated_at`, `tool_calls[]`) | The harness will reuse `rag-app/rag_app/trace.py` helpers via import so record IDs and fingerprints are byte-identical across builds. |

The Anthropic + stdlib stack means this build needs exactly one API key
(`ANTHROPIC_API_KEY`) to run end-to-end — same key the `rag-app/` build
uses. No second account, no vector DB, no model download.

## Architecture

```
user question
   │
   ▼
agent loop  ──►  Claude (tool_choice="auto")
   ▲                │
   │                │  emits a tool_use block:
   │                │    {name: "read_repo_file", input: {...}}
   │                ▼
   │         dispatch via tool catalog
   │                │
   │                ▼
   │         tool runs locally (stdlib)
   │                │
   │                ▼
   │         tool_result block back to Claude
   └────────────────┘
              (repeat, bounded by max_steps)
              │
              ▼
       final answer with inline tool-result citations
```

Notes:
- The loop terminates in exactly one of three states, all surfaced via
  `stop_reason` and a parallel `refusal_reason` discriminator on
  `AgentResult`: (a) `end_turn` — the model emitted no `tool_use`
  block this turn, `refusal_reason` is `null` unless the model's text
  is byte-equal to `REFUSAL_SENTENCE` (in which case
  `refusal_reason="model_refused"`); (b) `max_steps_exhausted` — the
  cap was hit, `final_text` is `REFUSAL_SENTENCE`,
  `refusal_reason="max_steps_exhausted"`; (c) `repeated_tool_error` —
  the same `(tool, input)` errored in two consecutive steps,
  `final_text` is `REFUSAL_SENTENCE`,
  `refusal_reason="repeated_tool_error"`. Recoverable single-shot
  errors (a different input the next step, or a successful retry)
  continue the loop normally.
- All tool outputs are passed back to the model as plain JSON strings.
  Binary outputs are never produced; tools that would otherwise return
  bytes (none in v1) would Base64-encode at the boundary.
- The catalog is exposed to the model via the SDK's `tools=[…]` parameter
  with full JSON schema. The model never sees the Python implementations.

## What an AI PM would do with this in production

This section is the interview leave-behind. It frames how a PM would
productize a system shaped like this one.

### Success metrics

- **Tool-call accuracy:** % of queries where the agent picks the right
  tool on the first call. Measured against a labeled eval set (this is
  what `evals-harness/` will build).
- **Termination accuracy:** % of queries that end with `end_turn` (model
  decides it has enough) vs. `max_steps_exhausted` (agent timed out) vs.
  `tool_error_giveup`. A healthy agent terminates cleanly most of the
  time.
- **Calls per answered query (p50, p95):** cost proxy. Each tool call is
  a model round-trip. Bounded by `max_steps`; tracked to detect drift.
- **Refusal-when-uncertain rate:** % of out-of-tools questions where the
  agent declines vs. confabulates an answer the tools cannot support.
- **Cost per answered query:** end-to-end token cost across the full
  loop. Tool-using agents are materially more expensive than RAG per
  query, and a PM should know by how much.

### Failure modes worth designing around

- **Tool-name hallucination:** model invents a tool that does not exist
  (e.g. `delete_file`). Mitigation: SDK enforces the schema; calls that
  do not match the registered name return a structured error to the
  model so it can recover.
- **Parameter hallucination:** model calls a real tool with wrong types
  (e.g. `start_line: "first"`). Mitigation: schema validation at the
  dispatch boundary; structured error back to the model.
- **Infinite loops:** model keeps asking for the same file or never
  emits `end_turn`. Mitigation: `max_steps` hard cap, plus a soft
  detector for repeated-identical calls.
- **Over-reading:** model reads a whole file when one section would do,
  inflating cost. Mitigation: `read_repo_file` enforces `start_line` /
  `end_line` and the tool description nudges the model toward bounded
  reads.
- **Tool-result injection:** a corpus file contains text that looks
  like instructions to the model ("ignore previous and …"). Mitigation:
  tool results are passed as `tool_result` content blocks, not as user
  text; the system prompt explicitly states tool results are data.

### What's intentionally out of scope here

- **No write tools.** No `edit_file`, no `git_commit`, no `send_message`.
  A read-only tool catalog is the demonstrably-safe v1; write tools are
  a separate set of product questions (confirmation UX, undo, scoping)
  that belong in a follow-on iteration, not this one.
- **No network tools.** No `fetch_url`, no `search_web`. Same reason —
  separate set of failure modes (rate limits, untrusted inputs, content
  injection) that would dilute the agent-loop demo.
- **No tool composition / planning.** The agent decides each step from
  the conversation so far; there is no separate planning model. ReAct-
  style explicit chain-of-thought is also out — the model's reasoning
  shows up only as its sequence of tool calls.
- **No persistence between queries.** Each `ask` invocation is a fresh
  conversation. Multi-turn chat with shared memory is a separate
  product question.

### Productization questions a PM should ask before shipping this for real

1. What is the read/write boundary? Which user actions justify which
   tool capabilities? (For this demo: read-only. In a real product: a
   policy.)
2. How does the tool catalog evolve, and who owns the schema? A flaky
   tool gates everything downstream.
3. How is the loop bounded in production — both per-query (cost) and
   per-user (rate)?
4. How is the agent observable to non-engineers? A PM needs to see the
   tool trace, not just the final answer.
5. What is the failure mode the user sees when a tool errors twice — a
   refusal? a partial answer? a "try again"? Each has different
   product implications.

## Roadmap (subsequent iterations)

Each line below is intended to map to a single future iteration:

1. **Tool catalog implementation.** *(Shipped.)* Six v1 tools landed
   as pure-Python stdlib-only functions with explicit JSON schemas in
   `tool_use_agent/catalog.py`. `python -m tool_use_agent tool <name>
   [flags]` invokes any tool directly (argparse flags are materialized
   from the schema, so enum/required/default constraints are enforced
   at the CLI boundary the same way they will be by the Anthropic SDK
   in slice 2). `python -m tool_use_agent catalog` prints the catalog
   in `{name, description, input_schema}` shape ready to pass to
   `client.messages.create(tools=…)`.
2. **Single-step agent loop.** *(Shipped, superseded by slice 3.)* The
   initial `ask` subcommand ran a single tool-call cycle and surfaced
   `stop_reason=single_step_cap_reached` if the model wanted a second
   call. Slice 3 generalizes this into a bounded multi-step loop, so
   `--max-steps 1` is now the closest equivalent (it exits with
   `stop_reason=max_steps_exhausted` instead of the slice-2 cap
   string). Implementation in `tool_use_agent/agent.py`; dry-run and
   `--json` shape inherited unchanged.
3. **Multi-step agent loop.** *(Shipped.)* `run_agent` in
   `tool_use_agent/agent.py` runs the model in a bounded loop with
   `--max-steps` (default 6) tool-execution rounds. Each step is one
   round of (model call → tool execution). The loop terminates when
   (a) the model emits no `tool_use` blocks — `stop_reason=end_turn`
   with `steps_taken < max_steps` — or (b) the cap is reached —
   `stop_reason=max_steps_exhausted`. Parallel `tool_use` blocks in
   one turn share a step number (`ToolCallTrace.step`), so the trace
   distinguishes "two tools in one round" from "two tools in two
   rounds." Recoverable dispatch errors still surface as
   `tool_result.is_error=true`. Slice 4 will replace the
   `max_steps_exhausted` cap note with the canonical
   `REFUSAL_SENTENCE` so refusals bucket the same as
   `rag-app/`'s.
4. **Refusal + bounded-step termination.** *(Shipped.)*
   `REFUSAL_SENTENCE` is now defined once in
   `tool_use_agent/verify.py` (byte-identical with
   `rag-app/rag_app/verify.py`) and is the `final_text` for every
   non-`end_turn` exit of the bounded loop. The slice also adds a
   `refusal_reason` discriminator on `AgentResult` (additive JSON
   field — no `tool-use-agent.ask.v1` schema bump needed when slice
   5 lands) populated in three cases: `max_steps_exhausted` (cap hit
   without an `end_turn`), `repeated_tool_error` (canonical
   `(tool, input)` key — built via `verify.canonical_call_key` —
   errored in two consecutive steps), and `model_refused` (the
   model's `end_turn` text is byte-equal to `REFUSAL_SENTENCE` per
   system-prompt rule 1). The `end_turn` happy path leaves
   `refusal_reason=null`. The evals harness can bucket every
   refusal across both builds with a single string-equality check
   on `REFUSAL_SENTENCE` or by grouping on `refusal_reason`.
5. **Eval-trace records.** *(Shipped.)* `ask --json` now emits a
   `tool-use-agent.ask.v1` record. Trace-record fields lead the
   payload: `schema_version`, `record_id`, `generated_at`,
   `corpus_fingerprint`. The `record_id` is a deterministic
   16-hex-char SHA-256 over the logical-query tuple `{schema,
   question, requested_model, max_steps, mode,
   corpus_fingerprint}` — same question against the same catalog
   yields the same id across days. `corpus_fingerprint` is a
   16-hex-char SHA-256 of the canonical-JSON serialization of
   `catalog_as_anthropic_tools()` (the model-facing surface), so a
   behavior-preserving `impl` refactor does *not* bust the id.
   `tool_calls[]` gains additive `latency_ms` and `output_len`
   fields per call (the slice-3/4 `tool`/`input`/`output`/
   `is_error`/`step` keys are unchanged), serving as the per-step
   cost signal the harness reads without re-running tools.
   Implementation in `tool_use_agent/trace.py` mirrors
   `rag-app/rag_app/trace.py` structurally (same hashing
   algorithm, same truncation, same timestamp shape) so the
   harness can use one verification path across both builds; the
   two modules are *not* cross-imported — each build remains
   self-contained, and byte-equality of the helper *behavior* is
   a harness-asserted contract, mirroring the same approach taken
   for `REFUSAL_SENTENCE` in slice 4.

## How to run

All five slices have landed: the six tools, the `catalog`/`tool`
subcommands, the bounded multi-step `ask` subcommand, canonical
refusal on every non-`end_turn` exit, and the
`tool-use-agent.ask.v1` eval-trace record on `--json`. Live `ask`
needs `ANTHROPIC_API_KEY` and `pip install -r requirements.txt`;
everything else is stdlib-only.

```bash
cd tool-use-agent

# Inspect the catalog the model will see (no API key needed):
python -m tool_use_agent catalog

# Direct tool invocation (no API key needed):
python -m tool_use_agent tool count_by_stage
python -m tool_use_agent tool count_by_bucket
python -m tool_use_agent tool list_pipeline_rows --bucket B2
python -m tool_use_agent tool list_repo_files --directory rag-app --pattern "*.py"
python -m tool_use_agent tool read_repo_file --path OBJECTIVE.md --start-line 1 --end-line 5
python -m tool_use_agent tool grep_repo --query "BM25" --max-matches 3

# Emit a JSON tool result instead of the human-readable view:
python -m tool_use_agent tool grep_repo --query "no-fabrication" --json

# Bounded multi-step agent loop. With ANTHROPIC_API_KEY set this calls
# Claude with tools=[…] in a loop, executes whichever tool(s) the
# model picks per turn, and prints the final answer plus a per-step
# trace. The default cap is 6 tool-execution rounds; raise or lower
# with --max-steps:
python -m tool_use_agent ask "<question>"
python -m tool_use_agent ask "<question>" --max-steps 3

# Dry-run (auto-enabled when ANTHROPIC_API_KEY is unset, also forceable
# with --dry-run): prints the assembled prompt + the tool catalog the
# model would see, without importing the SDK. --max-steps is surfaced
# in the dry-run output so you can verify the cap that would apply:
python -m tool_use_agent ask "<question>" --dry-run

# Structured JSON output for downstream tooling. The payload is a
# tool-use-agent.ask.v1 record: top-level `schema_version`,
# `record_id` (deterministic across days for the same logical query
# + catalog), `generated_at`, `corpus_fingerprint` (catalog hash),
# plus `tool_calls[]` (each with `step`, `latency_ms`, `output_len`)
# and the refusal/termination discriminators from slices 3 and 4:
python -m tool_use_agent ask "<question>" --json
```

Notes:
- All invocations resolve the repo root by walking up from the package
  path until `OBJECTIVE.md` is found, so the commands above work from
  any cwd inside the repo.
- `list_pipeline_rows`, `count_by_stage`, and `count_by_bucket`
  currently return empty / zero histograms because the tracker
  contains only placeholder rows. They start returning real data the
  moment the user fills in real rows, with no code change required.
- The `--json` payload carries a `refusal_reason` field (one of
  `null`, `"model_refused"`, `"max_steps_exhausted"`,
  `"repeated_tool_error"`). The first three states share
  `stop_reason=end_turn` or `=max_steps_exhausted`; the fourth
  introduces `stop_reason=repeated_tool_error` for the
  consecutive-same-input failure case. `final_text` on every refusal
  path is byte-equal to `REFUSAL_SENTENCE` from
  `tool_use_agent/verify.py`, which is byte-equal to
  `rag-app/rag_app/verify.py::REFUSAL_SENTENCE`.

## Design tradeoffs called out for interview discussion

- **Tool-use vs. RAG.** Same data, different access pattern. RAG wins on
  "find the passage that answers this"; tool use wins on "compute
  something structured." A PM should be able to articulate when a
  product is one vs. the other, and what the migration path looks like
  when a tool-using surface needs RAG bolted in (or vice versa).
- **Bounded loop vs. unbounded planner.** `max_steps=6` is deliberately
  small. The PM tradeoff is reliability vs. capability: an unbounded
  planner can solve harder problems but has a much worse worst-case
  cost profile. Show why the bounded version is the right v1.
- **Read-only catalog vs. read/write.** Read-only is provably safe and
  ships fast; read/write multiplies the product surface (confirmation,
  undo, scoping). A real product picks where on this spectrum to land
  and why.
- **Schema-validated tools vs. free-form function calling.** The
  Anthropic tool-use API enforces the schema, which catches parameter
  hallucinations cheaply. A free-form alternative (text parsing the
  model's call) is reversibly equivalent in capability but materially
  worse in reliability.
- **Shared trace helpers across builds.** Reusing `trace.py` from
  `rag-app/` keeps `record_id` and `corpus_fingerprint` definitions
  identical across both builds, so the evals harness can compare
  refusal behavior between RAG and tool-use without per-build glue.

## License

MIT. See [LICENSE](LICENSE), byte-identical to the repo-root
[/LICENSE](../LICENSE) and to the LICENSE files shipped under each sibling
build (`rag-app/`, `evals-harness/`); the per-build copy is what
`setuptools` bundles into `dist-info/LICENSE` for wheel installs.
