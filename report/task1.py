#!/usr/bin/env python3
"""Task 1 figures from data/task1 (final runs, 25M warmup + 25M sim).

Usage: python3 report/task1.py
    rewrites data/task1/stats.csv from the logs, writes report/figures/t1_*.png

Per-trace plots compare IP-stride and SPP (the code defaults, IP table 32x4;
config DEFAULT below) against the no-prefetcher baseline, as in PS.pdf's examples. t1_ipt.png is the IP table
size sweep. Means over traces: geometric for speedup, arithmetic otherwise
(same as tools/exp.py). Accuracy is ChampSim's own (useful / issued).
"""
import re
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
# SPP's code default IP table (set bits, ways) and the config that ran it. The
# "spp" config ran the earlier 64x4 default, so it equals ipt 64x4 instead.
DEFAULT = (5, 4)
DEFAULT_CFG = "ipt.SPP_IPT_SET_BITS={}.SPP_IPT_WAYS={}".format(*DEFAULT)
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
    many = len(series) > 3       # too many bars to label each one
    fig, ax = plt.subplots(figsize=(10 if many else 6.4, 3.8 if many else 3.4))
    for i, (cfg, label, color) in enumerate(series):
        d = df[df.config == cfg].set_index("trace")[metric]
        vals = [d[t] for t in traces] + [mean(d, geo)]
        pos = x - 0.4 + w * (i + 0.5)
        ax.bar(pos, vals, w * 0.92, color=color, label=label)
        for p, v in ([] if many else zip(pos, vals)):
            ax.annotate(fmt.format(v), (p, v), xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, color=MUTED)
    if baseline is not None:
        ax.axhline(baseline, color=MUTED, ls="--", lw=1, label="Baseline (no prefetcher)")
    ax.axvline(len(traces) - 0.5, color=GRID, lw=1)
    ax.set_xticks(x, [t.replace("Trace", "Trace ") for t in traces] + ["Mean"])
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    n = len(series) + (baseline is not None)
    ax.legend(loc="lower left", ncols=min(n, 5), fontsize=8, bbox_to_anchor=(0, 1.0))
    fig.savefig(FIG / name)   # name may be an absolute path, which / keeps as is
    plt.close(fig)
    print(f"[task1] {Path(name).name}")


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
        colors = [SPP if (r[0], r[1]) == DEFAULT else IPS for r in rows]
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
    axes[0].set_title(f"Default ({1 << DEFAULT[0]}x{DEFAULT[1]}) in orange; y axes are zoomed", fontsize=9, color=MUTED, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "t1_ipt.png")
    plt.close(fig)
    print("[task1] t1_ipt.png")
    return rows


CATEGORICAL = ["#8a8985", "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
METRICS = {
    "ipc": "IPC", "speedup": "Speedup over baseline", "l1d_load_miss": "L1D load misses",
    "l1d_load_mpki": "L1D load MPKI", "l1d_accuracy_issued": "L1D prefetch accuracy, useful / issued (%)",
    "l1d_accuracy_resolved": "L1D prefetch accuracy, useful / (useful + useless) (%)",
    "l1d_pf_useful": "Useful L1D prefetches", "l1d_pf_useless": "Useless L1D prefetches",
    "l1d_coverage": "L1D coverage (%)", "l2c_load_mpki": "L2C load MPKI",
    "l2c_data_load_mpki": "L2C data load MPKI", "l2c_instr_load_mpki": "L2C instruction load MPKI",
}


def label(cfg):
    if cfg.startswith("ipt."):
        sb, w = (int(p.split("=")[1]) for p in cfg.split(".")[1:])
        return f"SPP {1 << sb}x{w}" + (" (default)" if (sb, w) == DEFAULT else "")
    return {"base": "Baseline", "ip_stride": "IP-stride", "spp": "SPP"}[cfg]


def all_metrics(df, out):
    """One grouped bar chart per stats.csv metric, every config except spp
    (identical to the ipt 64x4 point)."""
    cfgs = ["base", "ip_stride"] + sorted((c for c in df.config.unique() if c.startswith("ipt.")),
                                          key=lambda c: tuple(-int(p.split("=")[1]) for p in c.split(".")[1:]))
    for m, ylabel in METRICS.items():
        d = df[df.config.isin(cfgs)]
        # The baseline is 1 or 0 by definition for speedup and coverage, and NaN for accuracy.
        series = [(c, label(c), col) for c, col in zip(cfgs, CATEGORICAL)
                  if d[d.config == c][m].notna().all() and not (c == "base" and m in ("speedup", "l1d_coverage"))]
        ylim = None
        if m == "speedup":   # all within a few percent of 1: zoom in
            v = d[d.config != "base"][m]
            ylim = (min(v.min(), 1.0) - 0.005, v.max() + 0.005)
        bars(d, m, series, ylabel, out / f"{m}.png", geo=m == "speedup",
             baseline=1.0 if m == "speedup" else None, ylim=ylim, fmt="{:.3g}")


SPP_CLS = re.compile(r"SPP (uniform|pattern) candidates: (\d+) fills: (\d+) timely: (\d+) late: (\d+) accuracy: (\S+)")
SPP_HIST = re.compile(r"degree histogram:((?: \d+:\d+)+)")


def spp_internals(out):
    """SPP's own stats for the default config: uniform vs pattern prefetches,
    and the share of epochs spent at each degree."""
    traces = sorted(p.stem for p in (DATA / DEFAULT_CFG).glob("*.log"))
    logs = {t: (DATA / DEFAULT_CFG / f"{t}.log").read_text() for t in traces}
    x = np.arange(len(traces))
    names = [t.replace("Trace", "Trace ") for t in traces]

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for i, (cls, color) in enumerate((("uniform", IPS), ("pattern", SPP))):
        rows = [next(r for r in SPP_CLS.findall(logs[t]) if r[0] == cls) for t in traces]
        fills = [int(r[2]) + int(r[4]) for r in rows]          # filled + late = counted as issued
        acc = [float(r[5]) for r in rows]
        for ax, vals, fmt in ((axes[0], fills, "{:,}"), (axes[1], acc, "{:.1f}")):
            pos = x - 0.2 + 0.4 * i
            ax.bar(pos, vals, 0.37, color=color, label=cls.capitalize())
            for p, v in zip(pos, vals):
                ax.annotate(fmt.format(v), (p, v), xytext=(0, 2), textcoords="offset points",
                            ha="center", va="bottom", fontsize=7, color=MUTED)
    axes[0].set_ylabel("Prefetches counted as issued")
    axes[1].set_ylabel("SPP accuracy (%)")
    axes[1].set_ylim(0, 100)
    for ax in axes:
        ax.set_xticks(x, names)
        ax.legend(loc="lower left", ncols=2, fontsize=8, bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(out / "spp_classes.png")
    plt.close(fig)
    print("[task1] spp_classes.png")

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    w = 0.8 / len(traces)
    for i, (t, color) in enumerate(zip(traces, CATEGORICAL[1:])):
        hist = dict(map(int, kv.split(":")) for kv in SPP_HIST.search(logs[t]).group(1).split())
        total = sum(hist.values())
        ds = sorted(hist)
        ax.bar(np.array(ds) - 0.4 + w * (i + 0.5), [100 * hist[d] / total for d in ds], w * 0.92,
               color=color, label=names[i])
    ax.set_xticks(ds)
    ax.set_xlabel("Prefetch degree")
    ax.set_ylabel("Epochs at this degree (%)")
    ax.legend(loc="upper left", fontsize=8)
    fig.savefig(out / "spp_degree.png")
    plt.close(fig)
    print("[task1] spp_degree.png")


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    df = load()
    plots = DATA / "plots"
    plots.mkdir(exist_ok=True)
    all_metrics(df, plots)
    spp_internals(plots)
    pfs = [("ip_stride", "IP-stride", IPS), (DEFAULT_CFG, "SPP", SPP)]
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
    for cfg in ["base", "ip_stride", DEFAULT_CFG]:
        d = df[df.config == cfg]
        print(f"  {label(cfg):18s}", "  ".join(f"{c}={mean(d[c], c == 'speedup'):.4f}" for c in cols))
    print("IPT sweep (sets x ways: speedup, coverage)")
    for sb, w, s, c in rows:
        print(f"  {1 << sb:3d}x{w}: {s:.5f}  {c:.3f}")


if __name__ == "__main__":
    main()
