# Target Companies — AI PM Bucket-Aware Sourcing List

A populatable sourcing scaffold that sits **upstream of**
`../templates/OUTREACH.md` for the AI PM search defined in
`../OBJECTIVE.md`. The point of this file is to make the Day-30
target ("10+ active loops") arithmetically reachable by holding a
disciplined inventory of companies worth a DM — not to write the
DM (that is OUTREACH's job) and not to log an active engagement
(that is `../templates/INTERVIEW_TRACKER.md`'s job). Replace every
`_<placeholder>_` italic span with a real value before treating
the row as researched. Nothing in this file is auto-populated —
the agent does not invent companies, AI surfaces, contacts, or
hiring state. See `../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. **Build the list to 30–50 rows before sending the first DM.** The
   funnel math is rough but load-bearing: at typical AI PM cold-
   outreach response rates (~10–15% for warm hooks, higher for
   referrals), a 30–50-row inventory is what makes 10+ active loops
   reachable inside the Day-30 window without depending on a single
   referral landing. Lists shorter than ~25 rows force you to
   overweight whichever rows you found first; lists longer than ~50
   rows turn researching the next row into procrastination on
   reaching out to the rows you already have.
2. **One row per company, not per role.** A company that has shipped
   three AI PM postings still counts as one row — the relationship
   you build with that company is portable across roles. Track which
   specific role you are reaching out about in the **Role** column;
   if the company opens a second role later, edit the row rather
   than duplicate it.
3. **Status workflow: `not-researched` → `researched` →
   `outreached` → `promoted-to-tracker`.** Once a contact responds
   and a real conversation opens, promote the row into
   `../templates/INTERVIEW_TRACKER.md`'s **Active pipeline** table
   and delete it from this file. This file is the *pre-engagement*
   inventory; the tracker is the *engaged* inventory. Mixing the
   two collapses the diagnostic value of both.
4. **Bucket priority: B2 > B1 > B3** — same vocabulary as
   `../templates/INTERVIEW_TRACKER.md` (`B1` AI-native, `B2`
   established product with AI features (PRIORITY), `B3` adjacent
   bridge role pointed at an AI PM seat within 6–12 months).
   Out-of-scope generic SaaS PM roles do not belong in this file
   either. If at least half your rows are not B2, the list is
   skewed away from the objective's stated priority — re-balance
   before sending DMs, not after.
5. **The Fit hypothesis column is the highest-signal field.** One
   sentence on *why you specifically* are a fit for *this specific*
   AI surface — the same sourced-observation → trade-off rhetoric
   `../teardown-prd/cursor-teardown.md` uses, scaled down to a
   single clause. "Strong AI team" is not a fit hypothesis; "Their
   inline-edit UX has the same review-friction problem the Cursor
   teardown's §1.1 names, and my evals-harness build maps to the
   methodology gap their public roadmap implies" is. If you cannot
   write a fit hypothesis at this density, the row is not yet
   `researched` — move it back to `not-researched` and either do
   the research or drop the row.

## Discovery sources (where candidate rows come from)

A non-exhaustive set of categories where AI PM postings and
AI-PM-shaped companies surface. Names below are pointers to real
public services and conventions, not endorsements or invented
listings — go look, do not trust this file as the source of truth
on what each service contains today.

- **AI PM job aggregators and PM-specific boards.** Wellfound (née
  AngelList Talent), Pallet boards run by AI-focused funds, the PM
  channel on Hampton / On Deck / Reforma communities, "Who's
  hiring" threads on AI-focused Substacks. Filter aggressively by
  bucket — most aggregator hits are B1 (AI-native) and the
  objective prioritizes B2.
- **VC portfolio pages.** a16z, Sequoia, Index, Greylock, Lightspeed
  portfolio pages each list their AI investments; cross-reference
  against the fund's recent AI-thesis posts to filter to companies
  in growth phases that hire PMs (Series A and later, not pre-seed).
- **LinkedIn structured search.** Title contains "Product Manager"
  AND keyword "AI"/"ML"/"LLM"/"AI features" AND filter by 1st/2nd-
  degree connections — this surface is where the **referral-ask**
  variant of OUTREACH actually pays off, because the connection
  graph is the input the cold-DM scaffold cannot synthesize.
- **Direct competitive scans.** For each Bucket 2 company already
  on your radar, scan their nearest five public competitors: if
  Company X shipped an AI feature you can name, the competitor list
  is implicitly hiring against the same scope. The Cursor teardown
  PRD's §1–§3 are themselves a worked example of the rhetoric this
  scan produces.
- **AI-PM-shaped communities and newsletters.** The published AI PM
  Slack/Discord groups, newsletters explicitly framed as AI-PM
  career (not generic AI hype), and the "I'm hiring" tweet threads
  from AI PMs in your existing follow graph. These produce the
  warmest hooks because the company is sourcing from a community
  that has self-selected on bucket fit.
- **Inbound — track it here too.** Recruiter outbound that hits
  your LinkedIn or email belongs as a row in this file the same day
  it arrives. Inbound rows ship straight to `outreached` status
  (the recruiter has already reached out; the next action is your
  reply, not theirs).

## Brainstorm prompts (when the list is stuck below 30 rows)

If the list is under 30 rows, the problem is almost never "no
companies are hiring AI PMs" — it is that the search has narrowed
to one bucket or one category of company. Use these prompts to add
diversity before optimizing density:

1. **Five mid-stage AI-native companies (Series A–C) whose PM org
   I can name at least one person at, or whose product I have used
   in the last six months.** B1 bucket — these are the warm-graph
   B1 entries.
2. **Five established SaaS products that shipped a non-trivial AI
   feature in the last twelve months** (e.g. Notion AI, Linear AI,
   Atlassian Intelligence, Asana Intelligence, GitHub Copilot
   inside the GitHub PM org, Figma's AI features, etc.). B2 bucket
   and PRIORITY — these are the volume hits.
3. **Five Big Tech AI-product teams with public PM postings** (the
   AI-features org inside Microsoft / Google / Amazon / Meta /
   Apple, plus the model-lab PM seats at OpenAI / Anthropic /
   DeepMind / xAI). Mix of B1 and B2 depending on whether the
   team's AI surface is product or platform.
4. **Five vertical AI plays in domains I have a credibility hook
   in** (legal, health, finance, dev tools, sales, support, ops) —
   B1 or B2 depending on whether AI is the core product or a
   feature inside the vertical product.
5. **Five PMs at AI companies in my 1st- or 2nd-degree network**
   whose product I have a substantive opinion about. Track the
   *person* in the Contact path column even if the role is
   speculative — when the company posts a fit role, you already
   have a warm path.

Five prompts at five rows each is twenty-five candidates; the last
five to reach 30 come from inbound and the competitive scans of
rows you already added.

## Quality bar — when to cut a row instead of researching it

Cut a row (delete or move to **Dropped**) if any apply. Do not let
a row sit at `not-researched` for more than a week — either
research it or cut it; a 50-row list that is 40% stale is worse
than a 30-row list that is 100% live.

- **No identifiable AI surface.** The company's website lists "AI"
  as a buzzword but you cannot name the specific product, feature,
  team, or model in one sentence. Cut.
- **Out of scope per OBJECTIVE.md.** Generic SaaS PM with no AI
  component; contract under six months; B3 bridge role with no
  explicit AI PM seat pathway within 6–12 months. Cut.
- **Bucket overweight already.** If your list is 60%+ B1 and you
  add another B1 row, cut the weakest existing B1 row first — the
  objective prioritizes B2, and a list that systematically over-
  samples B1 will produce a Day-30 rollup biased away from the
  priority.
- **No realistic contact path.** Zero existing connections, no
  recent posts to anchor a cold-DM hook on, and no specific public
  product observation you can falsify. A row with no contact path
  is a wish, not a target.
- **You would not take the role at any reasonable offer.** Be
  honest about this one early. Carrying a row you would decline at
  offer stage is sunk-cost research and a slot a real target could
  occupy.

## Target list

| # | Company | AI surface (one phrase) | Role / link | Bucket | Fit hypothesis (one sentence) | Contact path | Status | Date added | Notes |
|---|---------|-------------------------|-------------|--------|--------------------------------|--------------|--------|------------|-------|
| 1 | _<Company name>_ | _<what they ship that's AI in one phrase>_ | _<role title and JD URL, or "no public role — speculative">_ | B2 | _<why YOU specifically, in one sentence — sourced observation → trade-off rhetoric>_ | _<cold \| referral via _<name>_ \| inbound recruiter _<name>_>_ | not-researched | YYYY-MM-DD | _<JD highlights, AI scope, red flags, last touched>_ |
| 2 | _<placeholder — delete this row when you add a real one>_ |  |  |  |  |  |  |  |  |
| 3 | _<placeholder>_ |  |  |  |  |  |  |  |  |
| 4 | _<placeholder>_ |  |  |  |  |  |  |  |  |
| 5 | _<placeholder>_ |  |  |  |  |  |  |  |  |

Add rows freely. Keep this table sorted by **Status** descending
(`promoted-to-tracker` rows are removed daily; `outreached` rows
sit at the top so the no-reply window is visible at a glance;
`researched` rows below; `not-researched` rows at the bottom as
the working brainstorm pool).

### Status vocabulary (use these exact strings so counts work)

- `not-researched` — added to the list, no research done yet.
  Default state for brainstorm-prompt entries.
- `researched` — you can name the AI surface, the specific role
  (or confirmed-no-public-role), and have written a one-sentence
  fit hypothesis. Ready to outreach.
- `outreached` — DM/email/application sent. Record the date in
  Notes. Cross-reference: also log the send in
  `../templates/INTERVIEW_TRACKER.md`'s **Outreach log** section
  the same day (single source of truth on what was sent and when;
  this file holds the *target*, the tracker holds the *send*).
- `promoted-to-tracker` — contact responded, real engagement
  opened. Delete the row from this file and add it to the
  tracker's **Active pipeline** table within 24h. Carrying a
  promoted row in both files diverges the two diagnostic counters
  and is the leading cause of double-counting at the Day-30
  rollup.
- **Off-ramp:** `dropped` — moved out of the active table with a
  one-line reason in Notes (per the Quality bar section above).

## Dropped (off-ramp — keep visible for one week, then delete)

A row sits here for ~one week after cutting so the reason for the
cut stays auditable, then gets removed. The point is not to
maintain a graveyard; it is to make sure the same row does not
silently reappear on next week's brainstorm because the cut
reason was forgotten.

| Company | Original bucket | Date dropped | Reason (one line) |
|---------|-----------------|--------------|--------------------|
| _<empty>_ |  |  |  |

## How this feeds the rest of the kit

This file → `../templates/OUTREACH.md` → `../templates/COVER_LETTER.md`
and `../templates/RESUME.md` → `../templates/INTERVIEW_TRACKER.md`.

- **Researched rows feed OUTREACH.** Pick the DM variant that
  matches the **Contact path** column (cold → Variant A,
  referral-via-name → Variant B, dormant connection → Variant C),
  then quote the **Fit hypothesis** as the hook clause in the
  selected variant. The fit hypothesis is the field that makes
  the hook clause writeable in 30 seconds rather than 30 minutes.
- **Outreached rows feed the tracker's Outreach log.** Same-day
  logging is what keeps the Day-30 rollup honest about outbound
  volume vs. interview performance — if active loops < 10 by
  Day 30, the rollup needs to be able to answer "did we send
  enough" with a single grep, which means the log has to be live.
- **Promoted rows feed the tracker's Active pipeline.** This is
  the only transition that *deletes* from this file. Keeping a
  promoted row here would mean two files own the same engagement,
  and the next status update would diverge between them within
  one cycle. Tracker is the single source of truth on engaged
  pipeline.
- **Cover letter and resume are downstream of the tracker, not
  this file.** You do not write a cover letter for a `researched`
  row — you write it when a real application is in flight or a
  warm intro has happened. Drafting cover letters off this file
  is the failure mode that turns the search into busywork.

## Rollup — list health (update manually)

The numbers in parentheses are list-health targets, not Day-30
milestones (the Day-30 milestones live in
`../templates/INTERVIEW_TRACKER.md`'s rollup, which is the
authoritative dashboard).

- **Total candidates** (target: 30–50): `0`
- **B2 share** (target: ≥ 50% per OBJECTIVE.md priority): `0 / 0`
- **Researched share** (target: ≥ 60% of total — the rest are the
  fresh brainstorm pool): `0 / 0`
- **Outreached this week** (target: 5–10 sends/week sustained, per
  the OUTREACH "send one, then stop" rule per contact): `0`
- **Promoted to tracker this week**: `0`
- **Dropped this week**: `0`

If **Total candidates < 30**, the gap is sourcing, not outreach —
run the **Brainstorm prompts** section above before drafting any
DMs.

If **Outreached this week < 5** for two consecutive weeks, the gap
is cadence, not list quality — set a daily outreach quota (2–3
sends/day from the `researched` pool) rather than optimizing the
list further.

---

_Before treating any row as `researched`: re-read for any remaining
italic placeholders. The fastest grep is `_<` — if it appears
inside a row, that row is still a placeholder, not a real target.
Same convention as `../templates/INTERVIEW_TRACKER.md`,
`../templates/RESUME.md`, `../templates/COVER_LETTER.md`, and
`../templates/OUTREACH.md`, so one regex (`_<.*>_`) validates all
five scaffolds._
