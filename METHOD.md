# Working method

This file is the operating base of the program. It exists so that a new researcher can join
by reading one document, and so that the program survives its authors' enthusiasm. If a
contribution does not fit these rules, the rules win.

## The unit of work

The unit of work is the **iteration**: one essay that advances the principle by exactly one
step. Not a paper, not a benchmark, not a demo. An iteration is done when it states something
that was not stated before AND says how that statement could be wrong.

Every iteration has the same anatomy:

1. **Claim** — one falsifiable or derivable statement, written first, before any prose.
2. **Evidence** — what supports it, with verified sources. Own experiments live in
   `evidence/`; external work is cited by verified arXiv ID (fetch the abstract before
   citing — this program has been burned by unverified IDs before).
3. **Refutation condition** — what observation would kill the claim. If none can be written,
   the claim is an opinion and does not ship.
4. **Boundary** — what the claim does NOT say. Overclaiming is the main reputational risk;
   every essay carries an explicit limitations section.

## Evidence standards

- An arXiv ID is citable after fetching its abstract page and confirming title/topic. Any
  claim about a paper's methods, numbers, production setting or limitations additionally
  requires reading the relevant section of the paper itself — the abstract is not enough.
- Numbers from our own experiments must be reproducible from a seed, from code in
  `evidence/`, by a stranger, in minutes, without API keys where possible.
- Numbers from papers are quoted with their scope ("author-reported, N=87 cases") — never
  laundered into general truths.
- Production claims require a production source. Design-paper claims are labeled as such.

## Writing rules

- English, plain engineering register. It must read as written by a person: no decorative
  triads, no "the key insight is", no bullet-point parallelism, varied sentence length,
  admits uncertainty without hedging formulas. (Full list in the project's governance.)
- The claim appears in the first three paragraphs. Limitations before the close.
- Strategy layer (why it matters for builders/CTOs) is 3–5 sentences, at the end, never
  mixed into the argument.

## Publication flow

1. Essay is drafted in `essays/NN-name.md` and reviewed against this METHOD.
2. Published as a **markdown gist** (the conversation surface — comments and revisions live
   there), linking back to this repo (the canon).
3. Distribution is by commenting on existing active conversations with audience, linking the
   gist. No own posts on LinkedIn or blogs. No arXiv for now.
4. Feedback from gist comments feeds the next revision or the next iteration. Substantive
   objections get recorded in the essay's changelog, with credit.

## Roles (for when more researchers join)

- **Author** — owns one iteration end to end: claim, evidence, essay, revisions.
- **Adversary** — assigned per iteration; their only job is to attack the claim before
  publication (find the WritePolicyBench-style misattribution, the straw-man baseline, the
  unverified ID). No essay ships without surviving an adversary pass.
- **Curator** — keeps the canon consistent: README current, evidence reproducible, watchlist
  updated.

One person can hold several roles today; the separation matters more than the headcount.
Authorship of each essay is explicit (name on the gist); the program is citable as a whole.

## Priority watchlist

The program's window is open but not empty. Watch for anyone articulating the same principle:
the provenance survey authors (arXiv:2606.04990), the Zep/Graphiti team (bitemporal
invalidation), Kumiho's author (arXiv:2603.17244, AGM belief revision over versioned memory).
If someone gets there first, the correct move is to cite them and reposition, not to pretend
we did not see it.

## What this program refuses to do

- Ship a claim whose refutation condition cannot be written.
- Cite a paper nobody in the program has opened.
- Compete on benchmark numbers. Our experiments illustrate; they do not rank systems.
- Attack named products. Failure modes are discussed as patterns, with issue links where
  public, never as "X is broken".
