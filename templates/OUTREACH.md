# AI PM Outreach Scaffold

A populatable scaffold for the front-of-funnel outreach that feeds
`../templates/INTERVIEW_TRACKER.md`. Three short DM variants for the three
materially different channels — cold, referral-ask, and dormant
re-engagement — for the AI PM search defined in `../OBJECTIVE.md`. Replace
every `_<placeholder>_` italic span with a real value before sending.
Nothing in this file is auto-populated — the agent does not invent
companies, people, prior relationships, or context you do not have. See
`../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. **Pick exactly one variant per message** and delete the other two
   before sending. The three variants (cold / referral-ask / dormant
   re-engagement) are mutually exclusive by relationship state — leaving
   more than one in the draft advertises the scaffold and forfeits the
   relationship-specific signal.
2. **Target length: 30–80 words per DM** (signature lines do not count).
   This is materially shorter than `../templates/COVER_LETTER.md`'s
   250–400-word band because DMs are read on mobile, in a notifications
   pane, in three seconds — anything longer gets skimmed for the ask and
   the rest is wasted. If your draft is over 80 words, the first thing
   to cut is the self-introduction (one phrase, not a sentence) and the
   second is any qualifier on the ask ("if you have time" / "no pressure"
   — these read as hedging, not politeness).
3. **One ask per DM**, named explicitly and time-bounded. The default ask
   for variants A and C is a 15-minute intro call within the next two
   weeks. For variant B the ask is the introduction itself, not the
   eventual call. A DM with two asks lands as a take-home and is the
   leading cause of no-reply.
4. **The hook is the highest-leverage clause** — a specific, falsifiable
   observation about the recipient's company AI product (variant A) or a
   specific reason for the referral (variant B) or a specific reason for
   the re-engagement (variant C). Generic praise ("love what you're
   doing with AI") is the cheapest possible signal and the easiest to
   discount. The hook should pattern-match the company-specific
   observation slot in `../templates/COVER_LETTER.md`'s opener — see
   that file's rule 5 for the shape.
5. **Reference the repo, do not restate the resume.** A DM that quotes a
   `_<repo URL>_` (or a single artifact link, e.g.
   `_<repo URL>_/teardown-prd/cursor-teardown.md`) and lets the
   recipient click is materially stronger than a DM that lists three
   shipped projects in prose — same single-source-of-truth discipline
   `../templates/COVER_LETTER.md`'s paragraph 3 uses for the resume.
6. **Channel hygiene: plain text, no Markdown, no link previews chasing
   tracking parameters.** LinkedIn renders DMs in a constrained pane;
   anything that survives a copy-paste cleanly is safe. If you are
   sending via email instead of LinkedIn, the same body works — just
   add a subject line of the form **`AI PM intro — _<Your full name>_
   ↔ _<Their company>_`** and keep everything else identical.
7. **Send one, then stop.** A second DM if the first did not get a
   reply is a follow-up scaffold, not this scaffold — and a separate
   future iteration if outbound cadence justifies it (see
   `../DECISIONS.md` for the deferral rule). The single most common
   misuse of an outreach scaffold is sending the same hook twice
   within a week; the second send burns the contact for both the
   current and future search.

## Variant A — Cold outreach to a PM (no prior relationship)

Use when you have identified a PM at a target AI-native company or an
established product with AI features (Bucket 1 or 2 per
`../templates/INTERVIEW_TRACKER.md`) and have no warm intro path.
Target length: **40–70 words**.

> Hi _<First name>_ — I'm an AI PM looking at the _<Role title or team
> shape: e.g. "AI features team" / "AI Platform PM seat">_ at
> _<Company>_ and noticed _<specific product observation in one clause:
> a UX choice, a missing affordance, a trade-off you can name from the
> public surface — pattern-match the COVER_LETTER opener>_. I've been
> shipping AI work end-to-end (_<repo URL>_), including a teardown PRD
> of _<product>_ that proposes three specific shipments. Open to a
> 15-min chat in the next two weeks?

**Why this works.** The first sentence proves you read the product
rather than the company tagline. The second sentence is the credential
in one phrase plus the repo as the proof surface, not in prose. The
third sentence is one ask, time-bounded, low-stakes. Nothing else.

## Variant B — Referral ask (to a known connection)

Use when you know someone who works at, or has a strong connection to,
a target company. The ask is the *introduction*, not the call — the
call happens after the intro lands. Target length: **50–80 words**.

> Hi _<First name>_ — hope _<one-clause acknowledgement of something
> current in their life: a recent post, a project they shipped, a move
> they made — only if you actually have one; otherwise omit and go
> straight to the ask>_. I'm targeting AI PM roles and _<Company>_'s
> _<specific team or surface — name the seat, not the company>_ is
> high on my list. Would you be open to introducing me to
> _<Hiring manager / PM name if known, otherwise "whoever owns that
> roadmap on your side">_? Happy to send a forwardable blurb so the
> intro is one-click for you.

**Why this works.** The opening acknowledgement (if used) is specific
and current, not "hope you're well." The ask is named (intro), the
target is named (specific seat, specific person if known), and the
load is named as low (you'll write the blurb). The forwardable-blurb
offer is what converts a referral ask from a chore for the recipient
into a copy-paste — without it, the response rate halves.

### Forwardable blurb (to attach in a follow-up to your contact)

Use this once the contact says yes. Send as a second message so the
contact can forward it without editing.

> Here's a one-paragraph version you can forward as-is:
>
> _<Your full name>_ is an AI PM with _<one phrase on years/seat,
> e.g. "five years of PM experience, the last two on AI features">_,
> looking at the _<Role title or team shape>_ at _<Company>_. He/she
> has been shipping AI work in the open at _<repo URL>_ — three
> production-shaped builds (RAG, tool-use agent, evals harness) and a
> six-section teardown PRD of _<product>_. _<One sentence on the
> specific reason for the interest in this team, lifted from your
> COVER_LETTER paragraph 4>_. Open to a 15-min screen at
> _<Hiring manager / PM>_'s convenience over the next two weeks.

## Variant C — Re-engagement (dormant connection, 6+ months silent)

Use when reaching back to a former colleague, classmate, or past
networking contact you have not spoken to in 6+ months. The trap is
making the message read as transactional ("hi I haven't talked to you
in a year and I need a favor"). The defense is leading with the share,
naming the silence honestly, and asking small. Target length:
**50–80 words**.

> Hi _<First name>_ — long overdue. I've been heads-down building AI
> PM work I think you'd find interesting (_<single specific artifact
> link, not the repo root: e.g. the teardown PRD URL or one build's
> README URL>_) and you came to mind because _<one specific reason:
> a past project you worked on together, a conversation you had, a
> domain they care about — only if it's true; if you can't name one,
> use Variant A and treat them as a cold contact instead>_. Would
> love to catch up — 15 min in the next two weeks if you're around?

**Why this works.** The first clause names the silence ("long
overdue") so the recipient does not have to. The middle clause leads
with a share (an artifact link the recipient can open right now)
rather than an ask, which is what distinguishes a re-engagement from
a transactional reach-out. The specific reason for thinking of them
is the load-bearing clause: if you cannot name a real reason, you do
not actually have a dormant connection here — you have a cold contact
and Variant A is the right scaffold.

## After you send

1. Log every send in `../templates/INTERVIEW_TRACKER.md`'s **Outreach
   log** section the same day. The log row is what later becomes a
   pipeline row once the contact responds — keeping it current is what
   makes the Day-30 rollup honest about outbound volume vs. interview
   performance.
2. Do not send a second DM to the same contact within the same week.
   A follow-up scaffold for the no-reply case is intentionally
   deferred — see `../DECISIONS.md` for the deferral rule and the
   threshold at which a follow-up scaffold ships.
3. When a contact responds and a conversation opens, the next
   artifact you need is `../templates/COVER_LETTER.md` (for the formal
   application) and `../templates/RESUME.md` (as the leave-behind),
   not another DM. The outreach scaffold ends at "they replied."

---

_Before sending any DM: re-read for any remaining italic
placeholders. The fastest grep is `_<` — if it appears anywhere in the
draft, the message is not ready to send. Same convention as
`../templates/INTERVIEW_TRACKER.md`, `../templates/RESUME.md`, and
`../templates/COVER_LETTER.md`, so one regex (`_<.*>_`) validates all
four scaffolds._
