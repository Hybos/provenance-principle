"""
write-path suite — experiment runner (v0)

Usage:
    python run.py                 # run full experiment, print table, dump JSON
    python run.py --plot          # also write curve PNG (needs matplotlib)

Arms:
    A  store-all                 (naive baseline / floor)
    B  store-all + read-filter   (the honest read-time competitor)
    C  write-gated               (write-time supersession)

Two regimes:
    recency      -> read path HAS the provenance signal the write path used
    no-recency   -> read path lacks it (common in production memory stores)
"""

from __future__ import annotations
import argparse
import json
from writepath import run_experiment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratios", type=int, nargs="+", default=[1, 4, 8, 16])
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--k", type=int, default=5, help="answer-time context budget")
    ap.add_argument("--pool", type=int, default=15, help="arm B over-retrieve pool")
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()

    results = run_experiment(tuple(args.ratios), tuple(args.seeds),
                             k=args.k, pool_size=args.pool)

    # ── table ────────────────────────────────────────────────────────────────
    print(f"\nbudget k={args.k}  |  arm B pool={args.pool}  |  seeds={args.seeds}")
    print("accuracy = % of queries answered with the CURRENT (valid) value\n")
    for regime in ("recency", "no-recency"):
        print(f"== regime: {regime} "
              f"({'read path HAS provenance' if regime=='recency' else 'read path LACKS provenance'}) ==")
        print(f"{'ratio':>6} | {'A store-all':>12} | {'B read-filter':>14} | {'C write-gated':>14} | {'C-B gap':>8}")
        print("-" * 70)
        for ratio in args.ratios:
            row = {r.arm: r for r in results if r.regime == regime and r.ratio == ratio}
            gap = row["C"].acc_current - row["B"].acc_current
            print(f"{ratio:>6} | {row['A'].acc_current:>12.2f} | "
                  f"{row['B'].acc_current:>14.2f} | {row['C'].acc_current:>14.2f} | {gap:>8.2f}")
        print()

    # ── verdict ───────────────────────────────────────────────────────────────
    def gap_for(regime):
        gaps = [
            next(r for r in results if r.regime == regime and r.ratio == ra and r.arm == "C").acc_current
            - next(r for r in results if r.regime == regime and r.ratio == ra and r.arm == "B").acc_current
            for ra in args.ratios
        ]
        return max(gaps)

    g_rec, g_norec = gap_for("recency"), gap_for("no-recency")
    print("VERDICT")
    print(f"  recency regime    max(C-B) = {g_rec:+.2f}  "
          f"-> {'read filtering compensates (claim NOT supported here)' if g_rec < 0.1 else 'write gating wins'}")
    print(f"  no-recency regime max(C-B) = {g_norec:+.2f}  "
          f"-> {'write gating wins (claim supported here)' if g_norec >= 0.1 else 'read filtering compensates'}")
    print("  => Thesis 2 holds CONDITIONALLY on the provenance signal.\n"
          if (g_rec < 0.1 <= g_norec) else
          "  => see table; interpret honestly.\n")

    payload = [r.__dict__ for r in results]
    with open(args.out, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"wrote {args.out}")

    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
            for ax, regime in zip(axes, ("recency", "no-recency")):
                for arm, label in (("A", "store-all"), ("B", "store-all+read-filter"),
                                   ("C", "write-gated")):
                    ys = [next(r for r in results if r.regime == regime
                               and r.ratio == ra and r.arm == arm).acc_current
                          for ra in args.ratios]
                    ax.plot(args.ratios, ys, marker="o", label=label)
                ax.set_title(f"regime: {regime}")
                ax.set_xlabel("staleness/pollution ratio")
                ax.set_ylim(0, 1.05)
                ax.grid(alpha=0.3)
            axes[0].set_ylabel("accuracy (current value)")
            axes[1].legend(loc="lower left", fontsize=8)
            fig.tight_layout()
            fig.savefig("curve.png", dpi=130)
            print("wrote curve.png")
        except ImportError:
            print("matplotlib not available — skipped plot")


if __name__ == "__main__":
    main()
