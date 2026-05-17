# Mock Interview Q&A — Cursor Teardown PRD

A populatable interview-prep file for the Cursor teardown PRD at
`../teardown-prd/cursor-teardown.md`. Ten likely interviewer questions,
each followed by the strong-answer rubric (what a credible answer covers,
not what the user *should* say) and a `_<your draft>_` italic-marker
placeholder for the user's own draft. Nothing in this file is auto-
populated — the agent does not invent the user's answers. See
`../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. **Read the teardown end-to-end first.** Every rubric below cites a
   teardown section by number (e.g. `§2.1`, `§4.2.2`). A strong answer
   grounds in the teardown's own claims rather than re-arguing them
   from scratch — if you find yourself drafting an answer that
   contradicts the teardown, either you've found a real weakness worth
   patching upstream or the rubric is reading a section you should
   re-read before answering.
2. **Draft one answer at a time.** Replace each `_<your draft>_`
   placeholder with your own prose. Aim for 90–180 spoken seconds per
   answer (roughly 200–400 words written out); longer than that and
   the interviewer will interrupt, shorter and the answer will read as
   under-prepared on a question they expected you to have a view on.
3. **The rubric is a checklist, not a script.** It lists the moves a
   credible answer makes — name the trade-off, point at the section,
   defend the cut, etc. — without dictating phrasing or stance. You
   are allowed to disagree with the teardown's own call as long as
   the disagreement is reasoned and you can name what would have to be
   true for the teardown to be wrong.
4. **Delete the rubric before any live use.** Rubrics are study aids,
   not talking points. Pasting a rubric bullet into a live answer
   reads as recited; recite the *idea*, not the rubric's framing.
5. **Cross-link discipline.** Several rubrics name other portfolio
   pieces (`../rag-app/`, `../tool-use-agent/`, `../evals-harness/`)
   that strengthen an answer when referenced. Use those cross-links;
   they're the highest-leverage interview move this portfolio shape
   permits, because they prove the teardown is part of a *kit* rather
   than a one-off artifact.
6. **The placeholder grammar is `_<your draft>_`** matching the rest
   of `../templates/` — so one regex (`_<.*>_`) finds every unfilled
   slot across all portfolio scaffolds.

---

## Q1. Why Cursor instead of Copilot, Windsurf, or Cline?

**What a strong answer covers.** The interviewer is reading for scope
discipline, not Cursor advocacy. A credible answer names the criteria
that drove the pick (live AI product the candidate uses daily,
publicly observable surface, PM-design choices that are *contested*
rather than commoditized) and applies them honestly: Copilot's
PM-design surface is older and more commoditized; Windsurf and Cline
are reasonable picks but have a narrower public-surface footprint to
read from. The answer also names the cost of the choice — Cursor's
release cadence means weekly drift on surface details, which the
teardown's masthead acknowledges and the per-claim citation discipline
in §§1–2 mitigates. Bonus: explicitly cites the teardown's scope
decision paragraph (top of `cursor-teardown.md`) rather than re-
arguing it from memory.

**Your draft:** _<your draft answer here — 90–180 seconds spoken, cite §scope decision and the source posture from the masthead>_

---

## Q2. You scoped to the chat / inline-edit / agent triad. What's the most important surface you cut, and why?

**What a strong answer covers.** Names the cuts explicitly (Tab
autocomplete and the Cursor CLI — both in §5.5 and §5.4) and defends
each one on a different axis: Tab is cut because the PM craft on
single-line completions (latency, hit-rate, cancellation UX) is a
*different genre* from assistive-decision UX, not because it doesn't
matter; the CLI is cut because folding it into a desktop teardown
would dilute the scope without commensurate gain. A strong answer
also names *both* sub-section-level cuts (the §1 pricing-tier cut and
the §2 free-tier-quota cut) as separate from the document-level §5
cuts, because confusing the two levels is the easiest way to
under-read the teardown's narrowing discipline. The honest move is to
admit this is a defensible cut, not the only one — a teardown of Tab
or the CLI would be a legitimate document on its own, and a competing
candidate could defend a different scope choice and not be wrong.

**Your draft:** _<your draft answer here — name §5.4, §5.5, the §1 pricing cut, and the §2 free-tier cut; defend each on its own axis>_

---

## Q3. What's your #1 ship-next pick from §3, and why that one over the other two?

**What a strong answer covers.** Picks one of the three proposals
(A: routing transparency, B: index-freshness indicator, C: agent
stop-criteria UI) and defends the pick on a *named* dimension — user-
trust restored per dollar of engineering, ratio of fixable-symptom to
craft-investment, or alignment with the autonomy-ramp framing from
§1.3 — not on aesthetic preference. The strongest answer also names
*why the other two lose on that same dimension*, so the interviewer
sees the candidate ranked them rather than picked one. Bonus: the
answer explicitly cross-references §4 — which §4 metric the pick is
paired with, and why that pairing is the cleanest read on whether
the proposal worked (Proposal A → §4.1.2, Proposal B → §4.2.2,
Proposal C → §4.2.1). Caveat the answer should *not* fall into: do
not claim a hard ranking based on user impact estimates the public
surface cannot pin down. Either pick a defensible heuristic
(reversibility, user-visible asymmetry of harm) or admit the ranking
is judgment-shaped and own the call.

**Your draft:** _<your draft answer here — name the pick, the dimension, why the other two lose on it, and the §4 metric pairing>_

---

## Q4. How would you instrument index-freshness coverage in production, end-to-end?

**What a strong answer covers.** Walks the interviewer through the
measurement pipeline that produces §4.2.2's metric: where the
event is emitted (at request time on every `@Codebase` and agent
turn, carrying the index-lag-in-seconds and the working-tree-rev),
what the aggregation pipeline does (per-turn → rolling-7-day, with
the repo-size cohort split the §4.2.2 metric definition names),
and what the dashboard surfaces (the *trend* on the rolled-up
number, not the absolute level, because the interesting signal is
whether Proposal B's chip changes behavior post-launch). A strong
answer also names the *failure mode of the instrumentation itself* —
clock skew between client and indexer service inflating the lag,
the repo-size cohort splitter mis-bucketing monorepos with submodule
checkouts — and proposes the smallest defensive check (a sanity
clamp on negative lag values, a unit-test on the cohort splitter)
rather than waving past it. Bonus: cross-references the
`evals-harness/` build as the structurally similar precedent for
per-record schema + aggregation against a fixture set.

**Your draft:** _<your draft answer here — name event shape, aggregation, dashboard surface, two named failure modes, and the evals-harness analogy>_

---

## Q5. Defend stop-aggressive as the default. Power users will read it as nagging.

**What a strong answer covers.** Reframes the question from "is
stop-aggressive friction-free" (no) to "is the friction profile
asymmetric in the right direction" (yes, per §2.3 and §3.3). A
strong answer names the asymmetry concretely: a wrong-direction
agent edit ten steps deep costs the user Cancel + inspect + revert +
the time to rebuild trust in the agent for the next session, while a
confirmation prompt costs one click. Friction amortizes; bad overrun
ends the day. The answer also points at the per-task opt-in toggle
from §3.3 as the escape hatch for power users who knowingly want
stop-permissive — the design isn't "stop-aggressive only," it's
"stop-aggressive default with one-click opt-in scoped to the current
task." Honest concession to leave on the table: the toggle has its
own failure mode (users forget they enabled it), which §3.3
mitigates by scoping it to the current task only. Naming the
mitigation makes the answer feel designed rather than evangelical.

**Your draft:** _<your draft answer here — name the asymmetry, point at the per-task opt-in, concede the toggle-forgetfulness failure mode>_

---

## Q6. What part of this teardown is your weakest claim?

**What a strong answer covers.** The interviewer is reading for
intellectual honesty, not a confession. A credible answer names a
specific claim — not a vague self-deprecation — and explains why it's
the weakest: candidates include (a) §1.3's "sequencing autonomy" call,
which leans on Anysphere's stated philosophy and could read as
post-hoc rationalization if the actual launch order had different
internal drivers the public surface can't see; (b) §2.1's framing of
Auto-mode opacity as a *fixable UX gap* rather than a deliberate
trade for routing strategy secrecy, which would change the proposed
fix; (c) §4.2.1's stop-precision metric, which depends on labeling
ground-truth that's expensive to maintain at the scale §6.4
implies. The strongest version of the answer also names what would
have to be true for the claim to *be* wrong (so the interviewer sees
the candidate can imagine being argued out of it) and what cheap test
would settle it. What the answer should *not* do: confess to
something the teardown's no-fabrication posture already protects
against (no invented metrics, no fabricated user counts), because
that's not a weakness, it's a discipline.

**Your draft:** _<your draft answer here — name one specific claim, why it's weakest, and what would settle it>_

---

## Q7. A Cursor PM disagrees with §2.1's Auto-mode opacity framing. How do you change their mind?

**What a strong answer covers.** The honest first move is *don't try
to change their mind on the framing itself* — start by asking what
they think the user-side cost of opacity is, because a Cursor PM has
internal data the teardown cannot read. The answer then re-anchors
the argument on §2.1's documented observable behavior (no per-message
model label, no per-thread routing summary, no surfaced fallback
signal), all of which are reproducible on 2026-05-16 and don't
require either side to defer to private data. The point of the
argument isn't to win the framing — it's to agree on the *symptom*
(users can't reproduce, learn, or triage Auto-mode turns) and then
let the Cursor PM decide whether the §3.1 proposal's reveal-after-
the-fact label is the right fix or whether a different fix
(e.g. exposing the routing rationale only in an opt-in advanced
view) better fits their cost model. Honest concession: a strong
candidate signals they'd update §2.1's framing in the teardown's
next revision if the conversation surfaced internal data the public
surface couldn't see. Static teardowns are wrong forever; revisable
ones get less wrong.

**Your draft:** _<your draft answer here — name the ask-first move, the agreed-symptom pivot, and the willingness to revise the doc>_

---

## Q8. Your §4 has no targets or baselines. Why not?

**What a strong answer covers.** Names the call directly: "no targets
or baselines" is a deliberate posture, not an omission. The teardown
is written by an external author with no access to Anysphere's
internal telemetry, so any target number on the page would either be
fabricated or quoted from a public source that doesn't exist. The
framework is the artifact; the dashboard would be Anysphere's to
define on internal data. A strong answer also names what this *gives
up* — a teardown with targets reads as more decisive and lets the
interviewer test whether the candidate can defend a specific number —
and what it *preserves*: no claim in the document fails an honesty
audit, which is load-bearing for a portfolio piece whose purpose is to
demonstrate AI-PM craft, not to predict Cursor's internal numbers.
Bonus: name the §6 validation methods as the place where target-
shaped numbers *do* appear (§6.1's "≥60% of internal subjects" and
§6.4's "≥90% agreement with ground-truth") because those are
*methodology thresholds*, not *product targets*, and the distinction
is the same one the §4 framework vs. §6 methodology split makes.

**Your draft:** _<your draft answer here — name the deliberate-posture framing, the trade given up, and the §6 threshold contrast>_

---

## Q9. §6.5 says pricing-page A/B is explicitly not a validation method. Walk me through why.

**What a strong answer covers.** The point of §6.5 is *naming the
non-method explicitly*, not just declining to use it. A pricing-page
A/B can read whether users will pay more for the same product, but
every proposal in §3 is a user-trust UX intervention, not a price-
discovery one. Running a pricing experiment on top of, say, a flag-
gated routing-transparency rollout would conflate two signals
(willingness to pay with willingness to trust) and any lift could
come from either or both. A strong answer names where the
pricing-signal *does* belong (§4.4.1 Business-tier NRR, in a separate
cycle not entangled with §3) and why naming the non-method is part
of the document's craft signal — the discipline mirrors the §1 and
§2 cut paragraphs that name what was deliberately not done. Honest
concession: there's nothing wrong with pricing experiments as a
class; they're the wrong tool for *this* set of proposals, on *this*
surface, in *this* document.

**Your draft:** _<your draft answer here — name the conflation, point at §4.4.1, and frame the non-method discipline as a craft signal>_

---

## Q10. If you joined Anysphere as a PM tomorrow, what's the first thing you'd kill from this teardown?

**What a strong answer covers.** The interviewer is testing whether
the candidate can hold the teardown's views provisionally — read the
artifact as a current-best-guess rather than a permanent position.
A strong answer picks a specific section (likely candidates: §1.3
sequencing-autonomy, §2.3 stop-criteria framing, or one of the §3
proposals) and explains what internal data on day one at Anysphere
would update the call: e.g. seeing actual stop-precision numbers
might surface that stop-permissive *is* the right default for the
current user mix; seeing routing-cost data might surface that §2.1's
"fixable UX gap" framing is missing a load-bearing cost-secrecy
constraint. The answer should *not* perform humility ("oh I'd kill
the whole thing"), and should *not* refuse to commit ("I wouldn't
change anything until I had more data") — both read as evasive. The
honest move is "here's the specific thing I'd kill, here's the
specific data that would justify killing it, and here's what I'd
replace it with." Bonus: name the §1 and §2 cut paragraphs as the
*existing* precedent for killing sections with a one-paragraph
rationale, so the candidate signals they understand teardown
revision is a documented discipline, not an admission of failure.

**Your draft:** _<your draft answer here — name the section, the data that would justify killing it, and the replacement; cite the §1/§2 cut precedent for how to do it>_

---

## Cross-cutting "walk me through your portfolio" question

This question doesn't belong in the per-artifact Q&A bank because it
spans the whole portfolio. It will live in `interview-prep/README.md`
under the "common cross-artifact questions" section (NEXT_WORK item 7
sub-checkbox 5), with a one-paragraph stub here so a reader of *just*
this file knows the question exists and where to find its rubric. If
you are practicing answers cold, expect this question first and the
ten above as follow-ups — the interviewer will use the walk-through
to pick which two or three of the ten to probe in depth.

---

## Source of truth & cross-links

- The teardown itself: `../teardown-prd/cursor-teardown.md`
  (interview-ready as of 2026-05-16, per its masthead).
- Other portfolio Q&A banks (NEXT_WORK item 7, sub-checkboxes 2–4):
  `rag-app.md`, `tool-use-agent.md`, `evals-harness.md` —
  each anticipates 8–10 questions on its own artifact and ships
  in subsequent iterations of the same item.
- Index file (NEXT_WORK item 7, sub-checkbox 5):
  `README.md` will link the four Q&A banks, name the suggested
  prep order, and carry the cross-artifact questions section.
- The no-fabrication rule for the `_<your draft>_` slots:
  `../DECISIONS.md` (search for "no-fabrication"). The agent never
  drafts the user's answers; the slots are the user's to fill.

This file is interview-prep, not a deliverable for Cursor or Anysphere.
The questions and rubrics anticipate what an AI-PM interviewer is
likely to probe given the teardown's actual content; they are not
sourced from Cursor or Anysphere staff and make no claim to mirror
any specific company's interview process.
