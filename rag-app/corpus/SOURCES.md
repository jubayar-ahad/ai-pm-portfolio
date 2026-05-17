# Corpus sources

This file lists every corpus file under `rag-app/corpus/`, its origin URL,
retrieval date, and a per-source license / fair-use rationale. **No URLs or
content here are fabricated** — every file traces to a real page on the live
source as of the retrieval date.

The corpus is now complete for the three subdirectories named in
`NEXT_WORK.md` item 5: `cursor-docs/`, `anthropic-docs/`, and `willison/`,
added incrementally across iterations 79 / 80 / 81.

Combined chunk count at the default chunker (400-word chunks with 80-word
overlap) is **61 chunks** — cursor-docs 18 + willison 18 + anthropic-docs 25
— comfortably inside the 30–80 chunk combined target band the rag-app's
NEXT_WORK item 5 sets, with each per-subcorpus count inside its own 10–30
band.

---

## `willison/` — selected posts from Simon Willison's weblog

**Subject matter:** AI agents, prompt injection, LLM coding tools, agent
safety. Strong AI-PM fluency signal: each post pairs a technical observation
with a product-level "what should builders do about this" take.

**License / reuse rationale:** Simon Willison's blog at
`https://simonwillison.net/` does not publish an explicit copyright /
reuse-license statement on its `/about/` page (verified 2026-05-17 via
WebFetch — see "Retrieval method" below). The content is used here under
**fair use for non-commercial portfolio demonstration with full attribution
and source URLs**. Every essay file is a verbatim transcription of the
public blog post body with paragraph structure preserved; navigation,
sidebars, social-share UI, and inline image markup are stripped; block
quotes are preserved as `>`-prefixed markdown. If the author requests
removal, all files under `willison/` should be deleted in a single commit.

**Retrieval method:** Each file was fetched via Claude Code's WebFetch
against the URL recorded below on the recorded retrieval date. The fetch
prompt asked for "the full article body text as plain text" with explicit
instructions to skip nav / footer / comments / social-share UI and preserve
paragraph breaks. The returned text was then saved as markdown without
further editorial changes other than the H1 title line and the `Posted
<date> by Simon Willison.` byline.

| File | Origin URL | Retrieval date |
|---|---|---|
| `normalization-of-deviance.md` | https://simonwillison.net/2025/Dec/10/normalization-of-deviance/ | 2026-05-17 |
| `claude-chrome-cloudflare.md` | https://simonwillison.net/2025/Dec/22/claude-chrome-cloudflare/ | 2026-05-17 |
| `claude-cowork-first-impressions.md` | https://simonwillison.net/2026/Jan/12/claude-cowork/ | 2026-05-17 |
| `moltbook.md` | https://simonwillison.net/2026/Jan/30/moltbook/ | 2026-05-17 |
| `clinejection.md` | https://simonwillison.net/2026/Mar/6/clinejection/ | 2026-05-17 |
| `pragmatic-summit-agentic-engineering.md` | https://simonwillison.net/2026/Mar/14/pragmatic-summit/ | 2026-05-17 |
| `snowflake-cortex-ai.md` | https://simonwillison.net/2026/Mar/18/snowflake-cortex-ai/ | 2026-05-17 |
| `auto-mode-for-claude-code.md` | https://simonwillison.net/2026/Mar/24/auto-mode-for-claude-code/ | 2026-05-17 |

---

## `cursor-docs/` — selected pages from Cursor's public documentation

**Subject matter:** Cursor's AI-coding-editor product surface — agent behavior,
tab completion, inline edit, rules / AGENTS.md, MCP tool integrations, model
pricing, Agent Skills, and recent changelog highlights. Each page is a primary
product-doc artifact from the same vendor whose product the
`/cursor-teardown.md` PRD reviews, which is why this subcorpus is the
load-bearing portfolio-fit selection (the rag-app demo can answer questions
that the teardown's analysis frames, using the vendor's own words as the
retrieval source).

**License / reuse rationale:** Cursor publishes its product documentation
publicly at `cursor.com/docs` and `cursor.com/changelog` without an explicit
permissive-license statement on the docs root (verified 2026-05-17). The
content is used here under **fair use for non-commercial portfolio
demonstration with full attribution and source URLs**. Every file is a
near-verbatim transcription of the public docs page body with navigation,
sidebars, search UI, "On this page" outlines, and footer cruft stripped.
Lists and code blocks are preserved as markdown; in-page links were
de-rendered to plain text. The changelog file is a single condensed view of
the 4 most recent entries at retrieval time (not a verbatim archive — the
changelog page is rolling and individual entries do not have stable
per-entry URLs that the chunker can usefully attribute to). If the
publisher requests removal, all files under `cursor-docs/` should be
deleted in a single commit.

**Retrieval method:** Each file was fetched via Claude Code's WebFetch
against the URL recorded below on the recorded retrieval date. The fetch
prompt asked for the verbatim article body with explicit instructions to
skip nav / sidebars / footer / search UI / "On this page" outline and
preserve paragraph breaks. The returned text was saved as markdown with the
H1 title line restored from the page heading; no paraphrase or content
addition was performed.

| File | Origin URL | Retrieval date |
|---|---|---|
| `agent.md` | https://cursor.com/docs/agent | 2026-05-17 |
| `tab.md` | https://cursor.com/docs/tab | 2026-05-17 |
| `rules.md` | https://cursor.com/docs/rules | 2026-05-17 |
| `inline-edit.md` | https://cursor.com/docs/inline-edit | 2026-05-17 |
| `mcp.md` | https://cursor.com/docs/mcp | 2026-05-17 |
| `models.md` | https://cursor.com/docs/models | 2026-05-17 |
| `skills.md` | https://cursor.com/docs/skills | 2026-05-17 |
| `changelog-recent.md` | https://cursor.com/changelog | 2026-05-17 |

## `anthropic-docs/` — selected pages from Anthropic's Claude API documentation

**Subject matter:** Anthropic's public Claude API documentation — overview /
quickstart (`intro`), the model family and pricing table (`models-overview`),
the prompt-engineering hub page (`prompt-engineering`), extended thinking
(`extended-thinking`), prompt caching (`prompt-caching`), tool use
(`tool-use`), Agent Skills (`agent-skills`), and Citations (`citations`).
The pages selected cover the three NEXT_WORK-named buckets (API docs, model
cards, prompting guide) and the three agentic surfaces (tool use, Agent
Skills, citations) that the `tool-use-agent` and `rag-app` builds in this
repo demonstrate against; this lets the rag-app demo answer questions
that the other two builds frame, using Anthropic's own documentation as the
retrieval source.

**License / reuse rationale:** Anthropic publishes its Claude API
documentation publicly without an explicit permissive-license statement on
the docs root (verified 2026-05-17). The content is used here under **fair
use for non-commercial portfolio demonstration with full attribution and
source URLs**. Every file is a near-verbatim transcription of the public
docs page body with navigation, sidebars, search UI, "On this page"
outlines, footer cruft, and Mintlify-specific MDX components
(`<CardGroup>`, `<Tip>`, `<Note>`, `<Tabs>`, etc.) stripped or de-rendered
to plain markdown. Internal cross-links (e.g. `/docs/en/...`) were de-rendered
to plain prose to keep chunks self-contained. Code blocks are preserved as
fenced markdown. If the publisher requests removal, all files under
`anthropic-docs/` should be deleted in a single commit.

**URL redirect note:** All eight original `docs.anthropic.com` URLs (the
host name NEXT_WORK.md item 5 names) returned HTTP 301 redirects to the
corresponding `platform.claude.com/docs/...` paths on 2026-05-17. The
content saved here was fetched from the redirect destinations. The "Origin
URL" column below records the original `docs.anthropic.com` URL the user
or interviewer would type and expect to land at; the redirect chain is
real-as-of-retrieval-date and is not a typo.

**Retrieval method:** Each file was fetched via Claude Code's WebFetch
against the URL recorded below on the recorded retrieval date (following
the 301 to `platform.claude.com`). The fetch prompt asked for the verbatim
article body with explicit instructions to skip nav / sidebar / footer /
search UI / "On this page" outline, preserve paragraph breaks and code
blocks, and not generate any system-reminder-like content (a hygiene rule
added after the cursor-docs iteration where the small/fast summarizing
model occasionally leaked the harness's TodoWrite system-reminder block
into its output — observed in 1 of 8 fetches this iteration as well, and
manually stripped from `prompt-caching.md` before saving).

| File | Origin URL | Retrieval date |
|---|---|---|
| `intro.md` | https://docs.anthropic.com/en/docs/intro | 2026-05-17 |
| `models-overview.md` | https://docs.anthropic.com/en/docs/about-claude/models/overview | 2026-05-17 |
| `prompt-engineering.md` | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview | 2026-05-17 |
| `extended-thinking.md` | https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking | 2026-05-17 |
| `prompt-caching.md` | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching | 2026-05-17 |
| `tool-use.md` | https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview | 2026-05-17 |
| `agent-skills.md` | https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/overview | 2026-05-17 |
| `citations.md` | https://docs.anthropic.com/en/docs/build-with-claude/citations | 2026-05-17 |
