# Personal landing page — `landing-page/`

A single-file portfolio landing page (`index.html`) that serves as the
"front door" for someone Googling the user's name or clicking through
from a LinkedIn message. Inline CSS, no external resources (no fonts,
no images, no JS), mobile-responsive via plain CSS — opens in any
browser with zero setup. Shipped 2026-05-17 under NEXT_WORK item 10
sub-checkbox 1.

---

## How to deploy

Two paths, pick the one matching the user's hosting setup. **Both depend
on the same relative-link structure of `index.html`** — every card
links into the repo via `../`-prefixed paths
(`../rag-app/README.md`, `../teardown-prd/cursor-teardown.md`, etc.),
which renders correctly when the file is opened locally from a
checked-out repo but requires a link-rewrite step before either
production deploy path serves a working site to a remote visitor.

**Path A — GitHub Pages from the repo.** No git remote is configured
yet (verified via `git remote -v` at the time of writing); set one
with `git remote add origin <url>` and `git push -u origin main`,
then in the repo's *Settings → Pages* set the source to
*Deploy from a branch* with branch `main` and folder `/` (root). The
landing page will then be served at
`https://<username>.github.io/<repo>/landing-page/`. Caveat: GitHub
Pages serves `.md` files as raw text by default rather than rendering
them, so the shipped relative `../foo.md` links will download or
display source rather than show the formatted artifact a visitor
expects. Once the remote is set, rewrite each relative `../<path>.md`
link in `index.html` to its canonical github.com blob URL
(`https://github.com/<user>/<repo>/blob/main/<path>.md`) so each card
opens the rendered markdown in the GitHub web UI; the rewrite is the
one manual step Path A requires and only needs to happen once.

**Path B — copy `index.html` to a personal site's root.** Copy this
one file to wherever a personal site is hosted (Netlify, Vercel, a
static S3 bucket, an existing GitHub-Pages user site at
`<user>.github.io`), then apply the same `../<path>.md` →
github.com blob URL rewrite as Path A, since the linked artifacts
will not exist relative to the copied file. Without the rewrite the
copied page 404s on every card. No other portion of the file needs
adjustment: the inline CSS, the responsive grid, and the structural
markup are self-contained and travel with the single file.

---

## The user-editable intro

The one-sentence intro paragraph inside `index.html` is bracketed by a
matched pair of HTML comments:

```html
<!-- USER: rewrite this intro -->
<p class="intro">…</p>
<!-- /USER: rewrite this intro -->
```

Rewrite the contents of the `<p class="intro">` element to match the
user's actual situation, target role, and tone — the shipped sentence
is a deliberately generic 90-day-portfolio framing chosen so the file
ships without inventing personal details. The matched comment pair
makes the boundary of the editable region unambiguous; everything
outside it (header, role tagline, cards, footer) is structurally
load-bearing and should be edited deliberately rather than as part of
the intro pass.

---

## No-fabrication rule

The landing page is governed by the same no-fabrication discipline the
rest of the portfolio uses:

1. **No invented testimonials, comp expectations, or credentials.** The
   page links to real artifacts in this repo and names the user with
   the LICENSE-canonical display form *Jubayar Ahad*; it does not
   include any quote, endorsement, salary band, school name, employer
   name, or job title beyond the user's own choice in the editable
   intro.
2. **No broken links.** Every `<a href="...">` target in `index.html`
   was verified to exist at the linked path before the file shipped.
   If a future artifact is moved, renamed, or deleted, update the
   landing page in the same commit — a 404 from this page is a
   first-impression failure that does not recover.
3. **No fabricated framing of unshipped work.** Cards describe each
   linked artifact in terms of what the artifact actually contains
   today (the rag-app card names the three corpora that exist in
   `rag-app/corpus/`, the tool-use-agent card names the nine tools
   that ship in the catalog, etc.). If an artifact's scope changes,
   update the card's prose in the same commit; if a card's framing
   stops matching its artifact, that's a fabrication in the same
   sense as a broken link.

---

## Scope of this directory

`landing-page/` holds exactly one HTML file plus this README. The
constraint is structural, not stylistic: NEXT_WORK item 10 explicitly
scopes this to a single self-contained file with no build tooling, no
frameworks, no external image hosts, no JS, and inline CSS. Future
additions (analytics, contact forms, dark-mode toggle, multi-page
expansion, a custom domain) are out of scope for this list and would
be added by the user, not the agent. If the editable intro grows
beyond one sentence, that's the user's call — but the structural
constraints above stay locked.
