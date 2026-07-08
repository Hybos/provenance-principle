# Validation verdict (Jun 2026) — frozen as v0

Expert review + self-critique. Status: frozen. This folder is linked from essay I1 as a
constructed illustration only — do not cite its numbers as findings. The three real defects,
kept public on purpose (the essay's argument does not depend on them being absent):
1. Generator saturation: each slot has 6 values, so `chain = opts[:ratio+1]` caps at 6.
   Ratios 8 and 16 are not real (max 6 stale). The curve's plateau from ratio 4 is an
   artifact of saturation, not a measured effect.
2. The no-recency read-filter baseline returns the pool unchanged → B == A. It does not
   compete; "defined to fail" without provenance.
3. The write-gated arm keeps max-timestamp per (entity,slot): structured entity + field +
   reliable timestamp + knowledge that new replaces old. That is *state supersession with
   structured provenance*, not generic "write-time gating".
Compounding: the corpus also forces the semantic tie. Three independent choices all push
toward the hypothesis → demonstration, not evidence.

Novelty problem: Selective Memory (arXiv:2603.15994) already makes the strong write-time
vs read-time claim with LLM eval and distractor scaling. T2's ceiling is "minimal mechanism
explainer", not a research contribution.

Narrow valid claim if revisited inside T1: "supersession/provenance must be captured before
retrieval; it is the base case of memory-lifecycle quality." Any future v1 needs a corpus
that *sometimes* gives read-time baselines recoverable signal, or the comparison stays
circular.

---

# Design notes

These are the notes I wrote before touching code, plus the conditions under which
the experiment is allowed to say I was wrong. They belong in the repo because the
result only means something if the design was fixed in advance.

## The claim

> Write-time decisions affect long-term memory quality more than retrieval-time
> filtering does.

It fails if `store-all + read filtering` matches `write-gated` on end-to-end answer
quality under a comparable budget. The whole thing is set up so that outcome is
reachable. If the read filter compensates, the table shows it and I report it.

## The three arms

All three share one retriever, one reader, and one answer-time budget. What changes
is where curation happens.

| arm | write | read | role |
|-----|-------|------|------|
| A, store-all | accept everything | raw top-k | naive floor |
| B, store-all + read filter | accept everything | over-retrieve, dedup, prefer recent, trim to k | the read-time competitor |
| C, write-gated | supersede stale on write | raw top-k | the write-time arm |

The point of the experiment is whether C beats B. Without a real B, nothing is being
tested. The old version of this piece compared write-gating against store-all + top-1,
which is not a read-time strategy at all, just a missing baseline. Here B over-retrieves
and applies recency-aware dedup before trimming, so it is a fair opponent.

## Matched budget

The easy mistake is letting the write gate store less and then declaring it the winner
because there is less noise around. That proves nothing except that less noise helps.

So every arm gets the same context budget at answer time: the same number of facts in
front of the reader. The question that isolates is whether what you stored (C) matters
more than how you filter what you retrieved (B), given the same final context.

## What is held constant

Same embedding model and same top-k for the retriever. Same model, same prompt,
temperature 0 for the reader. Same signal facts across arms. Same budget. The only free
variable between B and C is the moment of curation: after retrieval for B, before
indexing for C.

## The gate

The write gate does two jobs. It rejects near-duplicates on novelty, and it supersedes
a contradicted fact when a newer value for the same field arrives. The second one is the
interesting half, and it connects straight to the aging thesis (T1). Superseding is a
write-time operation by nature. At read time you cannot reliably tell which of two
contradictory facts is the current one without metadata that only exists if it was
written down. Arm B will try to recover it with a recency heuristic, and the experiment
measures how far short that falls.

This gives a reason to expect C to win, which is fine. It is a mechanism, not a guess.
It still gets measured and reported even if it does not hold.

## Dataset

v0 uses a synthetic generator. Each entity has fields that change over time; updates
invalidate the previous value. Noise comes from template distractors and from redundant
restatements. Questions ask for the current value of each field, and the correct answer
is known by construction, so scoring is exact-match with no LLM judge.

v1 will add a real slice (LongMemEval knowledge-update questions, or LoCoMo) to show the
effect is not an artifact of the generator. The synthetic part gives control and a clean
repro; the real slice gives external validity. Having both answers the "this is a toy"
objection up front.

## Metric

End-to-end answer accuracy, not retrieval precision. That was the main weakness of the
old version. The reader gets the retrieved context and returns the field value, which is
compared against the value that is current by construction.

Primary number: percentage of answers with the current value. Secondary, diagnostic:
percentage of answers with a stale value, which measures the cost of not superseding and
is the bridge to T1. Exact-match on categorical fields keeps it deterministic, free, and
auditable.

## Stress axes

Distractor and staleness pressure at ratios {1, 4, 8, 16}. At least 5 seeds per point,
reported as mean. The output is a curve: pressure on the x-axis, accuracy on the y, one
line per arm.

## Reading the outcome

- C above B, gap widening under pressure, bands apart: claim supported.
- C roughly equal to B across the range: claim refuted, read filtering compensates.
- C above B only when novelty gating is off: the effect is supersession, not novelty.
  That refines the thesis instead of breaking it.

## Feasibility, honestly

What makes it serious and not a toy: a real read-time baseline plus matched budget, a
deterministic end-to-end metric, two datasets, and a design that can fail.

What costs and where the risk sits. An LLM reader would mean API cost, so v0 uses a
rule-based reader instead, which is fully deterministic and free; the LLM reader is a v1
option. Arm B has to be an honest effort, recency plus rerank, not a straw man, because
that is exactly where a critic would push. The real-data slice adds work and can land as
v1.1 after the synthetic version ships.

Effort: v0 (synthetic, rule-based reader, all three arms, curve, 5 seeds) is a small
repo, two to three days. v1 (LLM reader plus real slice) is another two or three. It is
a repo, not a gist, though it can carry a gist teaser with the main curve.

When to pivot to T1: if B turns out as good as C on the synthetic data, or if building an
honest B becomes a project in itself, drop to T1 and send T2 back to the backlog with
whatever was learned.
