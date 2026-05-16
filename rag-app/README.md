# rag-app

A small Retrieval-Augmented Generation demo, framed for an AI PM portfolio.

This README is the design contract for the build. It locks scope, stack, and
the PM-relevant decisions so subsequent iterations can land code without
re-litigating choices. Code lives alongside this README and lands
incrementally — see [Status](#status) for what currently runs.

---

## Status

| Slice | State |
| --- | --- |
| Design doc (this README) | Shipped |
| Corpus loader and chunker | Shipped (`python -m rag_app load`) |
| Retrieval CLI (BM25) | Shipped (`python -m rag_app retrieve "<question>"`) |
| Generation with Claude | Not yet implemented |
| End-to-end `ask` demo | Not yet implemented |
| Refusal + citation hardening | Not yet implemented |
| Evaluation hooks (for `evals-harness/`) | Not yet implemented |

The repo root README will only link this build as "demo-ready" once the
end-to-end `ask` slice runs against a real model. Until then it is linked as
"in progress."

## What this demo is, in one sentence

A command-line question-answering tool that retrieves relevant chunks from a
small markdown corpus and asks Claude to answer using only those chunks, with
citations.

## Why this corpus

**Corpus v1:** the repo's own markdown — `OBJECTIVE.md`, `DECISIONS.md`,
`templates/INTERVIEW_TRACKER.md`, and this README. Small (a few KB), legally
clean, and self-contained, so the demo runs without a separate dataset
download or a license footnote. It also eats its own dog food: an interviewer
can ask the running demo *"What is the Day 20 milestone?"* or *"Why was the
RAG app built first?"* and get a grounded, cited answer.

**Corpus v2 (deferred):** a small set of public AI-PM-relevant documents
(e.g. a handful of canonical PM blog posts, public PRD examples) added once
the v1 loop is working. The exact selection is deferred to that iteration to
avoid speculative scope.

## Stack choices

| Concern | Choice | Why |
| --- | --- | --- |
| Language | Python 3.11+ | Most readable to a non-engineering interview audience; widely understood; matches the typical AI-PM portfolio reading audience. |
| Generation | Anthropic Claude (`claude-haiku-4-5-20251001` as default, configurable) | Cheap, fast, current, and pluggable. Default favors low spend on a demo. |
| Retrieval | Stdlib BM25 (Okapi, k1=1.5, b=0.75) over the loaded chunks | Zero model download, zero extra dependencies, runs on any Python. BM25 is the established sparse baseline; at this corpus size (tens of chunks) it is competitive with dense embeddings. Dense retrieval is deferred to a future hybrid (BM25 + reranker) rather than treated as the primary index — see [DECISIONS.md](../DECISIONS.md) for the supersession. |
| Chunking | Paragraph-aware word windows with paragraph-level overlap (defaults: 400 words, 80 overlap) | Word counts as a stdlib-only stand-in for token counts — keeps the loader dependency-free; the embedding step can re-measure if needed. |
| CLI | Single entry: `python -m rag_app ask "<question>"` | One command keeps the demo legible to a recruiter watching a screen share. |

The Anthropic + BM25 stack means the demo needs exactly one API key
(`ANTHROPIC_API_KEY`) to run end-to-end. No vector DB to provision, no
embedding model to download, no second account to create.

## Architecture

```
corpus/*.md
   │
   │  (1) load + chunk → chunks.jsonl
   ▼
chunks: list[{id, source, span, text}]
   │
   │  (2) at query time: BM25 over chunk tokens, take top-k
   ▼
top-k chunks
   │
   │  (3) prompt Claude with question + chunks + citation instructions
   ▼
answer with [source:span] citations
```

Notes:
- BM25 is built fresh from `chunks.jsonl` on each `retrieve` invocation.
  Persistence would only matter at a corpus size where the load itself is
  no longer cheap, and this corpus is well below that.
- Citations are non-negotiable — without them this is a chatbot, not a
  grounded QA demo. The prompt instructs the model to refuse to answer if
  the retrieved context is insufficient.

## What an AI PM would do with this in production

This section is the interview leave-behind. It frames how a PM would
productize a system shaped like this one.

### Success metrics

- **Groundedness rate:** % of answers where every claim has a retrievable
  citation. Measured against a labeled eval set (this is what
  `evals-harness/` will build).
- **Refusal-when-uncertain rate:** % of out-of-corpus questions where the
  system declines vs. confabulates. A demo that always answers is worse
  than one that knows when to abstain.
- **Time-to-first-token (p50, p95):** latency budget per query. RAG hides
  embedding + retrieval cost behind the user-visible LLM stream.
- **Cost per answered query:** end-to-end token cost; rises with k (top-k
  retrieved chunks) and corpus growth. The PM tradeoff is k vs. cost vs.
  groundedness.

### Failure modes worth designing around

- **Stale corpus:** retrieval returns confidently outdated facts. Mitigation
  in production: per-doc `last_indexed_at` surfaced in citations, plus a
  freshness signal in ranking.
- **Adversarial questions designed to bypass refusal:** prompt-injection
  payloads inside corpus chunks. Mitigation: treat retrieved text as data,
  not instructions; sanitize and isolate.
- **Top-k miss:** the right chunk wasn't in the top-k, so the model
  confabulates. Mitigation: hybrid retrieval (BM25 + dense), and a
  "no-context → refuse" guardrail.
- **Cost runaway:** large corpus + large k + verbose answers. Mitigation:
  bound k, cap output tokens, and monitor cost-per-query as a first-class
  metric.

### What's intentionally out of scope here

- **No vector database.** Real systems use one; a demo at this scale would
  obscure the loop. The README and code call this out so an interviewer
  can ask the obvious follow-up: *"What would you reach for at 10M
  chunks?"* — answer: a managed vector DB plus a hybrid retriever.
- **No dense retriever yet.** BM25 alone is the v1 retriever; a dense
  embedding model would be added as a *reranker* on the BM25 top-N rather
  than as the primary index, since hybrid (lexical + dense) is the modern
  production pattern. Listed in the roadmap.
- **No reranker.** A cross-encoder reranker is the next obvious quality
  knob — deliberately deferred to keep the iteration small.
- **No multi-turn / chat history.** Single-shot QA only, to keep the eval
  surface clean.

### Productization questions a PM should ask before shipping this for real

1. What's the abstention bar? (i.e. when must the system say "I don't
   know"?) A wrong-but-confident answer in a production setting is far
   more expensive than a refusal.
2. How does the corpus get updated, and who owns staleness?
3. What's the user's recourse when the answer is wrong — feedback, edit,
   escalate?
4. How is groundedness measured continuously in production (not just at
   ship)?
5. What's the cost ceiling per query before product economics break?

## Roadmap (subsequent iterations)

Each line below is intended to map to a single future iteration:

1. **Corpus loader + chunker.** Read every `.md` in the corpus, chunk into
   overlapping windows with paragraph awareness, persist a `chunks.jsonl`.
   *(Shipped.)*
2. **Retrieval CLI.** `python -m rag_app retrieve "<question>"` ranks
   chunks with BM25 and prints the top-k with scores. No model call yet.
   *(Shipped.)*
3. **Generation.** `python -m rag_app ask "<question>"` retrieves top-k,
   prompts Claude with strict citation instructions, prints the answer.
4. **Refusal + citation hardening.** Force the model to abstain on weak
   context (e.g. BM25 top score below a threshold); verify every citation
   resolves back to its chunk span.
5. **Eval hooks.** The existing `--json` flag on `retrieve` already emits a
   structured `{question, results}` record; extend `ask` similarly so the
   `evals-harness/` build can consume the full `{question, retrieved,
   answer, citations}` trace.
6. **Hybrid retrieval (optional quality lift).** Add a dense reranker over
   the BM25 top-N. Treat dense as a quality knob on top of the lexical
   baseline, not as a replacement.

## How to run

Run from the `rag-app/` directory so Python can import the `rag_app`
package directly. No third-party dependencies are required for the loader.

```bash
cd rag-app
python -m rag_app load
# Wrote N chunks to .../rag-app/.cache/chunks.jsonl
#   OBJECTIVE.md: ... chunks
#   DECISIONS.md: ... chunks
#   templates/INTERVIEW_TRACKER.md: ... chunks
#   rag-app/README.md: ... chunks
```

The loader auto-locates the repo root by walking up from the package
location until it finds `OBJECTIVE.md`, so the command works from any
cwd inside the repo. Override with `--corpus-root`, `--chunk-words`,
`--overlap-words`, or `--out` as needed.

Once chunks are loaded, retrieve the top-k chunks for a question with
BM25 (no model call, no API key required):

```bash
python -m rag_app retrieve "What is the Day 20 milestone?"
# Question: What is the Day 20 milestone?
# Top 5 of N chunks (BM25):
#
#   #1  score=... OBJECTIVE.md::... span=(..., ...)
#         ...preview of the chunk...
#   ...
```

Override `--top-k`, point at a different `--chunks` path, or emit a
structured record with `--json` (useful for the upcoming evals harness).

The end-to-end query interface is not yet wired up; once the generation
slice lands, the invocation will look like:

```bash
export ANTHROPIC_API_KEY=...
python -m rag_app ask "What is the Day 20 milestone?"
```

## Design tradeoffs called out for interview discussion

- **BM25 vs. dense embeddings as the v1 retriever.** A PM should be able to
  defend why a sparse baseline is the right *first* move (zero setup, strong
  lexical recall, instantly explainable) and articulate what triggers
  adding a dense reranker on top (semantically paraphrased queries that
  the lexical index keeps missing, or recall plateauing on the eval set).
- **In-memory index vs. a vector DB.** Same theme: don't overbuild the
  demo, but know the production answer (managed vector DB + hybrid
  retriever once corpus crosses ~10⁵ chunks).
- **Single-shot QA vs. multi-turn.** Cleaner eval surface; multi-turn is a
  separate product question, not a "make the demo bigger" question.
