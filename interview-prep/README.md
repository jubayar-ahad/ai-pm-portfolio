# Mock Interview Q&A — Portfolio Index

The index for the five mock-interview Q&A banks in this directory —
four anchored to portfolio artifacts (cursor-teardown / rag-app /
tool-use-agent / evals-harness) plus a fifth behavioral bank anchored
to the user's own lived experience — plus a "common cross-artifact
questions" section for the prompts an interviewer will use to range
*across* the portfolio rather than drill into any single artifact.
Nothing in this file is auto-populated — the agent does not invent
the user's answers, nor does it invent the user's behavioral stories.
See `../DECISIONS.md` for the no-fabrication rule.

The four per-artifact banks each carry ten questions on their own
artifact with strong-answer rubrics and `_<your draft>_` italic-marker
placeholders. The behavioral bank carries fifteen questions on the
canonical PM behavioral surface with the same rubric + draft-slot
grammar, plus a per-question structure name (STAR / PARLA / one of
five named alternatives) so the user picks the right shape per
question rather than forcing every answer into STAR. This README sits
one level above all five: it links the banks, names the suggested
prep order, and owns the cross-artifact rubrics each per-artifact
file stubs with a pointer back here.

---

## The five Q&A banks

| File | Source of truth | Topics in scope | NEXT_WORK |
| --- | --- | --- | --- |
| [`cursor-teardown.md`](cursor-teardown.md) | [`../teardown-prd/cursor-teardown.md`](../teardown-prd/cursor-teardown.md) | Why Cursor over Copilot, ship-next picks, instrumentation, stop-aggressive default, the weakest claim, post-hire kill list | item 7 sub-checkbox 1 |
| [`rag-app.md`](rag-app.md) | [`../rag-app/`](../rag-app/) | BM25 vs. dense, reranker tradeoffs, abstention bar, groundedness measurement, corpus ownership, cost ceiling, multi-turn deferral, citation verifier, ship/cut | item 7 sub-checkbox 2 |
| [`tool-use-agent.md`](tool-use-agent.md) | [`../tool-use-agent/`](../tool-use-agent/) | `max_steps` cap, refusal taxonomy, trace schema, tool catalog design, two-layer safety guardrails, productionization, tool-use vs. RAG, schema-validated function calling | item 7 sub-checkbox 3 |
| [`evals-harness.md`](evals-harness.md) | [`../evals-harness/`](../evals-harness/) | Rubric selection, per-rubric defense, cost rubric (p50/p95/max), what's missing, cross-build invariants, scaling, deterministic vs. LLM-graded, bad-eval-set diagnostics | item 7 sub-checkbox 4 |
| [`behavioral.md`](behavioral.md) | The user's own lived experience (no portfolio artifact source) | Tell-me-about-a-time (hard decision / conflict / failure / launch / ambiguity), why-leaving / why-this-role / why-AI-PM, biggest strength / biggest weakness, manager-style fit, influencing without authority, cross-functional conflict, saying no to a stakeholder, wrong call learned from | item 9 sub-checkbox 1 |

The four per-artifact banks each ship ten questions in the 8–10 range
item 7 names; the behavioral bank ships fifteen questions in the
12–15 range item 9 names. The question count is portable across the
four per-artifact banks by deliberate choice (see the consolidating
DECISIONS entry for item 7 sub-checkbox 6); the *anchoring* grammar
is parameterized by the source artifact and differs between banks —
the cursor-teardown bank cites the teardown's `§n.m`-numbered
sections, the three README-based banks cite the README's named
headings (`Stack choices`, `Refusal threshold row`, `Design
tradeoffs`, etc.). This is a feature, not drift: a rubric that
fabricates a `§n.m` citation against an artifact that uses named
headings would violate the no-fabrication rule at the citation level.

The behavioral bank's anchoring grammar shifts again because its
source is *not* a portfolio artifact: it cites the *evidence type* a
strong answer would carry (a specific role, a measurable outcome, a
named cross-functional partner, a dated decision) without naming the
specifics, which only the user can supply. The most consequential
no-fabrication violation in that bank is story-level fabrication
(inventing the user's actual experiences) rather than citation-level
fabrication against a document — and unlike a `§n.m` citation, that
violation is unverifiable by any auditor with access to the artifact
only. The behavioral bank's per-question rubric structure also
varies: STAR for the seven situational tell-me-about-a-time prompts,
PARLA for the three reflection-heavy prompts where Learning +
Application carry the answer, and five named alternative structures
for the five non-narrative fit/POV/preferences prompts that would
read as forced under STAR.

---

## Suggested prep order

This is one credible order, not the only one. The reasoning is named
inline so a reader can deviate when their interview slate has
different signals.

1. **Start with [`cursor-teardown.md`](cursor-teardown.md).** The
   teardown PRD is the single highest-density artifact in the
   portfolio — one document the user wrote end-to-end, with explicit
   tradeoff calls, a no-targets posture in §4, and a documented
   precedent for killing sections. It rewards re-reading once and
   stress-tests the user's ability to defend authored prose under
   pushback. If a candidate can defend the teardown's ten anticipated
   questions cleanly, the other three banks fall out faster because
   the same defending-a-call discipline transfers.
2. **Then [`rag-app.md`](rag-app.md).** It is the most-named build in
   the portfolio: the root README's milestone map lists it first; the
   `../evals-harness/` build consumes its `verify.py` byte-equality
   invariant; the `../tool-use-agent/` README's "Why an agent and not
   RAG" section forward-references it. An interviewer who reads any
   of those three artifacts will reach for rag-app questions first.
3. **Then [`tool-use-agent.md`](tool-use-agent.md).** Its surface area
   is the largest of the three builds (nine catalog tools, a four-
   bucket refusal taxonomy, a two-layer safety story for the three
   new tools), so the rubrics are correspondingly the longest. After
   rag-app, the agent build reads as the second-stack-choice question
   set — schema-validated function calling, why an agent and not RAG,
   etc. — which builds on rather than competing with the rag-app
   prep work.
4. **Then [`evals-harness.md`](evals-harness.md).** It is structurally
   the most senior-PM-flavored bank — every question is some flavor
   of "how do you know your build is good?" and the rubrics lean on
   the rag-app + tool-use-agent prep work above (the harness scores
   *their* outputs, so a candidate who hasn't internalized those
   builds will struggle to defend the rubric set). Save it for last
   among the *artifact* banks.
5. **Draft [`behavioral.md`](behavioral.md) alongside the artifact
   banks, not after.** The behavioral bank is the only one whose
   drafting *does not* depend on the per-artifact prep — its source
   is the user's own lived experience, not the portfolio artifacts.
   That makes it parallelizable: any evening between artifact-bank
   sessions, draft two or three behavioral answers, because the
   cost of being caught flat-footed on a behavioral is higher than
   on a technical question (the technical question lets you reason
   in real time; the behavioral demands a story you either have or
   do not). One credible scheduling note: tie the behavioral
   *failure* and *wrong-call* prompts (Q3, Q15) to the artifact
   prep — once you've drafted the cursor-teardown bank's "weakest
   claim" question, you'll have a sharper handle on what a strong
   "tell me about a wrong call" looks like, because the discipline
   transfers.
6. **Then this README's cross-artifact questions.** Once each per-
   artifact bank's ten questions and the behavioral bank's fifteen
   are drafted, the cross-artifact questions below are the
   synthesis prompts — they don't admit strong answers without the
   per-artifact prep first.

Two minor scheduling notes. If the user's actual interview slate is
heavier on infrastructure / evaluation than product-strategy, swap
the order to `evals-harness` first and `cursor-teardown` last. If
the interview is for a non-AI-PM role that happens to want AI
literacy, the teardown alone may be enough — skip the build banks
and skim only the cross-artifact questions here. The behavioral
bank stays in scope for any PM-shaped interview regardless of the
slate, since the canonical behavioral surface is universal.

---

## Common cross-artifact questions

These three questions range across the portfolio rather than drilling
into any single artifact. The "walk me through your portfolio"
question is the universal opener every per-artifact bank stubs with a
pointer here. The other two are the synthesis prompts an interviewer
will use after the user has fielded several per-artifact questions
and the interviewer wants to see whether the artifacts cohere.

### CA1. Walk me through your portfolio.

**Strong answer covers:** the *shape* of the portfolio before any
artifact-specific content — three runnable LLM builds + one teardown
PRD + a five-scaffold hiring-funnel kit, per the root README's
milestone map — and *why* that composition rather than five builds or
five teardowns; the cross-build invariants that bind the three
Day-10 builds (the byte-identical `REFUSAL_SENTENCE` across the
LLM builds, the algorithm-equivalent `compute_record_id` /
`compute_corpus_fingerprint` pair that lets the harness compare
across rather than benchmark in isolation), since those are the
single highest-leverage technical claim the portfolio makes; the
deliberate *no-fabrication* posture (no invented employment in the
funnel scaffolds, no fabricated Cursor internals in the teardown, no
hand-written user answers in this interview-prep directory) as the
discipline that ties the artifacts together; and a one-sentence
*pivot offer* at the end ("I can drill into any of the three builds
or the teardown — where do you want to start?") so the interviewer
can pick the follow-up rather than waiting for the candidate to
volunteer. The single move that distinguishes a strong walk-through
from a list-of-artifacts is naming the *cross-build invariant* — most
candidates list the artifacts, few name the contract that ties them.

**Your draft:** _<your draft answer here — name the four artifacts in shape order, name the two cross-build invariants by name, name the no-fabrication discipline, and end with the pivot offer; aim for 60–90 spoken seconds (roughly 150–240 words written out) so the interviewer can pick the follow-up before pacing becomes the problem>_

### CA2. Which artifact in this portfolio is the weakest, and what would you do about it?

**Strong answer covers:** the candidate's actual honest assessment of
which artifact is least defensible — the rag-app's current ouroboros
corpus (the repo's own markdown, flagged for replacement in NEXT_WORK
item 5 and currently in holding pattern awaiting the user's pick from
[`../rag-app/corpus/CORPUS_CANDIDATES.md`](../rag-app/corpus/CORPUS_CANDIDATES.md))
is one defensible pick; the tool-use-agent's lack of a real
multi-step orchestration demo beyond the bounded 6-step cap is
another; the teardown PRD's no-targets posture in §4 is a third
(arguably a strength, but a critic can frame it as evasion); the
evals-harness's deterministic-only rubric set is a fourth (no LLM-
graded coverage, by design — see the Design-tradeoffs section of
its README). The strong answer *picks one*, *names the upgrade path*
(e.g., "replace the corpus and re-run the existing 18-question eval
set, then publish the diff"), and *names the cost* (the rag-app
corpus replacement requires a user pick from CORPUS_CANDIDATES,
which is currently the bottleneck; the multi-step demo requires
real tool composition not just more tools, which is a design-think
item not a coding item). What distinguishes a strong answer is
willingness to *commit to a single weakest pick* under pressure —
hedging across all four signals an unwillingness to prioritize,
which is the same failure mode the evals-harness Q4 ("what's
missing?") tests for from a different angle.

**Your draft:** _<your draft answer here — pick exactly one artifact as weakest, name the specific upgrade, name the cost, and explicitly disclaim that "weakest" doesn't mean "broken">_

### CA3. If you had to cut one of the four artifacts entirely, which goes and why?

**Strong answer covers:** the structural difference between cutting
the teardown PRD (loses the highest-density PM-craft signal but
keeps three runnable builds + invariants), cutting any one build
(loses one third of the cross-build invariant proof — the harness
can't compare across what isn't there), cutting the evals-harness
(loses the *cross-build* claim entirely because the invariants are
asserted at the harness's startup), and cutting this interview-prep
directory (loses the rehearsal surface but doesn't touch the
artifacts themselves). The strong answer recognizes that the
evals-harness is *structurally* the load-bearing piece — cutting it
turns the portfolio from "three builds that share contracts on
purpose" into "three builds that happen to coexist" — and that the
teardown PRD is *signal-bearing* but not structurally load-bearing
(cutting it loses a PM-craft demo but leaves the runnable demos
intact). A defensible cut is the interview-prep directory itself
(meta, not deliverable) or the teardown PRD (one document, easier
to re-ship later). An indefensible cut is the evals-harness, and
naming *why* that's indefensible is the move that distinguishes a
strong answer from a guess. The interviewer is probing whether the
candidate can rank load-bearing vs. signal-bearing artifacts under
pressure — a senior-PM-flavored question that requires the same
discipline as Q4 of the evals-harness bank ("what's missing?")
applied across the portfolio rather than within one artifact.

**Your draft:** _<your draft answer here — pick exactly one artifact, name the load-bearing-vs-signal-bearing distinction explicitly, defend the cut, and name the artifact you'd never cut and why>_

---

## How to use this index

1. **Read the per-artifact bank end-to-end first** before drafting
   any cross-artifact answer above. The cross-artifact rubrics
   reference invariants, tradeoffs, and per-artifact framings that
   the per-artifact banks lock in — drafting cross-artifact answers
   first will read as generic, not portfolio-grounded.
2. **The cross-artifact questions get one draft each, like the
   per-artifact ones.** Three slots, three drafts. Don't try to
   prepare *every* possible cross-artifact question — the three here
   are the high-leverage ones an interviewer will actually ask;
   marginal others (e.g. "rank the artifacts by hardest to easiest")
   are not worth the prep time when they don't change the user's
   answer to CA2 or CA3 above.
3. **The placeholder grammar is `_<your draft>_`** matching the
   per-artifact banks and the rest of `../templates/`, so one regex
   (`_<.*>_`) finds every unfilled slot across all portfolio
   scaffolds.
4. **The rubrics are checklists, not scripts.** A strong cross-
   artifact answer names the moves the rubric lists (artifact shape,
   cross-build invariants, load-bearing vs. signal-bearing, etc.)
   without reciting the rubric's framing. Delete the rubric before
   any live rehearsal.
5. **Suggested prep order is in the previous section.** Read it
   before drafting the per-artifact banks — drafting in a different
   order is fine, but the prep order minimizes the work because each
   bank builds on the prior ones' grounding.
6. **Behavioral interview prep is now in scope** via
   [`behavioral.md`](behavioral.md), which ships under NEXT_WORK
   item 9 sub-checkbox 1. The fifteen canonical PM behavioral
   questions cover tell-me-about-a-time / failure / strength-
   weakness / why-leaving / why-this-role / why-AI-PM / manager-fit
   / influence-without-authority / cross-functional-conflict /
   saying-no / wrong-call. Three adjacent buckets remain deferred
   *out of scope* for this directory: **culture-fit** (interview
   prep aimed at one company's stated values, which needs a target
   company to ground the answers honestly), **case-prompt**
   (whiteboard-shaped "design product X" prompts that reward live
   structuring practice over written prep), and **negotiation**
   (compensation-and-offer prep that needs target-company-specific
   ranges to be useful and is unsafe to scaffold generically). The
   deferral is intentional and the gap is named here so a reader
   does not assume incompleteness — the user owns picking up any
   of the three deferred buckets later under a new NEXT_WORK item.

---

## Source of truth & cross-links

- The four per-artifact banks: [`cursor-teardown.md`](cursor-teardown.md),
  [`rag-app.md`](rag-app.md), [`tool-use-agent.md`](tool-use-agent.md),
  [`evals-harness.md`](evals-harness.md). Each has its own "Source of
  truth & cross-links" section pointing back at its underlying
  artifact and the no-fabrication rule.
- The behavioral bank: [`behavioral.md`](behavioral.md). Its
  source-of-truth is the user's own lived experience rather than a
  portfolio artifact, so its no-fabrication rule binds at the
  story level (the agent does not invent the user's actual
  experiences) rather than at the citation level. Its rubric
  structures (STAR / PARLA / five named alternatives) are named
  per-question in the preamble; ships under NEXT_WORK item 9.
- The portfolio's top-level index: [`../README.md`](../README.md) —
  carries the milestone map this README's CA1 rubric references.
- The chronological design log: [`../DECISIONS.md`](../DECISIONS.md) —
  carries the no-fabrication rule (search for "no-fabrication"), the
  cross-build invariant decisions (search for "REFUSAL_SENTENCE" or
  "compute_record_id"), and the item 7 sub-checkbox 6 consolidating
  entry when it ships.
- The corpus-pick bottleneck CA2 references:
  [`../rag-app/corpus/CORPUS_CANDIDATES.md`](../rag-app/corpus/CORPUS_CANDIDATES.md)
  is the ranked-candidates file awaiting a user pick under NEXT_WORK
  item 5.
- The cross-build invariants CA1 references in concrete code:
  [`../evals-harness/evals_harness/invariants.py`](../evals-harness/evals_harness/invariants.py)
  is where the `REFUSAL_SENTENCE` byte-equality and the
  `compute_corpus_fingerprint` / `compute_record_id` algorithm-
  equivalence checks fire at startup (loaded from
  `rag-app/rag_app/verify.py` and `tool-use-agent/tool_use_agent/verify.py`
  for the refusal sentence; from the same builds' `trace.py` for the
  fingerprint and record-id helpers).
- The no-fabrication rule for the `_<your draft>_` slots:
  `../DECISIONS.md` (search for "no-fabrication"). The agent never
  drafts the user's answers; the slots are the user's to fill.

This directory is interview-prep, not a deliverable for any specific
employer. The questions and rubrics anticipate what an AI-PM
interviewer is likely to probe given the underlying artifacts'
actual content; they are not sourced from any company's interview
process and make no claim to mirror one.
