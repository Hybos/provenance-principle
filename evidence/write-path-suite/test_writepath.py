"""
Deterministic tests for the write-path suite.

These guard the three things a reviewer would poke at:
  1. the reader / judge behaves as specified
  2. retrieval ties current and stale facts (the core assumption)
  3. results are reproducible across runs (same seed -> same numbers)
  4. the headline conditional result holds

Run: pytest -q
"""

import numpy as np
from writepath import (
    Fact, build_corpus, Retriever, store_all, write_gated,
    reader, read_filter, answer, run_experiment, SLOT_NAMES,
)


# ── 1. reader / judge ────────────────────────────────────────────────────────

def test_reader_picks_top_ranked_matching_fact():
    facts = [
        Fact("e0", "city", "berlin", t=2, is_current=True),
        Fact("e0", "city", "paris", t=1, is_current=False),
    ]
    assert reader(facts, "e0", "city") == "berlin"
    assert reader(facts[::-1], "e0", "city") == "paris"  # order-sensitive, as specified


def test_reader_returns_none_when_no_match():
    facts = [Fact("e1", "diet", "vegan", t=1, is_current=True)]
    assert reader(facts, "e0", "city") is None


# ── 2. retrieval ties current and stale (the crux assumption) ────────────────

def test_current_and_stale_are_tied_in_similarity():
    facts = [
        Fact("e0", "employer", "acme", t=1, is_current=False),
        Fact("e0", "employer", "beta", t=2, is_current=True),
        Fact("e9", "employer", "acme", t=3, is_current=False),  # distractor
    ]
    retr = Retriever(facts)
    qv = retr._qvec("e0", "employer")
    sims = retr.Mn @ qv
    assert abs(sims[0] - sims[1]) < 1e-6          # current vs stale: tied
    assert sims[2] < sims[0] - 1e-6               # distractor: strictly lower


# ── 3. reproducibility ───────────────────────────────────────────────────────

def test_corpus_is_deterministic_per_seed():
    a = build_corpus(seed=7, ratio=4)
    b = build_corpus(seed=7, ratio=4)
    assert [f.tokens() for f in a.facts] == [f.tokens() for f in b.facts]
    assert a.queries == b.queries


def test_experiment_is_reproducible():
    r1 = run_experiment(ratios=(4,), seeds=(1, 2), regimes=("no-recency",))
    r2 = run_experiment(ratios=(4,), seeds=(1, 2), regimes=("no-recency",))
    assert [x.acc_current for x in r1] == [x.acc_current for x in r2]


# ── 4. write-gating removes stale; ground truth is the latest ────────────────

def test_write_gated_keeps_only_latest_per_slot():
    corpus = build_corpus(seed=1, ratio=8)
    gated = write_gated(corpus)
    seen = {}
    for f in gated:
        key = (f.entity, f.slot)
        assert key not in seen, "more than one fact per (entity,slot) after gating"
        seen[key] = f
    # every queried slot's surviving value is the current one
    cur = {(e, s): v for (e, s, v) in corpus.queries}
    for (e, s), f in seen.items():
        if (e, s) in cur:
            assert f.value == cur[(e, s)]


# ── 5. the headline conditional result ───────────────────────────────────────

def test_thesis_is_conditional_on_provenance():
    res = run_experiment(ratios=(8,), seeds=(1, 2, 3), k=5, pool_size=15)
    def acc(regime, arm):
        return next(r for r in res if r.regime == regime and r.arm == arm).acc_current

    # with provenance, read-filter compensates: B ties C
    assert abs(acc("recency", "B") - acc("recency", "C")) < 0.05
    # without provenance, write-gating wins by a wide margin
    assert acc("no-recency", "C") - acc("no-recency", "B") > 0.5
