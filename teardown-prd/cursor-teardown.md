# Cursor — Teardown PRD

**Status:** §§1–6 ("What's working", "What's broken", "What to ship
next", "Proposed metrics", "Out of scope", "How I'd validate") drafted.
The final iteration is a polish / leave-behind framing pass per the
seven-step slicing plan locked in DECISIONS.md.

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

Three proposals follow, one per §2 sub-area (Proposal A → §2.1,
B → §2.2, C → §2.3). Each follows the same five-slot shape as §§1–2,
with slot 1 substituted to "the PM proposal" and slot 3 substituted
to "what could go wrong." No parallel cut paragraph: the proposal
count is bound one-to-one to §2's narrowed three, not drawn from an
independent outline list, so there is no fourth candidate to drop.

### 3.1 Proposal A — Routing transparency for Auto mode

**The PM proposal.** Surface the underlying model identity, fallback
events, and routing rationale to the user after each Auto-mode turn —
without changing how Auto routes. The minimal change is a compact
per-message label ("served by Sonnet 4.5 via Auto"), accompanied by
an opt-in per-thread routing summary in a collapsed panel. Power
users gain an opt-in advanced setting that pins the router to a
specific model from inside Auto. Auto remains the default; the
routing logic itself is untouched; only post-hoc transparency is
added.

**Proposed shape** (the user-facing behavior the proposal implies).
On each response, a single-line caption renders below the assistant
turn: model name, version, and the routing reason in three to six
words ("auto picked Sonnet for code edit"). A "show routing for this
thread" toggle in the thread header expands a collapsed panel listing
the chronological model-per-turn series, with hover-tooltips on
fallback events ("fell back from Sonnet to GPT-5: provider latency
> 4s"). A new Settings → Model entry adds an "Auto with model pinned"
radio that disables routing for the current session without forcing
the user out of the Auto mental model. None of the underlying routing
decisions or fallback triggers change.

**What could go wrong.** The reveal-after-the-fact label re-surfaces
the exact "which model is this?" decision Auto was supposed to hide.
A subset of users will read each label, internalize the model menu,
and pin manually — fine outcome on its own, but it loses the "users
don't have to think about it" property Auto promised. Mitigation:
typographic restraint (caption-grade text, not chrome) and a setting
to suppress the label for users who explicitly do not want it. A
second risk: the routing-summary panel becomes a debug surface the
support team relies on, locking routing-reason strings into a
user-facing contract that constrains future routing changes.
Mitigation: ship the reason strings as user-readable English from day
one, treated as part of the public surface.

**Tension worth naming:** revelation cost vs. user-learning compound
interest. Each per-message label costs visual real estate and
reintroduces the very decision Auto deflected. The trade favors
revelation because the alternative is users learning routing through
forum posts, trial-and-error, and support tickets — a compounding
cost the product carries every week the label is absent. Clutter
cost is bounded by typography; user-learning cost compounds.

*(Sources: PM proposal, not a fact-claim about Cursor internals.
Grounds in §2.1's documented opacity surface — observable on
2026-05-16, macOS / Pro tier — and in IDE-pattern precedent:
Copilot Chat, Cody, and Claude's chat surfaces all label per-turn
model identity in their current UIs, observable on those products'
2026-05-16 releases.)*

### 3.2 Proposal B — Index-freshness indicator

**The PM proposal.** Add a persistent index-freshness indicator to
the workspace footer: last-index timestamp, count of pending files,
and a one-click "resync now" affordance. The indicator is always
visible, lives at footer scale (small but readable), and persists
across sessions. The underlying indexer is not changed; the
user-facing signal during the staleness window is added.

**Proposed shape** (the user-facing behavior the proposal implies).
A small footer chip near the language-mode indicator reads "indexed
2s ago" in steady state, "indexing 3 files…" during refresh, and
"indexed 4m ago — 6 pending" when the indexer is behind. Hover
reveals a tooltip listing the pending files (truncated to a count for
large lists) and a "resync now" button; click-through opens the
existing Settings → Indexing pane. On reindex, the chip transitions
back to "indexed Ns ago" without modal interruption. The `@Codebase`
mention chip from §1.2 inherits the same freshness state: when the
indexer is behind by more than a configurable threshold (default 30
seconds), the chip carries a small staleness marker so the user sees
the trust state of the chip *before* sending the prompt — not after
acting on a stale answer.

**What could go wrong.** The freshness chip compounds the "always-on
UI" budget already crowded by the diff gutter, the Composer drawer,
and the model menu. Power users may add it to their hide-this-element
list, defeating the purpose. Mitigation: ship it on by default but
session-dismissable (not permanently), so each new session restores
the signal. A second risk: the freshness threshold is hard to set
defensibly — too tight and the chip spends the day red, too loose and
users miss real staleness. Mitigation: ship a default (30s) calibrated
against indexer behavior on the test repos Anysphere already
exercises, and expose the threshold as a setting so heavy users tune
it.

**Tension worth naming:** chrome cost vs. trust-by-default. A
persistent indicator costs always-on attention; without it, silent
staleness directly undercuts the §1.2 `@`-mention chip's
predictability contract. The trade favors the indicator because the
alternative — users discovering staleness by being wrong about their
own working tree — is the single fastest path to losing the trust the
chip system was built to earn. Footer real estate competes with the
quota meter the §1 and §2 cuts named as the natural home for
free-tier quota surprises; the proposal claims that real estate first
because index freshness is a craft signal and quota is a positioning
signal, and the craft signal should win when both want the same
pixels.

*(Sources: PM proposal, not a fact-claim about Cursor internals.
Grounds in §2.2's documented staleness surface — observable on
2026-05-16, macOS / Pro tier, repo size > 5k files — and in
IDE-pattern precedent: JetBrains and VS Code both expose index
state as a footer-or-sidebar first-class affordance, observable on
their 2026-05-16 stable releases.)*

### 3.3 Proposal C — Agent stop-criteria UI

**The PM proposal.** Replace the implicit "continue on user
acknowledgment" behavior of Composer and Background Agent with an
explicit pre-run plan the user confirms — "I'll stop when X, Y, Z are
done, or if I encounter Q" — plus a prominent pause-and-amend control
during execution. The default direction on the stop dimension is
**stop-aggressive**: any user message arriving mid-execution pauses
the agent and surfaces a "continue / amend / cancel" affordance, with
stop-permissive available as a per-task opt-in for users who knowingly
want the agent to push through ambiguity.

**Proposed shape** (the user-facing behavior the proposal implies).
Before Composer starts a multi-step task, the agent emits a short
plan summary ("I'll do A, then B, then C, and stop if D"). The user
clicks "start" to proceed or edits the plan inline before starting.
During execution, every user message is treated as an interrupt by
default. The agent pauses, displays the current step's status, and
prompts the user with "continue from here / amend the plan / cancel."
A per-task toggle ("auto-continue on acknowledgment, this task only")
opts the user into the old stop-permissive behavior for tasks where
they knowingly want it. Background Agent inherits the same plan +
interrupt flow, with the pause surfaced as a notification when the
user is offscreen rather than as an inline prompt.

**What could go wrong.** Stop-aggressive means more confirmation
prompts on routine multi-step tasks, which power users will read as
nagging. A non-trivial fraction will reach for the per-task
auto-continue toggle and then forget they enabled it, re-creating the
original overrun risk one session later. Mitigation: scope the toggle
to the current task only (no persistent setting), so the user
re-makes the trust decision per run. A second risk: the pre-run plan
grows into a planning dialog the user has to negotiate before any
work happens, increasing time-to-first-edit. Mitigation: keep the
plan short (3–5 steps), let the user start without amending, and
treat the plan as a checkpoint rather than a contract — the agent
can revise the plan mid-execution by pausing and proposing the
revision through the same interrupt surface.

**Tension worth naming:** stop-aggressive friction vs. overrun-damage
asymmetry. Stop-aggressive costs the user attention on tasks where
the agent would have proceeded safely — a per-task tax. The trade
favors stop-aggressive because the damage profiles are asymmetric:
a wrong-direction agent edit ten steps deep costs Cancel + inspect +
revert + the rebuilt trust the agent needs to be useful in the next
session, while a confirmation prompt costs one click. Friction
amortizes; a single bad overrun in a refactor-heavy session can end
the day, and users remember the overrun far longer than the prompts.

*(Sources: PM proposal, not a fact-claim about Cursor internals.
Grounds in §2.3's documented stop-condition surface — observable on
2026-05-16, macOS / Pro tier — and in public Anysphere statements on
agent autonomy posture, cited by post title and date in the source
list at document end.)*

**Evidence sources for this section:** PM recommendations rather than
fact-claims, so the source posture is "the draft makes the case;
the reader is free to disagree." Each proposal grounds in §2's
documented Cursor surface (which is itself sourced) plus PM-craft
argument and IDE-pattern precedent observable on competing products'
2026-05-16 surfaces. No internal Cursor information is assumed (e.g.
"Cursor's index already supports incremental refresh" would need a
source or be rewritten as conjecture), no fabricated metrics, no
roadmap claims beyond what Anysphere has stated publicly.

---

## 4. Proposed metrics

**Section intent:** a metric framework the Cursor PM team could
adopt to evaluate the proposals in section 3 and to monitor the
broader triad surface. The framework is the PM artifact, not the
specific numbers — naming any specific number Cursor should hit
would either fabricate it or quote it without attribution.

Six metrics follow, organized in the standard PM 2×2 (leading vs.
lagging × adoption vs. quality-or-business) with a 2-2-1-1
distribution across the four quadrants. The leading-heavy
distribution is deliberate: PM action lives on the leading side, so
the framework should be denser there; the lagging side gets the
minimum needed to anchor the leading metrics to outcomes Anysphere
already tracks. Each metric names what it computes, what PM
decision it informs, the §3 proposal or §1–§2 sub-section it most
directly maps to, and a caveat naming the common way the metric
would mislead. No targets, no baselines — the framework is the
artifact, not the dashboard.

Each §3 proposal has at least one leading-quadrant metric pointed
at it. §4.1.2 Auto-mode mix evaluates Proposal A (routing
transparency), §4.2.1 Agent stop-precision evaluates Proposal C
(stop-criteria UI), and §4.2.2 Index-freshness coverage evaluates
Proposal B (index-freshness indicator). The two
adoption-quadrant metrics (§4.1.1 `@`-mention adoption and §4.3.1
retention by cohort) test the §1.1/§1.2 thesis that the
explicit-context model is what earns long-tenure trust. The single
business-quadrant metric (§4.4.1) is deliberately minimal,
mirroring the §1 and §2 pricing-tier and free-tier cuts: a teardown
that cannot pin Cursor's revenue numbers without fabrication is
better off naming one defensible business-shaped check than
inventing a dashboard.

### 4.1 Leading × adoption

**4.1.1 `@`-mention adoption rate.** Share of chat and Cmd+K
sessions in a given week containing at least one explicit
`@`-mention before the first model turn. Computed as
sessions-with-mention ÷ total-sessions over a rolling 7-day window,
segmented by user-tenure cohort (first-week / first-month /
90-day+). **What decision it informs:** whether the §1.2
explicit-context bet is paying off in the field. A rising rate
inside the first-month cohort confirms cold-start friction is
amortizing as designed; a flat or falling rate inside that cohort
warns the `@` discovery path needs more empty-state surfacing or a
better in-product onboarding nudge. **Caveat:** a high headline rate
driven by `@Codebase`-only usage can mask the deeper
`@File` / `@Docs` / `@Web` value, so split the metric by mention
type — reading "one mention-shaped behavior" as adoption of the
whole context system would let a single popular chip carry credit
for the system's design.

**4.1.2 Auto-mode mix.** Share of triad-surface turns served via
Auto vs. served via an explicitly pinned model, computed weekly.
The *trend* is the actionable signal, not the level — the absolute
level reflects user preference and is not directly actionable; the
trend responds to Proposal A's per-message routing labels and the
"Auto with model pinned" setting. **What decision it informs:**
whether the per-message model label re-surfaces the model menu so
visibly that users abandon Auto. A small post-launch drop is
expected (some users pin to the model the label revealed, a fine
outcome on its own); a large or sustained drop warns Auto's
"users don't have to think about it" property is being eroded
faster than the transparency benefits compound, which would mean
typographic restraint on the label is the wrong knob and a stronger
"hide this caption" affordance is needed. **Caveat:** pinning is
not failure. A user who pins to the right model for their workflow
may end up better off than under Auto. Pair this metric with
§4.3.1 retention to read whether the pinned cohort sticks; without
that pairing, the mix shift reads as loss when it may be a quality
gain.

### 4.2 Leading × quality

**4.2.1 Agent stop-precision.** Among agent runs that halted before
hitting a hard stop (max-steps or user-cancel), the share that
halted at the user's intended boundary, measured against an
offline labeled eval set of agent transcripts. The eval set is the
same fixture shape this repo's evals-harness scores in its
termination rubric, named explicitly because §6's "How I'd
validate" section calls out the eval-harness as a PM-craft
validation method and §4.2.1 is the metric that worked example
would feed. **What decision it informs:** whether Proposal C's
pre-run plan + pause-and-amend interrupt actually reduces overrun.
A pre/post-deployment lift is the primary read; a flat number
warns the stop-criteria UI is being dismissed or ignored, which
would mean the affordance needs to be louder or less skippable.
**Caveat:** heavy power users in stop-permissive mode (Proposal C's
per-task opt-in) contribute "no-stop-needed" runs that inflate the
precision number without telling you anything about default
behavior. Report default-mode and opt-in-mode separately, treat
the default-mode number as the headline, and resist any temptation
to "average across modes" — the per-task scope from slice-4
DECISIONS is a feature of the proposal, not a detail to abstract
over.

**4.2.2 Index-freshness coverage.** Share of `@Codebase` and agent
turns served when the project indexer was within a configurable
lag threshold (default 30 seconds) of the working tree. Computed
per-turn at request time, aggregated weekly, segmented by repo-size
cohort (small / medium / large). **What decision it informs:**
whether Proposal B's freshness indicator changes user behavior
post-launch. The metric should rise (users resync before asking,
or learn to wait) or rise-then-plateau (users learn the staleness
signal and only ask when it is clean). A flat or falling rate after
launch means the chip is being ignored or hidden, and the
indicator's typography or placement needs revisiting. **Caveat:**
large-repo cohorts will always run colder than small-repo cohorts;
segmenting prevents the small-repo majority from making the
headline number look healthier than the large-repo subset's reality,
which is exactly the segment where indexer staleness was the
original §2.2 symptom.

### 4.3 Lagging × adoption

**4.3.1 90-day retention by `@`-mention cohort.** Among users
active in a given week N, the share still active 90 days later,
split by their week-N usage of `@`-mentions (zero / 1–3 / 4+
mentions in the cohort week). **What decision it informs:** whether
the §1.2 explicit-context bet correlates with stickiness in a way
that survives self-selection scrutiny. If the 4+ cohort retains
markedly higher than the zero cohort and the gap holds when matched
on tenure and repo size, the thesis is doing real work and the
§1.2 PM defense rests on more than a predictability argument. If
the gap collapses on matching, the explicit-context system may be
correlated with — rather than causing — retention, and the §1.2
defense should rest on the predictability argument alone.
**Caveat:** power users self-select into `@` usage, so the
observational retention gap is suggestive, not causal. Any product
call that claims causation should be backed by a flag-gated
experiment that varies the `@` empty-state surfacing, not by the
cohort read alone — confusing cohort correlation with intervention
effect is the most common metric-misread in this quadrant.

### 4.4 Lagging × business

**4.4.1 Net revenue retention on the Business tier.** Among Cursor
accounts that crossed into Business tier in quarter Q, the share
still on Business 12 months later, plus seat-expansion or
contraction within retained accounts. **What decision it informs:**
whether the developer-relevant features the Business tier sells
continue to earn the upgrade over time. Falling NRR within the
12-month window points to a thin upper tier (Business buyers
churning back to Pro or off-platform); flat-or-rising NRR suggests
the Business surface is doing genuine work for buyers and the tier
is defensible. **Caveat:** 12 months is the wrong window for a
fast-moving product whose adjacent market reshapes quarter by
quarter — report the metric alongside the quarter-by-quarter trend
so the lagging read does not lag so far it ceases to inform action.
This is the only business-shaped metric in the framework, same
posture as the §1 pricing-tier and §2 free-tier quota cuts: a
teardown that cannot pin Cursor's revenue numbers without
fabrication is better off naming one defensible business check than
inventing a dashboard.

**Evidence sources for this section:** the metric *categories* are
standard PM craft and need no external citation. The *applicability*
to Cursor specifically is grounded in publicly observable product
behavior already sourced in §§1–2 — the `@`-mention surface from
§1.2, Auto mode from §2.1, the project indexer from §2.2, agent
stop conditions from §2.3, and the Business tier as named on
cursor.com/pricing accessed 2026-05-16. No fabricated baselines,
no invented benchmarks, no quoted targets — the framework is the
artifact, the dashboard would be Anysphere's to define on internal
data this teardown cannot read.

---

## 5. Out of scope

This section names the seven categories the teardown is deliberately
silent on, each with one paragraph of rationale, so a reader cannot
fault the document for omissions that were intentional. Five items
are carried verbatim from the scope decision at the top of this
document; two more were added once the §§1–4 draft made their absence
visible. The §1 pricing-tier and §2 free-tier-quota cuts are *not*
restated here — those are sub-section-level narrowings inside §§1
and §2, not document-level exclusions.

**5.1 Enterprise admin and policy controls.** Team-level SSO, audit
logs, IP allowlists, model-access policies, and the admin-dashboard
surface that exposes them. These are a real product surface and a
real source of Business-tier purchase rationale, but they sit behind
a paywall this author cannot access on a paid seat without invented
credentials, and the public docs cover *scope* but not the actual
admin UX. A teardown that named specific control shapes would either
fabricate the surface or restate marketing copy. §4.4.1 (Business-
tier NRR) carries the lightest possible acknowledgement that
admin-and-policy is a Business-tier purchase driver; no §3 proposal
targets this surface.

**5.2 Provider economics and per-model unit costs.** What Anysphere
pays Anthropic, OpenAI, and Google per inference, how cursor.com/
pricing relates to that cost, and how Auto-mode routing optimizes
for cost vs. quality at the unit level. This is the most-requested
cut among PM-craft readers but it is squarely outside the public
surface: per-call unit costs are not disclosed by any provider or
by Anysphere, and any number a teardown puts on paper would be
invented. The §2.1 Auto-mode opacity treatment names cost as one of
two router objectives without quoting any number — that is the
deepest the no-fabrication posture permits.

**5.3 VS Code shell parity and extension marketplace.** Which VS
Code extensions work, which break on the fork, and what staying
current with upstream actually costs Anysphere release-over-release.
This is a meaningful risk to Cursor's roadmap — every VS Code
release is a fork-rebase cost — but it sits on the engineering /
platform-strategy side of the ledger, not the user-product side this
teardown is scoped to. A PM working on AI features would not own
the fork-rebase work even if the product team funded it. The right
document for that surface is a separate engineering-strategy memo,
not §3 of this teardown.

**5.4 Cursor CLI / cursor-agent as a separate product.** The
terminal-native agent surface Anysphere ships alongside the desktop
IDE. It overlaps the desktop Composer surface on intent but differs
substantively on input shape, tool surface, and termination
semantics — enough that a teardown of both products would dilute the
desktop-triad scope locked in the scope decision. The CLI deserves
its own teardown if it justifies one; restating the §§1–3 arguments
with "and also on the CLI" caveats would mislead a reader into
thinking the desktop analysis transferred when in places it does
not.

**5.5 Tab autocomplete as a deep-dive subject.** The single-line
ghost-text completion that predates the chat / inline-edit /
Composer triad. It is the original feature most users meet first,
but the PM craft on it (latency, hit-rate, cancellation UX) is
materially different from the assistive-decision craft §§1–3
examine, and the two genres do not share design vocabulary. A future
teardown could do Tab justice as its own document; folding it into
this one would have either left it underwritten or pulled the
document into a two-genre hybrid neither audience would read end-to-
end.

**5.6 Competitive landscape ranking.** Where Cursor sits relative
to GitHub Copilot, Windsurf, Cline, Aider, Zed AI, and Continue.
This category was added at draft time, not at scope-decision time,
because §§1–3 kept generating natural "compared to X, Cursor's
approach is …" sentences that would be short and dishonest without
a market-map document underneath them. A teardown is a product
analysis; a market map is a separate artifact with its own honesty
demands (which competitors get a fair representation, what evidence
each ranking rests on). Conflating the two genres weakens both —
the right move is to write neither here.

**5.7 Founder / company analysis.** Anysphere as a company — its
funding history, hiring, founder backgrounds, and product
philosophy as stated in interviews. Added at draft time because
§1.3's "sequencing autonomy" sub-section pulls toward founder-
philosophy explanations the public surface does not support without
speculation. A teardown is product-shaped, not company-shaped;
founder-philosophy claims need to be cited from specific public
statements with dates, and even when cited they substitute for
analysis of the product surface a reader could themselves observe.
The teardown's job is to read the product, not the operator.

**Evidence sources for this section:** none required at the
per-item level — each entry is a scope decision, not a fact-claim
about Cursor. The two added-at-draft-time items (§5.6, §5.7) are
named here so a reader who notices their absence in the scope
decision at the top of the document sees them documented
explicitly rather than as an apparent oversight.

---

## 6. How I'd validate

If §3 is the proposals and §4 the metrics, §6 is the methodology
that takes a proposal from "PRD opinion" to "shipped feature whose
effect we believe." Each method below names *what it would
validate*, *which §3 proposal or §4 metric it ties to*, and the
threshold that would let an engineering org move forward. Methods
are ordered roughly pre-launch first, post-launch later, so the
section reads as a workflow. Pricing-page A/B testing is listed
last as a deliberate *non-method*, because the load-bearing
trade-offs in §§2–3 are about user-trust UX and pricing experiments
would conflate the signal.

**6.1 Internal replay of §2 failure modes.** Recruit ~10–15
Anysphere engineers who use Cursor heavily, give them the exact
prompts that reproduced the §2.1 routing-opacity, §2.2 index-
staleness, and §2.3 overrun symptoms in this teardown, and observe
whether each subject hits the failure mode and how long they take
to recover. This is the pre-investment check: if internal users
(above-average sophistication, repo familiarity, product mental-
model) cannot reproduce the symptoms, the proposals don't deserve
engineering time yet; if they reproduce easily, the proposals shift
from "PM conjecture" to "PM observation." Success threshold: ≥60%
of internal subjects hit each symptom within their first three
relevant interactions. Limit: internal users self-select and over-
index on power-user repos — this method *validates that the
symptoms exist*, not *that the proposals fix them*.

**6.2 Flag-gated rollout with product analytics.** For each §3
proposal, ship the affordance behind a percentage-rollout flag to
~5% of users for two to four weeks before opening to GA. Read the
§4 metric the proposal is paired with: Proposal A → §4.1.2
Auto-mode mix in the rolled-out cohort vs. control; Proposal B →
§4.2.2 index-freshness coverage trend; Proposal C → §4.2.1 stop-
precision on default-mode runs (the opt-in mode requires the §6.4
offline eval, not analytics). Thresholds are *comparison-shaped*: a
routing label that produces a 15%+ drop in "which model is this"
support tickets in the flagged cohort is ship-ready; a 0% drop and
unchanged Auto-mode mix is iterate-or-cut territory. Limits: 5%
rollouts cannot read low-base-rate symptoms, and a flag that paints
a UI element will see novelty-bump activation that decays over
weeks — read four-week-out activation, not week-one.

**6.3 Targeted qualitative research on the index-freshness
symptom.** 10–15 sixty-minute conversations with developers split
across two recruited cohorts: heavy Cursor users on monorepos
(≥100k files), where §2.2's indexer staleness is most likely to
bite, and recent churners who left Cursor in the last quarter for a
reason that *could plausibly* be index-related (the screener is
what cuts the latter group from "general churner" to "index-related
churner"). The interview probes the §2.2 symptom directly: "show
me a time the assistant misread your repo state." Success
threshold: Proposal B's freshness chip materially shifts the
user's reported trust in the assistant's repo-knowledge against a
pre-interview baseline question. Limit: 10–15 conversations
generate hypotheses, not statistics — this method is wrong-input
*defense* for the §6.2 analytics rollout, not a substitute.

**6.4 Offline evaluation harness for agent stop-criteria.** Build
an offline labeled fixture set of ~200 agent turns, each tagged
with a ground-truth "stop here" or "keep going" decision derived
from the user's *actual* subsequent reply ("yes that's enough" vs.
"keep going"), and score Proposal C's stop-criteria UI against the
labeled set using a rubric whose shape matches this repo's
`evals-harness/` termination scorer. The harness exists in the
repo adjacent to this teardown as a worked example: same per-
record JSONL shape, same `stop_reason` enum, same separation
between *ended_clean* and *cap-exhausted* terminations. This is
the validation path for §4.2.1's default-mode stop-precision; the
opt-in stop-permissive subset (the per-task scope locked in §3.3 /
slice-4 DECISIONS) is reported on a separate fixture sub-set, with
its own threshold, so the proposal's "per-task scope is a feature,
not a detail" promise is preserved end-to-end through validation.
Success threshold: ≥90% agreement with ground-truth on the
default-mode subset before the proposal can ship; the opt-in subset
number is reported but not a ship-gate. Limit: labeled sets
calcify around the labeled symptoms — a quarterly novel-symptom
fixture refresh is the maintenance cost.

**6.5 Pricing-page A/B testing — explicitly NOT a validation
method here.** A pricing-page experiment can read whether users
will pay more for the same product, but every proposal in §3 is a
user-trust UX intervention, not a price-discovery one. Running a
pricing A/B on top of a flag-gated routing-transparency rollout
would conflate two signals (willingness to pay with willingness to
trust) and the lift could come from either or both. §4.4.1 NRR is
the right home for a lagging business-quadrant read on Business-
tier purchase rationale; a pricing-experiment signal belongs there,
in a separate cycle not entangled with §3. Listing the non-method
explicitly mirrors the §1 and §2 cut paragraphs — the discipline
of naming what is deliberately *not* done is part of the
document's PM-craft signal.

**Evidence sources for this section:** §6 is methodology, not
fact-claim, so it stands on argument quality and on cross-binding
to §§3–4 rather than on cited surfaces in Cursor's product. The
single verifiable cross-reference is §6.4: the worked-example
`evals-harness/` build in this repository, which a reader can
inspect directly and which intentionally shares the per-record
JSONL shape and `stop_reason` enum semantics §6.4 names.

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
