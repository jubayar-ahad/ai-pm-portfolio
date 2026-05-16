# evals-harness

A small evaluations harness for this repo's two LLM builds (`rag-app/` and
`tool-use-agent/`), framed for an AI PM portfolio.

This README is the design contract for the build. It locks scope, stack, and
the PM-relevant decisions so subsequent iterations can land code without
re-litigating choices. Code lives alongside this README and lands
incrementally — see [Status](#status) for what currently runs.

---

## Status

| Slice | State |
| --- | --- |
| Design doc (this README) | Shipped |
| Labeled query set scaffold (`queries.jsonl`) | Shipped |
| Trace ingester + startup invariant checks | Not started |
| Refusal-bucket scorer (cross-build) | Not started |
| Groundedness + termination + cost scorers, aggregate report | Not started |

The harness deliberately performs **no model calls of its own**. It scores
trace records that the two LLM builds already emit via their `ask --json`
output (`rag-app.ask.v1` and `tool-use-agent.ask.v1`), against a labeled
query file the user (or a future generation script) provides. That means
the harness runs without `ANTHROPIC_API_KEY`, in any sandbox or CI
environment, and re-runs are deterministic — the eval result depends only
on the trace records and the labels, never on a live API.

## What this is, in one sentence

A stdlib-only Python CLI that reads `ask --json` trace records from this
repo's RAG app and tool-use agent, scores them against a labeled query
set, and produces a per-build, per-rubric Markdown report fit for an
interview leave-behind.

## Why an evals harness, and why this shape

The Day-10 milestone in `OBJECTIVE.md` names three builds: a RAG
application, a tool-use agent, and an evals harness. The first two are
demoable in isolation. The third earns its keep by saying something
interesting *across* them — "for the same labeled set of questions, which
pattern is more grounded? more cost-efficient? which one refuses
correctly?" That cross-build comparison is the PM-relevant artifact, not
an abstract benchmark over a hypothetical system.

Three properties shape the build:

- **Scores records, doesn't generate them.** The two builds already emit
  trace records (`schema_version`, `record_id`, `corpus_fingerprint`,
  full `tool_calls[]` / `verification` blocks, refusal discriminators)
  that contain everything a scorer needs. Re-implementing generation
  inside the harness would couple it to provider/model choices and break
  the "harness runs without a key" property — which is the property that
  makes the eval result reproducible.
- **One labeled query set, one harness, two builds.** Each labeled query
  carries an `expected_outcome` (e.g. `answer`, `refuse`) plus optional
  per-build expectations (e.g. an in-corpus citation source for the RAG
  side, an expected tool for the tool-use side). The harness routes by
  the trace's `schema_version` prefix to the right per-build scorer, but
  the labeled file is single-source-of-truth.
- **Cross-build invariants are asserted at startup, not at score time.**
  The two builds independently define `REFUSAL_SENTENCE` (in
  `rag-app/rag_app/verify.py` and `tool_use_agent/verify.py`) and
  independently implement the trace-helper algorithms (in
  `rag-app/rag_app/trace.py` and `tool_use_agent/trace.py`). The
  harness asserts byte-equality on the refusal string and behavior
  equivalence on the helpers (two ~3-line fixtures: hash a known corpus
  twice, compare). If either drifts, the harness fails fast with a
  named error rather than producing a silently-skewed report.

## Stack choices

| Concern | Choice | Why |
| --- | --- | --- |
| Language | Python 3.9+ (matches the other two builds) | Same runtime, same import path, same audience. No new toolchain. |
| Dependencies | Stdlib only | Mirrors `rag-app/`'s loader and the entire `tool-use-agent/` build. The harness's job is reading JSONL, doing arithmetic, and printing Markdown — none of it needs a third-party dep. |
| LLM access | None — the harness never calls an LLM | Eval scoring is deterministic over already-emitted records. Live calls would defeat reproducibility and re-introduce the key dependency the builds already engineered around. |
| Inputs | (a) one or more trace files (JSONL of `ask --json` records), (b) one labeled query file | Trace files are the build outputs; labels are the human-curated ground truth. Both are plain JSONL so an interviewer can read them. |
| CLI | Three subcommands of one entry point: `python -m evals_harness {ingest,score,report}` | Mirrors the `{load,retrieve,ask}` and `{tool,catalog,ask}` shapes from the prior builds. Each subcommand is one slice; they compose by file. |
| Trace routing | By `schema_version` prefix (`rag-app.ask.v1` vs `tool-use-agent.ask.v1`) | Each build's trace is dispatched to its own scorer. Unknown schemas are rejected, not silently downgraded. |
| Scoring output | Per-record JSONL (machine-readable) + aggregate Markdown report (human-readable) | The JSONL is what a future iteration can diff across runs; the Markdown is what gets pasted into the interview leave-behind. |
| Startup invariants | (a) `REFUSAL_SENTENCE` byte-equal across the two builds, (b) trace-helper hashing produces a known fixture digest in both builds | Two tiny checks that prevent silent cross-build drift. They run before any scoring and exit with a named error message if they fail. |
| Determinism | Same trace files + same labels → same scored JSONL + same Markdown report | No wall-clock fields in scored output (the harness records `generated_at` at the report level only); no nondeterministic ordering (records are sorted by `record_id`). |

The Anthropic SDK is **not** a dependency of the harness. The two builds
each have their own `requirements.txt`; the harness has none. This is
intentional — it is the property that makes eval results reproducible on
any machine that has Python.

## Architecture

```
labeled queries (JSONL)                trace records (JSONL)
    │                                      │
    │  question, expected_outcome,         │  schema_version, record_id,
    │  optional per-build expectations     │  corpus_fingerprint, …
    │                                      │
    ▼                                      ▼
                  ingest + invariant checks
                  (REFUSAL_SENTENCE byte-equality,
                   helper-behavior equivalence)
                            │
                            ▼
              route by schema_version prefix
                  │                       │
                  ▼                       ▼
        rag-app.ask.v1 scorer    tool-use-agent.ask.v1 scorer
                  │                       │
                  └─────────┬─────────────┘
                            ▼
                    scored.jsonl
                    (one record per (record_id, rubric))
                            │
                            ▼
                    aggregate report
                    (per-build × per-rubric Markdown table)
```

Notes:
- "Ingest" is a lightweight read-and-validate pass: every input file is
  parsed, `schema_version` is checked against the harness's
  known-version list, and the two startup invariants are asserted.
  Failures are loud and named.
- The router is structural: a `rag-app.ask.v1` record cannot accidentally
  be scored by the tool-use rubric (groundedness expects a
  `verification` block; termination quality expects `refusal_reason`).
  Unknown schemas raise rather than being treated as the closest known
  version.
- The aggregate report is Markdown by design: it is small enough to
  paste into a recruiter email or an interview slide, and it renders
  correctly in GitHub when this repo is shared as a portfolio link.

## What an AI PM would do with this in production

This section is the interview leave-behind. It frames how a PM would
productize a system shaped like this one.

### Success metrics (the rubrics the harness will score)

- **Refusal-when-uncertain rate** (both builds). For queries labeled
  `expected_outcome=refuse`, the harness checks whether `final_text`
  (rag-app) / `final_text` (tool-use-agent) equals `REFUSAL_SENTENCE`,
  or whether the rag-app trace short-circuited with
  `reason: low_retrieval_score`. A single equality check is enough
  because both builds emit a byte-identical canonical refusal string.
- **Groundedness rate** (rag-app only). For queries labeled
  `expected_outcome=answer`, the harness reads the trace's
  `verification` block (`N/M citations resolved`) and scores the
  fraction of answers where every cited span resolves to a retrieved
  chunk. A citation pointing at a real corpus chunk not in this query's
  top-k still counts as unresolved — that is the property `verify.py`
  shipped in rag-app slice 4.
- **Termination quality** (tool-use-agent only). For queries labeled
  `expected_outcome=answer`, the harness groups records by
  `refusal_reason` and scores the fraction that ended with
  `stop_reason=end_turn` and `refusal_reason=null`. The
  `max_steps_exhausted` / `repeated_tool_error` buckets are reported
  separately so a PM can read "the agent timed out 12% of the time"
  vs. "the agent gave up retrying 3% of the time" as two different
  product signals.
- **Cost per answered query** (both builds, separately). The harness
  sums `input_tokens + output_tokens` from each trace and reports
  p50/p95/max per build. For the tool-use agent it additionally reports
  the p50/p95 of `steps_taken` and the sum of per-call `latency_ms` to
  surface the tool-side cost separately from the model-side cost. (The
  latency split is the named decision from tool-use-agent slice 5.)
- **First-call tool accuracy** (tool-use-agent only, when the labeled
  query carries an `expected_first_tool` field). For each such query,
  the harness checks whether `tool_calls[0].tool == expected_first_tool`.
  Mismatches are listed in the report so an interviewer can see *which
  question* tripped the agent up, not just the rate.

### Failure modes worth designing around

- **Label drift.** As the corpus or the catalog evolves, a query
  labeled `expected_outcome=answer` may correctly become `refuse`
  (because the answer was removed from the corpus) or vice versa.
  Mitigation: the labeled file carries a `corpus_fingerprint_at_label`
  field; mismatching that against a trace's `corpus_fingerprint`
  surfaces as a per-record warning, not a silent miscount.
- **Scoring on stale traces.** A trace recorded against an older
  schema version (e.g. a hypothetical `rag-app.ask.v0`) would be
  silently misinterpreted. Mitigation: `schema_version` is matched
  exactly; unknown versions raise.
- **Cross-build drift on the canonical refusal string.** If a future
  iteration changes `REFUSAL_SENTENCE` in one build but not the other,
  the harness's refusal scorer would split one logical bucket into two
  and over-report variance. Mitigation: the byte-equality assertion at
  startup is the single line that prevents this.
- **Trace size growth.** As the tool-use-agent runs longer queries,
  trace records get bigger (each tool call carries `output`). The
  harness reads JSONL line by line and streams; nothing is held in
  memory beyond the current record + a running accumulator.
- **Confounded comparison.** "RAG is more grounded than the agent" is
  only meaningful if both were given the same labeled set, on the same
  day, against the same corpus. The harness reports the
  `corpus_fingerprint` set seen across all input traces; if more than
  one distinct fingerprint appears for a single build, the report
  flags it explicitly rather than averaging across mismatched corpora.

### What's intentionally out of scope here

- **No model-graded scoring.** No "use an LLM to score the LLM." Every
  rubric is a deterministic function of the trace fields the builds
  already emit. Model-graded scoring is a separate product surface
  (provider choice, judge prompts, judge variance) that would
  re-introduce the API-key dependency this build is trying to avoid.
  Listed as a candidate for a follow-on iteration.
- **No labeled-set authoring tools.** The labeled query JSONL is hand-
  edited at the start. A future iteration may add a `seed` subcommand
  that proposes label candidates from a sample of trace records, but
  not in v1.
- **No regression dashboard / persistence.** Reports are Markdown
  snapshots, not a database. A future iteration may add a "diff two
  reports" mode that calls out per-record changes by `record_id`.
- **No latency benchmarking.** The harness reads the `latency_ms`
  field the tool-use-agent already emits per tool call, but does not
  re-time anything itself. Wall-clock benchmarks are a separate
  question (consistent hardware, warm cache, multiple runs) that this
  harness deliberately does not own.
- **No fine-tuning loop.** Evaluations score behavior; they do not
  change weights or prompts. Any improvement loop ("the eval says
  refusal rate is low, so we'll raise the BM25 threshold to 1.7") is a
  separate iteration that updates the build, then re-runs the harness.

### Productization questions a PM should ask before shipping this for real

1. What is the cadence — per-PR, per-day, pre-release? Each implies a
   different cost ceiling and a different on-call expectation.
2. Who owns the labeled set? A stale label set silently degrades every
   metric; ownership prevents that.
3. What is the action when a rubric regresses — block the merge, file a
   bug, page the on-call? Different teams pick different answers; a
   PM picks one and writes it down.
4. How is groundedness measured in production, not just at ship? A
   shipped harness on a sampled tail of live queries is the production
   answer; this v1 only handles the offline case.
5. What is the false-positive rate of the refusal scorer? If
   `expected_outcome=refuse` is a small fraction of the labeled set,
   even small label errors swing the metric.

## Roadmap (subsequent iterations)

Each line below is intended to map to a single future iteration:

1. **Labeled query set scaffold.** *Shipped.*
   `evals-harness/queries.jsonl` carries 16 hand-authored labeled
   queries spanning the four shapes: 6 `in_corpus`, 4
   `out_of_corpus`, 3 `tracker_rollup` (tool-use-only), 3
   `adversarial_in_corpus`. The record shape is uniform — every
   line carries `id`, `question`, `shape`, `expected_outcome`,
   `applies_to`, `expected_citation_source`,
   `expected_first_tool`, `corpus_fingerprint_at_label`, and
   `notes` (with optional values explicitly null). The schema
   is locked in DECISIONS so subsequent slices can rely on the
   key set without re-litigation.
2. **Trace ingester + startup invariant checks.** `python -m
   evals_harness ingest --traces <path…> --labels <path>` reads every
   JSONL line, validates against the known-version list
   (`rag-app.ask.v1`, `tool-use-agent.ask.v1`), asserts the two
   startup invariants (cross-build `REFUSAL_SENTENCE` byte-equality,
   helper-behavior equivalence on a known fixture), and emits a
   normalized `ingested.jsonl` plus a one-line counts summary
   (`N traces, M labels, K invariant checks passed`). Fails fast on
   any mismatch.
3. **Refusal-bucket scorer (cross-build).** `python -m
   evals_harness score --rubric refusal …` joins ingested traces with
   labels by `record_id`/question, computes a refusal confusion matrix
   per build (`expected=refuse, observed=refuse|answer` × build), and
   emits a per-record scored JSONL plus a small Markdown table. This
   is the smallest cross-build comparison the harness can produce and
   the one that directly exercises the canonical-refusal-string
   invariant locked in the prior builds' slice 4.
4. **Groundedness + first-call tool scorers.** Per-build rubrics that
   are not cross-cuttable: groundedness reads the rag-app trace's
   `verification` block; first-call tool accuracy reads
   `tool_use_agent`'s `tool_calls[0].tool` against the label's
   `expected_first_tool`. Each emits scored JSONL rows tagged with
   their rubric name, so the report aggregator stays uniform.
5. **Termination quality + cost scorers, aggregate report.** Final
   slice rolls up `refusal_reason` distribution and token/cost
   p50/p95 per build, joins every per-record scored row into a single
   Markdown report (`python -m evals_harness report
   --scored <path>`), and reports `corpus_fingerprint` diversity as
   a warning row when more than one fingerprint shows up per build.
   This is the artifact an interviewer reads.

## How to run

No subcommand has shipped yet — slice 1 only delivered the labeled
query file. `queries.jsonl` is plain JSONL: 16 records, one query
per line, every record carries the same nine keys (see DECISIONS
for the per-field contract). It is human-readable and can be
inspected directly:

```bash
cd evals-harness
wc -l queries.jsonl          # → 16
head -n 1 queries.jsonl      # → first labeled record (in_corpus, expects answer)
python3 -c "import json; print(set(json.loads(next(open('queries.jsonl'))).keys()))"
# → {'id','question','shape','expected_outcome','applies_to',
#    'expected_citation_source','expected_first_tool',
#    'corpus_fingerprint_at_label','notes'}
```

The locked CLI shape for the next iterations is:

```bash
cd evals-harness

# (slice 2) read traces + labels, run startup invariants, emit
# ingested.jsonl. No model calls, no API key.
python -m evals_harness ingest \
    --traces ../rag-app/.cache/traces.jsonl \
              ../tool-use-agent/.cache/traces.jsonl \
    --labels queries.jsonl \
    --out .cache/ingested.jsonl

# (slice 3) score the refusal rubric across both builds.
python -m evals_harness score \
    --rubric refusal \
    --ingested .cache/ingested.jsonl \
    --out .cache/scored.jsonl

# (slice 4) score per-build rubrics.
python -m evals_harness score --rubric groundedness \
    --ingested .cache/ingested.jsonl --out .cache/scored.jsonl  # appends
python -m evals_harness score --rubric first_call_tool \
    --ingested .cache/ingested.jsonl --out .cache/scored.jsonl  # appends

# (slice 5) roll up to a Markdown report.
python -m evals_harness report --scored .cache/scored.jsonl
```

A note on producing trace files for the harness to consume: the rag-app
build emits a trace record on every `python -m rag_app ask --json`
invocation, and the tool-use-agent build emits one on every
`python -m tool_use_agent ask --json`. Appending those to a JSONL file
(one record per line) is the simplest way to assemble a trace input for
the harness; no special script is required.

## Design tradeoffs called out for interview discussion

- **Scoring records vs. generating them.** Eval frameworks split into
  two families — ones that drive an LLM and ones that score what a
  product already produced. This harness is the second kind. A PM
  should be able to defend why (reproducibility, single-source-of-
  truth on provider/model choice in the builds, no key dependency)
  and articulate when the first kind is the right reach (live A/B,
  multi-provider comparison, online judging).
- **Deterministic rubrics vs. LLM-graded rubrics.** Every rubric in
  v1 is a function of fields the trace already carries — refusal
  becomes a string-equality check, groundedness becomes a count
  over the `verification` block. LLM-graded scoring is the obvious
  next quality knob ("is this answer *good*?"), with a real cost:
  judge variance, judge prompt drift, and a re-introduced API-key
  dependency. The v1 path is deliberately the cheaper, more
  defensible one.
- **One labeled file vs. per-build files.** A single
  `queries.jsonl` makes cross-build comparison legible. Per-build
  files would let each build evolve its label set independently but
  would erode the property that motivates the harness — comparing
  the same question across two different patterns.
- **Two invariants vs. a full helper test suite.** The harness
  could fully replicate and assert every behavior in both builds'
  `verify.py` and `trace.py`. It does not. It asserts the two
  specific properties whose drift would produce a silently wrong
  report (refusal-string byte-equality, helper-hash equivalence on
  a known fixture). The rest is the unit-test job inside each
  build.
- **Markdown report vs. structured dashboard.** A Markdown table
  fits an interview leave-behind; a dashboard would not. If this
  build were productized, the Markdown report would be the seed
  for a per-PR comment generator, not a Datadog graph.
