# Mock Interview Q&A — evals-harness

A populatable interview-prep file for the evals-harness build at
`../evals-harness/`. Ten likely interviewer questions, each followed
by the strong-answer rubric (what a credible answer covers, not what
the user *should* say) and a `_<your draft>_` italic-marker
placeholder for the user's own draft. Nothing in this file is auto-
populated — the agent does not invent the user's answers. See
`../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. **Read `../evals-harness/README.md` end-to-end first.** Every
   rubric below cites a section of that README by heading name
   (e.g. "Success metrics (the rubrics the harness will score)",
   "Stack choices", "Failure modes worth designing around",
   "Productization questions a PM should ask before shipping this
   for real", "Design tradeoffs called out for interview
   discussion"). A strong answer grounds in the README's documented
   decisions rather than re-arguing them from scratch — if your
   draft contradicts the README, either you've found a real
   weakness worth patching upstream or you should re-read the
   section before answering.
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
   (`../rag-app/`, `../tool-use-agent/`) or the Cursor teardown
   (`../teardown-prd/cursor-teardown.md`); use those cross-links
   when they strengthen an answer — they prove the evals-harness is
   the *integrator* of the kit, not a standalone toy.
6. **The placeholder grammar is `_<your draft>_`** matching the rest
   of `../templates/` — so one regex (`_<.*>_`) finds every unfilled
   slot across all portfolio scaffolds.

---

## Q1. How did you select the rubrics? Why these five and not three or eight?

**What a strong answer covers.** Reframes from "what is a complete
rubric set" to "what is the *minimum* rubric set that lets a PM
defend the two builds across the dimensions an interviewer probes."
The README's "Success metrics (the rubrics the harness will score)"
section names exactly five — refusal-when-uncertain, groundedness,
termination quality, cost per answered query, first-call tool
accuracy — and the selection logic is *coverage of the
PM-defensible failure surface*, not "every metric we could
compute." A credible answer walks the coverage matrix:
**correctness** (groundedness for rag-app, first-call-tool for
tool-use-agent), **calibration** (refusal-when-uncertain on both
builds — does the system know when it doesn't know), **runtime
discipline** (termination quality on the agent — did it stop for
the right reason), and **economics** (cost per answered query on
both builds). Five rubrics, four orthogonal product properties; the
fifth is the cross-build asymmetry between groundedness (rag-app
only, scoring the `verification` block) and first-call-tool
(tool-use-agent only, scoring `tool_calls[0].tool`) — they're
*different* rubrics because the builds answer different questions,
not redundant ones. Bonus: name the fact that none of the five are
LLM-graded — that's a deliberate design tradeoff covered in Q8, not
a coverage gap.

**Your draft:** _<your draft answer here — name the coverage matrix (correctness / calibration / runtime discipline / economics), call out the cross-build asymmetry between groundedness and first-call-tool, and frame five as the *minimum* defensible set>_

---

## Q2. Why these five rubrics specifically? Defend each one against an alternative.

**What a strong answer covers.** Q1 establishes the coverage matrix
shape; Q2 defends each rubric on the merits. The answer should walk
the five and name what each beats: **refusal-when-uncertain** beats
"accuracy on `expected=refuse`" because it's a *single equality
check against `REFUSAL_SENTENCE`* (the byte-equality invariant is
load-bearing — see Q5) rather than a fuzzy match; **groundedness**
beats "answer-correctness" because it's a deterministic count over
the `verification` block (`N/M citations resolved`) rather than an
LLM-graded judgment that would re-introduce the API-key dependency
the harness is engineered to avoid; **termination quality** beats
"agent succeeded" because it splits the five buckets
(`ended_clean` / `model_refused` / `max_steps_exhausted` /
`repeated_tool_error` / `no_observation`) so a PM reads "the agent
timed out 12% of the time" vs. "the agent gave up retrying 3% of
the time" as *two different product signals*; **cost** beats
"latency" because the harness sums `input_tokens + output_tokens`
from each trace deterministically rather than re-timing wall-clock
(which depends on hardware and warm-cache state — explicitly out of
scope per the README's "What's intentionally out of scope here"
section); **first-call-tool accuracy** beats "tool-call rate"
because it pins *which* tool the agent reached for first against
the label's `expected_first_tool`, surfacing planning errors a
hit-rate metric would average away. Bonus: each rubric has an
explicit `no_observation` bucket so dry-run / refused / verification-
missing rows never inflate the denominator — a PM-honest discipline
that LLM-graded scoring tends to omit.

**Your draft:** _<your draft answer here — defend each of the five rubrics against a named alternative and call out the `no_observation` denominator discipline>_

---

## Q3. Walk me through the cost rubric design. Why p50/p95/max and not mean?

**What a strong answer covers.** Names that the cost rubric is the
*only* rubric reporting **distributional statistics** rather than a
match/no-match accuracy — every other rubric collapses to a count
("N grounded out of M observable"), but cost is a distribution and
collapsing it to a single mean would hide the long tail that
matters for capacity planning. The p50/p95/max triple is the
defensible choice: **p50** is the typical-query cost (what budget
planning uses), **p95** is the long-tail cost that drives capacity
(a 5%-tail query costs 3-10× the median in real agent workloads),
**max** is the worst-case bound that a per-call rate-limit needs to
respect. A credible answer also covers the **latency split**
(README "Success metrics" → cost row): for the tool-use-agent
specifically, the harness reports `steps_taken` and
`tool_latency_ms_sum` p50/p95/max as a *separate sub-table* from
`total_tokens`, so a PM can read tool-side cost independently of
model-side cost — a real agent failure mode is "the model is cheap
but the tool calls are slow," which a single combined-cost metric
would average away. The locked iteration-14 latency-split decision
in the rag-app world drove this design — see DECISIONS for
"latency-split decision." Bonus: name the **`no_observation`
denominator discipline** (dry-run + `refused-low-score` +
refused-other-mode traces classify as `no_observation` and are
excluded from every stats denominator, but **live refusals still
count** because the tokens *were* consumed — the rubric is honest
about which costs were really paid).

**Your draft:** _<your draft answer here — defend p50/p95/max over mean, walk the latency-split sub-table rationale, and name the live-refusals-still-cost-money discipline>_

---

## Q4. What's missing from this harness? What would you build next?

**What a strong answer covers.** Names the five explicit deferrals
from the README's "What's intentionally out of scope here" section
and ranks them honestly by *what an interviewer would probe first*.
The five are: (1) **no model-graded scoring** ("use an LLM to score
the LLM" — explicitly deferred to preserve the no-API-key
property, not absent by oversight), (2) **no labeled-set authoring
tools** (the JSONL is hand-edited at start; a `seed` subcommand
that proposes labels from sample traces is named as the future
iteration), (3) **no regression dashboard / persistence** (reports
are Markdown snapshots, not a database; a "diff two reports" mode
is named), (4) **no latency benchmarking** (the harness reads
`latency_ms` from trace records but does not re-time anything —
wall-clock benchmarks belong in a separate harness with consistent
hardware), (5) **no fine-tuning loop** (the harness scores
behavior, not weights). A strong answer picks **#1
(model-graded scoring)** as the highest-leverage next ship because
it's the deferred quality knob ("is this answer *good*?" — a
property no deterministic rubric in v1 can score) and walks the
cost honestly: judge variance, judge prompt drift, the
re-introduced API-key dependency. The `corpus_fingerprint`
diversity warning — explicitly deferred at slice 7 because it
requires threading `corpus_fingerprint` through every per-rubric
scored row schema first — is a smaller-but-near-term ship worth
naming as the "free win." Bonus: cite the `Roadmap (subsequent
iterations)` section as the *existing* precedent for treating the
harness as a sequence of provisional commitments rather than a
fixed design.

**Your draft:** _<your draft answer here — rank the five deferrals by interviewer-leverage, pick model-graded scoring as the highest-leverage ship, name `corpus_fingerprint` diversity as the free win, and cite the Roadmap as the precedent>_

---

## Q5. Explain the cross-build invariants. Why two checks, and why at startup?

**What a strong answer covers.** Names the two invariants from the
README's "Stack choices" → Startup invariants row and the "Why an
evals harness, and why this shape" → third property: (1)
**`REFUSAL_SENTENCE` byte-equality** across the two builds
(`rag-app/rag_app/verify.py` and `tool_use_agent/verify.py` each
define the string independently; if one drifts, the refusal scorer
would split one logical bucket into two and over-report variance),
and (2) **trace-helper behavior equivalence** (two tiny ~3-line
fixtures — hash a known corpus twice and compare — verifying the
two independently-implemented helper algorithms in
`rag-app/rag_app/trace.py` and `tool_use_agent/trace.py` agree).
The "why two, not many" answer is the README's "Two invariants vs.
a full helper test suite" Design-tradeoff row: the harness could
fully replicate every behavior in both builds' `verify.py` and
`trace.py`, but it does not — it asserts the two specific
properties **whose drift would produce a silently wrong report**,
and leaves the rest to each build's own unit-test suite. The "why
startup, not score-time" answer is **fail-fast economics**: a
score-time check would still produce a *partial* scored.jsonl
before failing, leaving the user to wonder whether the partial
output is usable; a startup check exits with code 2 and a named
error before any scoring runs, so the only signal a user gets is
"the invariant failed, here is which one, fix the build." Bonus:
name the `score` subcommand's re-run of the startup invariants as
the defense-in-depth move — drift introduced between `ingest` and
`score` is still caught.

**Your draft:** _<your draft answer here — name the two invariants, defend "two not many" on the fail-loud-on-silently-wrong-report property, defend "startup not score-time" on fail-fast economics, and call out the score-subcommand re-run as defense in depth>_

---

## Q6. How does this scale to a larger eval set? What breaks at 100×?

**What a strong answer covers.** Reframes from "is it fast enough"
to "what property breaks first as N grows." The README's "Failure
modes worth designing around" → Trace size growth row already
locks the streaming property: the harness reads JSONL line by line
and streams, with nothing held in memory beyond the current record
plus a running accumulator — so memory is O(1) in trace count and
O(unique-`record_id`) in label count, both of which scale linearly
to 100×16 = 1,600 labels without any architectural change. The
**first** thing that breaks is not memory or runtime but **label
ownership** (README "Productization questions" #2): a 16-label set
is hand-curatable by one PM; a 1,600-label set needs an *owner* —
without one, label drift silently degrades every metric (per the
"Failure modes" → Label drift row). The **second** thing that
breaks is the Markdown report shape: per-record listings of
non-clean termination buckets or unresolved-citation rows fit on
one screen at N=16, but at N=1,600 they overflow — and the right
fix is *not* "make the table scroll" but to add the deferred
"regression dashboard / persistence" (README "What's intentionally
out of scope here" #3) so the per-PR diff names *changed* rows
rather than listing all rows. The **third** thing that breaks is
the `corpus_fingerprint` confounded-comparison check (README
"Failure modes" → Confounded comparison row): at N=16, "did all
traces come from the same corpus?" is a one-glance check; at
N=1,600 across multi-day runs, the harness needs to *partition* by
fingerprint and report per-corpus metrics rather than flagging
diversity as a warning. Bonus: name **scoring throughput** as the
*non*-blocker — the rubrics are O(1) per record and there's no
per-record API call, so 1,600 records score in <1s on a laptop.

**Your draft:** _<your draft answer here — name what breaks first (label ownership), second (report shape), third (`corpus_fingerprint` partitioning), and call out scoring throughput as the non-blocker>_

---

## Q7. Why one labeled file across both builds, not one per build?

**What a strong answer covers.** Names the README's "Design
tradeoffs called out for interview discussion" → "One labeled file
vs. per-build files" row as the explicit decision: **one
`queries.jsonl`** with `applies_to` field on each label, listing
which build(s) the question applies to. The defended property is
**cross-build comparability** — the *same* question's behavior
across the two builds is the PM-relevant artifact, and per-build
label files would erode that property by letting each build's label
set drift independently. A credible answer walks the cost: a
per-build file would let the rag-app evolve corpus-specific labels
and the tool-use-agent evolve tool-specific labels without either
side having to negotiate — at the cost of losing the property that
*motivates* the harness ("for the same labeled set of questions,
which pattern is more grounded? more cost-efficient?"). The single
labeled file forces the inverse trade: any new label must pass the
both-builds-care test, OR explicitly carry `applies_to` =
single-build, which is the README's escape hatch
(`tracker_rollup` shape, 3 tool-use-only entries; the `applies_to`
field is *list-typed* precisely to permit this). Bonus: the
ingest-slice schema lock (the 9-key uniform record shape per
README "Roadmap" #1) makes this trade enforceable mechanically —
a per-build file would let one side add a key the other doesn't
recognize, and the harness's known-key validator would not see the
divergence until score-time.

**Your draft:** _<your draft answer here — defend cross-build comparability as the motivating property, walk the cost honestly, and name `applies_to` as the explicit escape hatch>_

---

## Q8. Why deterministic rubrics? Why no LLM-graded scoring?

**What a strong answer covers.** Names the README's "Design
tradeoffs called out for interview discussion" → "Deterministic
rubrics vs. LLM-graded rubrics" row and walks the trade as the
README states it: every rubric in v1 is a function of fields the
trace **already carries** — refusal becomes a string-equality
check against `REFUSAL_SENTENCE`, groundedness becomes a count
over the `verification` block — and the *cost* of stepping up to
LLM-graded scoring is real and triple: **judge variance** (two
runs of the same judge on the same answer can disagree),
**judge prompt drift** (the prompt itself becomes a thing to
version and re-validate), and **a re-introduced API-key
dependency** that defeats the property motivating the build (the
README's first-sentence summary calls out "scores trace records
that the two LLM builds already emit … without
`ANTHROPIC_API_KEY`, in any sandbox or CI environment"). A
credible answer also names what LLM-graded scoring *would* buy —
the deferred "is this answer *good*?" quality knob that no v1
rubric can score (a perfectly-grounded answer can still be
unhelpful, verbose, or off-topic) — and calls model-graded
scoring the obvious next ship per Q4. The honest framing: v1 is
the *cheaper, more defensible* path, not the *only* path; the
two-track future is (a) keep the deterministic rubrics as the
non-negotiable signal floor, (b) layer the LLM judge on top as an
optional richer signal with its own version + variance budget.
Bonus: name the iteration's `MARKDOWN_REPORT_PROVENANCE` discipline
(report rows are reproducible byte-for-byte from the same scored
JSONL) as the property an LLM judge would have to *not* break — a
judge run that varies across runs is allowed, but the report
generator should record judge model + seed so the variance is
auditable rather than silent.

**Your draft:** _<your draft answer here — walk the three real costs of LLM-graded scoring, name what it would buy, and frame the two-track future where deterministic and graded rubrics coexist>_

---

## Q9. How would you tell if the eval set itself is bad?

**What a strong answer covers.** Reframes from "are the metrics
right" to "are the *labels* right" — and names the three failure
shapes from the README's "Failure modes worth designing around"
section that surface bad labels: **(1) Label drift** (a query
labeled `expected_outcome=answer` may correctly become `refuse` as
the corpus evolves; the harness surfaces this via
`corpus_fingerprint_at_label` ≠ `corpus_fingerprint` on the trace,
as a *per-record warning, not a silent miscount*), **(2) Scoring
on stale traces** (a trace recorded against an older schema version
would be silently misinterpreted; `schema_version` matched exactly,
unknown versions raise), and **(3) Confounded comparison** (more
than one distinct `corpus_fingerprint` across traces for a single
build — flagged explicitly rather than averaged). The *fourth*
signal — not in the failure-modes section but in the README's
"Productization questions" #5 — is the **false-positive rate of
the refusal scorer**: if `expected_outcome=refuse` is a small
fraction of the labeled set (currently 4/16 are `out_of_corpus`,
and not every such label necessarily yields refusal), even small
label errors swing the metric. A credible PM-craft answer names
the diagnostic: at ingest time, the unpaired-labels / unpaired-
traces counts (already in the refusal rubric's table header per
README "Roadmap" #3) are the cheap first signal that a labeled set
has rot — labels that no trace ever answers are stale labels by
operational definition. Bonus: name the deferred "labeled-set
authoring tools" (README "What's intentionally out of scope here"
#2) as the eventual fix — a `seed` subcommand that proposes label
candidates from a sample of trace records would close the loop
between trace evolution and label maintenance.

**Your draft:** _<your draft answer here — walk the three failure-mode signals plus the false-positive-rate productization question, name unpaired-counts as the cheap diagnostic, and frame the deferred seed subcommand as the long-term fix>_

---

## Q10. Post-hire: name one thing you'd ship next on this harness, and one thing you'd cut.

**What a strong answer covers.** Picks one **ship** and one **cut**
with the specific data that would justify each. The ship slot
should pull from the Q4 deferrals — model-graded scoring is the
most-leveraged but also the most-controversial, so an interview-
strong pick is the **`corpus_fingerprint` diversity warning**
(README "Roadmap" slice 7 explicit deferral) because (a) it's a
small additive-schema change rather than a re-architecture,
(b) it closes one of the three named failure modes (confounded
comparison), and (c) the data that justifies shipping it is the
ingest-time observation of multi-corpus traces in any single eval
run — a one-line counts check, not a multi-day measurement effort.
The cut slot should pick something the harness currently does that
isn't earning its keep. A credible cut is **the per-record
"not-grounded" / "mismatch" listing** in the groundedness and
first-call-tool reports (README "Roadmap" slice 4): at the current
N=16 scale, naming the failing label_id is useful, but the listing
already lives in the scored.jsonl and duplicating it in the
Markdown report makes the leave-behind report less paste-able into
an interview slide. The data justifying the cut: paste-friendliness
(measured by "fits on one screen") is a real product property of a
leave-behind report; the per-record listing is *moved* to the
scored.jsonl artifact, not deleted, so no information is lost.
The answer should *not* perform humility ("I'd kill the whole
thing") or refuse to commit ("I wouldn't change anything until I
had more data"). Both read as evasive. The honest move: "here's
the specific thing I'd ship, here's the specific data that would
justify shipping it; here's the specific thing I'd cut, here's the
specific data that would justify cutting it." Bonus: name the
README's "Roadmap (subsequent iterations)" section as the
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
question exists and where to find its rubric. If you are practicing
answers cold, expect this question first and the ten above as
follow-ups — the interviewer will use the walk-through to pick
which two or three of the ten to probe in depth. An evals-harness-
flavored walk-through naturally pivots into Q1 (rubric selection as
the first PM-craft signal — "I picked the *minimum* defensible set,
not the maximum") or Q5 (cross-build invariants as the first
engineering-discipline signal — "two checks that prevent silently
wrong reports"), so prep those two with extra care.

---

## Source of truth & cross-links

- The build itself: `../evals-harness/` — README is the design
  contract; the `evals_harness/` package implements it; `tests/`
  covers the production surface with no network or API key; the
  `queries.jsonl` file at the build root is the labeled set the
  rubrics score against.
- Sibling Q&A banks (NEXT_WORK item 7, sub-checkboxes 1, 2, 3):
  `cursor-teardown.md` (shipped), `rag-app.md` (shipped),
  `tool-use-agent.md` (shipped) — each anticipates 8–10 questions
  on its own artifact.
- Index file (NEXT_WORK item 7, sub-checkbox 5): `README.md` will
  link the four Q&A banks, name the suggested prep order, and
  carry the cross-artifact questions section.
- Related portfolio piece (cross-link for rubrics Q2, Q5, Q7): the
  `../rag-app/` build, whose `verify.py` defines one of the two
  `REFUSAL_SENTENCE` strings the harness asserts byte-equality on
  and whose `verification` block the groundedness rubric reads.
- Related portfolio piece (cross-link for rubrics Q1, Q2, Q3, Q5):
  the `../tool-use-agent/` build, whose `verify.py` defines the
  other `REFUSAL_SENTENCE` string, whose `trace.py` is the second
  half of the trace-helper equivalence invariant, and whose
  `tool_calls[]` / `stop_reason` / `refusal_reason` fields the
  first-call-tool / termination / cost rubrics consume.
- Iteration-14 latency-split decision referenced by Q3:
  `../DECISIONS.md`, search for "latency-split decision".
- The no-fabrication rule for the `_<your draft>_` slots:
  `../DECISIONS.md` (search for "no-fabrication"). The agent never
  drafts the user's answers; the slots are the user's to fill.

This file is interview-prep, not a deliverable for any specific
employer. The questions and rubrics anticipate what an AI-PM
interviewer is likely to probe given the evals-harness README's
actual content; they are not sourced from any company's interview
process and make no claim to mirror one.
