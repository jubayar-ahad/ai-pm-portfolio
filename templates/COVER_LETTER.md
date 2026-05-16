# AI PM Cover Letter Scaffold

A populatable cover letter for the AI PM job search defined in
`../OBJECTIVE.md`. Replace every `_<placeholder>_` italic span with a real
value before sending. Nothing in this file is auto-populated — the agent
does not invent companies, products, prior roles, or accomplishments. See
`../DECISIONS.md` for the no-fabrication rule.

## How to use this file

1. One letter per role. Do not send the same body text to two companies —
   the opener and the company-specific paragraph are load-bearing and lose
   their entire signal the moment they read as templated.
2. Target length: **250–400 words** of body prose (Header + sign-off do
   not count). Under 250 words reads as effort-light; over 400 words
   reads as a second resume and recruiters skim past the middle. If your
   draft is over 400 words, cut from paragraph 3 (the AI craft paragraph)
   first — `../templates/RESUME.md`'s Selected AI/PM portfolio section
   already carries that load.
3. Company-agnostic claims (years of experience, what you shipped, the
   three builds and the teardown PRD) belong in **`../templates/RESUME.md`**
   as the single source of truth. The cover letter quotes one or two of
   them in prose form and points the reader at the resume for the rest —
   it does not restate the portfolio bullet by bullet. Keeping the two
   files in sync this way means you maintain the portfolio claims in one
   place.
4. Pick exactly one **Opener variant** below and delete the other two
   before sending. The three variants (cold / referral / inbound recruiter
   response) are mutually exclusive — leaving more than one in the draft
   advertises the scaffold and forfeits the company-specific signal.
5. The **Company-specific observation** in paragraph 1 is the highest-
   leverage sentence in the letter. It should be a specific, falsifiable
   thing you noticed about the company's AI product — a UX choice, a
   missing affordance, a metric they probably watch. Generic praise
   ("I admire your mission") is the cheapest possible signal and the
   easiest for a hiring manager to discount.
6. Delete every section, paragraph, and italic placeholder you do not use
   before sending. A live placeholder in a submitted letter is a
   credibility hole — the same rule the resume scaffold uses.
7. Sending channel hygiene: paste as plain text into the body of the
   email or ATS textarea (not as an attached docx) unless the application
   explicitly asks for an attachment. Strip any Markdown formatting marks
   that survive the paste — recruiters read in their mail client, not in
   a Markdown renderer.

## Header

_<Date in long form, e.g. May 16, 2026>_

_<Hiring manager name if known, otherwise omit this line>_ \
_<Their title if known, otherwise omit this line>_ \
_<Company name>_

Subject (if sending as email): **AI PM — _<Role title>_ — _<Your full name>_**

## Opening — pick one variant

### Variant A — Cold application

_<Hi `_<Hiring manager first name>_` or `Hi <Company> team` if no
named recipient>_,

I'm writing about the _<Role title>_ role at _<Company>_.
_<Company-specific observation in 1–2 sentences: name the AI product
surface, name a specific design or product decision you noticed, and
name the trade-off it implies — this is the highest-signal sentence in
the letter. Example shape: "Your <product surface> ships <observable
behavior> rather than <alternative>, which trades off <X> for <Y> —
the same kind of trade-off I work on in my own teardown of <product>
at <repo link>." Do not invent numbers or features you have not
verified yourself.>_

### Variant B — Referral

_<Hi `_<Hiring manager first name>_`>_,

_<Referrer full name>_ at _<Company>_ pointed me at the _<Role title>_
role — _<one sentence on the context, e.g. "we worked together on
<surface> at <prior company>" or "they saw my teardown of <product>
and thought the shape would fit your team">_. _<Company-specific
observation as in Variant A, one sentence — the referral does the
warm-intro work, so this sentence can go straight to the product
observation.>_

### Variant C — Inbound recruiter response

_<Hi `_<Recruiter first name>_`>_,

Thanks for reaching out about the _<Role title>_ role at _<Company>_.
_<One-sentence acknowledgement of something specific from their
outreach — the team, the product surface, the scope — that confirms
you read the message rather than auto-replying. Then one sentence
that pivots to your own product observation about their AI surface,
as in Variant A.>_

## Body

### Paragraph 2 — Track record

_<Two to three sentences naming one or two specific things you have
shipped that are directly relevant to this role. Lead with the most
recent and most relevant. Quote the role and the result in prose form;
do not bullet — the resume bullets the same content and the letter
should read as a hiring manager's three-minute version of the resume.
Example shape (rewrite, do not copy verbatim): "At `_<Company>_` I
owned the `_<surface>_` roadmap for `_<duration>_` and shipped
`_<feature>_`, which moved `_<metric>_` from `_<X>_` to `_<Y>_`. Before
that I led `_<scope>_` at `_<Earlier company>_` and learned `_<one
sentence on what that experience taught you that applies here>_." Do
not invent the numbers — if you do not have a verified metric, lead
the sentence with the decision you made instead.>_

### Paragraph 3 — AI craft proof

_<Two to three sentences pointing the reader at concrete AI work you
have shipped. The Selected AI/PM portfolio section in
`../templates/RESUME.md` carries the full claim shape; this paragraph
names one or two of those artifacts in prose and links the repo.
Example shape: "Outside of `_<Most recent company>_` I have been
building production-grade RAG, tool-use agents, and evals end-to-end
in `_<repo URL>_` — including a six-section teardown PRD of `_<product
the user actually picked: Cursor / Perplexity / GitHub Copilot>_` that
proposes three specific shipments and the leading/lagging metrics that
would tell you whether they worked. I write about AI product decisions
the way I would expect to argue them at `_<Company>_`: every claim
sourced, every metric named to the decision it would inform, every
proposal paired with what could go wrong." Only claim artifacts you
can demo on a screen share — see the resume scaffold's "delete only
what you cannot demo" rule.>_

### Paragraph 4 — Why this role and what you would do first

_<Two to three sentences on why this specific role and not any AI PM
seat. Name the role's scope (the surface you would own, the team
shape, the product stage) and tie it to your strongest one-line claim
about how you would approach the first 30 days. Avoid "I'm passionate
about AI" — that sentence is the conversational dial tone and carries
no signal. Better shape: "What draws me to this specific seat is
`_<the surface / customer / problem named in the JD>_`. In my first
30 days I would `_<one concrete, falsifiable first move: e.g. shadow
support tickets to map the top failure modes, replay the last quarter
of feature launches against the live evals to find regression
candidates, sit with the on-call PM to understand the escalation
shape>_` before proposing any roadmap changes." Do not promise
specific deliverables you cannot defend from outside the company.>_

## Closing

_<One to two sentences. State the ask explicitly (a screening
conversation, not a job offer), and acknowledge a logistical detail if
relevant (timezone, notice period, work-authorization status only if
the JD asked). Example shape: "Happy to walk through any of the above
in a 25-minute screen — I am `_<timezone>_` and flexible most
`_<weekday windows>_`. My CV is attached / linked below for the
specifics, and the repo above is the fastest read on how I work.">_

Best, \
_<Your full name>_ \
_<email>_ · _<phone, optional>_ · _<LinkedIn URL>_ · _<GitHub URL>_

---

_Before sending: re-read top to bottom for any remaining italic
placeholders. The fastest grep is `_<` — if it appears anywhere in the
file, the letter is not ready to send. Same convention as
`../templates/INTERVIEW_TRACKER.md` and `../templates/RESUME.md`, so
one regex (`_<.*>_`) validates all three._
