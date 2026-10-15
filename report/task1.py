#!/usr/bin/env python3
"""Task 1 figures from data/task1 (final runs, 25M warmup + 25M sim).

Usage: python3 report/task1.py
    rewrites data/task1/stats.csv from the logs, writes report/figures/t1_*.png,
    and prints the numbers the report quotes.

"SPP" is the code default: IP table 16 sets x 6 ways, no prefetch distance,
i.e. the sweep point DEFAULT_CFG. The "spp" config directory is not used: its
logs are from an earlier SPP (64x4 IP table, 1024-entry pattern table).
Means over traces: geometric for speedup, arithmetic otherwise (same as
tools/exp.py). Accuracy is ChampSim's own (useful / issued to L2).
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

SETS, WAYS, DISTS = (4, 5, 6), (4, 6, 8), (0, 1, 2, 3, 4)   # the sweep in exp/task1.toml
DEFAULT = (4, 6)                                             # code default: (set bits, ways)


def cfg(sb, w, d=0):
    return f"ipt.SPP_IPT_SET_BITS={sb}.SPP_IPT_WAYS={w}.DISTANCE={d}"


DEFAULT_CFG = cfg(*DEFAULT)

BASE, IPS, SPP = "#8a8985", "#2a78d6", "#eb6834"      # gray baseline, categorical slots 1 and 2
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # categorical slots 1-4, in order
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
    df = exp.parse(configs, traces, DATA)
    # SPP's storage line, from one log per config (it does not depend on the trace).
    store = {}
    for c in df.config.unique():
        m = re.search(r"SPP storage bits: IPT (\d+)x(\d+) PT (\d+)x(\d+) RPF (\d+)x(\d+) ctrl (\d+) total (\d+)",
                      (DATA / c / "Trace1.log").read_text())
        if m:
            v = list(map(int, m.groups()))
            store[c] = {"ipt": v[0] * v[1], "ipt_entry": v[1], "pt": v[2] * v[3], "rpf": v[4] * v[5],
                        "ctrl": v[6], "total": v[7]}
    return df, store


def summary(df, c):
    d = df[df.config == c]
    return {m: mean(d[m], m == "speedup") for m in
            ("ipc", "speedup", "l1d_load_mpki", "l1d_accuracy_issued", "l1d_coverage", "l1d_pf_late_pct")}


def note(ax, x, y, text, size=7):
    ax.annotate(text, (x, y), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom",
                fontsize=size, color=MUTED)


def save(fig, name):
    fig.savefig(FIG / name)
    plt.close(fig)
    print(f"[task1] {name}")


# ---- mandatory plots: IP-stride and SPP against the baseline, per trace -------------------
def bars(df, metric, series, ylabel, name, geo=False, baseline=None, ylim=None, fmt="{:.2f}"):
    traces = sorted(df.trace.unique())
    x = np.arange(len(traces) + 1)
    w = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for i, (c, label, color) in enumerate(series):
        d = df[df.config == c].set_index("trace")[metric]
        vals = [d[t] for t in traces] + [mean(d, geo)]
        pos = x - 0.4 + w * (i + 0.5)
        ax.bar(pos, vals, w * 0.92, color=color, label=label)
        for p, v in zip(pos, vals):
            note(ax, p, v, fmt.format(v))
    if baseline is not None:
        ax.axhline(baseline, color=MUTED, ls="--", lw=1, label="Baseline (no prefetcher)")
    ax.axvline(len(traces) - 0.5, color=GRID, lw=1)
    ax.set_xticks(x, [t.replace("Trace", "Trace ") for t in traces] + ["Mean"])
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.legend(loc="lower left", ncols=4, fontsize=8, bbox_to_anchor=(0, 1.0))
    save(fig, name)


def mandatory(df):
    pfs = [("ip_stride", "IP-stride", IPS), (DEFAULT_CFG, "SPP", SPP)]
    withbase = [("base", "Baseline", BASE)] + pfs
    bars(df, "speedup", pfs, "Speedup over baseline", "t1_speedup.png", geo=True, baseline=1.0,
         ylim=(0.95, 1.05), fmt="{:.3f}")
    bars(df, "ipc", withbase, "IPC", "t1_ipc.png", fmt="{:.3f}")
    bars(df, "l1d_load_mpki", withbase, "L1D load MPKI", "t1_mpki.png")
    bars(df, "l1d_accuracy_issued", pfs, "L1D prefetch accuracy (%)", "t1_accuracy.png", ylim=(0, 100), fmt="{:.1f}")
    bars(df, "l1d_coverage", pfs, "L1D coverage (%)", "t1_coverage.png", fmt="{:.1f}")


# ---- design choices ------------------------------------------------------------------------
def ipt_sweep(df):
    """Speedup and coverage for each IP table size (sets x ways), no distance."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
    for ax, m, ylabel, fmt in ((axes[0], "speedup", "Speedup (geomean)", "{:.4f}"),
                               (axes[1], "l1d_coverage", "L1D coverage (%, mean)", "{:.2f}")):
        x = np.arange(len(SETS))
        w = 0.8 / len(WAYS)
        allv = []
        for i, ways in enumerate(WAYS):
            vals = [summary(df, cfg(sb, ways))[m] for sb in SETS]
            allv += vals
            pos = x - 0.4 + w * (i + 0.5)
            ax.bar(pos, vals, w * 0.92, color=SERIES[i], label=f"{ways} ways")
            for p, v, sb in zip(pos, vals, SETS):
                note(ax, p, v, fmt.format(v) + ("*" if (sb, ways) == DEFAULT else ""), size=6)
        lo, hi = min(allv), max(allv)
        ax.set_ylim(lo - (hi - lo) * 0.8, hi + (hi - lo) * 0.5)
        ax.set_xticks(x, [f"{1 << sb} sets" for sb in SETS])
        ax.set_ylabel(ylabel)
    axes[0].legend(loc="lower left", ncols=3, fontsize=8, bbox_to_anchor=(0, 1.0))
    axes[1].set_title("* = default (16 x 6); y axes zoomed", fontsize=8, color=MUTED, loc="right")
    fig.tight_layout()
    save(fig, "t1_ipt.png")


def storage(df, store):
    """Left: SPP storage per structure for each IP table size. Right: speedup against total storage."""
    pts = sorted(((sb, w) for sb in SETS for w in WAYS), key=lambda p: store[cfg(*p)]["total"])
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4), gridspec_kw={"width_ratios": [1.4, 1]})
    ax = axes[0]
    x = np.arange(len(pts))
    bottom = np.zeros(len(pts))
    for (k, label), color in zip((("ipt", "IP table"), ("pt", "Pattern table"), ("rpf", "Recent-prefetch filter"),
                                  ("ctrl", "Throttle")), SERIES):
        vals = np.array([store[cfg(*p)][k] / 8 for p in pts])
        ax.bar(x, vals, 0.7, bottom=bottom, color=color, label=label, edgecolor="white", linewidth=0.5)
        bottom += vals
    for xi, b in zip(x, bottom):
        note(ax, xi, b, f"{b:,.0f}")
    ax.set_xticks(x, [f"{1 << sb}x{w}" + ("*" if (sb, w) == DEFAULT else "") for sb, w in pts], fontsize=8)
    ax.set_xlabel("IP table: sets x ways (* = default)")
    ax.set_ylabel("SPP storage (bytes)")
    ax.legend(loc="lower left", ncols=4, fontsize=7, bbox_to_anchor=(0, 1.0))
    ax = axes[1]
    for sb, w in pts:
        b, s = store[cfg(sb, w)]["total"] / 8, summary(df, cfg(sb, w))["speedup"]
        ax.scatter(b, s, s=40, color=SPP if (sb, w) == DEFAULT else IPS, zorder=3)
        ax.annotate(f"{1 << sb}x{w}", (b, s), xytext=(4, 3), textcoords="offset points", fontsize=7, color=MUTED)
    ax.set_xlabel("SPP storage (bytes)")
    ax.set_ylabel("Speedup (geomean)")
    ax.ticklabel_format(axis="y", useOffset=False)
    ax.grid(axis="x", color=GRID)
    fig.tight_layout()
    save(fig, "t1_storage.png")


def distance(df):
    """Speedup, coverage and lateness against the prefetch distance; one line per IP table size."""
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.0))
    for ax, m, ylabel in zip(axes, ("speedup", "l1d_coverage", "l1d_pf_late_pct"),
                             ("Speedup (geomean)", "L1D coverage (%)", "Late prefetches (%)")):
        for sb in SETS:
            for w in WAYS:
                vals = [summary(df, cfg(sb, w, d))[m] for d in DISTS]
                default = (sb, w) == DEFAULT
                ax.plot(DISTS, vals, color=SPP if default else BASE, lw=2 if default else 1,
                        alpha=1 if default else 0.5, marker="o" if default else None, ms=4,
                        label="Default (16 x 6)" if default else None, zorder=3 if default else 2)
        ax.set_xticks(DISTS)
        ax.set_xlabel("Prefetch distance (steps skipped)")
        ax.set_ylabel(ylabel)
    axes[0].plot([], [], color=BASE, lw=1, alpha=0.5, label="Other IP table sizes")
    axes[0].legend(loc="lower left", ncols=2, fontsize=8, bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    save(fig, "t1_distance.png")


SPP_CLS = re.compile(r"SPP (uniform|pattern) candidates: (\d+) fills: (\d+) timely: (\d+) late: (\d+) accuracy: (\S+)")
SPP_HIST = re.compile(r"degree histogram:((?: \d+:\d+)+)")


def internals():
    """For the default SPP: prefetches and accuracy of the uniform and pattern predictors,
    and the share of epochs spent at each degree. Returns the numbers for the report."""
    traces = sorted(p.stem for p in (DATA / DEFAULT_CFG).glob("*.log"))
    logs = {t: (DATA / DEFAULT_CFG / f"{t}.log").read_text() for t in traces}
    names = [t.replace("Trace", "Trace ") for t in traces]
    x = np.arange(len(traces))
    out = {}
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    for i, (cls, color) in enumerate((("uniform", IPS), ("pattern", SPP))):
        rows = [next(r for r in SPP_CLS.findall(logs[t]) if r[0] == cls) for t in traces]
        counted = [int(r[2]) + int(r[4]) for r in rows]         # filled + late = counted as issued
        acc = [float(r[5]) for r in rows]
        out[cls] = (counted, acc)
        pos = x - 0.2 + 0.4 * i
        for ax, vals, fmt in ((axes[0], counted, "{:,}"), (axes[1], acc, "{:.1f}")):
            ax.bar(pos, vals, 0.37, color=color, label=cls.capitalize())
            for p, v in zip(pos, vals):
                note(ax, p, v, fmt.format(v))
    axes[0].set_ylabel("Prefetches counted as issued")
    axes[1].set_ylabel("SPP accuracy (%)")
    axes[1].set_ylim(0, 100)
    for ax in axes:
        ax.set_xticks(x, names)
        ax.legend(loc="lower left", ncols=2, fontsize=8, bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    save(fig, "t1_classes.png")

    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    w = 0.8 / len(traces)
    hists = {}
    for i, t in enumerate(traces):
        h = dict(map(int, kv.split(":")) for kv in SPP_HIST.search(logs[t]).group(1).split())
        total = sum(h.values())
        hists[t] = {d: 100 * n / total for d, n in h.items()}
        ds = sorted(h)
        ax.bar(np.array(ds) - 0.4 + w * (i + 0.5), [hists[t][d] for d in ds], w * 0.92,
               color=SERIES[i], label=names[i])
    ax.set_xticks(ds)
    ax.set_xlabel("Prefetch degree")
    ax.set_ylabel("Epochs at this degree (%)")
    ax.legend(loc="upper left", fontsize=8)
    save(fig, "t1_degree.png")
    out["hist"] = hists
    return out


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    df, store = load()
    mandatory(df)
    ipt_sweep(df)
    storage(df, store)
    distance(df)
    inner = internals()

    cols = ["ipc", "speedup", "l1d_load_mpki", "l1d_accuracy_issued", "l1d_coverage", "l1d_pf_late_pct"]
    print("\nper trace")
    for c in ["base", "ip_stride", DEFAULT_CFG]:
        for _, r in df[df.config == c].sort_values("trace").iterrows():
            print(f"  {c[:22]:22s} {r.trace}", "  ".join(f"{k}={r[k]:.4f}" for k in cols),
                  f"fill_l2={r.l1d_pf_fill_l2:.0f} to_l2={r.l1d_pf_to_l2:.0f}")
    print("mean")
    for c in ["base", "ip_stride", DEFAULT_CFG]:
        print(f"  {c[:22]:22s}", "  ".join(f"{k}={v:.4f}" for k, v in summary(df, c).items()))
    print("IP table sweep, distance 0 (speedup, coverage, late %, storage bits / bytes, IPT entry bits)")
    for sb in SETS:
        for w in WAYS:
            s, st = summary(df, cfg(sb, w)), store[cfg(sb, w)]
            print(f"  {1 << sb:2d}x{w}: {s['speedup']:.4f} {s['l1d_coverage']:.2f} {s['l1d_pf_late_pct']:.1f}"
                  f"  {st['total']} / {st['total'] / 8:.2f}  entry {st['ipt_entry']}"
                  f"  ipt {st['ipt']} pt {st['pt']} rpf {st['rpf']} ctrl {st['ctrl']}")
    print("distance, default IP table (speedup, coverage, accuracy, late %)")
    for d in DISTS:
        s = summary(df, cfg(*DEFAULT, d))
        print(f"  d={d}: {s['speedup']:.4f} {s['l1d_coverage']:.1f} {s['l1d_accuracy_issued']:.1f} {s['l1d_pf_late_pct']:.1f}")
    print("speedup falls with every distance step for all sizes:",
          all(summary(df, cfg(sb, w, d))["speedup"] > summary(df, cfg(sb, w, d + 1))["speedup"]
              for sb in SETS for w in WAYS for d in DISTS[:-1]))
    print("classes (counted, accuracy):", inner["uniform"], inner["pattern"])
    print("degree histogram %:", {t: {d: round(v, 1) for d, v in h.items()} for t, h in inner["hist"].items()})


if __name__ == "__main__":
    main()
