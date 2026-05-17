# rag-app demo corpus — ranked public-domain candidates

**Status:** awaiting user pick. Three candidates, ranked best-fit first. If no
pick is recorded after one iteration of waiting, NEXT_WORK item 5 stops and
the queue moves on; see [NEXT_WORK.md](../../NEXT_WORK.md) item 5 for the
deferral rule. The user records a pick by editing this file's `Pick:` line at
the bottom (e.g. `Pick: 1`) or by saying so in the next prompt.

## Why this swap is happening

The current corpus is the repo's own markdown (`OBJECTIVE.md`, `DECISIONS.md`,
the templates folder, and the rag-app `README.md`). That's legally clean and
self-contained, but it has two demo weaknesses: (1) BM25 over the repo's own
prose is a closed loop — every plausible question is in the corpus by
construction, so a grounded answer is the only possible answer and the
demo never gets to *prove* it can refuse out-of-corpus questions on
unfamiliar text; (2) an interviewer reading the answer cannot independently
verify that the cited chunk actually says what the model claims, because
they're being asked to trust a corpus they've never read.

The replacement corpus has to clear three bars:

1. **Licensing certainty** — durably public domain in the United States,
   with a citable provenance (Library of Congress, Project Gutenberg,
   Wikisource). No CC-BY, no "probably public domain," no Wikipedia
   article text (CC-BY-SA is not public domain).
2. **Right size for the chunker** — the rag-app default is 400-word chunks
   with 80-word paragraph overlap. The corpus should produce roughly 20–80
   chunks total. Too small and BM25 has nothing to rank against; too large
   and the demo's load step becomes slow without changing the demo's
   point.
3. **Prose style that lets BM25 work and citations look honest** — short,
   topical, noun-phrase-dense sentences with named entities. BM25 is a
   sparse term-overlap retriever; the demo looks strongest on prose where
   the answer to a question is a discrete claim made in one or two
   sentences, not paraphrased across pages.

The ranking below is *for this demo's evaluation goals*. It is not a
literary judgement. All three corpora are excellent reading.

---

## Rank 1 — Selected Federalist Papers (recommended)

A curated subset of 5–10 essays from *The Federalist* (Hamilton, Madison,
Jay, 1787–1788), with #10 (Madison on factions), #51 (Madison on checks
and balances), #70 (Hamilton on the executive), and #78 (Hamilton on the
judiciary) as the spine. Source: Library of Congress digitized originals
or Project Gutenberg's plain-text edition (eBook #1404).

- **Licensing certainty:** unambiguous. US public domain by date — all 85
  essays were first published 1787–1788, more than a century before the
  1928 public-domain cliff. No translation issues (originally English),
  no edition-copyright issue if pulled from Project Gutenberg's plain text
  rather than a modern annotated edition.
- **Length:** the full 85 essays total ~150,000 words. A 5-essay subset
  (#10, #51, #70, #78, #84) is ~17,000 words, which the default chunker
  turns into roughly 50 chunks. That's the right size — large enough that
  BM25 ranking is non-trivial, small enough that the demo's `load` step
  stays sub-second and the README can show example output without
  truncating.
- **Prose style fit for Q&A demo:** very strong. The essays are
  argumentative-declarative, structured around named institutions
  ("the Senate," "the Executive," "the judiciary") and named threats
  ("faction," "tyranny of the majority"). A question like *"What does
  Federalist 10 say is the cure for the mischiefs of faction?"* has a
  single, locatable answer that BM25 surfaces on the first try and that
  a reader can independently verify against the cited span. Sentence
  structure is dense but not paraphrastic — claims are made *once*, in
  one place, in noun-phrase-heavy prose that BM25 was built for.
- **Concerns:** 18th-century syntax — long sentences, embedded clauses,
  archaic spelling preserved in some editions (e.g. "publick"). Pick
  the Gutenberg "production note" edition that normalizes spelling, not
  the facsimile. Also: the demo answer will sound like
  18th-century political theory, which may feel off-tone for an AI-PM
  interview audience expecting product-prose. Mitigation: a one-line
  README sentence framing the corpus as a deliberately neutral test
  bed, not a domain choice.
- **Sample demo question:** "According to Federalist 10, what is the
  difference between a pure democracy and a republic?" — Madison gives
  a clean two-sentence definitional answer that a grounded citation
  can pin to a single chunk.

## Rank 2 — Selected Emerson essays

A curated subset of 3–5 essays from Ralph Waldo Emerson's *Essays: First
Series* (1841) and *Essays: Second Series* (1844), with "Self-Reliance,"
"Compensation," and "The Over-Soul" as obvious spine candidates. Source:
Project Gutenberg (eBook #16643 for the first series).

- **Licensing certainty:** unambiguous. US public domain by date
  (1841/1844, both pre-1928). Gutenberg plain-text edition has clean
  provenance.
- **Length:** "Self-Reliance" alone is ~11,000 words, so a 3-essay subset
  lands around 30,000 words — roughly 80 chunks, which is on the high
  end of the target band. A 2-essay subset is the better packaging.
- **Prose style fit for Q&A demo:** weaker than the Federalist Papers,
  for a specific reason. Emerson is aphoristic, not declarative — his
  central claims arrive as compressed proverbs ("Trust thyself," "A
  foolish consistency is the hobgoblin of little minds") embedded in
  longer meditative passages that don't repeat the noun phrases of the
  question. BM25 over Emerson surfaces the aphorism only when the
  question accidentally contains its keywords; the underlying argument
  is dispersed across paragraphs and chunked away from the aphoristic
  payoff. The demo will *work* — citations resolve, answers ground —
  but the retrieved-chunk-to-answer alignment looks less crisp than on
  the Federalist Papers, which makes the grounded-citation behavior
  feel like a weaker proof.
- **Concerns:** the aphoristic style also makes refusal behavior harder
  to demo. A question like "What does Emerson think about technology?"
  is *legitimately out of corpus* in a strict sense, but a generous BM25
  match on "think" can squeak above the refusal floor and produce a
  hand-wavy grounded-but-unhelpful answer. The Federalist subset has
  cleaner in/out-of-corpus boundaries.
- **Sample demo question:** "What does Emerson say is the relation
  between solitude and society in 'Self-Reliance'?" — answerable, but
  the answer is reconstructed from two non-adjacent passages, so the
  citation array will have two entries rather than one.

## Rank 3 — Selected Project Gutenberg short stories

A curated subset of 5–8 short stories from pre-1928 public-domain
authors, e.g. Edgar Allan Poe ("The Cask of Amontillado," "The Tell-Tale
Heart"), Kate Chopin ("The Story of an Hour," "Désirée's Baby"), Saki
("The Open Window," "Sredni Vashtar"). Source: Project Gutenberg per-story
eBook IDs.

- **Licensing certainty:** clean per-author after the death+95-year /
  pre-1928 publication rules, but selection requires per-story
  verification rather than a single date check (the way the Federalist
  Papers' 1787 date settles everything in one sweep). Defensible, but
  more administrative overhead in `SOURCES.md`.
- **Length:** five short stories average ~3,000 words each, totaling
  ~15,000 words and ~40 chunks. Comparable to the Federalist subset's
  size.
- **Prose style fit for Q&A demo:** weakest of the three for this
  specific demo. Narrative fiction encodes its key facts (who did what
  to whom, what happened next) across a plot arc, not in topical
  declarative sentences. BM25 surfaces chunks that share *words* with
  the question, not chunks that share *plot causation*. A question like
  "Why does Montresor wall up Fortunato?" has a plausible grounded
  answer ("for an insult, fifty years ago, that the narrator refuses to
  specify"), but the answer is paraphrased and synthesized across the
  whole story rather than stated in one chunk — exactly the failure
  mode BM25 + grounded-citation handles least gracefully. The corpus
  will *look* most demo-friendly to a general audience because everyone
  has read these stories, but the demo's actual mechanism (sparse
  retrieval + chunk-anchored citations) will look weakest on it.
- **Concerns:** per-author license verification, weakest BM25 fit, and
  a subtle interview risk — interviewers who recognize the stories may
  evaluate the answer against their own memory of the story rather than
  against the cited chunk, which conflates the model's grounding with
  their own recall.
- **Sample demo question:** "In 'The Story of an Hour,' what causes
  Mrs. Mallard's death?" — answerable, but the famous twist depends on
  the final two sentences of the story being in the retrieved chunk
  set; if chunking splits them off, the grounded answer is technically
  wrong by the standards of the actual story.

---

## What "pick" means

The chosen corpus drives three downstream artifacts in the next
iterations of NEXT_WORK item 5:

1. The corpus files themselves under `rag-app/corpus/<name>/`, copied
   verbatim from the cited Project Gutenberg / Library of Congress
   source.
2. `rag-app/corpus/<name>/SOURCES.md` listing the exact URL per file
   and the retrieval date (so the citation chain back to a public
   record is intact).
3. A `make-demo.sh` or `python -m rag_app demo` one-shot script that
   loads, retrieves, and asks the hand-picked sample question above
   in dry-run mode, with the output snippet pasted into the README's
   Status section.

## Pick

Pick: _<user fills with `1`, `2`, or `3`>_

If this line still reads `_<user fills...>_` at the start of the
iteration after the one that ships this file, NEXT_WORK item 5 stops
per its own deferral rule and the queue moves to item 6.
