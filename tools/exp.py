#!/usr/bin/env python3
"""Build, run, parse and show ChampSim experiments defined in exp/*.toml.

    tools/exp.py run  exp/task1.toml [--test] [--only NAME ...] [-j N]
    tools/exp.py show exp/task1.toml [--test] [METRIC ...] [--sort METRIC] [--plot]
    tools/exp.py selftest

See tools/README.md for the file format.
"""
import argparse
import glob
import itertools
import os
import re
import subprocess
import sys
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / "tools" / "docker" / "build-gcc7.sh"
# Final settings are fixed by PS.pdf: every trace, 25M warmup, 25M simulation.
# Only --test (the toml's [test] section) or the CLI flags change them.
FINAL = {"traces": ["../traces/Trace*.gz"], "warmup": 25_000_000, "sim": 25_000_000}
TEST = {"traces": ["../traces/Trace*.gz"], "warmup": 1_000_000, "sim": 5_000_000}
TOP_KEYS = {"metrics", "test", "config"}
CONFIG_KEYS = {"pf", "repl", "env"}
END = "Region of Interest Statistics"  # printed only when a run finishes

# Metric name -> regex with one capture group. The last match in the log wins.
METRICS = {
    "ipc":                 r"CPU 0 cumulative IPC: (\S+) instructions",
    "l1d_load_miss":       r"L1D LOAD +ACCESS: +\d+ +HIT: +\d+ +MISS: +(\d+)",
    "l1d_load_mpki":       r"L1D LOAD +ACCESS:.*MPKI: (\S+)",
    # ChampSim's own accuracy: useful / prefetches issued to the lower level (L2), in %.
    "l1d_accuracy_issued": r"L1D USEFUL LOAD PREFETCHES:.*ACCURACY: (\S+)",
    "l1d_pf_useful":       r"L1D PREFETCH +REQUESTED:.*USEFUL: +(\d+)",
    "l1d_pf_useless":      r"L1D PREFETCH +REQUESTED:.*USELESS: +(\d+)",
    "l2c_load_mpki":       r"L2C LOAD +ACCESS:.*MPKI: (\S+)",
    "l2c_data_load_mpki":  r"L2C DATA LOAD MPKI: (\S+)",
    "l2c_instr_load_mpki": r"L2C INSTRUCTION LOAD MPKI: (\S+)",
}
DERIVED = ["speedup", "l1d_coverage", "l1d_accuracy_resolved"]  # see parse()

# Plain ANSI codes work on any modern terminal; skip them when piped or on TERM=dumb.
TTY = sys.stdout.isatty() and os.environ.get("TERM", "dumb") != "dumb"


def paint(text, code):
    # code: 1 bold, 2 dim, 31 red, 32 green, 33 yellow, 36 cyan
    return f"\033[{code}m{text}\033[0m" if TTY else str(text)


def say(tag, text=""):
    print(f"{paint(f'[{tag}]', '1;36')} {text}", flush=True)


def binary(pf, repl):
    # Slot order is fixed by BINARY_NAME= in build_champsim.sh; only the
    # L1D prefetcher and L2C replacement slots vary.
    return REPO / "bin" / f"hashed_perceptron-no-{pf}-no-no-no-no-no-lru-lru-lru-{repl}-lru-lru-lru-lru-1core-exp"


def load_configs(path, only):
    """Expand the toml into {name: {pf, repl, env}}. The no/lru baseline
    is always included because speedup and coverage are relative to it."""
    spec = tomllib.loads(Path(path).read_text())
    # A typo like "prefetcher = ..." would otherwise silently run the baseline.
    check_keys(spec, TOP_KEYS, path)
    check_keys(spec.get("test", {}), set(TEST), f"{path} [test]")
    configs = {"base": {"pf": "no", "repl": "lru", "env": {}, "defaults": set()}}
    for name, c in spec.get("config", {}).items():
        check_keys(c, CONFIG_KEYS, f"{path} [config.{name}]")
        if only and name not in only:
            continue
        env = {k: v if isinstance(v, list) else [v] for k, v in c.get("env", {}).items()}
        for values in itertools.product(*env.values()):
            chosen = dict(zip(env, map(str, values)))
            # Only swept (list-valued) keys go into the name.
            suffix = "".join(f".{k}={v}" for k, v in chosen.items() if len(env[k]) > 1)
            configs[name + suffix] = {"pf": c.get("pf", "no"), "repl": c.get("repl", "lru"), "env": chosen,
                                      "defaults": {"pf", "repl"} - set(c)}
    return spec, configs


def check_keys(table, allowed, where):
    unknown = set(table) - allowed
    if unknown:
        sys.exit(f"[exp] unknown key(s) {sorted(unknown)} in {where}; allowed: {sorted(allowed)}")


def settings(spec, args):
    """Traces, warmup and sim for this invocation: final by default, the
    toml's [test] section with --test, CLI flags on top of either."""
    s = dict(FINAL)
    src = dict.fromkeys(s, "final, fixed by PS.pdf")
    if args.test:
        s |= TEST
        src = dict.fromkeys(s, "test default")
        for key, val in spec.get("test", {}).items():
            s[key], src[key] = val, "[test] in toml"
    for key in ("traces", "warmup", "sim"):
        if getattr(args, key) is not None:
            s[key], src[key] = getattr(args, key), "command line"
    traces = sorted({t for pattern in s["traces"] for t in glob.glob(str(REPO / pattern))})
    if not traces:
        sys.exit(f"[exp] no traces match {s['traces']}")
    return traces, s["warmup"], s["sim"], src


def out_dir(path, warmup, sim):
    name = Path(path).stem
    if (warmup, sim) != (FINAL["warmup"], FINAL["sim"]):
        name += f"_w{warmup}_s{sim}"  # test runs never mix with final ones
    return REPO / "results" / name


def trace_name(trace):
    name = Path(trace).name
    for suffix in (".gz", ".xz", ".champsimtrace"):
        name = name.removesuffix(suffix)
    return name


def done(log):
    return log.exists() and END in log.read_text(errors="ignore")


def run_one(job):
    log, cmd, env = job
    log.parent.mkdir(parents=True, exist_ok=True)
    tmp = log.with_suffix(".tmp")
    rel = log.relative_to(REPO)
    say("run", f"start  {rel}")
    t0 = time.time()
    with open(tmp, "w") as f:
        f.write(f"# env={env} cmd={' '.join(cmd)}\n")
        f.flush()
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, **env}, cwd=REPO)
    tmp.rename(log)
    ok = done(log)
    say("run", f"{paint('done  ', 32) if ok else paint('FAILED', '1;31')} {rel} ({time.time() - t0:.0f}s)")
    return ok


def cmd_run(args):
    spec, configs = load_configs(args.file, args.only)
    traces, warmup, sim, src = settings(spec, args)
    out = out_dir(args.file, warmup, sim)
    metrics = spec.get("metrics", ["ipc", "speedup"])

    jobs, to_build, skipped = [], set(), 0
    for name, c in configs.items():
        for t in traces:
            log = out / name / f"{trace_name(t)}.log"
            if done(log) and not (args.force and name != "base"):
                skipped += 1
                continue
            to_build.add((c["pf"], c["repl"]))
            # Paths relative to the repo (runs start there), so logs, which may be
            # published in data/, don't carry this machine's directory layout.
            cmd = [str(binary(c["pf"], c["repl"]).relative_to(REPO)), "-warmup_instructions", str(warmup),
                   "-simulation_instructions", str(sim), "-traces", os.path.relpath(t, REPO)]
            jobs.append((log, cmd, c["env"]))

    print_plan(args, configs, traces, warmup, sim, src, out, metrics, to_build, len(jobs), skipped)
    t0 = time.time()
    # Builds share one source tree (build_champsim.sh copies modules into
    # fixed paths), so they must run one at a time. Always rebuild a binary
    # that has pending runs, so a stale binary is never used.
    # Compiler output goes to a log, not the screen, so the plan and summary stay readable.
    for pf, repl in sorted(to_build):
        blog = out / "_build" / f"{pf}-{repl}.log"
        blog.parent.mkdir(parents=True, exist_ok=True)
        say("build", f"start  {pf}/{repl}")
        tb = time.time()
        with open(blog, "w") as f:
            r = subprocess.run([str(BUILD), pf, repl, "exp"], cwd=REPO, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode:
            say("build", f"{paint('FAILED', '1;31')} {pf}/{repl}, last lines of {blog.relative_to(REPO)}:")
            print("".join(blog.read_text(errors="ignore").splitlines(keepends=True)[-15:]))
            sys.exit(1)
        say("build", f"{paint('done  ', 32)} {pf}/{repl} ({time.time() - tb:.0f}s), log: {blog.relative_to(REPO)}")
    # Runs are independent static binaries, safe to run in parallel.
    with ThreadPoolExecutor(args.j) as pool:
        results = list(pool.map(run_one, jobs))
    df = parse(configs, {trace_name(t) for t in traces}, out)

    failed = results.count(False)
    print()
    say("summary", f"{len(to_build)} build(s), {len(jobs)} run(s): "
                   f"{paint(f'{len(jobs) - failed} done', 32)}, "
                   f"{paint(f'{failed} failed', '1;31') if failed else '0 failed'}, "
                   f"{skipped} skipped (already done), {time.time() - t0:.0f}s")
    print_table(df, metrics)
    say("summary", f"all columns: {(out / 'stats.csv').relative_to(REPO)}")


def print_plan(args, configs, traces, warmup, sim, src, out, metrics, to_build, n_jobs, skipped):
    dflt = lambda text: paint(f"{text} (default)", 2)
    say("plan", paint(f"{args.file}, {'test' if args.test else 'final'} settings", 1))
    print(f"  warmup    {warmup:,}  {paint(src['warmup'], 2)}")
    print(f"  sim       {sim:,}  {paint(src['sim'], 2)}")
    print(f"  traces    {len(traces)}  {paint(src['traces'], 2)}: {', '.join(trace_name(t) for t in traces)}")
    print(f"  output    {out.relative_to(REPO)}")
    print(f"  parallel  -j {args.j}")
    print(f"  metrics   {' '.join(metrics)}")
    print(f"  {paint('available: ' + ' '.join([*METRICS, *DERIVED]), 2)}")
    say("plan", paint(f"{len(configs)} config(s)", 1))
    width = max(map(len, configs))
    pf_w = max(len(f"pf={c['pf']} (default)") for c in configs.values())
    repl_w = max(len(f"repl={c['repl']} (default)") for c in configs.values())
    for name, c in configs.items():
        pf, repl = f"pf={c['pf']}", f"repl={c['repl']}"
        pf = dflt(pf) + " " * (pf_w - len(pf) - 10) if "pf" in c["defaults"] else pf.ljust(pf_w)
        repl = dflt(repl) + " " * (repl_w - len(repl) - 10) if "repl" in c["defaults"] else repl.ljust(repl_w)
        env = " ".join(f"{k}={v}" for k, v in c["env"].items()) or paint("env: none, code defaults", 2)
        note = paint("  baseline, always run", 2) if name == "base" else ""
        print(f"  {paint(name.ljust(width), 33)}  {pf}  {repl}  {env}{note}")
    builds = ", ".join(f"{pf}/{repl}" for pf, repl in sorted(to_build)) or "none"
    say("plan", f"builds: {builds}")
    say("plan", f"runs: {n_jobs} to do, {skipped} already done")
    print(flush=True)


def summarize(df, metrics, geo=("speedup",)):
    """Per-trace rows plus one "avg" row per config: geometric mean for
    the ratio metrics in `geo`, arithmetic mean for everything else."""
    avg = []
    for name, g in df.groupby("config", sort=False):
        row = {"config": name, "trace": "avg"}
        for m in metrics:
            vals = g[m].dropna()
            if m in geo:
                row[m] = float(np.exp(np.log(vals).mean())) if len(vals) else float("nan")
            else:
                row[m] = vals.mean()
        avg.append(row)
    return pd.concat([df[["config", "trace", *metrics]], pd.DataFrame(avg)], ignore_index=True)


def print_table(df, metrics, sort=None, ratios=None):
    table = summarize(df, metrics, metrics if ratios else ("speedup",))
    if sort:
        is_avg = table.trace == "avg"
        table = pd.concat([table[~is_avg].sort_values(sort, ascending=False),
                           table[is_avg].sort_values(sort, ascending=False)])
    # One color per trace (bright red, green, blue, yellow, magenta, cyan), avg rows bold.
    colors = ["91", "92", "94", "93", "95", "96"]
    traces = [t for t in dict.fromkeys(table.trace) if t != "avg"]
    code = {t: colors[i % len(colors)] for i, t in enumerate(traces)} | {"avg": "1"}
    header, *rows = table.to_string(index=False, float_format="%.4f").splitlines()
    print(header)
    for line, trace in zip(rows, table.trace):
        print(paint(line, code[trace]))
    if ratios:
        print(paint(f"every value is a ratio to config {ratios!r}, same trace; avg rows: geometric mean", 2))
        return
    print(paint("speedup and l1d_coverage are relative to base: no L1D prefetcher, LRU at L2C, same trace", 2))
    print(paint("avg rows: geometric mean for speedup, arithmetic mean otherwise; NaN values skipped", 2))


def parse_log(text):
    row = {}
    for name, pattern in METRICS.items():
        found = re.findall(pattern, text)
        row[name] = float(found[-1]) if found else float("nan")
    return row


def parse(configs, trace_names, out):
    """Only the configs and traces of this invocation go into stats.csv,
    even if the directory holds logs from earlier, wider runs."""
    rows = []
    for name, c in configs.items():
        for log in sorted((out / name).glob("*.log")):
            if log.stem not in trace_names:
                continue
            if not done(log):
                say("parse", paint(f"skip incomplete {log.relative_to(REPO)}", 33))
                continue
            rows.append({"config": name, "trace": log.stem, "pf": c["pf"], "repl": c["repl"],
                         **c["env"], **parse_log(log.read_text(errors="ignore"))})
    if not rows:
        sys.exit("[parse] no complete runs")
    df = pd.DataFrame(rows)
    base = df[df.config == "base"].set_index("trace")
    df["speedup"] = df.ipc / df.trace.map(base.ipc)
    # Second accuracy, over prefetches whose fate is known: useful / (useful +
    # useless), in %. "Useless" counts prefetched lines evicted unused.
    resolved = (df.l1d_pf_useful + df.l1d_pf_useless).replace(0, np.nan)
    df["l1d_accuracy_resolved"] = 100 * df.l1d_pf_useful / resolved
    # In %, like the accuracies and PS.pdf's example plot. Undefined (NaN, not
    # -inf) when the baseline has no misses.
    df["l1d_coverage"] = 100 * (1 - df.l1d_load_miss / df.trace.map(base.l1d_load_miss).replace(0, np.nan))
    df.to_csv(out / "stats.csv", index=False)
    return df


def cmd_show(args):
    spec, _ = load_configs(args.file, None)
    _, warmup, sim, _ = settings(spec, args)
    out = out_dir(args.file, warmup, sim)
    if not (out / "stats.csv").exists():
        sys.exit(f"[show] no {(out / 'stats.csv').relative_to(REPO)}; run the same command with `run` first")
    df = pd.read_csv(out / "stats.csv")
    metrics = args.metrics or spec.get("metrics", ["ipc", "speedup"])
    if args.ratios:
        if args.ratios not in set(df.config):
            sys.exit(f"[show] no config {args.ratios!r} in stats.csv")
        ref = df[df.config == args.ratios].set_index("trace")
        for m in metrics:
            df[m] = df[m] / df.trace.map(ref[m]).replace(0, np.nan)
    print_table(df, metrics, args.sort, args.ratios)

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        for m in metrics:
            if df[m].isna().all():
                say("plot", paint(f"skip {m}: every value is NaN", 33))
                continue
            ax = df.pivot_table(index="trace", columns="config", values=m).plot.bar(figsize=(8, 4), rot=30)
            name = f"{m}_vs_{args.ratios}" if args.ratios else m  # never overwrite the plain plots
            ax.set_ylabel(f"{m} / {args.ratios}" if args.ratios else m)
            ax.legend(title="config", bbox_to_anchor=(1.01, 1), loc="upper left")  # outside the bars
            ax.figure.tight_layout()
            ax.figure.savefig(out / f"{name}.png", dpi=150)
            say("plot", (out / f"{name}.png").relative_to(REPO))


def cmd_selftest(_):
    row = parse_log((Path(__file__).parent / "testdata" / "sample.log").read_text())
    assert abs(row["ipc"] - 0.4386) < 1e-9, row
    assert row["l1d_load_miss"] == 0, row
    assert row["l2c_instr_load_mpki"] == 0, row
    assert row["l1d_pf_useful"] == 0 and row["l1d_pf_useless"] == 0, row
    print("[selftest] ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "show"):
        p = sub.add_parser(name)
        p.add_argument("file")
        p.add_argument("--test", action="store_true", help="use the toml's [test] settings instead of the final ones")
        p.add_argument("--traces", nargs="+", help="override trace globs (relative to the repo)")
        p.add_argument("--warmup", type=int, help="override warmup instructions")
        p.add_argument("--sim", type=int, help="override simulation instructions")
    run = sub.choices["run"]
    run.add_argument("--only", nargs="+", help="config names to run (base is always included)")
    run.add_argument("-j", type=int, default=4, help="parallel runs")
    run.add_argument("--force", action="store_true", help="rerun configs whose logs exist (not base)")
    show = sub.choices["show"]
    show.add_argument("metrics", nargs="*", help="columns to print (default: metrics in the toml)")
    show.add_argument("--sort", help="sort rows by this column, descending")
    show.add_argument("--ratios", metavar="CONFIG", help="show every metric as a ratio to CONFIG, geometric-mean avg")
    show.add_argument("--plot", action="store_true", help="save one bar chart per metric")
    sub.add_parser("selftest")
    args = ap.parse_args()
    {"run": cmd_run, "show": cmd_show, "selftest": cmd_selftest}[args.cmd](args)


if __name__ == "__main__":
    main()
