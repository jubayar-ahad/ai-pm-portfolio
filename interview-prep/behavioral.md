# Mock Interview Q&A — Behavioral Bank

A populatable interview-prep file for the behavioral / "tell me about a
time" surface of a PM interview slate. Fifteen canonical questions, each
followed by the strong-answer rubric (what a credible answer covers,
not what the user *should* say) and a `_<your draft>_` italic-marker
placeholder for the user's own draft. Nothing in this file is auto-
populated — the agent does not invent the user's stories, projects,
teams, timelines, or outcomes. See `../DECISIONS.md` for the no-
fabrication rule.

This bank ships under NEXT_WORK item 9 sub-checkbox 1. It is the fifth
file in `interview-prep/` and the only one whose source-of-truth is
*not* a portfolio artifact — the source is the user's own lived
experience, which the agent has no access to. The anchoring grammar
adapts accordingly: each rubric names the *evidence type* a strong
answer cites (a specific role, a measurable outcome, a named cross-
functional partner) without inventing the specifics, and the draft
slot is where the user supplies the actual time-bound story.

## How to use this file

1. **Draft before the interview, refine after.** The fifteen questions
   below cover the canonical behavioral surface a PM interview will
   pull from. Most interviews will pick three to six of these; you
   want a drafted answer for *every* one before you walk in, because
   the cost of being caught flat-footed on a behavioral is higher than
   on a technical question (the technical question lets you reason in
   real time; the behavioral demands a story you either have or do
   not).
2. **Use one structure consistently per question.** Each rubric names
   a structure at the top. **STAR** (Situation / Task / Action /
   Result) is the default for tell-me-about-a-time prompts (Q1, Q2,
   Q4, Q5, Q12, Q13, Q14). **PARLA** (Problem / Action / Result /
   Learning / Application) is used for failure, weakness, and wrong-
   call prompts (Q3, Q10, Q15) where the Learning + Application moves
   are the load-bearing part of the answer. The remaining five
   prompts (Q6 why-leaving, Q7 why-this-role, Q8 why-AI-PM, Q9
   biggest-strength, Q11 manager-style-fit) are *not* tell-me-about-a-
   time narratives — they reward different structural moves and so
   each rubric names a fit-shaped structure (Forward-looking framing,
   Fit framing, POV framing, Claim + Evidence + Edge, Preferences +
   Adaptability) instead. Don't mix structures inside a single
   answer — picking one and executing it cleanly reads as composed.
3. **Aim for 90–180 spoken seconds per answer** (roughly 220–450
   words written out) for the short ones (Q6–Q11), and **120–240
   spoken seconds** (roughly 300–600 words) for the STAR-structured
   ones (Q1–Q5, Q12–Q15). Behavioral answers run longer than
   technical answers because the Situation move costs ~20–30 seconds
   on its own and the Result move needs a specific outcome that
   takes time to ground. Longer than four minutes and the
   interviewer will interrupt; shorter than 90 seconds and the answer
   reads as evasive on a question they expected you to have a story
   for.
4. **The rubric is a checklist, not a script.** It lists the moves a
   credible answer makes — name the trade-off, separate the decision
   from the outcome, own the agency, name what you'd do differently —
   without dictating phrasing, stance, or which specific story to
   tell. You pick the story; the rubric only checks that the moves
   are present.
5. **No fabrication.** Every draft slot stays empty until the user
   fills it. The agent never drafts a story for the user. If a slot
   has been filled with content that does not match the user's actual
   experience (e.g., an interviewer asks about a project and the
   draft cites a project the user did not work on), the slot has
   been mis-used — the rubric is for *anchoring* the user's actual
   memory, not for fabricating a more flattering version of it.
6. **The placeholder grammar is `_<your draft>_`** matching the rest
   of `../templates/` and the per-artifact banks in this directory —
   so one regex (`_<.*>_`) finds every unfilled slot across all
   portfolio scaffolds.
7. **Delete the rubric before any live use.** Rubrics are study aids,
   not talking points. Pasting a rubric bullet into a live answer
   reads as recited; recite the *idea*, not the rubric's framing.

## What this bank does NOT cover

Per the NEXT_WORK item 9 framing, three adjacent prep buckets remain
deferred and are explicitly out of scope for this bank:

- **Culture-fit / values-fit questions** specific to a target
  company ("what does our value X mean to you", "tell me about a
  time you exemplified our principle Y"). These are company-specific
  and resist a portable rubric; they live downstream of a specific
  interview slate.
- **Case-prompt / product-sense questions** ("design Spotify for
  dogs", "improve Gmail search"). The four per-artifact Q&A banks
  in this directory already cover the user's PM-craft surface via
  actual built artifacts; case prompts are a separate prep modality
  and would dilute this bank.
- **Compensation / negotiation prep.** Out of scope by NEXT_WORK
  iteration-75 DECISIONS — negotiation is interview-stage-specific
  (offer stage, not screen stage) and depends on the user's
  geographic and total-comp constraints.

A reader of this bank should understand the deferral is intentional,
not an oversight. The DECISIONS entry shipping under NEXT_WORK item 9
sub-checkbox 3 will lock the three deferrals.

---

## Q1. Tell me about a time you made a hard decision.

**Structure: STAR.** **What a strong answer covers.** Names a
*specific*, time-bound decision (a quarter, a sprint, a deadline),
not a class of decisions or a recurring tendency. Separates the
decision from the outcome explicitly — the question is testing
decision-making under uncertainty, not whether the bet paid off,
so a strong answer makes the call seem hard *at the time of making
it* rather than retrospectively obvious. Names the trade-off both
ways: what was given up, what was gained, what data the candidate
had and what they wished they had. Owns the agency: "I decided"
rather than "we decided" or "it was decided." Closes with a
specific outcome (a number, a date, a stakeholder reaction) and
what would have to be true for the candidate to make the call
differently next time. The trap to avoid: the safe answer where
the decision was hard but happened to land well — interviewers
score for whether the *process* was sound, not whether luck was
kind, so an answer that conflates the two reads as outcome-driven.
A second trap: choosing a decision that wasn't really hard (e.g.,
"I had to pick between two reasonable options") — the question
expects genuine tension (resource cuts, stakeholder pushback,
career risk, ethical edge).

**Your draft:** _<your draft answer here — STAR structure: 120–240 spoken seconds; pick a decision where the trade-off was symmetric, separate decision from outcome, own the agency>_

---

## Q2. Tell me about a time you had a conflict with a teammate or stakeholder.

**Structure: STAR.** **What a strong answer covers.** Names a real
disagreement, not a "we had different perspectives but worked it
out" softener — the question is testing whether the candidate can
hold tension in front of a stranger, so a disagreement that
reads as merely a miscommunication will be probed for the real
conflict. Names the substantive disagreement (what each side
wanted, why), not the emotional register (whether anyone got
upset). Owns the candidate's own contribution to the conflict —
the strongest answers admit the candidate was partially wrong
or that their initial framing missed something the other party
saw clearly. Names a specific move that resolved it (a
conversation, a data pull, a written doc, a stakeholder
escalation) and the *durability* of the resolution (did the
relationship hold afterward, did the underlying issue stay
fixed). The trap to avoid: the answer where the other party is
the villain — interviewers read these as immature and worry the
candidate will be the villain in *their* next conflict. A second
trap: avoiding the conflict ("I just worked around them") —
the question is specifically asking what you do *with* conflict,
not how you route around it.

**Your draft:** _<your draft answer here — STAR structure: 120–240 spoken seconds; name the substantive disagreement, own partial responsibility, name the resolution move and its durability>_

---

## Q3. Tell me about a time you failed.

**Structure: PARLA.** **What a strong answer covers.** Picks a
real failure — a project that did not ship, a launch that missed
its target by a margin large enough that the candidate had to
own it, a hire that didn't work out — not a "failure" that was
secretly a success ("I worked too hard and burned out") or a
near-miss that recovered. Names the specific outcome that made
it a failure (a number, a project cancellation, a customer
loss). Owns the candidate's role in causing it: not "the team
failed" or "we missed", but "I missed because [specific
decision]". The Learning move is load-bearing — a failure
answer without an articulated learning is the textbook anti-
pattern, and an articulated learning that's generic ("I learned
to communicate better") fails as hard as no learning at all. The
Application move closes the loop: what specifically the
candidate has done *since* that proves the learning stuck —
ideally a later situation where the candidate noticed the same
pattern early enough to change the outcome. The trap to avoid:
choosing a failure so small it doesn't read as a real failure,
or choosing one so large it raises hiring concerns (a fired-from-
a-job story is too large for this question unless the candidate
has a concrete and credible post-mortem). A second trap:
choosing a failure where the cause was entirely external —
interviewers will probe for the candidate's own contribution
and an answer with no internal cause reads as evasive.

**Your draft:** _<your draft answer here — PARLA structure: 120–240 spoken seconds; pick a real failure with a measurable cost, own the internal cause, name the learning and a later instance where the learning was applied>_

---

## Q4. Tell me about a launch you're proud of.

**Structure: STAR.** **What a strong answer covers.** Names a
specific launch (a product, a feature, a release, a campaign)
with a date or quarter, not a general "I shipped a lot of
things." Frames *why* the candidate is proud — the move the
interviewer wants is "I am proud of this because [specific PM
craft signal: tight scope cut, stakeholder alignment under
constraint, a non-obvious metric design that caught a quiet
regression]," not "we shipped on time and customers liked it"
(which is the baseline, not the signal). The Result move names
a specific outcome that the launch caused — engagement number,
revenue impact, customer-segment unlock, a deprecation that
became safe to do — and ideally separates *signed* from
*attributable* impact, because conflating those two reads as
glossing. Names what the candidate *personally* did vs. what
the team did — the question is interviewing the candidate, not
the team. The trap to avoid: the launch that was a success by
volume but not by quality — interviewers are reading for whether
the candidate has internalized "shipped" as "shipped *and*
moved the metric the launch was supposed to move." A second
trap: pride in launches that any PM in that role would have
shipped (i.e., the launch was on the roadmap and the candidate
executed) — strong answers name a launch where the candidate
*shaped* the launch in some way that another PM might not have.

**Your draft:** _<your draft answer here — STAR structure: 120–240 spoken seconds; name the launch, the PM-craft reason for pride, the specific outcome, and what the candidate personally shaped>_

---

## Q5. Tell me about a time you operated in an ambiguous situation.

**Structure: STAR.** **What a strong answer covers.** Defines
what "ambiguous" meant in the specific situation — unclear
goal, unclear ownership, unclear timeline, unclear stakeholders,
unclear data — because "ambiguous" is the most overloaded
behavioral word and an answer that doesn't name *which kind*
of ambiguity reads as vague. Names the specific moves the
candidate made to *reduce* the ambiguity: writing a one-pager
to forcing a decision, scheduling a roundtable with the
stakeholders, designing a low-cost experiment to surface the
data, asking a manager an explicit "who decides this" question.
Owns the candidate's tolerance for sitting with ambiguity vs.
forcing premature closure — the strongest answers name the
trade-off ("I waited two weeks to gather more signal before
proposing a direction; in retrospect I could have moved faster
because [specific cost of waiting]"). Closes with the eventual
clarity that emerged and what role the candidate played in
producing it. The trap to avoid: framing ambiguity as a
problem the candidate suffered through ("it was confusing, I
asked my manager, eventually we figured it out") — the question
is reading for *productive* navigation, not endurance. A second
trap: claiming the candidate "thrives in ambiguity" without
ever sitting in the actual discomfort — a strong answer admits
that ambiguity costs something even when navigated well.

**Your draft:** _<your draft answer here — STAR structure: 120–240 spoken seconds; name the kind of ambiguity, name the specific moves that reduced it, own the trade-off between waiting and forcing closure>_

---

## Q6. Why are you leaving your current role? (or: Why are you on the market now?)

**Structure: Forward-looking framing.** **What a strong answer
covers.** The interviewer is screening for two things: (a) the
candidate's stated reason maps to a genuine driver the
interviewer can imagine, and (b) the candidate is not running
*from* something so much as running *toward* something. Strong
answers lead with the forward-looking driver (what the
candidate wants next, why now is the right time to move) and
back-anchor briefly to the current-role context (what the
current role offered, what its ceiling looks like for the
candidate's next phase). Names the *fit* between what the
candidate has built so far and what the next role would
extend — a credible career story has an arc, not a series of
unrelated jumps. The trap to avoid: leading with negatives
about the current role (manager, team, comp, culture) —
interviewers read these as the candidate likely repeating the
pattern in the next role. Even if the negative is real, frame
it as "the current role optimized for X; I'm now looking for
something that optimizes for Y" rather than "the current role
has problem X." A second trap: framing the move as financial
or logistical (visa, relocation, salary) — these may be true
but should not be the load-bearing answer to a "why are you
leaving" question, because they signal the candidate would
leave the next role for the same reasons.

**Your draft:** _<your draft answer here — 90–180 spoken seconds; lead with the forward-looking driver, name the arc, avoid framing the move as escape>_

---

## Q7. Why this role specifically?

**Structure: Fit framing.** **What a strong answer covers.** Three
moves: what the candidate knows about the role (specific to the
company, the team, the product surface — not generic AI-PM
prose), what about the candidate's specific background fits
this specific role (not "I'd be great at any AI PM role"), and
what about *this* role at *this* company makes it materially
different from the next-best alternative the candidate is
considering. Strong answers do their homework — they reference
something specific to the company that's hard to know without
having read recent product launches, engineering blog posts, or
public talks — and they name what *the candidate would do
differently* if they joined (a credible answer has at least one
opinion about something the company is doing that the
candidate would push on, not because the company is wrong but
because the candidate is a peer with views). The trap to
avoid: generic flattery ("you have an amazing team", "the
mission resonates with me") — interviewers screen for generic
answers because they read as "the candidate is interviewing
broadly and recycled the answer." A second trap: claiming
perfect fit ("this role is exactly what I've been preparing
for") — too tight a fit raises questions about whether the
candidate has growth headroom; some delta between current
strengths and role requirements is more credible than none.

**Your draft:** _<your draft answer here — 90–180 spoken seconds; show specific company knowledge, name the fit and the delta, surface at least one opinion you'd bring>_

---

## Q8. Why AI PM specifically — why now?

**Structure: POV framing.** **What a strong answer covers.** This
question is reading for *conviction* and *fluency*, not for the
candidate's resume narrative. Strong answers name a specific
view about AI products that the candidate holds — what makes AI
product work qualitatively different from non-AI product work
(stochastic outputs, evaluation as the central craft, capability
shifts on a 6-month cycle, agentic vs. assistive design
choices, the cost-of-error inversion in tool-using systems) —
and ground that view in something the candidate has built or
analyzed (cite the Cursor teardown, the rag-app build, the
tool-use-agent build, or the evals-harness build by name; this
portfolio exists specifically to make this question answerable
without bluff). The "why now" portion names what about the
current moment makes the candidate *able* to do AI PM work —
maturity of the underlying stack, presence of evaluation
tooling, hiring market — not a generic "AI is exciting." The
trap to avoid: the resume-restatement answer ("I've always
been interested in AI, I took these courses, I did these
side projects") — the question is interviewing for *thinking*,
not for credentials. A second trap: AI-hype prose
("transformative", "world-changing") — strong answers stay
specific and avoid the register interviewers associate with
candidates who are reading from a script.

**Your draft:** _<your draft answer here — 90–180 spoken seconds; name a specific view, cite a portfolio artifact by name, ground "why now" in stack maturity not hype>_

---

## Q9. What's your biggest strength?

**Structure: Claim + Evidence + Edge.** **What a strong answer
covers.** Names *one* strength, specifically (e.g., "I am
unusually willing to make decisions on incomplete data" or "I
write proposals tight enough that they ship without three
revision rounds") rather than a portmanteau ("I'm analytical
and collaborative"). Backs the strength with one specific
piece of evidence — a project, a habit, a documented artifact
the interviewer can verify — not "people I work with would say
this about me." Names the *edge* the strength has: where the
strength becomes a liability (the decisive-with-incomplete-
data candidate has to acknowledge they sometimes commit before
they should) — strong answers volunteer the limitation before
the interviewer probes for it, because the move signals
self-awareness. The trap to avoid: humblebrag strengths ("I
work too hard", "I care too much") — these are read as
evasive. A second trap: strengths so generic they read as
recycled ("strong communication", "a team player") — strong
answers pick an unusual strength specifically because the
interviewer has heard the common ones a dozen times that
week.

**Your draft:** _<your draft answer here — 90–180 spoken seconds; pick one specific strength, ground it in one piece of evidence, volunteer the edge>_

---

## Q10. What's your biggest weakness?

**Structure: PARLA — modified.** **What a strong answer covers.**
Names a *real* weakness, not a strength-in-disguise. The
weakness is plausible for the role (an engineering candidate
admitting to weak technical depth would not pass the screen;
a PM candidate admitting they sometimes over-commit to
deadlines is plausible and verifiable). Names the specific
cost the weakness has produced (a missed deadline, a
stakeholder who got frustrated, a launch that landed rougher
than it should have) — the cost is the part that proves the
weakness is real. Names the *system* the candidate uses to
manage the weakness (a habit, a checklist, a partner who
covers, a coach the candidate works with) — strong answers
demonstrate active management, not denial. Names a specific
recent instance where the system caught the weakness before
it caused damage. The trap to avoid: weaknesses framed as
strengths ("I'm a perfectionist", "I work too hard") — these
fail loudly and are read as the candidate not having an
honest self-assessment. A second trap: a weakness so severe
it raises hiring concerns (struggles with deadlines, can't
work with engineers, can't take feedback) — calibrate to a
weakness the interviewer can imagine living with for two years
without it being a problem. A third trap: the weakness the
candidate has obviously fixed ("I used to be bad at X but
I've solved it") — a weakness that has been fully resolved
reads as not a current weakness, which dodges the question.

**Your draft:** _<your draft answer here — 90–180 spoken seconds; pick a real, plausible weakness; name the cost it has produced; name the system you use to manage it; cite a recent instance>_

---

## Q11. What kind of manager do you work best with?

**Structure: Preferences + Adaptability.** **What a strong
answer covers.** Names the candidate's actual preferences
specifically (autonomy with weekly written check-ins, a
manager who gives crisp feedback rather than indirect signals,
a manager who shields the team from political noise) rather
than generic preferences ("supportive", "communicative"). Pairs
preferences with adaptability — names a manager style the
candidate has worked under that wasn't the preferred style and
how the candidate adapted, because no candidate gets to pick
their manager and the interviewer is reading for whether the
candidate can function under styles other than their first
choice. Implicitly answers the inverse question the
interviewer is also asking ("what kind of manager are *you*?"
if the role is people-managing) — strong answers signal
self-awareness about the candidate's own management style if
applicable. The trap to avoid: describing the *current*
manager (positively or negatively) as if they are the standard
— strong answers stay forward-looking. A second trap:
claiming to work well under all styles — interviewers read
this as evasion, because every candidate has a preferred
style and pretending not to is itself a signal about whether
the candidate has honest self-awareness.

**Your draft:** _<your draft answer here — 90–180 spoken seconds; name specific preferences, pair with adaptability, name a non-preferred-style manager you worked under and how you adapted>_

---

## Q12. Tell me about a time you influenced without authority.

**Structure: STAR.** **What a strong answer covers.** Names a
specific situation where the candidate did not have the
positional authority to make the decision (the candidate did
not own the engineering team, the design call, the budget, the
hiring slot) but the candidate's view shaped the outcome
anyway. Names the *mechanism* of influence — written proposal,
data pull, narrative reframing of the problem, building
allies, escalation path — not the emotional register ("I
listened a lot", "I built trust") which is too vague to read
as a real move. Owns that influence-without-authority is
slower than authority-with-authority — strong answers name the
patience cost. Names the eventual decision-maker who *did*
have authority and how the candidate's input was visible in
their decision. The trap to avoid: framing the influence as
manipulation or persuasion theater — the question is reading
for *substantive* influence (your view, well-argued, made the
decision better) not for political maneuvering. A second
trap: influencing in a context where the candidate did
actually have authority (e.g., a manager described as
"informal authority") — the question is reading for genuine
cross-team or cross-functional influence, not for managing
direct reports.

**Your draft:** _<your draft answer here — STAR structure: 120–240 spoken seconds; name the mechanism of influence, name the eventual decision-maker, own the patience cost>_

---

## Q13. Tell me about a cross-functional conflict you navigated.

**Structure: STAR.** **What a strong answer covers.** Picks a
conflict between *functions* (engineering vs. design,
product vs. legal, marketing vs. CS) not between
*individuals* — the latter is Q2 territory; this question is
reading for whether the candidate can hold the legitimate
interests of two functions in mind simultaneously. Names what
each function was optimizing for and why their goals were in
tension at the specific moment of the conflict. Names a
*structural* resolution, not a relational one — a single
escalation that resolved the personalities involved doesn't
solve a cross-functional conflict; what solves it is naming
the trade-off explicitly, getting a decision-rights call from
the right authority, or proposing a mechanism (a metric, a
review cadence, a charter) that lets the two functions
re-coordinate without ad-hoc friction next time. Closes with
how the relationship between the functions held after the
conflict — strong answers note that the candidate is still in
regular contact with their counterpart on the other function,
or that a follow-on conflict went easier because the precedent
was set. The trap to avoid: framing the conflict in moral
terms ("engineering didn't care about users", "legal blocked
everything") — both functions had legitimate interests, and
the answer that doesn't acknowledge that reads as the
candidate not understanding what the other function does. A
second trap: a conflict where the candidate's own function
was uniformly right — strong answers admit some of what the
other function pushed for ended up making the product better.

**Your draft:** _<your draft answer here — STAR structure: 120–240 spoken seconds; pick a conflict between functions, name what each was optimizing for, name a structural resolution, note the durability>_

---

## Q14. Tell me about a time you said no to a stakeholder.

**Structure: STAR.** **What a strong answer covers.** Names the
specific stakeholder (function and seniority — "the head of
sales", "an engineering tech lead", "a CS director") and the
specific ask, and why saying no was the right call (the ask
conflicted with a user need, with a quality bar, with a
strategic direction the candidate had been entrusted to
hold). Names *how* the no was delivered — a written
counter-proposal, a one-on-one conversation, a re-framed
version of the underlying problem — strong answers describe
the no as a *productive* move that moved the relationship
forward, not a refusal that ended a conversation. Names the
stakeholder's response and whether the relationship held —
the question is partly reading for whether the candidate can
maintain stakeholder relationships through disagreement.
Names what changed *after* the no — strong answers describe a
follow-on conversation where the candidate did say yes to a
related ask, because a candidate who only ever says no is as
unhelpful as one who never says no. The trap to avoid:
saying no on principle without a substantive reason ("they
asked for something off-roadmap, so I said no") — strong nos
explain the *opportunity cost* the candidate was protecting.
A second trap: saying no to a peer when the question is
implicitly asking about saying no to someone with more
positional power than the candidate — interviewers read this
as the candidate dodging the harder version of the question.

**Your draft:** _<your draft answer here — STAR structure: 120–240 spoken seconds; name the stakeholder's role and seniority, name how the no was delivered, describe the productive follow-on>_

---

## Q15. Tell me about a wrong call you made and what you learned from it.

**Structure: PARLA.** **What a strong answer covers.** Picks a
genuinely wrong call — a decision that the candidate, with the
data they had at the time, made a defensible-but-wrong choice
on — distinct from a failure caused by execution or
external events (which is Q3 territory). The cleanest signal
is a call the candidate made *against* a colleague's stated
view and the colleague turned out to be right. Names the
specific decision and the specific data the candidate had at
the time — interviewers read the rigor of the data
description as a proxy for whether the candidate is being
honest about the call rather than reverse-engineering a
flattering version of it. Names the moment the candidate
realized the call was wrong and how they signaled that
publicly (apology, written retrospective, course correction
visible to the team). Names the structural learning — what
change in decision-making process the call produced, not just
"I learned to listen more." The Application move closes the
loop with a later instance where the candidate noticed the
same pattern early and made the better call. The trap to
avoid: framing the wrong call as not really wrong ("with the
data we had, it was the right call; the world just
changed") — strong answers admit some calls are wrong on
their own terms even with hindsight blocked out. A second
trap: choosing a wrong call so far back that the candidate
has had years to integrate the learning — the strongest
versions pick a wrong call from the last 12–24 months, which
demonstrates the candidate is still actively recalibrating.

**Your draft:** _<your draft answer here — PARLA structure: 120–240 spoken seconds; pick a genuinely wrong call against a stated colleague view, name the data you had, name the structural learning, name a later instance where the learning was applied>_

---

## What the interviewer is testing across all fifteen questions

Three meta-patterns interviewers read for, that no single answer
can demonstrate but a *coherent set* of answers should:

1. **Specificity.** Every answer is grounded in a specific
   time-bound situation with named stakeholders, dates,
   outcomes. Candidates who answer behaviorals in the abstract
   ("usually, when I have a conflict, I…") fail the screen
   even when the abstract framing is correct, because the
   abstract framing cannot be probed for honesty.
2. **Agency.** Every answer makes clear what the candidate
   personally did. Candidates who answer in the first-person
   plural ("we decided", "the team shipped") on more than two
   of the fifteen questions read as either uncomfortable
   claiming credit or unsure what they own — both are
   disqualifying for a PM hire.
3. **Calibration.** Strengths are sized to be plausible
   (Q9). Weaknesses are sized to be real (Q10). Failures are
   sized to be costly enough to be real but not so large
   they raise hiring concerns (Q3). Wrong calls are recent
   enough to demonstrate active recalibration (Q15).
   Calibration across these four is itself a signal — a
   candidate whose strength is "very strong" but whose
   weakness is "very mild" reads as not calibrated.

If a drafted answer can pass these three meta-patterns and
fits the per-question rubric, it is interview-ready. The
fifteen questions above are not exhaustive of the behavioral
surface — interviewers will improvise variants ("tell me
about a time you had to give difficult feedback", "tell me
about a time you missed a deadline", "tell me about a time
you onboarded onto a new domain") — but a candidate who has
drafted these fifteen has the patterns to improvise the
others in the room.

---

## Source of truth & cross-links

- **The user's own experience.** Unlike the four per-artifact
  Q&A banks in this directory, this bank has no upstream
  document to cite. The source-anchoring discipline is internal
  to the user's memory: every rubric names the *evidence type*
  a strong answer cites (a specific role, a measurable
  outcome, a named cross-functional partner, a dated decision)
  without naming the specifics, which only the user can
  supply. A drafted answer that fabricates the user's
  experience violates the no-fabrication rule at the
  story-level, the most consequential level for this bank.
- Per-artifact Q&A banks (NEXT_WORK item 7, sub-checkboxes 1–4):
  [`cursor-teardown.md`](cursor-teardown.md),
  [`rag-app.md`](rag-app.md),
  [`tool-use-agent.md`](tool-use-agent.md),
  [`evals-harness.md`](evals-harness.md). These four cover the
  candidate's PM-craft surface via actual built artifacts.
  Cross-link to them in answers to Q7 (this role) and Q8
  (why AI PM) — those questions specifically reward citing
  the portfolio by name as proof of the answer's grounding.
- Index file (NEXT_WORK item 7, sub-checkbox 5):
  [`README.md`](README.md). The prep-order and cross-artifact
  questions live there. Behavioral prep slots into the
  prep-order after the four per-artifact banks — the
  rationale is that the per-artifact prep gives the candidate
  the concrete artifacts to *cite* inside behavioral answers
  (especially Q4, Q7, Q8, Q12), so doing the behavioral bank
  first would mean drafting answers without their strongest
  cross-references available.
- The no-fabrication rule for the `_<your draft>_` slots:
  `../DECISIONS.md` (search for "no-fabrication"). The agent
  never drafts the user's answers; the slots are the user's
  to fill. For this bank specifically, fabrication would mean
  inventing the user's stories, projects, teams, timelines, or
  outcomes — the most consequential possible violation, because
  unlike a citation against a portfolio document (which an
  auditor can verify), a story about the user's lived
  experience cannot be cross-checked against any source the
  agent has access to.
- NEXT_WORK item 9 — this bank ships under sub-checkbox 1;
  sub-checkbox 2 updates `README.md` to add the behavioral
  bank to the index + prep order; sub-checkbox 3 ships the
  consolidating DECISIONS entry locking the question
  selection rationale, the STAR / PARLA rubric naming
  convention, the per-question source-anchoring rule (no
  fabricated stories), and the explicit deferral of the
  three remaining out-of-scope buckets (culture-fit,
  case-prompt, negotiation).

This file is interview-prep, not a deliverable for any specific
company. The questions and rubrics anticipate what a PM
interviewer is likely to probe on the canonical behavioral
surface; they are not sourced from any specific company's
interview process and make no claim to mirror one.
