# Project Objective: Land an AI PM role within 90 days

By 2026-06-14, secure a full-time AI Product Manager role, prioritizing Bucket 2 (AI features inside established products) as the highest-volume and fastest entry point. Primary success is a signed offer. Secondary fallback, if the primary slips, is being in 3+ final-round interview loops with at least one verbal in hand by the deadline.

## Scope

**In scope:** roles where AI is the product or a core feature — titles like "AI PM," "PM, AI Platform," "ML PM," "PM, AI Features," "Founding PM" at AI-native startups.

**Out of scope:** generic SaaS PM roles with no AI component, individual-contributor engineering work, contracts under six months. Adjacent bridges (PMM, TPM, technical solutions) are only acceptable if explicitly pointed at an AI PM seat within 6–12 months.

## Milestones

- **Day 10:** AI fluency made visible. Three shipped builds on GitHub with writeups — a RAG application, a tool-use agent, and an evals harness. The point isn't the code; it's having something to point to in interviews and on LinkedIn.
- **Day 20:** Portfolio artifact published. A teardown PRD of a real, live AI product (what's working, what's broken, what to ship next, with proposed metrics). One strong piece, not five mediocre ones. This becomes your interview leave-behind.
- **Day 30:** Active in 10+ target-company interview loops, with at least one final round.

## Operating principle

Optimize for offer quality first, time-to-offer second. Don't take a non-AI PM role just to fill the gap unless runway forces the call.

## Assumptions (flag if any are wrong)

1. 30-day timeline is feasible — assumes meaningful runway. Shorter runway compresses milestones and lowers the role-quality bar.
2. ~25–35 focused hours per week available. Less means milestones stretch proportionally.
3. Starting from technical-curious but not yet shipping AI projects publicly. If a portfolio already exists, jump straight to Day 20.

---

## Operating guardrails for the agent

- The three GitHub builds (RAG app, tool-use agent, evals harness) are real coding work — implement them, don't just outline them. Each one lives in its own subdirectory with a working demo, a README explaining the PM-relevant decisions, and a writeup framing what an AI PM would do with this in production.
- The teardown PRD is a single high-quality document — pick a real, live AI product the user can name (default candidates: Cursor, Linear's AI features, Notion AI, Perplexity, GitHub Copilot). If the choice is ambiguous, write a `TEARDOWN_CANDIDATES.md` ranking 3 options with rationale and let the user pick.
- The interview-loop tracker is a populatable template (markdown table or simple structured file). Do NOT fabricate companies the user is interviewing with.
- Build resume and cover-letter scaffolds the user fills with specifics — never invent employment history, projects, or credentials.
- One small, focused, committed change per iteration. Prefer shipping a complete artifact over half-finishing several.
- Maintain a `DECISIONS.md` log capturing choices and rationale so the user can review and redirect quickly.
