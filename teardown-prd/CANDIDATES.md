# Teardown PRD — Candidate Shortlist

**Status:** RESOLVED 2026-05-16 — **Cursor** picked. See DECISIONS.md
final entry for the binding decision. This document is preserved below
as the record of how the pick was reached, not a live decision surface.
**How to use this doc:** Historical reference only. The next iteration
drafts the full teardown PRD against Cursor at
`teardown-prd/cursor-teardown.md`.

---

## Why this gate exists

The teardown PRD is the single highest-leverage interview leave-behind for
the Day-20 milestone (see OBJECTIVE.md). It depends on the user being able
to speak authentically about the product on a screen share — which means
the user must already use it, or be willing to use it heavily over the
drafting iterations. Picking the wrong product wastes a full slice and
produces a leave-behind that falls apart under interviewer follow-up.

The five default candidates from OBJECTIVE.md are: Cursor, Linear AI,
Notion AI, Perplexity, GitHub Copilot. Below is a ranked top-3 plus brief
rationale for the two not advanced.

## Selection criteria

These were applied uniformly across all five default candidates:

1. **AI-native vs. AI-add-on.** A product where AI is *the* surface gives
   more PM material to critique than one where AI is a sidebar feature. A
   teardown of an AI-add-on tends to drift into a teardown of the host
   product.
2. **Public surface depth.** The teardown stays honest only when grounded
   in observable product behavior (UI, settings, modes, tiers, error
   messages, docs, public roadmap). Products with thin public surface
   force speculation, which is exactly what the no-fabrication guardrail
   forbids.
3. **Failure-mode richness.** A great PM teardown spends most of its pages
   on what's broken and what to ship next. Products with no visible
   failure modes (or only obvious ones) flatten the document.
4. **Interview salience.** AI PM interviewers are likely to have used the
   product themselves and have opinions. Familiarity creates leverage; an
   obscure product forces the interviewer to take the user's framing on
   faith.
5. **User-can-actually-use-it.** A product that requires a paid tier the
   user does not already hold, or a closed beta, fails this gate
   regardless of how interesting it is on paper.

A candidate has to clear all five to be ranked above the cut.

## Ranked top 3

### 1. Cursor

**One-line:** AI-native code editor (VS Code fork) with chat, inline
edits, autocomplete, agents, and a project-wide indexer.

**Why it's strong as a teardown target:**
- AI is the entire product, not a sidebar feature. Every UX decision is
  PM-relevant: model selection (free vs. paid models, the auto-mode
  router), context strategy (open-files vs. indexer vs. @-mentions),
  edit-application UX (inline diff vs. side panel vs. agent-runs-it), and
  the recent shift toward background agents.
- The product surface is dense and public: docs, changelog, pricing
  tiers, model menu, settings, and a frequently-discussed indexer
  behavior. The teardown does not need to invent anything.
- Failure modes are observable on a normal day of use: indexer staleness
  on monorepos, model latency tail when the auto-router falls back,
  agent overruns and stop conditions, "applied edit" diffs that touch
  the wrong file, free-tier quota surprises.
- AI PM interviewers — especially at developer-tools companies — will
  have used Cursor or its competitors (Copilot, Windsurf, Zed) and can
  match opinions to the teardown's recommendations.

**Why this user might want a different pick:**
- The teardown will draw natural comparisons with GitHub Copilot. If the
  user is interviewing primarily at Microsoft / GitHub / a Copilot-shop,
  picking Cursor invites the interviewer to see the leave-behind as a
  partisan piece. Picking Copilot directly is the safer move there.
- The build portfolio in this repo is also developer-tools-shaped (RAG
  over markdown, tool-use-agent over the repo). A non-developer-tools
  teardown would broaden the interview-narrative range.

**Rough teardown shape (drafted only after user confirms):** what's
working (one section), what's broken (two sections — UX surface + model
behavior), what to ship next (one section, three concrete proposals with
rationale), proposed metrics (one section, ~6 metrics across leading and
lagging), out-of-scope (one section, names what was deliberately not
covered).

### 2. Perplexity

**One-line:** AI-native answer engine — search box that returns a cited
answer instead of a list of links, with follow-up threading.

**Why it's strong as a teardown target:**
- The most AI-native of the five candidates. Every pixel of the product
  is downstream of model behavior: the answer summary, the source
  citations, the follow-up suggestions, the "Pro Search" multi-step
  research mode, the spaces / threads / collections layer.
- Citation surface is unusually rich for a PM teardown: source ranking,
  citation density, "according to X" language, the trade-off between
  quoting verbatim vs. paraphrasing, and the user-trust loop when a
  cited source contradicts the summary. This is exactly the design
  surface an AI PM interview will ask about — the rag-app build in this
  repo (citation contract, refusal threshold, verifier) directly mirrors
  these PM choices, which lets the interview narrative tie the build
  and the teardown together cleanly.
- Failure modes are well-documented publicly: hallucinated sources,
  outdated cached answers, follow-up drift, mode confusion (Quick vs.
  Pro vs. Deep Research), and the recurring 'is this a search engine
  or an answer engine' identity tension.

**Why this user might want a different pick:**
- The product moves fast (modes and feature names change often); a
  teardown written in Week 3 risks being mildly stale at interview time
  if the user is targeting Day 60+ loops. Mitigation: timestamp claims
  and cite the changelog version inside the teardown itself.
- AI PM interviewers at Google, OpenAI, or Anthropic may consider this
  product a competitive-intel target rather than a neutral teardown,
  which can color the feedback. Less of a concern at Bucket 2 companies
  outside the model-lab orbit.

### 3. GitHub Copilot

**One-line:** AI-assisted developer suite from GitHub — completions,
chat, agents (incl. coding agent), and Workspaces, integrated into the
GitHub product surface.

**Why it's strong as a teardown target:**
- Mature product (the original mass-market AI-coding tool), so there is
  years of public surface to draw from: feature evolution from
  completions to chat to agents, model menu changes, free-tier launch,
  the Workspaces experiment, the recent autonomous-coding-agent rollout.
- Multiple AI surfaces in one product means the teardown can compare
  internal PM choices against each other (why does chat have model
  selection but completions doesn't, what's the relationship between
  Workspaces and the coding agent, etc.) — a richer structure than a
  single-surface teardown.
- Direct interview leverage at GitHub, Microsoft, and the broader
  Microsoft AI org. Bucket 2 fit is excellent: AI inside a deeply
  established product with a giant existing user base — exactly the
  product shape OBJECTIVE.md prioritizes.

**Why this user might want a different pick:**
- Less surprise per page than Cursor or Perplexity. Many PM critiques
  of Copilot are well-trodden (latency vs. acceptance rate, the chat-vs-
  completions tension, the agent's stop conditions), so the leave-behind
  has to work harder to say something the interviewer hasn't already
  read. Mitigation: pick one specific surface (e.g. the coding agent
  rollout) rather than teardowning the whole suite.
- The user must already use Copilot for the teardown to pass the
  authenticity bar; if the user is primarily a Cursor user, the
  teardown will read as armchair criticism.

## Cut from the shortlist

### Linear AI — cut

AI features (auto-labeling, drafting, summarization, agents) sit inside
a strong project-management product but are not the product. A teardown
risks drifting into a Linear teardown, which dilutes the AI-PM framing
that makes this leave-behind useful. Worth keeping on the bench if the
user is interviewing specifically at Linear or a competitor.

### Notion AI — cut

Similar shape to Linear AI: AI is an additive surface (Q&A over
workspace docs, writing assist, AI Connectors) on top of a host product
with its own non-AI design language. The Q&A-over-workspace surface is
PM-interesting but covers ground the rag-app build already exercises;
the teardown would echo rather than complement the portfolio.

## What "pick one" means in practice

When the user names a target, the next iteration:

1. Records the pick in DECISIONS.md (one entry, one paragraph) with the
   pick rationale in the user's own words if they offer one.
2. Drafts `teardown-prd/<product>-teardown.md` as a single self-contained
   document with the canonical six sections (what's working / what's
   broken / what to ship next / proposed metrics / out-of-scope / how
   I'd validate). One iteration may not be enough for the full draft;
   the iteration plan will say so up front and slice the draft if
   needed.
3. Avoids fabricating any metric, revenue, or user count. All quantitative
   claims must trace to a public source (changelog, blog post, public
   filing) cited inline.

If the user wants to teardown a product not on this list, that override
goes in the DECISIONS entry alongside the pick rationale and supersedes
the default-pool framing in OBJECTIVE.md for this single artifact.
