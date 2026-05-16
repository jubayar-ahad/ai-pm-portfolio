# AI PM Resume Scaffold

A populatable resume for the AI PM job search defined in `../OBJECTIVE.md`.
Replace every `_<placeholder>_` italic span with a real value before sending
this to a recruiter or pasting into Workday. Nothing in this file is
auto-populated — the agent does not invent prior roles, employers,
projects, or credentials. See `../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. Treat this as a one-page resume scaffold. If the populated draft runs to
   page two before the Education section, cut bullets from the oldest role
   first, not the most recent one.
2. Keep the section order. ATS parsers and human skim-readers both expect
   `Summary → Experience → Selected AI/PM portfolio → Skills → Education`.
   Reorder only if a specific application explicitly asks for a different
   shape.
3. Bullet shape: `Action verb + what you did + concrete result with a
   number`. If the result line has no number, the bullet is doing less work
   than it could — find a denominator (users, revenue, latency, p95, hours
   saved, %, $) or rewrite the bullet around a different result.
4. The **Selected AI/PM portfolio** section is the leave-behind hook this
   90-day plan is building toward. It is pre-stubbed with the three Day-10
   builds and the Day-20 teardown PRD this repo ships — replace the
   placeholders only with what you have actually run end-to-end and can
   demo on a screen share.
5. Delete every section, bullet, and italic placeholder you do not use
   before sending. A live placeholder in a submitted resume is a
   credibility hole.
6. ATS hygiene: do not add tables, columns, images, or text boxes when you
   export. Plain Markdown → PDF (or a single-column docx) parses cleanly.
   Section headers stay at H2 (`##`), role/build sub-headers at H3 (`###`).

## Header

**_<Full name>_** \
_<City, Country>_ · _<email>_ · _<phone, optional>_ · _<LinkedIn URL>_ · _<GitHub URL>_ · _<Portfolio URL, optional>_

## Summary

_<One to two sentences. Lead with the role you want — AI PM / PM, AI
Features / ML PM — and the strongest single proof point you can name
truthfully. Example shape (rewrite, do not copy verbatim): "PM with N years
shipping <product surface> at <company shape>, currently building
production-grade RAG, tool-use agents, and evals in <repo or portfolio
link>. Looking for AI PM roles where AI is the product or a core feature
(Bucket 2 per the objective)."_

## Experience

### _<Most recent role title>_ — _<Company>_

_<City, Country>_ · _<YYYY-MM>_ – _<YYYY-MM or Present>_

- _<Action verb + scope + metric. e.g. "Owned the <surface> roadmap for N quarters; shipped <thing> that moved <metric> from X to Y."> Do not invent the numbers — leave the number-shaped slot blank rather than guess._
- _<Cross-functional bullet: who you worked with (eng / design / DS / data) and what shipped. Quantify scope (team size, surface, region) if you can name it truthfully.>_
- _<AI-relevant bullet if you have one: LLM feature, ML model in production, agent surface, data labeling, evals, prompt iteration. If you have no AI-relevant work in this role, omit this bullet rather than stretch — the AI portfolio section below carries that signal.>_
- _<Optional bullet: a specific decision you made and what it cost you to make it. Trade-off bullets are the rarest and the highest-signal kind for PM interviews.>_

### _<Previous role title>_ — _<Company>_

_<City, Country>_ · _<YYYY-MM>_ – _<YYYY-MM>_

- _<Bullet>_
- _<Bullet>_
- _<Bullet>_

### _<Earlier role title>_ — _<Company>_

_<City, Country>_ · _<YYYY-MM>_ – _<YYYY-MM>_

- _<Bullet>_
- _<Bullet>_

_<Add or remove role blocks as needed. Three to five roles is the usual
band for a one-page PM resume. For roles older than ~10 years, keep them to
a one-line role + company + dates listing under a `### Earlier experience`
header rather than a full bullet block.>_

## Selected AI / PM portfolio

_<This section is the leave-behind hook. Each item below should be
something you can demo on a screen share and speak to in five minutes. If
you cannot, delete the entry — a placeholder portfolio bullet is worse
than no portfolio bullet.>_

### AI engineering builds — _<repo URL>_

- **RAG application** (`rag-app/`): paragraph-aware chunker, BM25 retrieval,
  Claude generation with `[source#span]` citation contract, refusal
  threshold with byte-identical refusal string across builds, and an
  eval-trace schema (`rag-app.ask.v1`) with deterministic `record_id`.
  _<One sentence on what the PM decision was — e.g. "Chose BM25 over dense
  embeddings to keep the demo runnable on any machine with one API key.">_
- **Tool-use agent** (`tool-use-agent/`): bounded multi-step agent loop
  over a read-only six-tool catalog (repo file ops + interview-tracker
  rollups), with `end_turn` / `max_steps_exhausted` / `repeated_tool_error`
  termination discriminator and the same trace schema shape.
  _<One sentence on the PM decision — e.g. "Locked max_steps as
  tool-execution rounds, not model calls, so cost is bounded by a single
  counter the user can reason about.">_
- **Evals harness** (`evals-harness/`): cross-build, stdlib-only,
  no-API-key scorer with five rubrics (refusal / groundedness /
  first-call-tool / termination / cost), asserting REFUSAL_SENTENCE
  byte-equality and trace-helper algorithm equivalence between the two
  builds at startup.
  _<One sentence on the PM decision — e.g. "Made the harness own no
  inference of its own so the cross-build comparison is reproducible
  without any vendor account.">_

### AI product teardown — _<repo URL or hosted link>_

- **_<Cursor / Perplexity / GitHub Copilot — pick the one you actually
  use>_** (`teardown-prd/cursor-teardown.md`): six-section PRD covering
  what's working, what's broken, what to ship next (three proposals tied
  one-to-one to the broken surfaces), six proposed metrics in a
  leading/lagging × adoption/quality/business grid, scope decisions, and a
  validation plan that hooks into this repo's `evals-harness/` build.
  _<One sentence on the PM angle — e.g. "Wrote it as an interview
  leave-behind: every claim is sourced inline, every metric names the
  decision it would inform, and every proposal names what could go
  wrong.">_

_<If you have other AI/ML projects you can demo and speak to truthfully
— a paper, a Kaggle/competition placement, an internal tool you shipped,
a published writeup with non-trivial reach — list them in the same shape:
one-line title, link, two-sentence-max description.>_

## Skills

**Product craft.** _<Discovery and prioritization frameworks you actually
use (RICE, weighted shortest job first, opportunity solution trees,
whatever you can defend in an interview). Roadmapping. Spec writing. A/B
test design. Customer research methods you've personally run.>_

**AI fluency.** RAG (retrieval shape choices, citation/groundedness
contracts, refusal thresholds). LLM agent loops (tool-calling, bounded
termination, error recovery). Eval design (labeled sets, per-rubric
classifiers, accuracy vs. observability, cost rubrics). Prompt
engineering. Vendor selection (Anthropic, OpenAI, open weights — name
only what you've actually used). _<Add or remove items so this list is
honest; an inflated AI skills list is the easiest thing for a technical
interviewer to puncture.>_

**Technical.** _<SQL fluency, Python read/write level, data tooling
(dbt, Snowflake, BigQuery), shipped-with frameworks (React, etc.).
Include only what you can answer follow-ups on.>_

**Tools.** _<Jira / Linear / Notion / Figma / Amplitude / Mixpanel /
Looker / Mode — list only what you've used recently enough to speak to
specific workflows.>_

## Education

### _<Degree>_, _<Field>_ — _<Institution>_

_<YYYY>_ – _<YYYY>_ · _<City, Country>_

_<Optional: one line on honors, relevant coursework, thesis, GPA if
strong-and-recent. Drop this line entirely if more than ~5 years out.>_

_<Add a second degree block if applicable. Otherwise delete this
paragraph.>_

## _<Optional: Selected writing / talks>_

_<Only include this section if you have at least two truthful items.
One-item sections look thin; zero-item sections look performative. Use
this shape per entry:>_

- **_<Title>_** — _<venue or publication>_, _<YYYY-MM>_. _<One-line
  description, then link.>_

## _<Optional: Certifications>_

_<Same rule — only include if you have at least two industry-recognized
items. Coursera completion certificates do not generally clear that bar
for PM roles; named programs (Reforge, PMI, AWS / GCP / Azure
certifications, Mind The Product) do.>_

- _<Certification name>_ — _<issuer>_, _<YYYY>_

---

_Before submitting: re-read top to bottom for any remaining italic
placeholders. The fastest grep is `_<` — if it appears anywhere in the
file, the resume is not ready to send._
