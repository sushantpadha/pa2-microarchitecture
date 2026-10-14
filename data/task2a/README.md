# Task 2A final run

Final settings: Trace1-3, 25M warmup + 25M simulation. Produced by `tools/exp.py run exp/task2a.toml --force` on 2026-10-14.

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show exp/task2a.toml --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2a.toml`: the experiment file used.
- `irrip.l2c_repl.ran`: the I-RRIP source used. It was not yet committed; the rest of the tree was at commit 9e77f3e.

`irrip_default` runs with no env (LVL=1), as a plain build does. `base` is no prefetcher with LRU at L2C.
