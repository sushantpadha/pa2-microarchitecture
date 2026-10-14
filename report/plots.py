#!/usr/bin/env python3
"""Make the report figures from the published results in data/.

Usage: python3 report/plots.py      (writes report/figures/*.png)

Each figure is a grouped bar chart, like the example plots in PS.pdf: one group
per trace plus a mean group (geometric mean for speedup, arithmetic otherwise),
one bar per config. Speedup bars start at 1.0 (the baseline), so a bar's
length is the change.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "report" / "figures"

COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, GRID = "#333333", "#dddddd"

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK,
    "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def mean(values, metric):
    values = values.dropna()
    return float(np.exp(np.log(values).mean())) if metric == "speedup" else values.mean()


def bars(task, metric, configs, ylabel, title, out, ref=None, first_color=0):
    """configs: list of (config name in stats.csv, legend label). first_color keeps a
    config's colour the same in charts that leave out the baseline."""
    df = pd.read_csv(DATA / task / "stats.csv")
    traces = sorted(df.trace.unique())
    groups = traces + ["Geomean" if metric == "speedup" else "Mean"]
    width = 0.8 / len(configs)
    fig, ax = plt.subplots(figsize=(3.6, 2.9))
    for i, (name, label) in enumerate(configs):
        rows = df[df.config == name].set_index("trace")[metric]
        assert len(rows), f"{task}: no rows for {name}"
        vals = np.array([rows.get(t, np.nan) for t in traces] + [mean(rows, metric)])
        x = np.arange(len(groups)) + (i - (len(configs) - 1) / 2) * width
        base = 0 if ref is None else ref
        ax.bar(x, vals - base, width * 0.92, bottom=base, color=COLORS[first_color + i], label=label, zorder=2)
    if ref is not None:
        ax.axhline(ref, color=INK, linestyle="--", linewidth=1, label="Baseline", zorder=3)
    ax.set_xticks(np.arange(len(groups)), [g.replace("Trace", "Trace ") for g in groups])
    ax.set_ylabel(ylabel)
    ax.set_title(title, color=INK)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6, zorder=0)
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.savefig(OUT / out)
    plt.close(fig)
    print(f"[plots] {out}")


def l2_figures(task, configs, prefix):
    bars(task, "speedup", configs, "Speedup", "Speedup over LRU", f"{prefix}_speedup.png", ref=1.0, first_color=1)
    c = [("base", "LRU (baseline)")] + configs
    bars(task, "ipc", c, "IPC", "IPC", f"{prefix}_ipc.png")
    bars(task, "l2c_load_mpki", c, "MPKI", "L2C load MPKI", f"{prefix}_mpki.png")
    bars(task, "l2c_instr_load_mpki", c, "MPKI", "L2C instruction load MPKI", f"{prefix}_mpki_instr.png")
    bars(task, "l2c_data_load_mpki", c, "MPKI", "L2C data load MPKI", f"{prefix}_mpki_data.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (DATA / "task2a" / "stats.csv").exists():
        l2_figures("task2a", [("rrip", "SRRIP"), ("irrip_default", "I-RRIP")], "t2a")


if __name__ == "__main__":
    main()
