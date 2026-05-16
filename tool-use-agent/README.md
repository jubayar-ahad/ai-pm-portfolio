# tool-use-agent

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
| Multi-step agent loop (chained tool calls, bounded) | Not yet |
| Refusal + bounded-step termination | Not yet |
| Eval-trace records (`tool-use-agent.ask.v1`) | Not yet |

The `ask` subcommand runs in two modes, matching the `rag-app/` build.
With `ANTHROPIC_API_KEY` set it calls Claude with `tools=[…]`, runs whichever
tool the model requests, returns the result, and prints Claude's final
answer plus a one-line trace per tool call. Without a key (or with explicit
`--dry-run`) it prints the assembled first-turn prompt and the tool
catalog the model would see — enough to validate the tool schema and prompt
construction in a sandbox or CI environment. Multi-step chaining lands in
slice 3.

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
- The loop terminates when (a) the model returns an `end_turn` without a
  new tool call, (b) `max_steps` is reached, or (c) a tool raises a
  recoverable error twice in a row on the same input — the agent emits the
  canonical refusal rather than spinning.
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
2. **Single-step agent loop.** *(Shipped.)* `python -m tool_use_agent ask
   "<question>"` calls Claude once with `tools=[…]`, executes whichever
   tool(s) the model requests in that turn, returns the tool results to
   the model, and prints the final answer plus a one-line trace per
   tool call. Implementation in `tool_use_agent/agent.py`. The
   single-step cap is enforced explicitly: if the model asks for a
   second tool-call cycle after seeing the first batch of results, the
   CLI surfaces `stop_reason=single_step_cap_reached` rather than
   silently dropping the request. Recoverable dispatch errors
   (unknown tool name, bad kwargs, bad value) become
   `tool_result.is_error=true` content so slice 4 can react. Dry-run
   path (`--dry-run` or no `ANTHROPIC_API_KEY`) prints the assembled
   prompt and the catalog the model would see, without importing the
   SDK. `--json` emits a structured record with `mode`, `prompt`,
   `tool_calls[]`, `stop_reason`, `model`, token usage, and
   `final_text` — slice 5 will add the
   `schema_version`/`record_id`/`corpus_fingerprint`/`generated_at`
   trace fields to this same shape via reused `rag-app/rag_app/trace.py`
   helpers.
3. **Multi-step agent loop.** Lift the single-step cap and run the loop
   until `end_turn` or `max_steps` (default 6). Render a human-readable
   tool trace inline (`step 1: read_repo_file(...) → 240 chars`).
4. **Refusal + bounded-step termination.** Canonical refusal sentence
   defined once and emitted whenever the loop terminates without a
   grounded answer (no useful tool result, or `max_steps` exhausted,
   or two consecutive tool errors on the same input). Mirrors
   `rag-app/`'s refusal pattern so the evals harness treats both as
   one bucket.
5. **Eval-trace records.** `ask --json` emits a
   `tool-use-agent.ask.v1` record carrying `schema_version`,
   `record_id`, `corpus_fingerprint`, `generated_at`, plus a
   `tool_calls[]` array with `{tool, input, output_len,
   latency_ms, error?}` per step. Reuses `rag-app/rag_app/trace.py`
   helpers via import so record IDs and corpus fingerprints are
   byte-identical across builds.

## How to run

Slices 1 and 2 have landed: the six tools, the `catalog`/`tool`
subcommands, and the single-step `ask` subcommand are all runnable.
Live `ask` needs `ANTHROPIC_API_KEY` and `pip install -r
requirements.txt`; everything else is stdlib-only.

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

# Single-step agent loop. With ANTHROPIC_API_KEY set this calls Claude
# with tools=[…], runs whichever tool the model picks, and prints the
# final answer plus a one-line trace per tool call:
python -m tool_use_agent ask "How many Bucket 2 loops are still in recruiter-screen?"

# Dry-run (auto-enabled when ANTHROPIC_API_KEY is unset, also forceable
# with --dry-run): prints the assembled prompt + the tool catalog the
# model would see, without importing the SDK:
python -m tool_use_agent ask "<question>" --dry-run

# Structured JSON output for downstream tooling:
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
- Slice 2 is deliberately capped at one tool-call cycle. If the model
  requests a second tool call after seeing the first batch of
  results, `ask` surfaces `stop_reason=single_step_cap_reached` rather
  than dropping the request silently. The bounded multi-step loop
  lives in slice 3.

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
