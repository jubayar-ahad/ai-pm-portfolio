# Cursor — Teardown PRD

**Status:** §1 "What's working" and §2 "What's broken" drafted; §§3–6
remain in outline / intent-paragraph state. Per-section prose lands
in subsequent iterations in the order locked in DECISIONS.md.

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

Three sub-sections follow, narrowed from the outline's four candidate
sub-areas. The cut — pricing-tier shape — is named at the end of this
section with a one-paragraph rationale.

### 1.1 Edit-application UX: inline-diff-then-accept

**The PM decision.** Route every model-initiated edit — Cmd+K inline
edits and Composer multi-file changes alike — through an in-editor
diff surface with explicit per-hunk or all-at-once acceptance, rather
than letting the model write the file and surface the change after the
fact via `git diff`. The model never reaches the working tree without
a human gesture.

**Observable behavior** (reproducible on 2026-05-16). Trigger an
inline edit on a function with Cmd+K: the proposed change renders as
a red/green diff in place before any byte hits disk; Tab (or the
Accept button) commits, Esc discards. Composer-driven multi-file edits
open a per-file diff list with the same accept/reject affordances at
the file and hunk level. The user is never asked to flip a one-time
"trust the model with write access" setting; the trust grant is
per-edit, and the visual review surface is the default, not an
opt-in.

**Why this is the right PM call.** The current model-reliability
regime makes delegated edits useful — the model can refactor across a
function in one shot, rename across files, port a code block to a
sibling language — but not reliable enough to trust unsupervised on
the working tree. Some non-trivial fraction of multi-line edits are
subtly wrong in a way `git diff` would catch in five seconds but a
mid-refactor user might miss for hours. Inline-diff is the lightest
review surface that still catches the wrong-direction cases before
they land. The friction cost — two clicks per accept — is dominated
by the cost of one accidental wrong-file edit ten layers deep in a
refactor.

**Tension worth naming:** review friction vs. autonomy. The default
is visibly conservative; power users who want fewer prompts chain
edits through Composer (which still diffs, but bundles the review)
rather than disabling the gate. The PM trade is to keep the gate
on-by-default and route autonomy seekers to a different surface, not
to weaken the safety property of the default surface.

*(Sources: observable behavior on 2026-05-16, macOS / Pro tier;
Cursor docs on inline edit and Composer, cursor.com/docs, accessed
2026-05-16.)*

### 1.2 Context as a first-class citizen: the `@` mention system

**The PM decision.** Context attached to a chat or edit prompt is
constructed by the user via an explicit `@`-mention typeahead palette
rather than silently inferred from the open buffer, the cursor
position, or the entire workspace. The user names what the model sees;
the model does not guess.

**Observable behavior** (reproducible on 2026-05-16). Typing `@` in
chat or in a Cmd+K prompt opens a typeahead listing `@File`,
`@Folder`, `@Codebase`, `@Docs`, `@Web`, `@Git`, and adjacent context
primitives. Each accepted mention becomes a visible chip in the
prompt that the user can hover to inspect (sees what the chip
resolves to) or click to remove. The chip persists into the
conversation history, so the next turn renders exactly what context
the model saw on the previous turn — including which docs source,
which folder, which git ref.

**Why this is the right PM call.** The alternative — silently
injecting "the open file" or "the whole repo" by default — makes
model behavior unpredictable from the user's perspective ("why did
it suggest changes to a file I didn't ask about?") and unauditable
after the fact ("what did the model actually see when it gave that
answer?"). The explicit-mention model pays for itself twice: once in
fewer surprise behaviors during normal use, and again as the
substrate for any future "why did the model say that?" reproducibility
property — a property AI products increasingly need to support as
users and reviewers start asking the question directly. It also lets
the model-context window be budgeted by the user rather than blown
by an over-eager auto-include heuristic.

**Tension worth naming:** cold-start friction vs. predictability. A
first-time user has to discover that `@` is meaningful — a small but
real learning curve. The PM trade favors predictability: cold-start
cost amortizes over a power user's tenure, while surprise behaviors
don't amortize for anyone. The product helps cold-start by surfacing
`@` hints in the empty-state of chat, but it does not remove the
explicitness requirement.

*(Sources: observable behavior on 2026-05-16; Cursor docs on
`@`-mentions and context, cursor.com/docs, accessed 2026-05-16.)*

### 1.3 Sequencing autonomy: Background Agent shipped after Composer matured

**The PM decision.** Ship the asynchronous, off-screen Background
Agent (and the related Cursor for Web surface) only after the
synchronous, in-loop Composer had been in users' hands long enough
for a mental model of agent failure modes to form — rather than
launching the autonomous surface first or alongside Composer.

**Observable behavior** (cited from the public changelog and
Anysphere's public communications, observed 2026-05-16). Composer's
general availability lands in the changelog timeline earlier than
Background Agent / Cursor for Web. Anysphere's public posts and
interviews around the Background Agent launch consistently position it
as an extension of Composer's autonomy gradient rather than a separate
product line. The autonomy ramp visible in the product is staged:
edits-in-front-of-you (Cmd+K inline) → edits-across-a-task-you're-
watching (Composer) → edits-while-you're-off-screen (Background
Agent). Each step inherits the diff-gate review surface from §1.1, so
the autonomy ramp is also a review-surface ramp: the user gives up
less per-edit attention only after the previous tier of attention has
established a calibration.

**Why this is the right PM call.** Trust in delegated AI work is
built incrementally. A user whose first exposure to Cursor's autonomy
is the Background Agent has no mental model for the surface's failure
modes — when the agent stops cleanly, when it overruns, when it
silently drifts off-task — and will either over-trust (walk away
assuming it finished safely) or under-trust (never run it). A user
who has spent months with Composer accepting and rejecting multi-file
edits arrives at Background Agent with a calibrated sense of where
the model is reliable, where it asks before acting, and where the
human review pass is non-negotiable. The autonomous mode inherits that
calibration on day one rather than having to build it from zero.

**Tension worth naming:** shipping order pushed Anysphere into a
competitive disadvantage on the agent dimension during the window
between Composer's GA and Background Agent's launch — a competitor
that led with an autonomy-first agent could claim the "agent-first"
narrative for that period. The PM trade is to accept the windowed
disadvantage in exchange for an autonomous surface users can actually
use when it arrives. The alternative — autonomy-first launches that
the market later abandons because users won't trust them — has played
out publicly in adjacent products, and a teardown reader will already
have examples in mind.

*(Sources: Cursor changelog, cursor.com/changelog, accessed
2026-05-16; Anysphere public communications around Background Agent
launch, cited inline by post title and date when referenced in
later sections.)*

### Cut from the outline's four: the pricing-tier shape

The outline named a fourth candidate sub-area — free tier with a real
model menu (rather than a degraded teaser), Pro at a defensible
price, Business tier selling features developers actually use. It is
a defensible product call but it lives more on the
monetization-and-positioning side than the PM-design-call side.
Defending it concretely requires specific tier prices and quota
numbers; the no-fabrication posture from the masthead would force the
draft to either pin every figure to a snapshot citation (which drifts
week-to-week) or replace them with placeholders, neither of which
strengthens the argument. The teardown is stronger with three
concrete PM-design calls than with four where one is positioning.
Pricing surfaces lightly in §4's lagging-business metrics row and in
§6's explicit exclusion of pricing-page A/B as a validation method.

**Evidence sources for this section:** Cursor docs (cursor.com/docs)
accessed 2026-05-16, Cursor changelog (cursor.com/changelog) accessed
2026-05-16, observable product behavior on 2026-05-16 (macOS, Pro
tier — labeled inline where reproduction matters), and named
comparisons with Copilot's equivalent surfaces where the contrast is
publicly verifiable. No internal Cursor information, no fabricated
specifics.

---

## 2. What's broken

**Section intent:** name the PM failures honestly. A teardown that
only celebrates is not an interview leave-behind — it's a marketing
deck. Each sub-point pairs an observable symptom with the PM choice
the symptom implies; each is framed as a fixable UX gap rather than
a strategy mistake, with the reasoning made explicit so a reader can
disagree concretely.

Three sub-sections follow, narrowed from the outline's four candidate
sub-areas. The cut — free-tier quota surprises — is named at the end
of this section with a one-paragraph rationale, mirroring the §1.4
cut paragraph.

### 2.1 Auto-mode router opacity

**The PM failure.** When the model menu is set to "Auto," Cursor
routes each turn to an underlying model — Sonnet, GPT, Gemini, or a
faster cost-tier model — without telling the user which model handled
the response, when a fallback fired, or how the routing decision was
made. The simple-surface default is also an unauditable surface.

**Observable behavior** (reproducible on 2026-05-16). With the model
menu set to "Auto," send a chat or Composer prompt. The response
renders with no per-message indicator naming the model that produced
it; the model menu in the composer still shows "Auto" rather than the
underlying selection. There is no per-thread routing summary in the
thread sidebar, no opt-in advanced view that exposes the routing
history, and no surfaced signal when an Auto turn falls back from a
preferred model to a faster one due to availability or cost. Switching
to a specific model from Auto changes the routing label, but does not
retrospectively show what Auto would have chosen.

**Why this is a fixable UX gap, not a strategy mistake.** The
strategic logic for Auto is sound: most users do not want to learn the
model menu, and a sane default that picks for them is the right
product call. The gap is at the UX layer — without a per-message
"served by X" affordance, users cannot learn which model is reliable
for which task, cannot reproduce a successful turn, and cannot triage
a bad response (model regression vs. prompt-quality vs. tool
failure). The minimal fix is reveal-after-the-fact: a compact label
on each response, optionally a per-thread routing summary in a
collapsed panel. Routing logic does not change; transparency over it
does.

**Tension worth naming:** surface clutter vs. user learning. A
per-message model label costs visual real estate and reintroduces the
exact "which model is this?" decision Auto was supposed to spare the
user from. The trade favors revelation because the alternative is
users learning the routing through forum posts and trial-and-error —
which a competing product reading this teardown would be happy to
exploit by leading with model transparency. The clutter cost is
bounded by typography choices; the user-learning cost compounds.

*(Sources: observable behavior on 2026-05-16, macOS / Pro tier;
Cursor docs on model menu and Auto, cursor.com/docs, accessed
2026-05-16; user-community discussion of Auto routing visibility, on
public Cursor forum threads, cited as a pattern rather than as
authoritative on Cursor internals.)*

### 2.2 Indexer staleness signals

**The PM failure.** Cursor's project indexer — the system that lets
`@Codebase` and the agent surfaces ground answers in repo content —
can serve stale chunks on larger repos after recent edits, and the
product offers no first-class index-freshness indicator the user can
read at a glance. The user discovers staleness by being wrong about
their own working tree.

**Observable behavior** (reproducible on 2026-05-16, on a repo larger
than ~5k files). Edit a file, save it, then immediately ask
`@Codebase` a question whose answer depends on the new content. The
model's response can reference the pre-edit version of the file, with
no in-thread signal that the answer was indexed-state-stale. There
is no persistent UI element in the workspace footer or sidebar that
reads "indexed N seconds ago, M files pending" the way IDE search
panes do; index controls live behind Settings → Indexing → Resync,
which the user must navigate to manually after realizing the answer
was stale.

**Why this is a fixable UX gap, not a strategy mistake.** Incremental
indexing on a fast-moving codebase is a hard engineering problem and
some staleness window is unavoidable — even a perfect indexer has a
sub-second gap between edit and reindex. That is the strategy
constraint, and it is fine. The PM gap is the user-facing signal
during that window: a persistent freshness indicator (last-index
timestamp, pending-file count, one-click resync) reduces user
confusion to near zero without changing the indexer's underlying
behavior. The pattern is borrowed wholesale from JetBrains and VS
Code search panes, which long ago made index state a visible
first-class affordance.

**Tension worth naming:** chrome cost vs. user trust. A persistent
freshness indicator is one more piece of always-on UI in a product
that already competes for attention with the diff gutter, the
Composer drawer, and the model menu. The trade favors visibility
because the alternative — silent staleness with no recovery path
the user can see — directly undercuts the `@Codebase` primitive from
§1.2, which is supposed to make the model's view of the repo
predictable. An unpredictable indexer behind a predictable mention
chip is a strictly worse position than a slightly busier UI with a
freshness signal.

*(Sources: observable behavior on 2026-05-16, macOS / Pro tier, repo
size > 5k files; Cursor docs on the project indexer and `@Codebase`,
cursor.com/docs, accessed 2026-05-16; user-community reports of
indexer staleness on public Cursor forum threads, cited as a
recurring pattern rather than authoritative on internals.)*

### 2.3 Agent stop conditions and overrun

**The PM failure.** Composer and Background Agent can interpret
ambiguous user acknowledgments ("ok," "go ahead," "looks good") as
license to continue work past the user's intended stopping point, and
the only mid-execution control is a Cancel button. The stop surface
is a hammer where the user often needed a scalpel — "pause and let me
amend the plan" — and the failure mode is the agent doing more work
than the user signed up for.

**Observable behavior** (reproducible on 2026-05-16). Give Composer a
multi-step task ("refactor function A, then update its three callers,
then add tests"). After the first step lands, respond to the agent's
progress message with "looks good" intending to acknowledge step one.
The agent often interprets this as license to proceed through steps
two and three autonomously, including continuing past a point where
the user would have wanted to inspect intermediate state. Recovery
requires Cancel — which leaves the working tree in a partially
edited state — followed by a fresh prompt to undo or redo the
last increment. Background Agent exhibits the same pattern offscreen,
with the additional cost that the user notices the overrun only on
return.

**Why this is a fixable UX gap, not a strategy mistake.** Aggressive
autonomy is the whole point of Composer and Background Agent — narrowing
autonomy by default would defeat the surface and was correctly avoided
in §1.3's autonomy ramp. The gap is the stop-criteria UI. A pre-run
"I'll stop when X" plan that the user confirms before the agent starts,
plus a pause-and-amend control during execution, would preserve
autonomy and add control. The harder PM call is the default direction
on the stop dimension: stop-aggressive (interrupt on every ambiguous
acknowledgment, slower but safer) vs. stop-permissive (continue on
ambiguity, faster but riskier). The teardown's §3 will recommend
stop-aggressive and defend the choice; the surface gap is the same
either way.

**Tension worth naming:** stop-aggressive defaults vs. friction on
routine multi-step tasks. Stop-aggressive means more confirmation
prompts on tasks where the user would have happily let the agent
continue, which reads as nagging. The trade favors aggressive because
overrun damage is asymmetric: a wrong-direction agent edit costs the
user the time-to-recover (Cancel, inspect, revert) plus the
time-to-rebuild trust in the agent for the next session. Friction
amortizes; a single bad overrun in a refactor-heavy session can end
the day. Power users who explicitly want stop-permissive should be
able to opt in per-task — but the default protects the cold user.

*(Sources: observable behavior on 2026-05-16, macOS / Pro tier;
Cursor docs on Composer and Background Agent, cursor.com/docs,
accessed 2026-05-16; public Anysphere statements on agent
stop-conditions and autonomy posture, cited by post title and date
where referenced in §3.)*

### Cut from the outline's four: free-tier quota surprises

The outline named a fourth candidate sub-area — free-tier monthly
quota limits documented in the pricing page but not displayed
prominently during normal use, surfacing to the user only by
interruption mid-edit. It is a real product friction and the fix is
straightforward (a persistent quota meter near the model menu, a
warning at 80% consumed, a clear path to upgrade). It is also
structurally a monetization-positioning concern more than a
PM-design call, mirroring the pricing-tier cut from §1.4: the deeper
"why is this acceptable" question is about Anysphere's free-tier-as-
funnel strategy, which the no-fabrication posture cannot interrogate
without snapshot-pinned quota numbers and conversion data the public
surface does not expose. Free-tier quota surfaces indirectly in §3's
Proposal B (an index-freshness indicator and a quota meter compete
for the same chrome real estate, which is a deliberate scope choice
worth naming there) and in §4's lagging-adoption metrics row
(free-to-paid conversion). The teardown is stronger with three
concrete PM-craft critiques than with four where one is positioning.

**Evidence sources for this section:** observable product behavior on
2026-05-16 (macOS / Pro tier, with file-count and repo-size
conditions named per sub-section), Cursor docs (cursor.com/docs)
accessed 2026-05-16, public Anysphere statements on agent autonomy
and stop-conditions (cited by title and date where referenced), and
user-community reports on public Cursor forums (cited only as
recurring patterns, never as authoritative on Cursor internals). No
internal Cursor information, no fabricated metrics, no invented
support-ticket volumes.

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
