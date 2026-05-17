# Linear — AI weekly retro auto-summarization (PRD)

**Status:** Draft v1, all sections complete (2026-05-17). PRD format
is the portfolio convention for `prds/`; section structure mirrors a
standard product brief (problem / users + JTBD / goals / non-goals /
proposed experience / metrics / risks + mitigations / open questions
/ phased rollout). The document is interview-ready as a "here's a
feature I would ship" companion to the Cursor teardown at
`teardown-prd/cursor-teardown.md`, which answers "here's how I would
analyze a product."

**Target product:** **Linear** — issue tracking and project management
for software teams. https://linear.app

**Proposed feature, short name:** *Cycle Recap* — an AI-generated
weekly retro summary that posts at cycle close to a per-team digest
surface, recapping what shipped, what slipped, why, and what to talk
about in the team retro meeting.

**Author POV.** Written as an AI PM proposing a Bucket-2 feature on
top of Linear (established product adding AI surface, per
OBJECTIVE.md). Not affiliated with Linear. All claims about
Linear's current AI surface are anchored to publicly observable
behavior — feature names quoted exactly from Linear's marketing
pages, with `linear.app/ai (observed 2026-05-17)` and other URLs
cited inline.

**Observation snapshot:** 2026-05-17. Linear's AI surface is
expanding actively, so any feature claim in §1.1 is dated; if a
future reviewer observes that Linear has shipped Cycle Recap or a
near-equivalent between this snapshot and the read date, the PRD's
proposal collapses into "validation, not invention" — see §10 Open
questions.

**No-fabrication discipline.** Every claim about Linear's current
behavior is anchored to a URL + observation date in §11 Sources. No
invented user quotes, no fabricated usage metrics, no invented
roadmap. Where a number is needed and unknown (e.g., "how many
teams currently run a weekly retro"), the PRD names the source the
PM or interviewer would consult to fill it in — never a placeholder
number presented as fact. This rule binds any future PRD in this
directory; see `prds/README.md` for the convention.

---

## Scope decision

The PRD proposes **one** feature — Cycle Recap — at the team scope
(one Linear team, one cycle close, one summary). Adjacent surfaces
named explicitly so the draft cannot drift into them:

- **Project / initiative summaries** are already shipped as *Pulse
  updates* (per linear.app/ai, observed 2026-05-17). Cycle Recap
  complements Pulse but does not replace it: Pulse rolls up across
  projects and initiatives on a daily/weekly cadence; Cycle Recap
  fires at the cycle-close event for one team's just-closed cycle.
- **Cross-team or org-wide recap** is out of scope. Aggregating
  recaps across teams is a v2 surface; the v1 target user is a
  single engineering manager looking at one team.
- **Live in-meeting note-taking** is out of scope. Cycle Recap
  produces a written digest before the retro meeting; what happens
  in the meeting is left to whatever the team already uses (Granola,
  Otter, Notion AI, a human notetaker).
- **Action-item assignment** is out of scope for v1 (named in §5
  Non-goals); it is a v3 candidate gated on the v1/v2 result.

The intentional narrowness is the PM bet: one focused feature
shipped well beats four half-shipped features in a slide.

---

## 1. Problem

### 1.1 The observable gap

Linear has shipped meaningful AI surface area: *Triage Intelligence*
(pattern-based auto-assignment of teams/labels/projects), *Linear
for Agents* (an SDK surface so agents can act inside Linear), *Linear
MCP* (Linear-as-a-tool for Cursor, Claude, ChatGPT), *AI-powered
search*, and *Pulse updates* (project/initiative digests via
email/audio).[^ai] Pulse rolls **up** to the project and initiative
layer. The team-cycle layer — the unit of work most engineering
teams operate on — is not directly served by any current AI surface.

Linear's atomic delivery cadence for engineering teams is the
**Cycle**: a recurring, time-boxed planning unit (typically one or
two weeks) with a defined start, end, and scope. At cycle close, the
team has a substrate that is unusually clean for summarization:
every shipped issue has a state transition with a timestamp; every
slipped issue carries its label, cycle, project, and any updated
estimate; comment threads on each issue contain the narrative of
*why*. This is the same substrate a human engineering manager
spends 30–60 minutes reading on the morning of the team retro.

### 1.2 What's missing

The pre-retro reading is a recurring, manual, low-strategic-leverage
task for engineering managers. It is also under-instrumented: most
teams capture retro outputs only as meeting notes, and many do not
capture them at all. The cost is twofold — (a) EM time spent each
week on read-and-summarize, and (b) loss of compounding signal,
because patterns visible across cycles (the same kind of blocker
recurring; the same engineer consistently under-estimating; the
same project leaking scope) are never aggregated.

A weekly *Cycle Recap* would automate the read-and-summarize step
and persist the digest as a queryable surface, so the second-order
benefit (cross-cycle pattern visibility) becomes available as a
side effect of the first-order benefit (EM time saved).

---

## 2. Users and jobs-to-be-done

**Primary user — Engineering Manager (EM)** running one Linear team
with a 1- or 2-week cycle. JTBD: *"On retro morning, in five
minutes instead of forty, get a defensible read on what shipped,
what didn't, and the two or three things worth talking through in
the meeting."*

**Secondary user — Individual Contributor (IC)** on the same team.
JTBD: *"Before the retro, see what the team will be talking about,
so I can come prepared with context on the parts I owned without
re-reading every comment thread."*

**Tertiary user — Skip-level / Director.** JTBD: *"Skim each team's
weekly recap to spot themes (recurring blockers, scope drift, cycle
quality trend) without dropping into each team's retro meeting."*
Tertiary is named for completeness; the PRD optimizes for primary.

**Explicit non-users.** Product Managers and Designers are not the
target user. They have their own retros and their own substrate
(comment threads on Project pages, design reviews, customer
interviews) that the engineering-cycle substrate does not cover.
Stretching v1 to serve PM/Design retros would dilute the substrate
quality and is left to v2/v3 consideration.

---

## 3. Goals

1. **Cut EM pre-retro prep time materially.** From a self-reported
   30–60 minutes to under 10 minutes, with the recap doing the bulk
   of the read-and-summarize step and the EM doing only the
   judgment overlay (which two of the surfaced themes are worth the
   meeting's time).
2. **Make cross-cycle patterns visible.** By persisting recaps as
   queryable artifacts attached to each cycle, surface patterns
   that are otherwise lost — recurring blocker types, estimate
   drift, scope leakage.
3. **Increase retro-meeting quality, not just retro-meeting
   efficiency.** A good recap is one the team *agrees with* and that
   *changes the meeting* — fewer minutes spent recapping what
   happened, more minutes spent on the two or three judgment calls
   worth a conversation.
4. **Be a believable AI surface for an Engineering Manager.** No
   hallucinated issue numbers, no invented engineer quotes, no
   confident summaries of work the model has not actually read.
   Every claim in the recap traces to an issue or a comment.

---

## 4. Non-goals (v1)

1. **Action-item assignment.** The recap surfaces themes; it does not
   open issues, assign owners, or update labels. Action-item
   assignment is a v3 candidate (see §9 phased rollout) and requires
   trust earned by v1/v2 results before crossing into write actions.
2. **Sentiment scoring of comment threads.** Tempting and easy to
   ship; it is also the surface most likely to feel surveillance-y to
   ICs and is the cleanest v1 cut to make. Re-visit in v2 only if
   user research surfaces explicit demand from ICs themselves, not
   from managers.
3. **Performance review input.** The recap is not designed for, and
   must not be used as, individual performance evaluation input. The
   feature exists to support team retros, not 1:1s or calibration.
4. **Mandatory adoption.** v1 is opt-in at the team level. A team
   that doesn't want a recap doesn't get one; no recap is generated
   in the background "just in case."
5. **Cross-team aggregation.** The org-wide / skip-level surface is a
   v2 candidate gated on v1 adoption signal.

---

## 5. Proposed experience

### 5.1 Trigger and delivery

When a team's Cycle closes, Cycle Recap generates a markdown digest
for that team and delivers it via three surfaces, in priority order:

1. **In-app**: a new tab on the closed-cycle view ("Recap") that
   renders the markdown directly, alongside the existing cycle
   issues view.
2. **Slack / Linear's existing notification surface**: a single
   message posted to the team's configured Linear channel, with a
   link to the in-app recap.
3. **Email**: opt-in digest mirroring Pulse's existing email
   delivery shape.

The recap fires once per cycle close. Re-firing on edits to closed
issues is a deliberate v1 cut — the recap is a snapshot, not a live
document.

### 5.2 Sketch — the recap itself (markdown)

```markdown
# Cycle 47 Recap — Web Platform team
Closed 2026-05-16 · 14-day cycle · 23 issues planned, 19 shipped,
4 slipped · Median cycle time 4.1d (prev cycle: 3.8d)

## What shipped
- Auth: SSO admin console (ENG-2103) — shipped on day 11.
  Reviewer note in ENG-2103 flagged a follow-up: token-refresh
  edge case in §SSO/refresh, not user-facing in this cycle.
- Billing: invoice PDF rendering rewrite (ENG-2115, ENG-2117) —
  shipped together on day 13, two days after the planned cycle-mid
  ship date.
- [... 17 more, grouped by Project ...]

## What slipped
- Search: typo-tolerant query parser (ENG-2098) — moved to Cycle
  48. Two comment threads (ENG-2098 #14, #21) attribute the slip
  to an upstream dependency on the indexing pipeline rewrite
  (ENG-2071, not yet shipped). This is the third cycle in a row
  where ENG-2098 has been re-planned.
- [... 3 more, each with the cited comment that explains the
  slip ...]

## Themes worth a 5-min conversation
1. **Indexing pipeline is becoming a blocker.** Cited in ENG-2098,
   ENG-2104, ENG-2119 across this cycle. The same pattern appeared
   in Cycle 46's recap.
2. **Estimate drift on Billing work.** Two of the three Billing
   issues this cycle shipped 1–2 days past their planned date.
   Cycle 45 and 46 show similar patterns on the same project.

## Cycle quality snapshot
- Carryover: 4 issues (prev cycle: 2)
- Re-estimated mid-cycle: 6 issues (prev: 3)
- Scope added mid-cycle: 0 (prev: 1)
```

The recap is short on purpose. The two "themes worth a 5-min
conversation" section is the load-bearing surface — that is what
saves the EM time, and that is what changes the meeting.

### 5.3 Sketch — the team setting

```
Settings → Team → Cycles → Cycle Recap (new)
  [✓] Generate a recap when this team's cycle closes
  Delivery:
    [✓] In-app (always on if recaps are on)
    [✓] Slack / Linear channel: #team-web-platform
    [ ] Email digest to team members
  Theme detection:
    [✓] Surface recurring patterns across the last 4 cycles
    [Limit to 3 themes ▾]
  Privacy:
    [ ] Include comment-thread excerpts in the recap
       (off by default — the recap will link to threads but not
       quote them)
```

The Privacy section's default-off on comment-excerpt inclusion is
deliberate: the IC trust posture is built into the default, not
delegated to a setting the EM may or may not find.

### 5.4 Sketch — the cross-cycle pattern surface

A small "appeared in N of the last 4 cycles" badge on themes
surfaces compounding patterns without forcing the EM to compare
recaps by hand. This is the v1 form of the cross-cycle benefit named
in §3 goal 2; v2 would expand to a proper cross-cycle dashboard.

```
## Themes worth a 5-min conversation
1. Indexing pipeline is becoming a blocker.
   [appeared in 3 of last 4 cycles]
   Cited this cycle: ENG-2098, ENG-2104, ENG-2119
```

---

## 6. Proposed metrics

Metrics split into **leading** (visible within a week of ship) and
**lagging** (visible within a quarter). All metrics are *proposed* —
the PRD does not assert what the numbers will be, only what numbers
the team would track.

### 6.1 Leading indicators

- **Recap-on rate per team.** Of teams that have seen at least one
  recap, what fraction keep recaps enabled after 4 cycles. Target
  reads as "does the recap survive its own honeymoon."
- **In-app recap open rate.** Of generated recaps, what fraction
  are opened in-app within 24 hours of the cycle close. Splits by
  user role (EM / IC / skip-level) to confirm the primary-user bet.
- **Theme-acceptance rate.** Of "themes worth a 5-min
  conversation" surfaced, what fraction the EM marks "discussed in
  retro" (one-click affordance below the theme). Proxy for whether
  the theme detection is actually useful.
- **Comment-excerpt opt-in rate.** Of teams with recaps enabled,
  what fraction opt into the Privacy → "include comment-thread
  excerpts" setting. A high opt-in rate suggests teams trust the
  digest enough to surface raw comments; a low rate validates the
  default-off posture.

### 6.2 Lagging indicators

- **EM self-reported pre-retro prep time.** Quarterly in-product
  survey on the recap tab, one question, opt-in. Target: median
  drops materially from the pre-feature baseline.
- **Retro meeting duration.** Linear does not currently observe
  retro meeting duration directly; the PRD names this as a
  *cross-product* signal that would have to come from a calendar
  integration (Granola, Google Calendar) or self-report — and
  flags it in §9 open questions, not as a measurable v1 metric.
- **Cycle quality trend.** Carryover rate, re-estimate rate, and
  scope-add rate per team across cycles. These are *already*
  computable from Linear's data; the feature does not move them
  directly but the cross-cycle pattern surface (§5.4) should
  correlate with teams *acting* on the trends. Watch the slope.
- **Retention proxy.** Teams using Cycle Recap vs. matched control
  teams, on (a) team-level Linear DAU 90 days post-enablement and
  (b) cycle-completion rate. Standard A/B-style readout; needs
  internal Linear analytics infra not modeled here.

### 6.3 Counter-metrics

- **IC trust erosion signal.** Negative-sentiment comments on
  recap posts in the team's Linear channel, or a spike in
  comment-excerpt opt-outs after a recap surfaced an IC's name
  unfavorably. Watching for this is the explicit counter to the
  "do no harm" goal in §3.
- **Recap-correction rate.** Of generated recaps, what fraction
  the EM edits before sharing. High edit rate means the model is
  generating low-quality recaps; very low edit rate combined with
  low open rate means recaps are being rubber-stamped rather than
  read.

---

## 7. Risks and mitigations

### 7.1 Hallucination — model invents issue numbers, slip causes, or quotes

**Mitigation.** The recap generator is constrained to cite only
issue IDs that exist in the closed cycle's issue set, and to quote
only comment text it can paste-verify (i.e., the cited quote must
appear verbatim in the comment thread it cites — same constraint as
the rag-app build's verify.py citation discipline in this
portfolio). Issue IDs and quoted comments are rendered as
hyperlinks in the recap; the read-time check is one click.

### 7.2 Surveillance feel — ICs feel watched by the recap

**Mitigation.** Three structural defaults: (a) comment-excerpt
inclusion is off by default (§5.3), (b) no individual-engineer
sentiment scoring (§4 non-goal), (c) the recap does not call out
specific engineers as "fast" or "slow" — only issues and projects.
The recap is about the team's work, not the team's individuals.

### 7.3 Manager dependency — EMs stop reading the substrate

**Mitigation.** The recap surfaces the *themes*, not a
hide-everything-else summary. The full cycle's issue list remains
on the closed-cycle view exactly as it is today. The recap is an
on-ramp, not a replacement.

### 7.4 Recap quality drift across model versions

**Mitigation.** Internal eval set, per the evals-harness build's
five-rubric pattern in this portfolio (refusal / groundedness /
first-call-tool / termination / cost). Cycle Recap's rubric maps to
groundedness (every cited issue exists) and refusal (no
recap-generation when the cycle has too few issues to summarize
meaningfully — a recap of "3 issues, 1 shipped" is noise, not
signal).

### 7.5 Cost per recap is unbounded

**Mitigation.** Cost is bounded structurally: one recap per team
per cycle close, with a hard cap on input tokens per cycle (the
generator summarizes a fixed-window context, not the entire issue
history). Cost rubric monitoring per the evals-harness pattern.

### 7.6 Cycle Recap competes with Pulse rather than complementing it

**Mitigation.** Pulse rolls up to projects and initiatives on a
time cadence; Cycle Recap fires on the cycle-close event for one
team. The two surfaces are *additive* — Pulse summarizes upward,
Cycle Recap summarizes the team's own delivery layer. The opt-in
team setting (§5.3) makes the choice explicit; teams can use both.

---

## 8. Open questions

1. **What baseline number for EM pre-retro prep time?** This PRD
   asserts "30–60 minutes" from general PM intuition; the
   defensible source is in-product user research with EMs using
   Linear today. Path: 5–10 EM interviews before v1 ship, plus a
   one-question in-product survey after ship.
2. **What fraction of Linear teams currently run a weekly or
   biweekly retro?** Unknown publicly; would need an internal
   Linear analytics readout. If the fraction is low, the feature's
   addressable user count is correspondingly smaller and the
   rollout sequencing in §9 changes.
3. **Should the recap also fire on a manual "Generate recap now"
   action mid-cycle?** Tempting for ad-hoc readouts (Friday standup
   prep, mid-cycle check-in). Cut from v1 to keep the feature
   conceptually one-shot; revisit in v2 if a meaningful fraction of
   EMs ask for it.
4. **Retro meeting duration is the cleanest lagging metric but is
   not Linear-observable.** Pursuing it requires a calendar
   integration or a self-report mechanism. v1 can ship without it;
   if v2 wants it, a Linear Calendar-integration partnership is
   the path.
5. **Does the cross-cycle pattern surface (§5.4) need a separate
   cross-cycle dashboard, or does the badge on themes carry the
   freight?** v1 ships the badge; v2 decision pending v1 usage
   data.

---

## 9. Phased rollout plan

**Phase 0 (pre-build, 1–2 weeks).** 5–10 EM interviews on the
current pre-retro workflow. Establish the §8 question 1 baseline.
Confirm the §5.3 default-off comment-excerpt posture with at least
two ICs as a sanity check, not just with EMs.

**Phase 1 — Closed alpha (4–6 weeks).** Cycle Recap shipped to
~10–20 self-selected teams inside Linear itself (Linear's own
engineering teams are the obvious dogfood population, per Linear's
public stance that they ship their own product internally first).
Metrics: leading indicators §6.1 only; no public messaging.

**Phase 2 — Opt-in beta (6–8 weeks).** Opened to external Linear
customers via a single toggle in Team settings. Marketing surface
limited to a changelog entry, no large announcement. Metrics:
leading + counter-metrics §6.3. Gate to phase 3 on (a) recap-on
rate ≥ 60% after 4 cycles, (b) no counter-metric red flags.

**Phase 3 — GA (4 weeks to GA).** Default-off-but-discoverable on
the closed-cycle view for all teams. Pulse-style email opt-in.
Linear.app/ai marketing surface updated to name Cycle Recap
alongside Pulse, Triage Intelligence, and the other five AI
features named in §1.1.

**Phase 4 — v2 candidates (not in v1 ship, named for editorial
clarity).** Cross-cycle dashboard. Skip-level / org-wide recap.
Comment-excerpt inclusion default review. Action-item assignment
(v3, gated on v2 trust signal).

**Explicit rollout non-goals.** No paid-tier gating in v1 or v2;
Cycle Recap is a Linear AI surface, not a SKU lever. No new
permission model — recap visibility follows the team's existing
issue visibility (private team's recap is private). No
public-roadmap commitment in this PRD; the phased plan is the PM
proposal, not a Linear commitment.

---

## 10. If Linear ships this between snapshot date and read date

If a reviewer reads this PRD after Linear has shipped Cycle Recap
or a near-equivalent, the PRD's value collapses from "feature
proposal" into "the PM author had read the substrate well enough
to predict where the product would go." That is itself a portfolio
signal; the PRD does not retract in that case, but the §11 Sources
section should be re-read with that update in mind.

The clearest signal that this has happened: a new feature named on
linear.app/ai that fires at cycle close. Pulse extending to cover
cycle close would be the soft-shipped form of the same idea.

---

## 11. Sources & observation snapshot

Every claim about Linear's current behavior in §1.1 and elsewhere
is anchored to one of the following:

- **linear.app/ai** (observed 2026-05-17) — source for the five
  currently-shipped AI feature names quoted in §1.1: Triage
  Intelligence, Linear for Agents, Linear MCP, AI-powered search,
  Pulse updates. Quoted feature names match Linear's marketing
  copy exactly.
- **linear.app/docs** (observed 2026-05-17) — source category for
  any claim about Linear's Cycle, Project, Issue, or Team
  primitives. Specific sub-URLs not pinned in this draft because
  the proposed feature targets the well-established Cycle primitive
  rather than a docs-edge behavior.
- **linear.app/method** (observed 2026-05-17) — source category
  for any claim about Linear's stated way of working. Cited as
  background for the cycle-as-atomic-delivery-unit framing in
  §1.1, not for any specific quote.
- **Author's PM reasoning** — anything labeled "proposed,"
  "target," "the PM bet," "the PM proposal," or appearing in §3
  goals, §5 proposed experience, §6 proposed metrics, §7 risks
  and mitigations, §8 open questions, §9 phased rollout. These are
  the PM author's own constructs, not Linear claims.

No internal Linear information, no fabricated user quotes, no
invented usage metrics, no roadmap claims that go beyond publicly
stated direction. Where a number is needed and unknown (most
visibly §8 question 1's EM prep-time baseline), the PRD names the
source the PM or interviewer would consult to fill it in — never a
placeholder presented as fact. This is the OBJECTIVE.md
no-fabrication guardrail restated at the artifact level, and the
binding rule for any future PRD in `prds/`.

[^ai]: https://linear.app/ai (observed 2026-05-17). Feature names
       quoted exactly: "Triage Intelligence," "Linear for Agents,"
       "Linear MCP," "AI-powered search," "Pulse updates."
