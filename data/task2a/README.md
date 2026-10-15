# Task 2A final run

Final settings: Trace1-3, 25M warmup + 25M simulation. Produced by `tools/exp.py run exp/task2a.toml --force` on 2026-10-15.

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show exp/task2a.toml --plot`.
- `<metric>_vs_rrip.png`: the same metrics as ratios to `rrip`, from `tools/exp.py show exp/task2a.toml --ratios rrip --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2a.toml`: the experiment file used.
- `irrip.l2c_repl.ran`: the I-RRIP source used. It was not yet committed; the rest of the tree was at commit 15a5533.

`irrip_default` runs with no env (LVL=8), as a plain build does. `irrip.LVL=1..7` are the other levels; the header of `irrip.l2c_repl.ran` describes each. `base` is no prefetcher with LRU at L2C.
