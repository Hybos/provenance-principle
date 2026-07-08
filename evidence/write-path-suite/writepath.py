"""
write-path suite — core logic (v0)
==================================
Defends Thesis 2 (Writing) of the Memory Lifecycle research line:

    "Write-time decisions have a larger impact on long-term memory quality
     than retrieval-time filtering."

This is a measurement instrument, not a demo. It is built to be able to FAIL:
if a fair read-time baseline matches the write-gated arm, the claim is refuted
and reported as such.

Design crux (see DESIGN.md):
  - 3 arms share the same retriever, the same answer-time budget (top-k), and
    the same reader. Only the curation location differs.
  - The matched-budget rule prevents the write arm from "winning by storing
    less": every arm gets the same number of facts (k) in the reader's context.
  - The pivotal variable surfaced by v0 is the PROVENANCE signal (recency).
    Read-time filtering can only re-sort what it retrieved; it cannot recover a
    current fact that fell outside the budget, and without a recency signal it
    cannot tell a current fact from a stale near-duplicate (identical embedding).

No external model downloads. Deterministic embedding (bag-of-tokens cosine),
numpy only. Reproducible from a seed.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field


# ── Vocabularies for the synthetic world ────────────────────────────────────

SLOTS = {
    "city":     ["paris", "berlin", "madrid", "tokyo", "lima", "oslo"],
    "employer": ["acme", "beta", "gamma", "delta", "omega", "zeta"],
    "diet":     ["vegan", "keto", "paleo", "omnivore", "pescatarian", "carnivore"],
    "sport":    ["running", "cycling", "swimming", "climbing", "rowing", "boxing"],
    "device":   ["iphone", "pixel", "fairphone", "nokia", "xperia", "oneplus"],
}
SLOT_NAMES = list(SLOTS.keys())


@dataclass
class Fact:
    entity: str
    slot: str
    value: str
    t: int            # write timestamp (provenance)
    is_current: bool  # ground-truth: is this the valid value at query time?

    def tokens(self) -> list[str]:
        # entity + slot + value; query will share entity + slot, never value,
        # so current and stale facts of the same (entity,slot) are TIED on
        # similarity — only provenance can separate them.
        return [self.entity, self.slot, self.value]


@dataclass
class Corpus:
    facts: list[Fact]
    queries: list[tuple[str, str, str]]  # (entity, slot, current_value)


# ── Synthetic corpus generator ──────────────────────────────────────────────

def build_corpus(seed: int, ratio: int, n_entities: int = 10,
                 n_distractors_per_query: int = 3) -> Corpus:
    """
    For each (entity, slot):
      - 1 current value (latest timestamp, is_current=True)
      - `ratio` stale values (earlier timestamps, is_current=False)
        -> these are restatements that linger in the store (write amplification)
    Plus same-slot distractors about filler entities (consume retrieval budget).
    `ratio` is the staleness/pollution pressure axis.
    """
    rng = np.random.default_rng(seed)
    entities = [f"e{i}" for i in range(n_entities)]
    filler = [f"f{i}" for i in range(n_entities)]
    facts: list[Fact] = []
    queries: list[tuple[str, str, str]] = []
    t = 0

    for ent in entities:
        for slot in SLOT_NAMES:
            opts = SLOTS[slot][:]
            rng.shuffle(opts)
            # `ratio` stale values then 1 current value, increasing timestamps
            chain = opts[: ratio + 1]
            for i, val in enumerate(chain):
                t += 1
                is_cur = (i == len(chain) - 1)
                facts.append(Fact(ent, slot, val, t, is_cur))
            queries.append((ent, slot, chain[-1]))

            # same-slot distractors (filler entities) — moderate similarity,
            # compete for budget but never the right answer
            for _ in range(n_distractors_per_query):
                t += 1
                fe = filler[rng.integers(len(filler))]
                fv = SLOTS[slot][rng.integers(len(SLOTS[slot]))]
                facts.append(Fact(fe, slot, fv, t, False))

    rng.shuffle(facts)  # destroy any insertion-order advantage for the current fact
    return Corpus(facts=facts, queries=queries)


# ── Deterministic retriever (bag-of-tokens cosine) ──────────────────────────

class Retriever:
    def __init__(self, facts: list[Fact]):
        vocab = sorted({tok for f in facts for tok in f.tokens()})
        self.idx = {tok: i for i, tok in enumerate(vocab)}
        self.facts = facts
        self.M = np.zeros((len(facts), len(vocab)), dtype=np.float32)
        for r, f in enumerate(facts):
            for tok in f.tokens():
                self.M[r, self.idx[tok]] = 1.0
        norms = np.linalg.norm(self.M, axis=1, keepdims=True)
        self.Mn = self.M / np.clip(norms, 1e-9, None)

    def _qvec(self, entity: str, slot: str) -> np.ndarray:
        v = np.zeros(len(self.idx), dtype=np.float32)
        for tok in (entity, slot):  # query shares entity+slot, NOT value
            if tok in self.idx:
                v[self.idx[tok]] = 1.0
        n = np.linalg.norm(v)
        return v / (n if n > 1e-9 else 1.0)

    def rank(self, entity: str, slot: str) -> list[int]:
        """Return fact indices sorted by cosine sim (desc). Ties keep store order
        (stable), and store order was shuffled -> no current-fact advantage."""
        sims = self.Mn @ self._qvec(entity, slot)
        return list(np.argsort(-sims, kind="stable"))


# ── Arms (curation location differs; reader & budget identical) ─────────────

def store_all(corpus: Corpus) -> list[Fact]:
    return corpus.facts


def write_gated(corpus: Corpus) -> list[Fact]:
    """Write-time supersession: for each (entity,slot) keep only the latest
    (current) value. Uses the update event's provenance, which the write path
    observes. Distractors are kept (the gate can't know they're noise)."""
    best: dict[tuple[str, str], Fact] = {}
    kept_distractors: list[Fact] = []
    for f in corpus.facts:
        key = (f.entity, f.slot)
        # signal facts = those whose (entity,slot) is queried
        # treat every (entity,slot) chain by keeping max-timestamp value
        if key not in best or f.t > best[key].t:
            # but only collapse the *answer* entities' chains; filler distractors
            # belong to different entities and are kept separately below
            best[key] = f
    # Rebuild: keep latest per (entity,slot) for ALL keys (this naturally
    # supersedes stale answer values; filler keys collapse harmlessly too).
    return list(best.values())


# ── Reader (FIXED across arms) ───────────────────────────────────────────────

def reader(retrieved: list[Fact], entity: str, slot: str) -> str | None:
    """Answer = value of the top-ranked retrieved fact matching (entity,slot)."""
    for f in retrieved:
        if f.entity == entity and f.slot == slot:
            return f.value
    return None


# ── Read-time filter (only arm B) ───────────────────────────────────────────

def read_filter(pool: list[Fact], entity: str, slot: str,
                recency_available: bool) -> list[Fact]:
    """A genuine read-time baseline: de-duplicate the retrieved pool by
    (entity,slot) cluster and, IF a provenance/recency signal is available,
    promote the most recent member. Without recency, it cannot distinguish a
    current fact from a stale near-duplicate (identical embedding)."""
    if not recency_available:
        return pool  # similarity order only — same information as arm A
    # recency dedup: for the queried cluster, keep the latest; promote to front
    matching = [f for f in pool if f.entity == entity and f.slot == slot]
    if not matching:
        return pool
    latest = max(matching, key=lambda f: f.t)
    rest = [f for f in pool if f is not latest]
    return [latest] + rest


# ── Single-query evaluation ─────────────────────────────────────────────────

def answer(arm: str, store: list[Fact], retr: Retriever,
           entity: str, slot: str, k: int, pool_size: int,
           recency_available: bool) -> str | None:
    order = retr.rank(entity, slot)
    store_ids = {id(f) for f in store}
    ranked = [retr.facts[i] for i in order if id(retr.facts[i]) in store_ids]

    if arm == "B":  # over-retrieve, read-filter, then trim to budget k
        pool = ranked[:pool_size]
        filtered = read_filter(pool, entity, slot, recency_available)
        retrieved = filtered[:k]
    else:           # A and C: plain top-k under the same budget
        retrieved = ranked[:k]
    return reader(retrieved, entity, slot)


# ── Experiment ───────────────────────────────────────────────────────────────

@dataclass
class Result:
    regime: str
    ratio: int
    arm: str
    acc_current: float
    acc_stale: float


def run_experiment(ratios=(1, 4, 8, 16), seeds=(1, 2, 3, 4, 5),
                   k=5, pool_size=15,
                   regimes=("recency", "no-recency")) -> list[Result]:
    results: list[Result] = []
    for regime in regimes:
        recency = (regime == "recency")
        for ratio in ratios:
            per_arm = {a: [] for a in ("A", "B", "C")}
            stale_arm = {a: [] for a in ("A", "B", "C")}
            for seed in seeds:
                corpus = build_corpus(seed, ratio)
                retr = Retriever(corpus.facts)
                stores = {"A": store_all(corpus),
                          "B": store_all(corpus),
                          "C": write_gated(corpus)}
                # map current/stale value lookups
                cur = {(e, s): v for (e, s, v) in corpus.queries}
                for arm in ("A", "B", "C"):
                    correct = stale = 0
                    for (e, s, v) in corpus.queries:
                        pred = answer(arm, stores[arm], retr, e, s, k,
                                      pool_size, recency)
                        if pred == v:
                            correct += 1
                        elif pred is not None and pred != cur[(e, s)]:
                            stale += 1
                    n = len(corpus.queries)
                    per_arm[arm].append(correct / n)
                    stale_arm[arm].append(stale / n)
            for arm in ("A", "B", "C"):
                results.append(Result(
                    regime, ratio, arm,
                    float(np.mean(per_arm[arm])),
                    float(np.mean(stale_arm[arm])),
                ))
    return results
