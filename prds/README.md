# Product Requirements Documents — Portfolio Index

The index for the `prds/` directory: PRDs proposing AI features on
recognized products, written as portfolio companions to the Cursor
teardown at [`../teardown-prd/cursor-teardown.md`](../teardown-prd/cursor-teardown.md).
The teardown answers *"here's how I'd analyze a live AI product"*;
the PRDs in this directory answer *"here's a feature I'd ship."*
The two shapes pair: a hiring manager who reads both gets both
analysis and authoring craft in one portfolio.

The directory currently holds one PRD (`linear-ai-retro-summarization.md`,
shipped 2026-05-17 under NEXT_WORK item 8 sub-checkbox 1). NEXT_WORK
item 8 deliberately scopes this run to one PRD; additional PRDs are
out of scope for this list and would be added by the user, not the
agent.

---

## The PRDs in this directory

| File | One-line product framing | NEXT_WORK |
| --- | --- | --- |
| [`linear-ai-retro-summarization.md`](linear-ai-retro-summarization.md) | *Cycle Recap* — an AI-generated weekly retro summary that posts at cycle close to a per-team digest surface, recapping what shipped/slipped and seeding the team retro meeting. Bucket-2 feature on [Linear](https://linear.app), primary user engineering manager. | item 8 sub-checkbox 1 |

---

## The no-fabrication rule for PRDs

Every PRD in this directory must obey the same no-fabrication
discipline the portfolio uses elsewhere — restated here at the PRD
artifact level because PRD prose tempts fabrication more than other
artifact types (a missing usage metric reads as a hole in a PRD,
where the same hole reads as honest scoping in a teardown).

1. **No invented internal metrics.** A PRD proposing a feature for a
   product the author doesn't work on cannot cite that product's
   internal usage data — DAU, retention, conversion, NPS, none of
   it. Where a number is needed and unknown, name the source the PM
   or interviewer would consult to fill it in (e.g., *"Linear's own
   product analytics — out of reach for this PRD; if working at
   Linear the PM would baseline current EM retro prep-time"*) rather
   than presenting a placeholder as fact.
2. **No fabricated user quotes.** No invented testimonials, no
   composite-persona quotes presented as real user voice. If the PRD
   needs user-voice texture, it must be either (a) flagged as
   *illustrative, not sourced* in the sentence around it, or (b)
   sourced from a publicly-attributable place (a podcast quote, a
   blog post, a public tweet with URL + observation date in the
   §Sources block).
3. **No invented roadmap.** A PRD proposes what the *PM author*
   would ship; it does not claim what the target company *will*
   ship. The phased rollout in the PRD is the PM's proposal, not a
   commitment by anyone at the target company.
4. **Source-anchor every observable behavior claim.** Every claim
   about the target product's current behavior — feature names,
   surface positions, what fires when — must be anchored to a URL
   and an observation date in a §Sources block at the end of the
   PRD. Feature names quoted from marketing pages must match the
   marketing copy exactly, with a footnote or inline anchor pointing
   at the URL.
5. **Date the snapshot.** Live products evolve; a PRD written
   against a snapshot becomes stale. State the observation date
   prominently at the top of the PRD so a future reviewer can re-
   verify against the live product at read time. If the target
   product has shipped the proposed feature between snapshot and
   read date, the PRD's value collapses from *"feature proposal"*
   into *"the PM author had read the substrate well enough to
   predict where the product would go"* — that is itself a portfolio
   signal; see `linear-ai-retro-summarization.md` §10 for the
   canonical handling of that case.

The five sub-rules are orthogonal binding levels: locking only one
(say, the source-anchoring rule) leaves the others fragile to drift.
This decomposition mirrors the no-fabrication rule's five-level
structure in `interview-prep/` (slot / citation / question-selection
/ anchoring-grammar / rubric-as-checklist — see the consolidating
DECISIONS entry at item 7 sub-checkbox 6) and the four-level
structure in `rag-app/corpus/SOURCES.md` (URL / content / license /
retrieval-method — see the consolidating DECISIONS entry at item 5
sub-checkbox 5).

---

## PRD section structure as portfolio convention

The Linear PRD ships with these sections, in this order:

1. Scope decision (what's proposed + adjacent surfaces explicitly
   named out)
2. Problem (observable gap + the cycle close as a substrate)
3. Users + JTBD (primary / secondary / tertiary user named with
   "when X, I want Y, so that Z" framing)
4. Goals
5. Non-goals
6. Proposed experience (with markdown sketches inline, not images)
7. Proposed metrics (leading + lagging + explicit counter-metrics)
8. Risks + mitigations
9. Open questions (each named with the source that would resolve
   it)
10. Phased rollout plan
11. *If the target ships this between snapshot and read date*
12. Sources & observation snapshot

The 4–6-page rendered length NEXT_WORK names is a guideline, not a
hard cap — substance and structure over arbitrary trim. Future PRDs
in this directory should follow the same section list so a reader
who has read one PRD can navigate any other in the directory by
section number; locking section structure as a convention is what
makes a multi-PRD directory readable, where each PRD adopting its
own structure would force a reader to re-orient per file.

---

## How to use this index

1. **Read the PRD itself.** The index file links the PRD; it does
   not summarize it. A summary in the index would either drift from
   the PRD's actual content as the PRD evolves, or duplicate work
   the PRD's own §1 / §3 already does.
2. **Pair with the teardown for portfolio readings.** A reader who
   wants to see "analysis + authoring" should read
   [`../teardown-prd/cursor-teardown.md`](../teardown-prd/cursor-teardown.md)
   first (analysis of a live product) and then this directory's PRD
   (authoring a feature for a different live product). The pairing
   is deliberate: different products, different shapes, same author.
3. **Adding a future PRD.** A future PRD must obey the no-
   fabrication rule above and follow the section structure named
   above. Add a row to the table in this README, with one-line
   product framing and the NEXT_WORK identity that authorized it.
   The agent does not add PRDs to this directory unilaterally — a
   new PRD requires a new NEXT_WORK item the user owns.

---

## Source of truth & cross-links

- The PRD itself:
  [`linear-ai-retro-summarization.md`](linear-ai-retro-summarization.md) —
  carries its own §11 Sources block with every Linear behavior
  claim anchored to a URL + observation date.
- The portfolio's top-level index:
  [`../README.md`](../README.md) — names this PRD in the
  milestone map alongside the three Day-10 builds and the Day-20
  teardown.
- The teardown PRD that this directory's PRDs pair with:
  [`../teardown-prd/cursor-teardown.md`](../teardown-prd/cursor-teardown.md).
- The chronological design log:
  [`../DECISIONS.md`](../DECISIONS.md) — carries the no-fabrication
  rule (search for "no-fabrication"), the product+feature pick
  rationale for the Linear PRD, and the consolidating entry for
  NEXT_WORK item 8 when it ships (sub-checkbox 3).
- The objective the portfolio serves:
  [`../OBJECTIVE.md`](../OBJECTIVE.md) — names the Bucket-2 framing
  the Linear PRD's product pick exploits.
- The active worklist:
  [`../NEXT_WORK.md`](../NEXT_WORK.md) — item 8 is the parent for
  this directory; sub-checkboxes 2 (this file) and 3
  (consolidating DECISIONS entry) close the item.

This directory is `prds/`, not a deliverable for any specific
employer. The PRDs propose features on publicly-observable products
to demonstrate PM craft; they are not affiliated with the named
companies and make no claim about those companies' actual roadmaps.
