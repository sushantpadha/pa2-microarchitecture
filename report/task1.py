#!/usr/bin/env python3
"""Task 1 figures from data/task1 (final runs, 25M warmup + 25M sim).

Usage: python3 report/task1.py
    rewrites data/task1/stats.csv from the logs, writes report/figures/t1_*.png

Per-trace plots compare IP-stride and SPP (the code defaults) against the
no-prefetcher baseline, as in PS.pdf's examples. t1_ipt.png is the IP table
size sweep. Means over traces: geometric for speedup, arithmetic otherwise
(same as tools/exp.py). Accuracy is ChampSim's own (useful / issued).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import exp  # noqa: E402

DATA = REPO / "data" / "task1"
FIG = REPO / "report" / "figures"

BASE, IPS, SPP = "#8a8985", "#2a78d6", "#eb6834"   # gray baseline, categorical slots 1 and 2
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "axes.axisbelow": True,
    "legend.frameon": False, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def mean(s, geo):
    return float(np.exp(np.log(s).mean())) if geo else float(s.mean())


def load():
    configs = exp.load_configs(REPO / "exp" / "task1.toml", None)[1]
    traces = {p.stem for p in (DATA / "base").glob("*.log")}
    return exp.parse(configs, traces, DATA)


def bars(df, metric, series, ylabel, name, geo=False, baseline=None, ylim=None, fmt="{:.2f}"):
    """Grouped bars: one group per trace plus a mean group, one bar per series."""
    traces = sorted(df.trace.unique())
    groups = traces + ["Mean"]
    x = np.arange(len(groups))
    w = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for i, (cfg, label, color) in enumerate(series):
        d = df[df.config == cfg].set_index("trace")[metric]
        vals = [d[t] for t in traces] + [mean(d, geo)]
        pos = x - 0.4 + w * (i + 0.5)
        ax.bar(pos, vals, w * 0.92, color=color, label=label)
        for p, v in zip(pos, vals):
            ax.annotate(fmt.format(v), (p, v), xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, color=MUTED)
    if baseline is not None:
        ax.axhline(baseline, color=MUTED, ls="--", lw=1, label="Baseline (no prefetcher)")
    ax.axvline(len(traces) - 0.5, color=GRID, lw=1)
    ax.set_xticks(x, [t.replace("Trace", "Trace ") for t in traces] + ["Mean"])
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.legend(loc="upper left", ncols=len(series) + (baseline is not None), fontsize=8,
              bbox_to_anchor=(0, 1.12))
    fig.savefig(FIG / name)
    plt.close(fig)
    print(f"[task1] {name}")


def ipt(df):
    """IP table sweep: speedup and coverage per (sets, ways), mean over traces."""
    d = df[df.config.str.startswith("ipt.")]
    rows = []
    for cfg, g in d.groupby("config"):
        sb, ways = int(g.SPP_IPT_SET_BITS.iloc[0]), int(g.SPP_IPT_WAYS.iloc[0])
        rows.append((sb, ways, mean(g.speedup, True), mean(g.l1d_coverage, False)))
    rows.sort(key=lambda r: ((1 << r[0]) * r[1], r[1]))
    labels = [f"{1 << sb}x{w}\n({(1 << sb) * w})" for sb, w, *_ in rows]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    for ax, k, ylabel, fmt in ((axes[0], 2, "Speedup (geomean)", "{:.4f}"),
                               (axes[1], 3, "L1D coverage (%, mean)", "{:.2f}")):
        vals = [r[k] for r in rows]
        colors = [SPP if (r[0], r[1]) == (6, 4) else IPS for r in rows]
        ax.bar(x, vals, 0.6, color=colors)
        lo, hi = min(vals), max(vals)
        pad = (hi - lo) * 0.6 or hi * 0.01
        ax.set_ylim(lo - pad, hi + pad)
        for p, v in zip(x, vals):
            ax.annotate(fmt.format(v), (p, v), xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, color=MUTED)
        ax.set_xticks(x, labels, fontsize=8)
        ax.set_xlabel("IP table: sets x ways (entries)")
        ax.set_ylabel(ylabel)
    axes[0].set_title("Default (64x4) in orange; y axes are zoomed", fontsize=9, color=MUTED, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "t1_ipt.png")
    plt.close(fig)
    print("[task1] t1_ipt.png")
    return rows


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    df = load()
    pfs = [("ip_stride", "IP-stride", IPS), ("spp", "SPP", SPP)]
    bars(df, "speedup", pfs, "Speedup over baseline", "t1_speedup.png", geo=True, baseline=1.0,
         ylim=(0.95, 1.05), fmt="{:.3f}")
    bars(df, "ipc", [("base", "Baseline", BASE)] + pfs, "IPC", "t1_ipc.png", fmt="{:.3f}")
    bars(df, "l1d_load_mpki", [("base", "Baseline", BASE)] + pfs, "L1D load MPKI", "t1_mpki.png")
    bars(df, "l1d_accuracy_issued", pfs, "L1D prefetch accuracy (%)", "t1_accuracy.png", ylim=(0, 100),
         fmt="{:.1f}")
    bars(df, "l1d_coverage", pfs, "L1D coverage (%)", "t1_coverage.png", fmt="{:.1f}")
    rows = ipt(df)

    cols = ["ipc", "speedup", "l1d_load_mpki", "l1d_accuracy_issued", "l1d_accuracy_resolved", "l1d_coverage"]
    print("\nmean over traces (speedup geomean)")
    for cfg in ["base", "ip_stride", "spp"]:
        d = df[df.config == cfg]
        print(f"  {cfg:10s}", "  ".join(f"{c}={mean(d[c], c == 'speedup'):.4f}" for c in cols))
    print("IPT sweep (sets x ways: speedup, coverage)")
    for sb, w, s, c in rows:
        print(f"  {1 << sb:3d}x{w}: {s:.5f}  {c:.3f}")


if __name__ == "__main__":
    main()
