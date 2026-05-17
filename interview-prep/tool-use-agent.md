# Mock Interview Q&A — tool-use-agent

A populatable interview-prep file for the tool-use-agent build at
`../tool-use-agent/`. Ten likely interviewer questions, each followed
by the strong-answer rubric (what a credible answer covers, not what
the user *should* say) and a `_<your draft>_` italic-marker
placeholder for the user's own draft. Nothing in this file is auto-
populated — the agent does not invent the user's answers. See
`../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. **Read `../tool-use-agent/README.md` end-to-end first.** Every
   rubric below cites a section of that README by heading name
   (e.g. "Tool catalog (v1)", "Failure modes worth designing around",
   "Refusal contract row"). A strong answer grounds in the README's
   documented decisions rather than re-arguing them from scratch — if
   your draft contradicts the README, either you've found a real
   weakness worth patching upstream or you should re-read the section
   before answering.
2. **Draft one answer at a time.** Replace each `_<your draft>_`
   placeholder with your own prose. Aim for 90–180 spoken seconds per
   answer (roughly 200–400 words written out); longer than that and
   the interviewer will interrupt, shorter and the answer will read
   as under-prepared on a question they expected you to have a view
   on.
3. **The rubric is a checklist, not a script.** It lists the moves a
   credible answer makes — name the trade-off, point at the section,
   defend the choice — without dictating phrasing or stance. You are
   allowed to disagree with the README's own call as long as the
   disagreement is reasoned.
4. **Delete the rubric before any live use.** Rubrics are study aids,
   not talking points. Pasting a rubric bullet into a live answer
   reads as recited; recite the *idea*, not the rubric's framing.
5. **Cross-link discipline.** Several rubrics name sibling builds
   (`../rag-app/`, `../evals-harness/`) or the Cursor teardown
   (`../teardown-prd/cursor-teardown.md`); use those cross-links
   when they strengthen an answer — they prove the tool-use-agent
   is part of a *kit* rather than a one-off.
6. **The placeholder grammar is `_<your draft>_`** matching the rest
   of `../templates/` — so one regex (`_<.*>_`) finds every unfilled
   slot across all portfolio scaffolds.

---

## Q1. Why is `max_steps` capped at 6? Why not 3? Why not 12?

**What a strong answer covers.** Reframes from "what's the right
number" to "what does the cap protect against." The README's "Agent
loop" Stack-choices row and the "Infinite loops" failure-mode row
together say the cap exists to bound the *worst case*, not to fit
the typical case. A credible answer names what cost the cap puts a
ceiling on (each step is one model round-trip plus one tool
execution, so the worst case is `6 × (model_call + tool_call)`
tokens and wall-clock, period) and what it gives up (a legitimate
7-step problem becomes a refusal rather than a success). The
strongest version walks the calibration honestly: 3 would refuse on
real chained-tool questions the demo handles today (read the
tracker → count_by_stage → grep_repo for context, that's three
already and the answer needs a fourth turn); 12 would let a stuck
model burn 2× the cost before refusing without materially raising
the success rate on the planned demos. Six is a *defensible
heuristic*, not a measured optimum — and the answer should say so,
then point at the `evals-harness/` build as the artifact that would
re-calibrate the cap against a labeled set. Bonus: name `--max-steps`
as the operator escape hatch and the `tool-use-agent.ask.v1` trace's
`steps_taken` field as the in-production signal that would surface a
mis-calibrated default.

**Your draft:** _<your draft answer here — name the worst-case cost framing, the calibration story, the operator override, and the evals-harness role in re-calibrating>_

---

## Q2. Walk me through your refusal taxonomy. Why four buckets?

**What a strong answer covers.** Names the four discriminator values
from the `tool-use-agent.ask.v1` record's `refusal_reason` field and
maps each to a different upstream cause: `null` is the happy path
(`end_turn` with grounded text); `"model_refused"` means the model
itself emitted the canonical `REFUSAL_SENTENCE` because no tool
returned useful info (the model knows it can't answer); `"max_steps_
exhausted"` means the cap hit before `end_turn` (the agent loop
gave up to bound cost); `"repeated_tool_error"` means the same
`(tool, input)` errored twice consecutively (the loop refused
rather than letting the model spin on a known-bad input). The
discriminator is load-bearing because a downstream dashboard or
eval rubric needs to *distinguish* these cases — they have
different fixes. `model_refused` is a corpus or tool-coverage
problem (add a tool, or document why this question is out of
scope); `max_steps_exhausted` is a cap-calibration problem
(consider raising it, or the model is loopy on this question
shape); `repeated_tool_error` is a tool-input-validation problem
(the tool's schema is letting through inputs that always fail).
Bonus: name `canonical_call_key` from `verify.py` as the mechanism
that makes the consecutive-same-input detection robust (canonicalized
JSON, not raw string compare), and note that all four cases share
the same `REFUSAL_SENTENCE` `final_text` for byte-equality with
`rag-app/` so the evals harness buckets refusals from both builds
with one string-equality check. The honest concession to make:
four buckets is the *minimum useful* taxonomy, not the only one;
a richer breakdown (e.g. splitting `model_refused` into
"tool said it didn't find anything" vs. "tool returned data but
the model didn't trust it") would land in the harness, not in the
agent itself.

**Your draft:** _<your draft answer here — name the four buckets, what each tells you about the fix, the byte-equal REFUSAL_SENTENCE invariant, and the canonical-call-key mechanism>_

---

## Q3. Walk me through the `tool-use-agent.ask.v1` trace record. What does a PM do with it?

**What a strong answer covers.** The README's "Eval trace row" in
Stack choices and the "Productization questions a PM should ask"
section together frame this as an observability artifact, not a
log. A credible answer walks the record's top-level fields in order:
`schema_version` (named contract — `tool-use-agent.ask.v1` — that
makes schema changes additive vs. breaking explicit);
`record_id` (deterministic 16-hex-char SHA-256 over the
logical-query tuple, so the same question against the same catalog
produces the same id across days — load-bearing for de-dup in eval
runs); `generated_at` (ISO timestamp); `corpus_fingerprint`
(catalog hash, so a behavior-preserving impl refactor of a tool
doesn't bust the id but adding/removing a tool does); then the
operational discriminators `stop_reason` + `refusal_reason` from
Q2; then `tool_calls[]` (the load-bearing per-step trace — each
entry carries `step`, `tool`, `input`, `output`, `is_error`,
`latency_ms`, `output_len`). What a PM does with it, concretely:
a non-engineer can read `tool_calls[]` to *see what the agent did*
without re-running it — which tool it tried first, whether it
chained, whether it retried on error, how long each call took.
This is the artifact that answers the README's "How is the agent
observable to non-engineers?" productionization question. The
strongest answer also names what the record *doesn't* capture
yet: token cost per step (deferred to evals-harness's cost rubric),
the model's intermediate reasoning (out of scope — ReAct-style
chain-of-thought is deliberately not exposed), and per-tool
budget breach (no per-tool latency cap exists yet, only the
loop-level `max_steps`). Bonus: cross-reference `rag-app/`'s
`rag-app.ask.v1` shape — same `schema_version` / `record_id` /
`corpus_fingerprint` conventions, deliberately so the harness
reads both with one verification path.

**Your draft:** _<your draft answer here — walk the trace fields, name the non-engineer use case, name the gaps, and cross-reference rag-app.ask.v1>_

---

## Q4. Why a tool catalog at all? Why these nine tools? Why not three, or twenty?

**What a strong answer covers.** Separates the *architecture*
question (why a catalog) from the *curation* question (why these
nine). On architecture: the catalog is the single mutable surface
of the build — adding a tool means appending to the catalog, not
changing the agent loop. The README's "Tool catalog (v1)" section
makes that explicit ("the catalog is the only mutable surface").
That property is load-bearing for safety review and for tool
deprecation: every tool the model can call is enumerable at one
import site (`tool_use_agent/catalog.py::build_catalog()`), so a
PM doing a safety review can answer "what can this agent do?" with
one file rather than walking the codebase. On curation: the nine
break into three families — three repo readers (`list_repo_files`,
`read_repo_file`, `grep_repo`); three pipeline-domain tools
(`list_pipeline_rows`, `count_by_stage`, `count_by_bucket`); and
three richer agent-y tools added in NEXT_WORK item 6 (`sql_query`,
`file_rewrite`, `regex_extract`). The first six are the README's
v1 — chosen because each is structurally different (enumeration
vs. content vs. search vs. structured-query vs. histogram) so the
catalog demonstrates that the agent picks across different
*shapes* of tool, not just different *names*. The three new tools
push the demo from read-only to includes-a-write (`file_rewrite`
is the only writer, sandboxed), from substring to regex
(`regex_extract` adds capture groups + line numbers), and from
markdown to structured data (`sql_query` against an in-memory
SQLite fixture). Three would under-demonstrate the
across-shapes property; twenty would dilute the catalog with
redundant tools that don't add a *new* shape and force the model
to pick among near-duplicates. Bonus: note that the catalog is
exposed to the model via the Anthropic SDK's `tools=[…]` parameter
with full JSON schema, so schema-validation enforcement (Q9 below)
is "free" — every parameter hallucination becomes a structured
error the model can recover from, not a silent mis-call.

**Your draft:** _<your draft answer here — name the catalog-as-mutable-surface architecture property, the three-family curation logic, the across-shapes vs. across-names framing, and the schema-validation property>_

---

## Q5. The three new tools include a writer (`file_rewrite`). Walk me through the safety story.

**What a strong answer covers.** Names the two-layer guardrail
pattern the README locks in (and `../DECISIONS.md` consolidates at
the "Agent-tool safety guardrails locked" entry): every tool that
touches an executable-language string or a file path uses an
input-language validator (Layer 1) plus a scope-and-resource bound
(Layer 2), and either layer alone has a documented bypass. For
`sql_query`: Layer 1 is a `WRITE_KEYWORDS` denylist on the SQL
string (rejects `INSERT`/`UPDATE`/`DELETE`/`DROP`/etc. before
opening the file); Layer 2 is `mode=ro` on the SQLite connection
URI (the engine refuses to even attempt a write). For
`file_rewrite`: Layer 1 is the operation enum
(`frozenset({'replace', 'append', 'prepend'})` — anything else
short-circuits to `ERROR`); Layer 2 is sandbox-root resolution
(`Path.resolve()` + `.relative_to(sandbox_root)`), so any path
that traverses out of `tool-use-agent/sandbox/` refuses before
the operation runs. For `regex_extract`: Layer 1 is
`re.compile()` + a 1000-char pattern-length cap (catches malformed
regex and bounds backtracking blast radius before file IO); Layer 2
is `_resolve_inside_repo` + a 1000-match hard ceiling. The
strongest answer also names the cross-cutting invariants the
DECISIONS entry locks: no network (`socket.socket` would raise),
no shell-out (`subprocess` is never imported), no API keys in any
tool, no global state, bounded output on every read path. The
honest concession: two-layer guardrails are *defense in depth*, not
formal verification; a pathological regex at 999 chars could still
hang (mitigated by the file-size cap on each scanned file, not the
length cap itself), and a clever symlink could in principle defeat
`.resolve()` on a system where the agent had write access to the
parent directory — but neither is exploitable from the model-facing
surface, and naming both honestly is part of the answer's craft
signal.

**Your draft:** _<your draft answer here — name the two-layer pattern, walk all three new tools through it, name the cross-cutting invariants, and concede defense-in-depth vs. formal-verification>_

---

## Q6. How would you productionize this? What's missing?

**What a strong answer covers.** Anchors on the README's
"Productization questions a PM should ask before shipping this for
real" list (five numbered questions: read/write boundary, tool-
catalog ownership, loop bounding, observability for non-engineers,
tool-error UX) and answers each as a *gap relative to the current
build*. The current build's read/write boundary is "read-only
catalog + one sandboxed writer scoped to `tool-use-agent/sandbox/`";
production would need a policy for which user actions justify which
tool capabilities — not just sandboxing, but a per-user permission
model. The tool-catalog ownership question maps to a versioning
story: today the catalog is one file with implicit additive-only
discipline; production needs an explicit schema version on the
catalog itself (parallel to the per-record `schema_version`) plus
a deprecation policy. Loop bounding is per-query (the `max_steps`
cap from Q1) but production needs per-user rate limits too. The
observability question is partially answered by the
`tool-use-agent.ask.v1` trace from Q3 — but the production
artifact is a *dashboard* over those records, not just the records
themselves; the evals-harness build is the closest existing
precedent for the per-record schema + aggregation surface that
would underlie such a dashboard. The tool-error UX question is the
genuinely open one: today a `repeated_tool_error` becomes a refusal,
but in production a user might prefer "the tool errored, want me to
try a different approach?" — which is a different product than the
silent refusal. The strongest answer names *which* of the five is
the most expensive to add post-hoc (the read/write permission model
— retrofitting permissions onto a permissive surface is harder than
shipping with the surface scoped from day one) and which is the
cheapest (the per-record dashboard — the records already exist).
Bonus: cross-reference `evals-harness/` as the build that would
own the production-eval set, not the tool-use-agent itself.

**Your draft:** _<your draft answer here — answer all five productization questions as gaps-vs-current, name the most-expensive-post-hoc add, and cross-reference evals-harness>_

---

## Q7. Tool-use vs. RAG — when do you reach for each, and how do you migrate between them?

**What a strong answer covers.** This is the cross-build question
the README's "Why an agent and not RAG" section sets up — and the
honest answer is *not* "tool-use is the modern default." A
credible answer reframes by question shape: RAG wins when the
question is "find me the passage that answers this" because the
retrieval index is pre-built, the per-query cost is one model call
plus one retrieval round-trip, and the answer is bounded by what
the index contains. Tool-use wins when the question requires
*structured computation* over the data ("how many Bucket-2 loops
are still in recruiter-screen?") because there is no passage that
contains the answer — the answer has to be computed at query time.
Tool-use also wins when *which document to read* is itself a
function of the question (the agent decides at query time whether
to read the README, the tracker, or the corpus). The migration
story is the load-bearing part: a tool-using surface that needs
RAG bolted in adds a `retrieve` tool to the catalog and lets the
model decide when to call it; a RAG surface that needs tool-use
adds a planner step that decides whether the question is
"find the passage" or "compute the answer." The two patterns are
*compositional*, not exclusive — which is why the portfolio ships
both as separate builds with a shared `REFUSAL_SENTENCE` and
parallel trace shapes (`rag-app.ask.v1` / `tool-use-agent.ask.v1`),
so the evals harness can compare refusal behavior between them
without per-build glue. Bonus: name the per-query cost contrast
(tool-use is materially more expensive than RAG per query because
of the multi-step loop), so the answer doesn't read as
tool-use-evangelical.

**Your draft:** _<your draft answer here — name the question-shape split, the migration story, the compositional framing, and the per-query cost contrast>_

---

## Q8. Of the five named failure modes (tool-name halluc, parameter halluc, infinite loops, over-reading, tool-result injection), which would you prioritize fixing first?

**What a strong answer covers.** The README's "Failure modes worth
designing around" section names five with current mitigations; the
question tests whether the candidate can rank them by user-visible
harm and current mitigation strength. A credible answer picks one
explicitly and defends the pick on a named dimension. Plausible
defensible picks:

- **Tool-result injection** if the answer is reading for adversarial
  robustness — the current mitigation (tool results are passed as
  `tool_result` content blocks, not user text; system prompt says
  tool results are data) is a *convention*, not a hard boundary, and
  a corpus file with prompt-injection content could still influence
  the model's tool selection on a subsequent turn. A real product
  reading user-supplied content would need a stronger boundary
  (content filtering at the tool boundary, or a separate
  injection-detection step).
- **Over-reading** if the answer is reading for cost discipline — the
  current mitigation (`read_repo_file` enforces `start_line`/
  `end_line`, tool description nudges the model) is mostly a *hint*,
  and the model is free to read a whole file when one section would
  do. A cost-per-query budget would benefit more from a hard cap on
  bytes-returned-per-tool-call than from a nudge.
- **Infinite loops** if the answer is reading for cost-ceiling
  reliability — `max_steps` and `repeated_tool_error` already cover
  the obvious cases, but a slow oscillation across different tools
  that never converges is not detected today.

What the answer should *not* do: pick "tool-name hallucination" or
"parameter hallucination" as the first priority, because the SDK's
schema enforcement already makes both into structured errors the
model recovers from cheaply — they are mitigated below the
threshold of "first priority." Bonus: name the trade-off in the
fix (e.g. a hard bytes-returned cap could break long-context
reads the agent legitimately needs) and cross-reference
`evals-harness/`'s groundedness rubric as the artifact that would
*measure* whether the fix helped without re-running production
queries.

**Your draft:** _<your draft answer here — pick one failure mode, name the dimension you're ranking on, defend the pick over the other four, name the trade-off in the fix>_

---

## Q9. Schema-validated tools vs. free-form function calling — why does this matter?

**What a strong answer covers.** The README's "Design tradeoffs
called out for interview discussion" section names this one
explicitly, and the credible answer is *not* about whether the
agent works without schemas (it could). The schema-validated path
makes parameter hallucinations *cheap to catch* — a malformed call
(`start_line: "first"`) becomes a structured error the model
recovers from in one extra turn. The free-form alternative (text-
parsing the model's call out of natural language) is *capability-
equivalent* on the happy path but materially worse on the failure
path: a malformed call has to be parsed leniently enough to
recover the intent or strictly enough to refuse, and either choice
loses information. A strong answer also names what the schema
*doesn't* validate: semantic correctness (asking
`read_repo_file('OBJECTIVE.md', start_line=1, end_line=1)` is
schema-valid but probably not what the user wanted), and *cross-
tool* coherence (calling `count_by_stage` and then `count_by_bucket`
when one of them was sufficient — both are schema-valid). Those
gaps are correctly *not* in the schema layer; they belong in the
eval set (`evals-harness/`'s first-call-tool rubric is the
canonical home for the cross-tool coherence question). Bonus:
note that the schema-validation property compounds with the safety
guardrails from Q5 — the operation enum on `file_rewrite`, the
denylist on `sql_query`, and the pattern-length cap on
`regex_extract` are all encoded in the JSON schema, so the SDK
rejects bad inputs at the tool-call boundary before the tool body
runs.

**Your draft:** _<your draft answer here — name the cheap-to-catch property, the free-form alternative's failure-path cost, the gaps schemas don't cover, and the compound with safety guardrails>_

---

## Q10. If you joined a team shipping this for real tomorrow, what's the first thing you'd ship from this build, and what's the first thing you'd kill?

**What a strong answer covers.** The interviewer is testing whether
the candidate holds the README's design provisionally — read the
artifact as a current-best-guess, not a permanent position. A
strong answer picks one specific *ship* and one specific *cut* and
defends each with the data that would justify it.

Plausible ships: the `tool-use-agent.ask.v1` trace record (it's
ready, it's underpriced as a PM-observability artifact, and
nothing in the production stack mirrors it); the bounded-step +
refusal-reason discriminator (the four-bucket taxonomy from Q2
would slot directly into a production dashboard with no schema
changes); the sandboxed `file_rewrite` pattern (one writer
scoped to a sandbox root is the demonstrably-safe shape for any
v1 writing tool).

Plausible cuts: the third-rail `sql_query` tool (the in-memory
SQLite fixture is a demo-shaped surface; production would either
need a real DB connection — and a separate set of safety
questions — or wouldn't need SQL at all); the `count_by_bucket`
and `count_by_stage` tools (they exist because the demo's data
*happens* to be the tracker; in any other product they'd be
domain-specific tools, not catalog primitives); the dry-run
auto-fallback when `ANTHROPIC_API_KEY` is unset (useful for
portfolio demoability, wrong for production where an unset key
should hard-fail with a clear error, not silently degrade).

The answer should *not* perform humility ("I'd kill the whole
thing") or refuse to commit ("I wouldn't change anything until I
had more data"). Both read as evasive. The honest move: "here's
the specific thing I'd ship, here's the specific data that would
justify shipping it; here's the specific thing I'd cut, here's
the specific data that would justify cutting it." Bonus: name
the README's "Roadmap (subsequent iterations)" section as the
*existing* precedent for treating the build as a sequence of
provisional commitments rather than a fixed design — the
ship/cut question is just the next entry in that sequence.

**Your draft:** _<your draft answer here — name one ship, one cut, the data justifying each, and cite the Roadmap section as the precedent for provisional commitments>_

---

## Cross-cutting "walk me through your portfolio" question

This question doesn't belong in the per-artifact Q&A bank because
it spans the whole portfolio. It will live in
`interview-prep/README.md` under the "common cross-artifact
questions" section (NEXT_WORK item 7 sub-checkbox 5), with a one-
paragraph stub here so a reader of *just* this file knows the
question exists and where to find its rubric. If you are
practicing answers cold, expect this question first and the ten
above as follow-ups — the interviewer will use the walk-through to
pick which two or three of the ten to probe in depth. A
tool-use-agent-flavored walk-through naturally pivots into Q1
(step cap rationale as the first cost-discipline signal) or Q5
(safety guardrails as the first PM-craft signal on agent-y
tools), so prep those two with extra care.

---

## Source of truth & cross-links

- The build itself: `../tool-use-agent/` — README is the design
  contract; the `tool_use_agent/` package implements it; `tests/`
  covers the production surface with no network or API key.
- Sibling Q&A banks (NEXT_WORK item 7, sub-checkboxes 1, 2, 4):
  `cursor-teardown.md` (shipped), `rag-app.md` (shipped),
  `evals-harness.md` (subsequent iteration) — each anticipates
  8–10 questions on its own artifact.
- Index file (NEXT_WORK item 7, sub-checkbox 5): `README.md` will
  link the four Q&A banks, name the suggested prep order, and
  carry the cross-artifact questions section.
- Related portfolio piece (cross-link for rubrics Q3, Q6, Q8): the
  `../evals-harness/` build, which is the mechanical home for the
  per-record aggregation, cost rubric, and groundedness rubric
  this tool-use-agent produces trace records for.
- Related portfolio piece (cross-link for rubric Q7): the
  `../rag-app/` build, the same-data-different-access-pattern
  counterpart that the README's "Why an agent and not RAG"
  section locks in.
- Safety-guardrails consolidating entry referenced by Q5:
  `../DECISIONS.md`, search for "Agent-tool safety guardrails
  locked for sql_query / file_rewrite / regex_extract".
- The no-fabrication rule for the `_<your draft>_` slots:
  `../DECISIONS.md` (search for "no-fabrication"). The agent
  never drafts the user's answers; the slots are the user's to
  fill.

This file is interview-prep, not a deliverable for any specific
employer. The questions and rubrics anticipate what an AI-PM
interviewer is likely to probe given the tool-use-agent README's
actual content; they are not sourced from any company's interview
process and make no claim to mirror one.
