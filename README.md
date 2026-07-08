# The Provenance Principle

A research program on agent memory, built around one claim:

> **Reads cannot recover what writes discarded.**
> The quality of a memory system is not a property of its storage or its retrieval. It is a
> property of how much evidence about the origin, validity and invalidation of each fact the
> system preserves. A memory is a belief ledger: writes are assertions with evidence, aging is
> revision, forgetting is verifiable invalidation.

This repo is the canon: the current statement of the principle, the evidence behind it, and
the essays that develop it. Each essay is published as a gist for discussion and archived
here. The program advances by iterations; nothing here is final.

## Where this comes from

This program did not start as a publication plan. The questions turned concrete while working
on a system for a regulated domain (compliance management), where memory must answer what was
true on a date, who validated it, and whether a deletion really happened — obligations the
law imposes and agent memory, as usually built, cannot meet. The research stands on its own;
that project is why it exists.

## Why this claim and not another

Three external signals, plus one controlled illustration of ours, converged before the principle had a name:

1. A production study (external): among the failure modes found in a live multi-agent
   memory service, the one most relevant here is a write-path ordering failure that silently
   disabled supersession — invisible to design review.
   → arXiv:2606.24535
2. The field's own trajectory (external): a 2026 survey calls for moving evaluation from
   final-answer correctness to process-level accountability, and maps provenance relations
   (SUPPORT / CONTRADICT / INVALIDATE / UPDATE) as the missing infrastructure.
   → arXiv:2606.04990
3. Cross-domain persistence: temporal supersession — invalidating instead of overwriting —
   is the core primitive both in agent memory systems and in the versioning of legal norms.
   The convergence is not fully independent (bitemporal database ideas circulate in both),
   but both kept exactly this mechanism while agent memory at large dropped it.
4. A controlled toy of ours, offered as an intuition pump, not proof (its design favors the
   hypothesis; limitations documented): it makes one mechanism executable — embedding-equivalent
   contradictory facts are unorderable without provenance.
   → [`evidence/write-path-suite`](evidence/)

## The corollaries

The three lifecycle theses this program grew out of are corollaries of the principle:

- **Writing.** Write-time decisions dominate because writing is the only moment provenance
  can be captured. It is born in the write path or not at all.
- **Aging.** Stale memories get returned with confidence because, without provenance,
  currency is undecidable at read time.
- **Forgetting.** Deletion cannot be shown complete because deleting is one more mutation
  that requires its own evidence. Verifiable forgetting is a provenance problem.

## Iterations

| # | Essay | Status |
|---|-------|--------|
| I1 | Agent memory is an evidence problem, not a retrieval problem | drafted — [`essays/01-evidence-problem.md`](essays/01-evidence-problem.md) |
| I2 | A formal note: when currency is undecidable at read time | planned |
| I3 | Provenance-complete memory: design obligations per lifecycle operation | planned |
| I4 | Measuring provenance-completeness | planned |

## How this could be wrong

The principle is falsifiable. It fails if someone demonstrates a read-time mechanism that
reconstructs the validity and invalidation of contradictory facts with no provenance signal
preserved at write time — for instance, if content semantics alone were always enough to
order beliefs in time. Our experiment suggests this is impossible in the embedding-equivalent
case; I2 will try to state exactly when.

If you can break it, open an issue. A clean refutation is worth more to this program than
ten confirmations.

## Working method

See [`METHOD.md`](METHOD.md) — evidence standards, how iterations are produced, and how to
contribute.

## License

MIT. Cite the individual essays or this repo.
