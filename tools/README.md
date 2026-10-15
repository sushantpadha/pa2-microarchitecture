# Experiments

`tools/exp.py` builds, runs, parses and plots the experiments in `exp/*.toml`, one file per task. Builds go through Docker with GCC 7 (run `tools/docker/setup.sh` once, see `tools/docker/README.md`).

```bash
tools/exp.py run  exp/task1.toml --test                   # test settings from the file's [test] section
tools/exp.py run  exp/task1.toml                          # final: every trace, 25M warmup + 25M sim
tools/exp.py run  exp/task3.toml --only spp_dyn -j 8      # one config, 8 runs in parallel
tools/exp.py show exp/task1.toml --test --sort speedup --plot
tools/exp.py show exp/task1.toml ipc l1d_load_mpki        # pick columns
tools/exp.py selftest                                     # check the stat regexes
```

## Plain build and run, without exp.py

For a one-off check, e.g. poking at a policy:

```bash
tools/docker/build-gcc7.sh spp lru dbg     # = ./build_champsim.sh spp lru dbg, with GCC 7
./bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-dbg \
    -warmup_instructions 1000000 -simulation_instructions 5000000 \
    -traces ../traces/Trace1.gz
KNOB=0.3 ./bin/...                         # set a getenv() knob for this run
```

The binary name is printed on the last line of the build. The run prints stats to stdout; `CPU 0 cumulative IPC` is near the top of the final block.

`./build_champsim.sh` alone uses the host's compiler. With GCC 16 it builds, but the binary aborts at startup with `std::bad_cast`, so use `build-gcc7.sh` for anything you run.

## Final and test settings

Final settings are fixed by `PS.pdf` and can't be changed in a file: every trace in `../traces/Trace*.gz`, 25M warmup, 25M simulation. Numbers for the report come from final runs only.

For testing, each file has a `[test]` section with smaller settings, used only when `--test` is passed. The flag makes the choice explicit. Without it you always get the final settings, so test numbers can't end up in the report by accident, and nobody has to edit a file back and forth between quick and final runs. Pick a few traces that behave like the full set:

```toml
[test]
traces = ["../traces/Trace1.gz"]   # default: all traces
warmup = 1_000_000                                              # default 1M
sim    = 5_000_000                                              # default 5M
```

`--traces`, `--warmup` and `--sim` on the command line override either setting for one invocation. Trace globs are relative to the repo root.

Check that the test settings exercise what the task measures. The start of a trace can be unrepresentative: on an earlier trace (`400.perlbench`), the baseline has 0 L1D load misses with the default 1M warmup + 5M sim, 774 with 5M + 20M, and 2842 with the final 25M + 25M. A test run with 0 baseline misses says nothing about a prefetcher. Look at the baseline's miss counts in `show --test` and raise `warmup`/`sim` in `[test]` if needed. On the course traces, the default test settings are fine: the baseline has L1D load MPKI 8-12 on all three.

For scale: a final run of `400.perlbench` (25M + 25M) took about a minute and a half on a 16-core laptop, builds included. On the course traces (`Trace1-3.gz`), a test run (1M + 5M) takes about 15 s per trace; task 1's 9 test runs took 1 minute with builds. Final runs haven't been timed yet.

## Experiment files

`exp/task1.toml`, `task2a.toml`, `task2b.toml` and `task3.toml` list every option. Commented-out lines show the defaults.

```toml
metrics = ["ipc", "speedup", "l2c_load_mpki"]   # columns `show` prints by default

[config.dyn]
repl = "dyn_irrip"                        # L2C replacement, default "lru"
pf   = "no"                               # L1D prefetcher, default "no"
env  = { DYN_THRESH = ["0.1", "0.2"] }    # a list is swept: dyn.DYN_THRESH=0.1, dyn.DYN_THRESH=0.2
```

- `pf` and `repl` are the names passed to `build_champsim.sh`.
- `env` values are set as environment variables for the run. The policy code reads them with `getenv()` and keeps a built-in default, so a sweep needs one binary, not one build per value.
- The `no`/`lru` baseline always runs as config `base`. `speedup` and `l1d_coverage` are computed against it, per trace.
- An unknown key (a typo like `prefetcher =`) stops the run instead of silently running the baseline.
- `--only` takes config names as written in the file (`dyn`, not `dyn.DYN_THRESH=0.1`).

## Output

```
results/<task>/<config>/<trace>.log   raw ChampSim output; the first line is the command and env
results/<task>/stats.csv              one row per config x trace of this invocation
results/<task>/<metric>.png           from show --plot
results/<task>/_build/<pf>-<repl>.log  compiler output of each build
```

Runs with non-final warmup or sim go to `results/<task>_w<N>_s<N>/`, so they never mix with final ones. `results/` is gitignored; results the team chooses to publish are copied into `data/`.

## What `run` prints

Before building, a plan:
- **Settings:** warmup, sim and traces, each with where it came from (final, `[test]` in toml, test default, or command line). Also the output directory, `-j`, the metrics the file asks for, and every metric available.
- **Configs:** every config with `pf`, `repl` and `env`. Values not set in the file are marked `(default)`.
- **Work:** the builds needed, and how many runs are left to do vs already done.

Then one line per build and per run, with its time. Compiler output goes to the build log, not the screen. If a build fails, `run` prints the last lines of its log and stops.

At the end, a summary: counts of builds, runs done/failed/skipped, total time, and the table of the file's metrics (the same table as `show`). Colors are used only when printing to a terminal (not when piped, and not on `TERM=dumb`).

## Tables

`run` and `show` print one row per config and trace, plus one `avg` row per config: the geometric mean for `speedup` (it's a ratio) and the arithmetic mean for everything else. NaN values are left out of the average. `--sort` sorts the per-trace rows and the `avg` rows separately. Under the table, a note says what `speedup` and `l1d_coverage` are relative to: the `base` config (no L1D prefetcher, LRU at L2C) on the same trace.

## Behavior

- `run` skips runs whose log is already complete. Rerun the same command to fill in anything that failed or was interrupted.
- `run` rebuilds every binary that still has runs to do, one build at a time, because `build_champsim.sh` writes into the shared source tree. Runs then go in parallel (`-j`, default 4). Each run is one single-threaded process using about 11 MB, so the limit is CPU cores: on a 16-core machine, `-j 12` to `-j 14` is fine.
- ChampSim is deterministic: its random seed comes from the trace path (see CLAUDE.md, "Traces"). The same binary, trace and settings always give the same numbers, so there's no point repeating a run or averaging repeats.
- `run` parses when it finishes. `show` only reads `stats.csv`, so give it the same `--test`/override flags as the `run`.

## Metrics

| Name | Source |
|------|--------|
| `ipc` | `CPU 0 cumulative IPC` |
| `speedup` | `ipc / ipc` of `base`, same trace |
| `l1d_load_miss`, `l1d_load_mpki` | `L1D LOAD` line |
| `l1d_accuracy_issued` | ChampSim's `ACCURACY`: useful / prefetches issued to the lower level (L2), in % |
| `l1d_accuracy_resolved` | useful / (useful + useless), in %, from the `L1D PREFETCH REQUESTED` line. Useless = prefetched lines evicted unused. NaN when both are 0 |
| `l1d_pf_useful`, `l1d_pf_useless` | the counts behind `l1d_accuracy_resolved` |
| `l1d_coverage` | `100 * (1 - l1d_load_miss / l1d_load_miss of base)`, in % (PS.pdf's definition); NaN when base has 0 misses |
| `l2c_load_mpki` | `L2C LOAD` line |
| `l2c_instr_load_mpki`, `l2c_data_load_mpki` | `L2C INSTRUCTION/DATA LOAD MPKI` lines |
| `llc_load_mpki` | `LLC LOAD` line |
| `l1d_pf_requested`, `l1d_pf_issued` | `L1D PREFETCH REQUESTED` line: prefetches the prefetcher asked for, and those that entered the PQ |
| `l1d_pf_to_l2` | `PREFETCH ISSUED TO LOWER LEVEL`: prefetches that missed in L1D and went to L2 (the denominator of `l1d_accuracy_issued`) |
| `l1d_pf_fill_l1`, `l1d_pf_fill_l2` | `L1D PREFETCHES SAME/DIFFERENT FILL-ORIGIN LEVEL`: of those, how many fill L1D, and how many fill only L2 |
| `l1d_pf_late` | `LATE PREFETCHES`: demand misses that merged into an in-flight prefetch in the L1D MSHR. Correct but late; still counted as misses |
| `l1d_pf_late_pct` | `100 * late / (useful + late)`: share of correct prefetches that arrived late, in %. NaN when both are 0 |
| `l1d_pf_dropped` | `DROPPED PREFETCHES` on the L1D line |
| `l2c_miss_latency`, `llc_miss_latency` | `AVERAGE MISS LATENCY` lines, in cycles. L1D's is left out: its counter is broken (it reports hundreds of thousands of cycles) |
| `spp_accuracy` | SPP's own accuracy checker (`SPP issued:` line), in %. NaN for other prefetchers |

To add a metric, add a regex to `METRICS` in `tools/exp.py` and extend `selftest` if it matters.
