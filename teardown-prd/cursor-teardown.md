# Cursor — Teardown PRD

**Status:** Outline slice (iteration 1 of a multi-iteration draft). The
six canonical sections below carry intent paragraphs only; per-section
prose lands in subsequent iterations in the order locked in
DECISIONS.md.

**Product under teardown:** Cursor — the AI-native code editor (VS
Code fork) by Anysphere. https://cursor.com

**Author POV:** Written as an AI PM evaluating Cursor as an interview
leave-behind. Not affiliated with Anysphere; not based on any internal
knowledge. All claims about Cursor in this document are grounded in
publicly observable product surface (UI, docs, changelog, public
statements) as of the observation snapshot below.

**Observation snapshot:** 2026-05-16. Cursor's release cadence is fast
enough that surface details drift week-to-week (model menu, agent
modes, pricing tiers); every numeric or surface-specific claim in the
drafted sections cites either a changelog version, a docs URL with the
date observed, or a "behavior reproducible on 2026-05-16" note. If a
fact cannot be pinned to a public source, the draft writes a
placeholder naming where the reader would look — never an invented
number.

---

## Scope decision

The teardown focuses on the **AI authoring triad: chat (Cmd+L), inline
edit (Cmd+K), and the agent surface (Composer + Background Agent /
Cursor for Web)**. These three surfaces share a model-routing layer, a
context-assembly layer, and an edit-application layer, so a teardown
that covers all three can compare PM choices across them rather than
treat each in isolation.

Treated as supporting context but **not deep-dove**: Tab autocomplete
(a near-commodity surface across Cursor, Copilot, Windsurf, Zed —
worth one paragraph for comparison, not a full section), and the
Rules / `.cursorrules` system (relevant only insofar as it shapes
model behavior in the three triad surfaces).

**Out of scope** (named explicitly so the draft cannot drift into
them): enterprise admin / SSO / Business-tier policy controls,
provider economics and model-cost pass-through, VS Code shell parity
and extension marketplace behavior, the Cursor CLI / cursor-agent
binary as a separate product surface. Each of these is a legitimate
teardown subject on its own; bundling them into this document would
dilute the AI-PM framing.

**Why this slice:** the chat / inline / agent triad is where Cursor's
PM choices are most visible, most contested by users in public forums,
and most relevant to the AI PM interview narrative this teardown
supports. The autocomplete-only slice would compete head-to-head with
Copilot on a single dimension; the full-product slice would force the
draft to spread thin across surfaces the user does not exercise
daily.

**User redirect:** the scope is not user-pre-gated (the candidate
pick was), so a user redirect to a narrower or different surface lands
as a one-paragraph DECISIONS amendment, not a full supersession. See
the "How I'd validate" section for the cheapest checks the user can
run before committing to the scope as drafted.

---

## 1. What's working

**Section intent:** identify the PM choices Cursor has made well —
ones a competing product would do well to copy, and ones the AI PM
author would defend in a review. Avoid feature-listing; each
sub-point is a *PM decision* with the observable behavior that
indicates the decision was right.

**Candidate sub-areas the draft will narrow to ~3:**

- **Edit-application UX.** Cursor's inline-diff-then-accept (vs.
  "model runs the edit and you discover what changed") materially
  lowers the trust bar for delegating multi-line edits to a model.
  The PM tension: review friction vs. autonomy. Cursor's default is
  visibly conservative, and the draft will argue this is correct for
  the current model-reliability regime.
- **Context-as-first-class-citizen.** The `@File`, `@Folder`,
  `@Codebase`, `@Docs`, `@Web`, `@Git` mention system makes
  context-construction an explicit user action with visible
  scope. Compared with implicit-context products that silently pull
  the open file or "the whole repo," the explicitness pays for itself
  in fewer surprise model behaviors.
- **The pricing tier story.** Free tier with a real model menu (not
  a degraded teaser), Pro at a defensible price point, and the
  business / enterprise tiers actually selling features developers
  use. The draft will frame this against Copilot's tier shape.
- **The Background Agent introduction.** Sequencing — bringing
  Background Agent in after the interactive Composer surface
  matured — let the user mental model build before autonomy was
  expanded.

**Evidence sources for this section:** Cursor docs (cursor.com/docs),
public changelog, pricing page snapshots, observable behavior on
2026-05-16, and named comparisons with Copilot's equivalent surfaces
where the contrast is publicly verifiable.

---

## 2. What's broken

**Section intent:** name the PM failures honestly. A teardown that
only celebrates is not an interview leave-behind — it's a marketing
deck. Each sub-point pairs an observable symptom with the PM choice
the symptom implies, and the draft commits to specific reproduction
steps a reviewer could verify.

**Candidate sub-areas the draft will narrow to ~3:**

- **Auto-mode router opacity.** When the model menu is set to "Auto,"
  the user is not told which underlying model handled a given turn,
  what triggered a fallback, or how latency and quality tracked.
  The PM choice — hide the routing — optimizes for a clean surface
  but breaks the user's ability to learn the product's reliability
  envelope. The draft will frame this as a fixable UX gap, not a
  product-strategy mistake.
- **Indexer staleness signals.** On large monorepos, the project
  indexer can serve stale chunks after recent edits. The user
  observes this as "Cursor doesn't seem to know about the file I
  just changed" — but the product offers no first-class
  "index-freshness indicator" the user can read at-a-glance. The
  draft will compare with the way IDE search products surface
  index state.
- **Agent stop conditions and overrun.** Composer and Background
  Agent occasionally continue past the point the user wanted them
  to stop, particularly when the model interprets an ambiguous
  acknowledgment as "continue." The PM tension: aggressive
  autonomy vs. user control. The draft will pin specific examples
  the user can reproduce and propose a stop-criteria UI that is
  not just "click cancel harder."
- **Free-tier quota surprises.** The free tier's monthly limits are
  documented but not displayed prominently enough during normal
  use; the user discovers them by being interrupted mid-edit.

**Evidence sources for this section:** reproducible behaviors on
2026-05-16, public Discord / forum posts that document the same
pattern (cited only as "users report" with link, never quoted as if
authoritative), Cursor's own changelog acknowledging fixes-in-flight
where applicable.

---

## 3. What to ship next

**Section intent:** three concrete proposals, one per top-ranked
broken sub-area from section 2. Each proposal is shaped as a PM would
write a one-page recommendation: problem statement, user / business
impact, proposed shape, scope boundaries, what could go wrong, and
how to know whether it worked.

**Initial shape (subject to draft-iteration refinement):**

- **Proposal A — Routing transparency for Auto mode.** A
  per-message "served by Sonnet 4.5 via Auto" affordance + a
  per-thread routing summary, opt-in advanced settings to lock
  the router to a specific model. Costs little; pays for itself in
  user-learning and in support-issue triage.
- **Proposal B — Index-freshness indicator.** A persistent UI
  element showing "indexed N seconds ago, M files pending"
  with a one-click re-index. Borrows the pattern from IDE search
  panes; trades a small amount of chrome for a large reduction in
  "the model doesn't see my changes" frustration.
- **Proposal C — Agent stop-criteria UI.** Replace the implicit
  stop-on-acknowledgment behavior with an explicit "I'll stop
  when X" plan the user confirms before the agent runs, plus a
  prominent pause-and-amend control during execution. The harder
  product call here is the default: stop-aggressive or
  stop-permissive. The draft will recommend stop-aggressive and
  argue why.

**Evidence sources for this section:** the proposals are PM
recommendations, not claims of fact, so the source posture is "the
draft makes the case; the reader is free to disagree." No external
citations required, but the proposals must not assume internal
information (e.g. "Cursor's index already supports incremental
refresh" — would have to be sourced or rewritten as conjecture).

---

## 4. Proposed metrics

**Section intent:** a metric framework the Cursor PM team could
adopt to evaluate the proposals in section 3 and to monitor the
broader triad surface. The framework is the PM artifact, not the
specific numbers — naming any specific number Cursor should hit
would either fabricate it or quote it without attribution.

**Coverage map (the draft will fill in ~6 metrics across the four
quadrants):**

- **Leading × adoption:** e.g. share of sessions using `@`-mentions,
  share of edits accepted vs. rejected, share of Auto-mode messages
  vs. pinned-model messages.
- **Leading × quality:** e.g. agent stop-precision (did the agent
  stop where the user wanted), index-freshness coverage (share of
  edits with index lag < N seconds).
- **Lagging × adoption:** e.g. paid-tier conversion from free,
  weekly-active developers, retention by tenure cohort.
- **Lagging × business:** e.g. revenue per developer, gross margin
  given model-cost mix, net dollar retention on Business tier.

**Evidence sources for this section:** the metric *categories* are
standard PM craft and need no citation; the *applicability* to
Cursor specifically is grounded in publicly observable product
behavior — no fabricated baselines, no invented benchmarks.

---

## 5. Out of scope

**Section intent:** name what this teardown is deliberately not
covering, with one-line rationale per item, so a reader cannot fault
the document for omissions that were intentional. Mirrors the
DECISIONS.md "explicit out-of-scope" pattern used in the build slices.

**The five out-of-scope categories (carried from this outline's
"Scope decision"), each will get a one-paragraph treatment in the
draft:** enterprise admin and policy controls; provider economics
and per-model unit costs; VS Code shell parity and extension
marketplace; Cursor CLI / cursor-agent as a separate product; Tab
autocomplete as a deep-dive subject. Plus two added at draft time:
**competitive landscape ranking** (a teardown is not a market map),
and **founder / company analysis** (a teardown is product-shaped,
not company-shaped).

---

## 6. How I'd validate

**Section intent:** the methodology section a PM would attach to a
proposal of this size — how the recommendations in section 3 would
be vetted before committing engineering resources to them. The point
is to show the author thinks about the gap between "an opinion in a
PRD" and "a shipped feature that worked."

**Methods the draft will name and justify (~5):**

- **Replay user sessions** with internal employees in the auto-mode
  / agent-overrun scenarios from section 2; measure how often the
  observed failure mode reproduces and whether the proposed fix
  shortens recovery time.
- **Lightweight quant from product analytics:** for the routing
  transparency proposal, deploy the new affordance behind a flag to
  ~5% of users and read activation, hover-rate, and any drop in
  "which model is this" support tickets.
- **Targeted user research:** 10–15 conversations with developers
  who recently churned off Cursor or who use Cursor heavily on
  monorepos, scoped to the index-freshness symptom specifically.
- **Eval-harness for agent stop-criteria:** offline test set of
  ambiguous-acknowledgment turns scored by humans for
  stop-correctness, used as a regression bar before shipping any
  stop-criteria UI change. This is the most directly PM-craft-y
  method on the list and ties back to this repo's evals-harness
  build as a worked example.
- **Pricing-page A/B is explicitly out** as a validation method —
  the recommendations in section 3 are about user-trust UX, not
  monetization, and pricing experiments would conflate the signal.

**Evidence sources for this section:** standard PM craft; the
section is methodology, not fact-claim, so it stands on argument
quality alone.

---

## Sources & observation snapshot (drafted alongside the body)

Every quantitative or surface-specific claim in the drafted sections
above will cite from one of these source categories, with the
specific URL or version recorded inline at draft time:

- Cursor docs (`cursor.com/docs`) — accessed 2026-05-16.
- Cursor changelog (`cursor.com/changelog`) — specific version
  numbers cited for any behavior tied to a release.
- Cursor pricing page (`cursor.com/pricing`) — snapshot date pinned.
- Public statements from Anysphere (blog posts, founder interviews,
  public conference talks) — cited by title + date, never
  paraphrased as if internal.
- Author's reproduction notes — labeled "observed on 2026-05-16,
  Cursor [version], [OS], [tier]" so a reader can recreate the
  conditions.
- User-community reports (Discord, X, Hacker News) — cited only
  as patterns ("multiple users report X") with a representative
  link, never quoted as authoritative on Cursor internals.

No internal Cursor information, no fabricated metrics, no invented
user counts or revenue numbers, no roadmap claims that go beyond
publicly stated direction. This is the no-fabrication guardrail from
OBJECTIVE.md restated at the artifact level.
