# Experiments

`tools/exp.py` builds, runs, parses and plots the experiments described in `exp/*.toml`. Builds use GCC 7 in Docker; please run `tools/docker/setup.sh` once before the first build (see `tools/docker/README.md`).

```bash
tools/exp.py run  exp/task2a.toml --test            # quick run with the file's [test] settings
tools/exp.py run  exp/task2a.toml --test --force    # rebuild and rerun after a code change
tools/exp.py run  exp/task2a.toml                   # final run: all traces, 25M warmup + 25M sim
tools/exp.py run  exp/task3.toml --only spp_dyn -j 8
tools/exp.py show exp/task2a.toml --test            # print the table again
tools/exp.py show exp/task1.toml ipc l1d_load_mpki --sort ipc --plot
tools/exp.py selftest                               # check the stat regexes
tools/save.sh irrip task2a                          # save a final results/ dir for the long term, into data/ (--force to replace)
```

## Final and test runs

Final runs use the settings fixed by `PS.pdf`: every trace in `../traces/Trace*.gz`, 25M warmup and 25M simulation instructions. Only final runs go in the report.

With `--test`, `exp.py` uses the file's `[test]` section instead. Each key is optional:

```toml
[test]
traces = ["../traces/Trace1.gz"]   # default: all traces
warmup = 2_000_000                 # default 1M
sim    = 10_000_000                # default 5M
```

`--traces`, `--warmup` and `--sim` override these for a single invocation. Test results go to `results/<task>_w<N>_s<N>/`, so they never mix with final results.

Please check that the test window exercises what the task measures. The start of a trace can be unrepresentative: on `400.perlbench`, the baseline had 0 L1D load misses at 1M + 5M but 2842 at 25M + 25M. On the course traces, the default test settings give a baseline L1D load MPKI of 8 to 12.

## Experiment files

There is one file per task. Each `[config.<name>]` is one configuration:

```toml
metrics = ["ipc", "speedup", "l2c_load_mpki"]   # columns that show prints by default

[config.dyn]
repl = "dyn_irrip"                       # L2C replacement policy, default "lru"
pf   = "no"                              # L1D prefetcher, default "no"
env  = { DYN_THRESH = ["0.1", "0.2"] }   # a list is swept: dyn.DYN_THRESH=0.1, dyn.DYN_THRESH=0.2
```

- `pf` and `repl` are the names passed to `build_champsim.sh`.
- `env` sets environment variables for each run. The policy reads them with `getenv()` and falls back to a built-in default, so a sweep needs only one build. A single value (`LVL = "3"`) is set without being swept.
- The baseline (`no` prefetcher, `lru` replacement) always runs as config `base`.
- `--only` takes config names as written in the file (`dyn`, not `dyn.DYN_THRESH=0.1`).
- An unknown key stops the run, so a typo cannot silently run the baseline.

## Behavior

- `run` skips any run whose log is already complete. Rerunning the same command fills in runs that failed or were interrupted.
- `--force` rebuilds and reruns every selected config except `base`. Please use it after changing policy code. If you change the core (`src/` or `inc/`), delete the `base/` folder as well.
- Builds run one at a time, because `build_champsim.sh` writes into the shared source tree. Runs then go in parallel (`-j`, default 4). Each run uses one core and about 11 MB.
- ChampSim is deterministic, so one run per config and trace is enough.
- `show` reads `stats.csv`, which holds only the configs from the latest `run`. After `run --only`, please run once without `--only` to see every config; complete logs are skipped, so this only re-parses. Give `show` the same `--test` and override flags as `run`.

## Output

```
results/<task>/<config>/<trace>.log    raw ChampSim output; the first line records the command and env
results/<task>/stats.csv               one row per config and trace from the latest run
results/<task>/<metric>.png            written by show --plot
results/<task>/_build/<pf>-<repl>.log  compiler output for each build
```

`results/` is not tracked by git. Results the team decides to publish are copied into `data/`.

## Tables

Tables have one row per config and trace, colored by trace, plus a bold `avg` row per config. The average is a geometric mean for `speedup` and an arithmetic mean for every other metric. NaN values are left out. `--sort` orders the trace rows and the `avg` rows separately.

## Metrics

All statistics are read from the ROI section of the log, so warmup is excluded. MPKI is misses per 1000 simulated instructions.

| Name | Meaning |
|------|---------|
| `ipc` | Instructions per cycle (`CPU 0 cumulative IPC`) |
| `speedup` | `ipc` divided by the `ipc` of `base` on the same trace |
| `l1d_load_miss` | L1D load misses |
| `l1d_load_mpki` | L1D load MPKI |
| `l1d_coverage` | `100 × (1 − l1d_load_miss / l1d_load_miss of base)`, in %, as defined in `PS.pdf`. NaN if `base` has no misses |
| `l1d_accuracy_issued` | ChampSim's accuracy: useful prefetches / prefetches issued to L2, in % |
| `l1d_accuracy_resolved` | useful / (useful + useless), in %. NaN if both are 0 |
| `l1d_pf_useful` | Prefetched L1D lines that were later used |
| `l1d_pf_useless` | Prefetched L1D lines evicted without being used |
| `l2c_load_mpki` | L2C load MPKI, instruction and data loads together |
| `l2c_instr_load_mpki` | L2C load MPKI for instruction fetches |
| `l2c_data_load_mpki` | L2C load MPKI for data loads |

A late prefetch (one still in flight when the demand load arrives) counts as a miss, so it lowers coverage. To add a metric, add a regex to `METRICS` in `tools/exp.py`.

## Building and running by hand

For a one-off check without `exp.py`:

```bash
tools/docker/build-gcc7.sh spp lru dbg      # L1D prefetcher, L2C policy, name tag
./bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-dbg \
    -warmup_instructions 1000000 -simulation_instructions 5000000 \
    -traces ../traces/Trace1.gz
LVL=3 ./bin/...                              # set a getenv() knob for this run
```

The last line of the build prints the binary name. Please always build with `build-gcc7.sh`: a binary built with the host's GCC 16 compiles but aborts at startup with `std::bad_cast`.
