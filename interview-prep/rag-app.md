# Mock Interview Q&A — rag-app

A populatable interview-prep file for the rag-app build at
`../rag-app/`. Ten likely interviewer questions, each followed by the
strong-answer rubric (what a credible answer covers, not what the user
*should* say) and a `_<your draft>_` italic-marker placeholder for the
user's own draft. Nothing in this file is auto-populated — the agent
does not invent the user's answers. See `../DECISIONS.md` for the
no-fabrication rule.

## How to use this file

1. **Read `../rag-app/README.md` end-to-end first.** Every rubric below
   cites a section of that README by heading name (e.g. "Stack choices",
   "Failure modes worth designing around", "Refusal threshold row"). A
   strong answer grounds in the README's documented decisions rather
   than re-arguing them from scratch — if your draft contradicts the
   README, either you've found a real weakness worth patching upstream
   or you should re-read the section before answering.
2. **Draft one answer at a time.** Replace each `_<your draft>_`
   placeholder with your own prose. Aim for 90–180 spoken seconds per
   answer (roughly 200–400 words written out); longer than that and the
   interviewer will interrupt, shorter and the answer will read as
   under-prepared on a question they expected you to have a view on.
3. **The rubric is a checklist, not a script.** It lists the moves a
   credible answer makes — name the trade-off, point at the section,
   defend the choice — without dictating phrasing or stance. You are
   allowed to disagree with the README's own call as long as the
   disagreement is reasoned.
4. **Delete the rubric before any live use.** Rubrics are study aids,
   not talking points. Pasting a rubric bullet into a live answer reads
   as recited; recite the *idea*, not the rubric's framing.
5. **Cross-link discipline.** Several rubrics name sibling builds
   (`../tool-use-agent/`, `../evals-harness/`) or the Cursor teardown
   (`../teardown-prd/cursor-teardown.md`); use those cross-links when
   they strengthen an answer — they prove the rag-app is part of a
   *kit* rather than a one-off.
6. **The placeholder grammar is `_<your draft>_`** matching the rest of
   `../templates/` — so one regex (`_<.*>_`) finds every unfilled slot
   across all portfolio scaffolds.

---

## Q1. Why BM25 as the v1 retriever instead of dense embeddings? Embeddings are the modern default.

**What a strong answer covers.** Reframes from "what's modern" to
"what's the right *first* move." A credible answer cites the README's
Stack choices "Retrieval" row and Design-tradeoffs section: BM25 has
zero model download, zero extra dependencies, zero embedding cost per
query, and is competitive at this corpus size (tens of chunks). Dense
embeddings would add a second moving part (model, dimensionality,
similarity metric) before there's an eval set that could tell whether
the move helped. The answer also names what *would* trigger swapping
in dense retrieval — semantically paraphrased queries that BM25 keeps
missing on a labeled eval set, or recall plateauing — and signals that
dense is intended to land as a *reranker on top of BM25's top-N*, not
as a replacement (per the "Hybrid retrieval" roadmap item and the
"No dense retriever yet" out-of-scope note). The honest concession:
BM25 is a *deliberate* first move, not a permanent stance; the
question of whether it stays is an evals question, not a taste
question. Bonus: cite the `evals-harness/` build as the artifact that
would tell you when to make the switch.

**Your draft:** _<your draft answer here — name BM25's zero-setup property, the corpus-size context, the trigger for adding dense as a reranker, and the evals-harness role in the decision>_

---

## Q2. When would you add a cross-encoder reranker, and how would you measure whether it earned its keep?

**What a strong answer covers.** Names the trigger condition concretely
rather than waving at "quality lift": a reranker earns its keep when
the eval set surfaces a recall-precision gap — top-k contains the
right chunk but it's not in the top-1 or top-2, so the answer either
cites the wrong span or refuses. The answer walks the measurement
pipeline: label a small set of (question, gold-chunk-id) pairs,
measure MRR@k or Recall@k for BM25 alone, add the reranker over the
BM25 top-N (N somewhere between 20 and 50), measure again, and ship
only if the lift exceeds the added per-query latency + cost budget.
The strongest version names *what would block the ship even if the
metric moved*: a reranker that doubles p95 latency to gain 3 points
on MRR is the wrong trade on an interactive demo; a 30% MRR jump for
80ms is obviously worth it. Cite the README's "BM25 vs. dense
embeddings as the v1 retriever" tradeoff and the Productization-
questions "cost ceiling per query" anchor. Bonus: cross-reference
`../evals-harness/` as the artifact that would mechanically run this
measurement and produce the decision-shaped output.

**Your draft:** _<your draft answer here — name the MRR/Recall@k measurement, the latency-cost block conditions, and the evals-harness handoff>_

---

## Q3. Defend the abstention bar. When does the system refuse, and how was the threshold set?

**What a strong answer covers.** Names the mechanism precisely: a BM25
top-score floor (default 1.5, `--min-score` override) that
short-circuits the live model call and emits the canonical refusal
sentence with `reason: low_retrieval_score`. A strong answer cites
the "Refusal threshold" row of Stack choices and the empirical
heuristic the README admits (in-corpus queries top ≥ ~3, out-of-corpus
< 0.2). The answer also names what the threshold is *not*: it is not
a model-confidence number, it is a retrieval-score floor, which means
it catches "the corpus doesn't contain anything relevant" but not
"the corpus contains relevant text and the model still hallucinates"
— that second class is what the citation verifier in `verify.py`
catches downstream. The honest concession: the README itself flags
that the threshold is a deliberate v1 floor and will be retuned
against a labeled eval set; admitting the threshold is a placeholder
is *more* credible than defending 1.5 as a magic number. Bonus: name
the "abstention bar" as the productization question the README
explicitly lists ("What's the abstention bar?" under Productization
questions) — the threshold is the v1 mechanical answer to a question
the PM still owns.

**Your draft:** _<your draft answer here — name the BM25 floor mechanism, the empirical separation, what it does NOT catch, and the eval-set retune plan>_

---

## Q4. How would you measure groundedness continuously in production, not just at ship?

**What a strong answer covers.** Walks the measurement pipeline:
every live `ask` emits a `--json` trace record carrying
`schema_version`, `record_id`, `corpus_fingerprint`, the retrieved
spans, the answer, and the `verification` block listing which
citations resolved against the retrieved chunks. In production those
records flow into the evals-harness rubric set, where the
groundedness rubric reads each record and computes the
% of claims with resolvable citations. A strong answer names the
*continuous* part of the question: groundedness is not a ship-time
gate, it is a rolling-window metric that surfaces when a corpus
update or a model swap regresses the rate. Cite the "Groundedness
rate" Success-metrics bullet and the `trace.py` schema that the
README's Stack-choices table pins. The honest move is to name what
the metric does *not* catch: a claim that's grounded in retrieved
text but the retrieved text is itself wrong (stale corpus, adversarial
chunk), which is the failure mode that needs a separate rubric on
the source side, not the answer side. Bonus: cross-reference
`../evals-harness/` as the artifact that does this measurement
mechanically, and the cursor-teardown's §4 framework-vs-targets
posture as the precedent for distinguishing methodology from
product target.

**Your draft:** _<your draft answer here — name the trace-record pipeline, the rolling-window framing, what groundedness does NOT catch, and the evals-harness pointer>_

---

## Q5. Who owns corpus ownership — staleness, updates, curation? This is a PM question, not an engineering one.

**What a strong answer covers.** Treats corpus ownership as a
product-policy question with three distinct sub-questions: (1) who
decides what's in-scope for the corpus (the product PM, scoped by
user-facing topic taxonomy), (2) who maintains freshness (the team
owning the source-of-truth documents, with a stale-by-default policy
unless they re-ingest), (3) who triages user complaints when the
answer is wrong because the corpus was wrong (the on-call rotation,
escalating to the PM if the same gap surfaces repeatedly). A strong
answer cites the README's "Stale corpus" failure mode under "Failure
modes worth designing around" and proposes the README's own
mitigation (`last_indexed_at` surfaced in citations, freshness signal
in ranking) as the *mechanical* part of an ownership policy — the
human policy is "someone is paged when freshness signal degrades."
Bonus: name the Corpus-v2 deferred decision (the README is explicit
that Corpus v1 is the repo's own markdown, deliberately small and
attributable; v2 would broaden to public AI-PM docs and the choice
of *which* docs is a product call). Honest concession: the README's
own posture is single-owner-implied; a real product needs a named
DRI for each axis.

**Your draft:** _<your draft answer here — name the three sub-questions, the README's stale-corpus mitigation, and the v1→v2 deferred selection as the PM call>_

---

## Q6. What's the cost ceiling per query before the product economics break, and how would you enforce it?

**What a strong answer covers.** Names cost-per-query as a first-class
metric (it's literally a Success-metrics bullet in the README) and
walks the levers: top-k controls input tokens linearly, output token
cap controls answer length, model choice swings the per-token rate
by 5–10x, and the abstention bar prevents the worst case (a refusal
emits zero model tokens). The "ceiling" is a product decision, not
a technical one — for a free-tier consumer demo, the ceiling might
be cents per query; for an enterprise vertical, dollars. A strong
answer names the *enforcement* layer: the README's existing
`--max-tokens` flag on `ask` is the per-call output-budget knob, the
default model `claude-haiku-4-5-20251001` is the per-token-rate knob,
and the abstention floor at `--min-score` is the prevent-spend-on-
out-of-corpus knob. The strongest version also names what the README
*doesn't* yet enforce: a hard ceiling per user-session, which is a
product-rate-limit feature that lives at the surrounding service
layer, not in the rag-app itself. Cite the "Cost runaway" failure
mode and the Productization Q5 ("cost ceiling before economics
break"). Bonus: cross-reference the cursor-teardown's §4.4.1
Business-tier NRR pairing for the precedent of pairing a
product-level cost metric with the right cohort split.

**Your draft:** _<your draft answer here — name the three levers, the product-decision-not-technical framing, the existing flags as enforcement, and the missing per-session ceiling>_

---

## Q7. Why single-shot QA only? Multi-turn would obviously be more useful.

**What a strong answer covers.** Names the deliberate-scope-cut framing
directly: the README's "What's intentionally out of scope here"
section calls out multi-turn explicitly as deferred for *evaluation
surface cleanliness*, not because it's hard to implement. A
multi-turn conversation entangles three signals — retrieval quality,
groundedness, *and* turn-coherence — which would make every eval
rubric either trickier to score or genuinely under-determined ("did
the model lose the thread or did the corpus not support the
follow-up?"). Single-shot QA is the *baseline* that produces
trustworthy eval signal; multi-turn is a follow-on product question.
A strong answer also names what multi-turn would actually need —
conversation-history-as-prompt management, per-turn retrieval (re-
retrieve every turn vs. accumulate context, both valid), an
abstention bar that knows about prior turns, and a citation verifier
that handles the "claim from turn 3 that depends on chunk retrieved
in turn 1" coreference problem. The honest concession: deferring
multi-turn does mean the demo can't answer a "yes, but…" follow-up,
which is a real UX shortfall — the answer should own that rather
than wave it away as obviously the right cut. Bonus: cite the
"Single-shot QA vs. multi-turn" line in Design-tradeoffs as the
README's own framing.

**Your draft:** _<your draft answer here — name the eval-surface-cleanliness reason, the four extensions multi-turn would need, and the UX shortfall concession>_

---

## Q8. Walk me through the failure modes. Pick the highest-priority one and defend the mitigation.

**What a strong answer covers.** Inventories the four named failure
modes from the "Failure modes worth designing around" section (stale
corpus, prompt-injection inside corpus chunks, top-k miss, cost
runaway) and *prioritizes* them rather than treating the list as
flat. A defensible priority order: (1) top-k miss (the model
confabulates with confidence, hurts user trust the most), (2)
prompt-injection inside corpus chunks (a security-shaped risk once
the corpus is user-influenced), (3) stale corpus (signal degradation,
but the user can usually detect it), (4) cost runaway (a product-
economics risk but recoverable with a kill switch). Pick top-k miss
and walk the mitigation: hybrid retrieval (BM25 + dense reranker)
plus the existing `--min-score` abstention floor that fires before
the model is even called. A strong answer also names what the
mitigation does NOT solve: the top-1 chunk being technically correct
but contextually misleading (the right span, wrong frame), which is
the case the citation verifier flags as "resolved" because the
citation is structurally valid, even though the answer reads as
slightly off. The honest concession: the priority order is
arguable; a product whose corpus is user-uploaded would re-order
(2) ahead of (1). Bonus: cite the "Hybrid retrieval" roadmap item as
the named mitigation path.

**Your draft:** _<your draft answer here — name all four modes, defend the priority order, pick top-k-miss and walk the mitigation, and concede the corpus-shape-dependent re-ordering>_

---

## Q9. The citation verifier in `verify.py` reports "resolved" if the (source, span) is in the retrieved set. That's a structural check, not a semantic one. Is that good enough?

**What a strong answer covers.** Treats the question as a real design
limitation rather than performing modesty. The verifier checks that
each `[source#start-end]` citation in the answer matches a retrieved
chunk's (source, start, end), which catches the failure mode "model
cited a chunk that wasn't retrieved" (fabricated citation) but does
NOT catch "model cited the right chunk but the prose claim doesn't
follow from the chunk's text" (cited-but-misrepresented). A strong
answer names that distinction crisply and explains why the v1
verifier is still load-bearing: fabricated citations are an
*objective* failure mode that's cheap to detect mechanically, while
misrepresentation requires a separate semantic-grounding rubric
(NLI-style or LLM-as-judge) that the README defers to the
evals-harness rubric set. The strongest version also names what
shipping *just* the structural check buys: the model is forced to
either cite a real chunk or refuse (no third option), which
collapses the failure surface from "any plausible-sounding hallucination"
down to "misrepresentation of a real retrieved span." Cite the
"Citation verification" row of Stack choices, the `--json verification`
block, and the cursor-teardown's §3 transparency-restored-per-dollar
framing as the same kind of cheap-mechanical-fix-that-isn't-the-whole-
story design pattern. Honest concession: a production system needs
the semantic check too; the v1 structural check is the *floor*, not
the ceiling.

**Your draft:** _<your draft answer here — name the structural-vs-semantic distinction, what the v1 check actually prevents, and the semantic check as a separate evals rubric>_

---

## Q10. If you joined a RAG-product team tomorrow, what's the first thing you'd ship from this design, and what's the first thing you'd cut?

**What a strong answer covers.** Interview is testing whether the
candidate can hold the design provisionally — read the README as a
current-best-guess rather than a permanent position. A strong answer
picks one specific add and one specific cut: ship-first candidates
include (a) the evals-harness rubric pipeline against a real labeled
set (so the abstention threshold can stop being a magic number),
(b) hybrid retrieval (BM25 + dense reranker) once the eval set says
recall is the bottleneck, (c) per-doc `last_indexed_at` surfaced in
citations (the README's own staleness mitigation, never implemented).
Cut-first candidates include (a) the dry-run fallback as a default
mode — useful for CI, but in a production product, an unset API key
should error rather than silently switch behavior, (b) the
repo's-own-markdown corpus, in favor of an attributable public corpus
that exercises the refusal floor on legitimately out-of-corpus prose
(per the cursor-teardown's §10 post-hire pragmatism shape and the
NEXT_WORK item 5 in-flight corpus swap). The strongest version names
the *data on day one* that would update the call: actual
groundedness numbers might surface that hybrid retrieval is over-
engineering, or that the threshold is fine and what's broken is the
chunker. The answer should *not* perform humility ("I'd rebuild
everything") or refuse to commit ("I'd need more data first") —
both read as evasive. Honest move: name the specific ship, the
specific cut, the data that would change either call.

**Your draft:** _<your draft answer here — name one ship, one cut, the data that would justify each, and the post-hire-pragmatism framing>_

---

## Cross-cutting "walk me through your portfolio" question

This question doesn't belong in the per-artifact Q&A bank because it
spans the whole portfolio. It will live in `interview-prep/README.md`
under the "common cross-artifact questions" section (NEXT_WORK item 7
sub-checkbox 5), with a one-paragraph stub here so a reader of *just*
this file knows the question exists and where to find its rubric. If
you are practicing answers cold, expect this question first and the
ten above as follow-ups — the interviewer will use the walk-through
to pick which two or three of the ten to probe in depth. A rag-app-
flavored walk-through naturally pivots into Q1 (BM25-vs-dense as the
first stack-choice signal) or Q8 (failure modes as the first
PM-craft signal), so prep those two with extra care.

---

## Source of truth & cross-links

- The build itself: `../rag-app/` — README is the design contract; the
  `rag_app/` package implements it; `tests/` covers the production
  surface at ~94% line coverage with no network or API key.
- Sibling Q&A banks (NEXT_WORK item 7, sub-checkboxes 1, 3, 4):
  `cursor-teardown.md` (shipped), `tool-use-agent.md` (subsequent
  iteration), `evals-harness.md` (subsequent iteration) — each
  anticipates 8–10 questions on its own artifact.
- Index file (NEXT_WORK item 7, sub-checkbox 5): `README.md` will
  link the four Q&A banks, name the suggested prep order, and carry
  the cross-artifact questions section.
- Related portfolio piece (cross-link for rubrics Q4, Q6): the
  `../evals-harness/` build, which is the mechanical home for the
  groundedness, refusal, and cost rubrics this rag-app produces
  trace records for.
- The no-fabrication rule for the `_<your draft>_` slots:
  `../DECISIONS.md` (search for "no-fabrication"). The agent never
  drafts the user's answers; the slots are the user's to fill.

This file is interview-prep, not a deliverable for any specific
employer. The questions and rubrics anticipate what an AI-PM
interviewer is likely to probe given the rag-app README's actual
content; they are not sourced from any company's interview process
and make no claim to mirror one.
