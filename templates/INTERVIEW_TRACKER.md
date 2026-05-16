# Interview Loop Tracker

A populatable tracker for the AI PM job search defined in `../OBJECTIVE.md`.
Replace every placeholder row with a real one before relying on the rollup.
Nothing in this file is auto-populated — the agent does not invent companies,
contacts, or pipeline state. See `../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. One row per role you have meaningfully engaged with (applied, recruiter
   contact, referral submitted, inbound). Do not log roles you only saved to
   read later — that is a separate "watchlist" concern and clutters the
   rollup.
2. Update the **Stage** and **Next action** columns whenever something
   changes. The rollup at the bottom reads from the Stage column, so stale
   stages produce a misleading dashboard.
3. **Bucket** maps to the scope section of `../OBJECTIVE.md`:
   - `B1` — AI-native company, AI is the product
   - `B2` — Established product, AI features inside it (PRIORITY per objective)
   - `B3` — Adjacent bridge role (PMM, TPM, technical solutions) explicitly
     pointed at an AI PM seat within 6–12 months. Out-of-scope generic SaaS
     PM roles do not belong in this tracker — track those separately or not
     at all.
4. **Stage values** (use these exact strings so counts work):
   `sourced` → `applied` → `recruiter-screen` → `hiring-manager` →
   `panel` → `final` → `offer-verbal` → `offer-written` → `accepted`.
   Terminal off-ramps: `rejected`, `withdrew`, `ghosted-30d`.
5. **Next action / due date** is the single most important field. If you do
   not know what the next action is, the answer is almost always "follow up
   with [name] by [date]" — write that down.

## Active pipeline

| # | Company | Role title | Bucket | Source | Stage | Next action | Due | Comp range | JD link | Recruiter / contact | Notes |
|---|---------|------------|--------|--------|-------|-------------|-----|------------|---------|---------------------|-------|
| 1 | _<Company name>_ | _<Role title>_ | B2 | _<inbound \| referral \| direct apply \| recruiter outbound>_ | sourced | _<what you will do next>_ | YYYY-MM-DD | _<$base + equity if known>_ | _<URL>_ | _<name, channel>_ | _<JD highlights, AI scope, red flags>_ |
| 2 | _<placeholder — delete this row when you add a real one>_ |  |  |  |  |  |  |  |  |  |  |
| 3 | _<placeholder>_ |  |  |  |  |  |  |  |  |  |  |

Add rows freely. Keep this table sorted by Stage descending (offers and
finals at the top) so the most load-bearing rows are visible first.

## Closed / off-ramp

Move rows here once they hit a terminal stage (`rejected`, `withdrew`,
`ghosted-30d`, or `accepted` for the one you took). Keeps the active table
honest about real pipeline size.

| Company | Role title | Bucket | Final stage | Closed date | Reason / learning |
|---------|------------|--------|-------------|-------------|-------------------|
| _<empty>_ |  |  |  |  |  |

## Rollup — map to OBJECTIVE.md milestones

Update these counts manually from the active table. The numbers in
parentheses are the Day 30 targets from `../OBJECTIVE.md`.

- **Active loops** (target: 10+): `0`
- **In final round or beyond** (target: 3+): `0`
- **Verbal offers in hand** (target: 1+ as fallback success): `0`
- **Bucket 2 share of active loops** (objective prioritizes B2): `0 / 0`

If active loops < 10 by Day 30, outreach volume is the gap, not interview
performance — see the assumptions section of OBJECTIVE.md before optimizing
the funnel further down.

## Outreach log (optional)

If you want to track outbound that has not yet produced a response, use
this section. Once a thread becomes a real engagement, promote it into the
active pipeline table above and delete the log row.

| Date sent | Company | Person | Channel | Message hook | Response? |
|-----------|---------|--------|---------|--------------|-----------|
| YYYY-MM-DD | _<placeholder>_ |  |  |  |  |
