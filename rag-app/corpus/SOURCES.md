# Corpus sources

This file lists every corpus file under `rag-app/corpus/`, its origin URL,
retrieval date, and a per-source license / fair-use rationale. **No URLs or
content here are fabricated** — every file traces to a real page on the live
source as of the retrieval date.

The corpus is rolled out one subdirectory at a time. Subdirectories present
today are listed below. The full target (per `NEXT_WORK.md` item 5) is three
subdirectories — `cursor-docs/`, `anthropic-docs/`, `willison/` — added
incrementally. Anything not yet present is not yet acquired.

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

## `cursor-docs/` — *(not yet acquired)*

Reserved for selected pages from `cursor.com/docs` and `cursor.com/changelog`.
To be added in a subsequent iteration under fair-use-for-non-commercial-
portfolio-demo with attribution. License rationale and the per-file URL +
retrieval-date table will be added here at that time.

## `anthropic-docs/` — *(not yet acquired)*

Reserved for selected pages from `docs.anthropic.com` (API docs, model
cards, prompting guide). To be added in a subsequent iteration under
fair-use-for-non-commercial-portfolio-demo with attribution. License
rationale and the per-file URL + retrieval-date table will be added here at
that time.
