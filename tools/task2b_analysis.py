#!/usr/bin/env python3
"""Summarize the Task 2B sweep and hysteresis runs in data/.

Usage: tools/task2b_analysis.py
    writes data/task2b_sweep/analysis/ and data/task2b_hyst/analysis/:
    summary.csv and a few figures (see each run's README).

Every ratio is to static I-RRIP ("irrip", same rules as dyn_irrip's I-RRIP mode),
per trace, then a geometric mean over traces. "irrip_frac" is the fraction of
decisions (epochs) that chose I-RRIP, read from each log's DYN_IRRIP line; it
counts only decisions made after warmup.
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
MPKI = ["l2c_load_mpki", "l2c_instr_load_mpki", "l2c_data_load_mpki"]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.dpi": 160, "savefig.bbox": "tight"})


def geo(v):
    return float(np.exp(np.log(v).mean()))


def load(run):
    """stats.csv plus per-row ratios to irrip and the DYN_IRRIP epoch stats."""
    d = pd.read_csv(DATA / run / "stats.csv")
    ref = d[d.config == "irrip"].set_index("trace")
    for m in ["speedup", *MPKI]:
        d[m + "_r"] = d[m] / d.trace.map(ref[m])
    epochs, frac = [], []
    for c, t in zip(d.config, d.trace):
        m = re.search(r"^DYN_IRRIP epochs (\d+) irrip_frac (\S+)",
                      (DATA / run / c / f"{t}.log").read_text(errors="ignore"), re.M)
        epochs.append(int(m.group(1)) if m else np.nan)
        frac.append(float(m.group(2)) if m else np.nan)
    d["epochs"], d["irrip_frac"] = epochs, frac
    return d


def summary(d, knobs):
    """One row per config: knob values, trace means, ratios, and per-trace columns."""
    rows = []
    for c, g in d.groupby("config", sort=False):
        g = g.set_index("trace")
        row = {"config": c, **{k: g[k].iloc[0] for k in knobs if k in g}}
        row["speedup"] = geo(g.speedup)
        row["speedup_vs_irrip"] = geo(g.speedup_r)
        for m in MPKI:
            row[m] = g[m].mean()
            row[m + "_vs_irrip"] = geo(g[m + "_r"])
        for t in g.index:
            row[f"speedup_vs_irrip_{t}"] = g.loc[t, "speedup_r"]
            row[f"irrip_frac_{t}"] = g.loc[t, "irrip_frac"]
            row[f"epochs_{t}"] = g.loc[t, "epochs"]
        rows.append(row)
    return pd.DataFrame(rows)


def panel_grid(s, x, xs, series, panels, title, out, xlabel):
    """Rows: speedup and MPKI ratios to irrip; columns: one per panel value;
    lines: one per series value. s: summary rows of dyn configs only."""
    metrics = [("speedup_vs_irrip", "Speedup / I-RRIP"), ("l2c_instr_load_mpki_vs_irrip", "Instr. MPKI / I-RRIP"),
               ("l2c_data_load_mpki_vs_irrip", "Data MPKI / I-RRIP")]
    pkey, pvals = panels
    skey, svals = series
    fig, axes = plt.subplots(len(metrics), len(pvals), figsize=(2.6 * len(pvals), 6.2), sharey="row", squeeze=False)
    for j, pv in enumerate(pvals):
        for i, (m, label) in enumerate(metrics):
            ax = axes[i][j]
            for k, sv in enumerate(svals):
                g = s[(s[pkey] == pv) & (s[skey] == sv)].set_index(x).reindex(xs)
                ax.plot(range(len(xs)), g[m], "o-", ms=3, color=COLORS[k], label=f"{skey} {sv}")
            ax.axhline(1, color="#333333", linestyle="--", linewidth=0.8)
            ax.set_xticks(range(len(xs)), [str(v) for v in xs])
            ax.yaxis.grid(True, color="#dddddd", linewidth=0.5)
            if j == 0:
                ax.set_ylabel(label)
            if i == 0:
                ax.set_title(f"{pkey} {pv}")
            if i == len(metrics) - 1:
                ax.set_xlabel(xlabel)
    axes[0][0].legend(fontsize=7)
    fig.suptitle(title)
    fig.savefig(out)
    plt.close(fig)
    print(f"[task2b_analysis] {out.relative_to(DATA.parent)}")


def rrip_cost(d, out):
    """Per (config, trace): speedup lost vs never switching, against the fraction of
    decisions that chose RRIP. If the loss were just "time in RRIP x RRIP's loss",
    points would sit on the line from (0, 0) to (1, rrip's loss)."""
    dyn = d[d.irrip_frac.notna()].copy()
    dyn["n"] = dyn.config.str.extract(r"^n(\d+)\.")[0].astype(int)
    # never-switching reference for the same leader count: T = 0 (sweep) or the
    # config with the highest irrip_frac on all traces is not unique, so use T = 0
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    for k, t in enumerate(sorted(dyn.trace.unique())):
        g = dyn[dyn.trace == t]
        never = g[g.irrip_frac == 1].groupby("n").speedup_r.max()   # best never-switching per leader count
        loss = 1 - g.speedup_r / g.n.map(never)
        ax.scatter(1 - g.irrip_frac, loss * 100, s=10, color=COLORS[k], label=t)
        r = d[(d.config == "rrip") & (d.trace == t)].speedup_r.iloc[0]
        ax.plot([0, 1], [0, (1 - r) * 100], color=COLORS[k], linewidth=0.8, linestyle=":")
    ax.set_xlabel("Fraction of decisions that chose RRIP")
    ax.set_ylabel("Speedup lost vs never switching (%)")
    ax.yaxis.grid(True, color="#dddddd", linewidth=0.5)
    ax.legend(fontsize=7, title="dotted: linear in RRIP time", title_fontsize=6)
    fig.savefig(out)
    plt.close(fig)
    print(f"[task2b_analysis] {out.relative_to(DATA.parent)}")


def rrip_decisions(d, out):
    """Speedup vs the number of post-warmup decisions that chose RRIP: one figure per
    hysteresis value (out/rrip_decisions_h<h>.png), one panel per trace (traces make
    different numbers of decisions), the same axes in every figure. Mode switches are
    not logged; a run with k >= 1 RRIP decisions switched at least once, at most 2k times."""
    dyn = d[d.irrip_frac.notna()].copy()
    dyn["n"] = dyn.config.str.extract(r"^n(\d+)\.")[0].astype(int)
    dyn["e"] = dyn.config.str.extract(r"DYN_EPOCH=(\d+)")[0]
    dyn["h"] = dyn.config.str.extract(r"DYN_HYST=([\d.]+)")[0]
    dyn["rrip_dec"] = (dyn.epochs * (1 - dyn.irrip_frac)).round().astype(int)
    traces = sorted(dyn.trace.unique())
    rrip = d[d.config == "rrip"].set_index("trace").speedup_r
    markers = {"512": "o", "1024": "s"}
    for h in sorted(dyn.h.unique(), key=float):
        fig, axes = plt.subplots(1, len(traces), figsize=(8.4, 2.9))
        for ax, t in zip(axes, traces):
            g = dyn[dyn.trace == t]
            for k, n in enumerate(sorted(dyn.n.unique())):
                for e, mk in markers.items():
                    x = g[(g.n == n) & (g.e == e) & (g.h == h)]
                    ax.scatter(x.rrip_dec, x.speedup_r, s=22, marker=mk, color=COLORS[k],
                               label=f"{n} leaders" if e == "512" else None)
            ax.axhline(rrip[t], color="#333333", linestyle=":", linewidth=0.8, label="SRRIP")
            ax.axhline(1, color="#333333", linestyle="--", linewidth=0.8, label="I-RRIP")
            lo = min(rrip[t], g.speedup_r.min())
            ax.set_ylim(lo - 0.1 * (1 - lo), 1 + 0.1 * (1 - lo))
            ax.set_xlim(-0.5, max(dyn.rrip_dec.max(), 1) + 0.5)
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
            ax.set_title(t)
            ax.set_xlabel("Decisions that chose RRIP")
            ax.yaxis.grid(True, color="#dddddd", linewidth=0.5)
        axes[0].set_ylabel("Speedup / I-RRIP")
        for e, mk in markers.items():
            axes[-1].scatter([], [], marker=mk, color="#777777", s=22, label=f"epoch {e}")
        axes[-1].legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.02, 1))
        fig.suptitle(f"T = 0.15, h = {h}, placement 0: speedup vs RRIP decisions", y=1.03)
        f = out / f"rrip_decisions_h{h}.png"
        fig.savefig(f)
        plt.close(fig)
        print(f"[task2b_analysis] {f.relative_to(DATA.parent)}")


def rrip_decisions_summary(d, out, trace="Trace3", leaders=(8, 16, 32)):
    """One trace, one figure per epoch (out/rrip_decisions_summary_e<epoch>.png), one
    panel per hysteresis value: speedup vs RRIP decisions, one point per leader count."""
    g = d[(d.trace == trace) & d.irrip_frac.notna()].copy()
    g["n"] = g.config.str.extract(r"^n(\d+)\.")[0].astype(int)
    g["e"] = g.config.str.extract(r"DYN_EPOCH=(\d+)")[0]
    g["h"] = g.config.str.extract(r"DYN_HYST=([\d.]+)")[0]
    g["rrip_dec"] = (g.epochs * (1 - g.irrip_frac)).round().astype(int)
    g = g[g.n.isin(leaders)]
    r = d[(d.config == "rrip") & (d.trace == trace)].speedup_r.iloc[0]
    hs = sorted(g.h.unique(), key=float)
    for e in sorted(g.e.unique(), key=int):
        fig, axes = plt.subplots(1, len(hs), figsize=(8.4, 2.9), sharey=True)
        for ax, h in zip(axes, hs):
            x = g[(g.e == e) & (g.h == h)].sort_values("n")
            for k, n in enumerate(leaders):
                p = x[x.n == n]
                ax.scatter(p.rrip_dec, p.speedup_r, s=30, color=COLORS[k], zorder=3, label=f"{n} leaders")
            ax.axhline(r, color="#333333", linestyle=":", linewidth=0.8, label="SRRIP")
            ax.axhline(1, color="#333333", linestyle="--", linewidth=0.8, label="I-RRIP")
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
            ax.set_xlim(-0.5, g.rrip_dec.max() + 0.5)
            ax.set_title(f"h = {h}")
            ax.set_xlabel("Decisions that chose RRIP")
            ax.yaxis.grid(True, color="#dddddd", linewidth=0.5)
        axes[0].set_ylabel("Speedup / I-RRIP")
        axes[-1].legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.02, 1))
        fig.suptitle(f"{trace}, T = 0.15, epoch {e}: speedup vs RRIP decisions (after warmup)", y=1.03)
        f = out / f"rrip_decisions_summary_e{e}.png"
        fig.savefig(f)
        plt.close(fig)
        print(f"[task2b_analysis] {f.relative_to(DATA.parent)}")


def r_over_time(run, out, trace="Trace1", prefix="rlog", threshs=("0.15", "0.25", "0.4")):
    """r at every decision (DYN_LOG lines) on one trace, one panel per T: every
    decision is a marker, filled when it chose SRRIP. Shaded: decisions in warmup."""
    fig, axes = plt.subplots(len(threshs), 1, figsize=(8.4, 1.9 * len(threshs)), sharex=True, sharey=True)
    for ax, T in zip(axes, threshs):
        rows = [l.split() for l in (DATA / run / f"{prefix}.DYN_THRESH={T}" / f"{trace}.log").read_text().splitlines()
                if l.startswith("DYN_LOG ")]
        roi = np.array([int(r[2]) for r in rows]); r = np.array([float(r[4]) for r in rows])
        mode = np.array([int(r[6]) for r in rows]); x = np.arange(1, len(r) + 1)
        if (roi == 0).any():
            ax.axvspan(0.5, x[roi == 0].max() + 0.5, color="#eeeeee", zorder=0)
        ax.plot(x, r, "-", color="#999999", linewidth=0.8, zorder=1)
        ax.scatter(x[mode == 1], r[mode == 1], s=12, facecolors="none", edgecolors=COLORS[0], zorder=2, label="chose I-RRIP")
        ax.scatter(x[mode == 0], r[mode == 0], s=14, color=COLORS[1], zorder=3, label="chose SRRIP")
        ax.axhline(float(T), color=COLORS[1], linestyle=":", linewidth=0.9)
        ax.set_title(f"T = {T}: {int((mode[roi == 1] == 0).sum())} of {int(roi.sum())} decisions after warmup chose SRRIP",
                     fontsize=8, loc="left")
        ax.set_ylabel("r")
        ax.yaxis.grid(True, color="#dddddd", linewidth=0.5)
    axes[0].legend(fontsize=7, loc="lower right")
    axes[-1].set_xlabel("Decision (shaded: warmup)")
    fig.suptitle(f"{trace}: r at every decision (8 leaders, E = 128, h = 0; dotted: T)", y=1.01)
    fig.savefig(out)
    plt.close(fig)
    print(f"[task2b_analysis] {out.relative_to(DATA.parent)}")


def main():
    d = load("task2b_sweep")
    out = DATA / "task2b_sweep" / "analysis"
    out.mkdir(exist_ok=True)
    s = summary(d, ["DYN_LEADERS", "DYN_EPOCH", "DYN_THRESH"])
    s.to_csv(out / "summary.csv", index=False, float_format="%.6g")
    dyn = s[s.DYN_LEADERS.notna()].astype({"DYN_LEADERS": int, "DYN_EPOCH": int})
    panel_grid(dyn, "DYN_THRESH", [0, 0.15, 0.25, 0.4, 0.5], ("DYN_LEADERS", [8, 16, 32, 64]),
               ("DYN_EPOCH", [512, 1024, 2048]), "Threshold sweep (placement 0, no hysteresis)",
               out / "by_threshold.png", "Threshold T")
    panel_grid(dyn, "DYN_LEADERS", [8, 16, 32, 64], ("DYN_THRESH", [0, 0.15, 0.25, 0.4, 0.5]),
               ("DYN_EPOCH", [512, 1024, 2048]), "Leader sweep (placement 0, no hysteresis)",
               out / "by_leaders.png", "Leader sets")
    panel_grid(dyn, "DYN_EPOCH", [512, 1024, 2048], ("DYN_THRESH", [0, 0.15, 0.25, 0.4, 0.5]),
               ("DYN_LEADERS", [8, 16, 32, 64]), "Epoch sweep (placement 0, no hysteresis)",
               out / "by_epoch.png", "Epoch (leader accesses)")
    rrip_cost(d, out / "rrip_cost.png")

    d = load("task2b_hyst")
    out = DATA / "task2b_hyst" / "analysis"
    out.mkdir(exist_ok=True)
    s = summary(d, ["DYN_LEADERS", "DYN_EPOCH", "DYN_HYST"])
    s.to_csv(out / "summary.csv", index=False, float_format="%.6g")
    dyn = s[s.DYN_LEADERS.notna()].astype({"DYN_LEADERS": int, "DYN_EPOCH": int})
    panel_grid(dyn, "DYN_HYST", [0, 0.05, 0.1], ("DYN_LEADERS", [8, 16, 32, 64]),
               ("DYN_EPOCH", [512, 1024]), "Hysteresis sweep (T = 0.15, placement 0)",
               out / "by_hysteresis.png", "Hysteresis h")
    rrip_decisions(d, out)
    rrip_decisions_summary(d, out)

    if (DATA / "task2b_rtrace1").exists():
        out = DATA / "task2b_rtrace1" / "analysis"
        out.mkdir(exist_ok=True)
        r_over_time("task2b_rtrace1", out / "plot1.png")


if __name__ == "__main__":
    main()
