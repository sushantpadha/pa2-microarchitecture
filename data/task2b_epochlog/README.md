# task2b_epochlog final run

dyn_irrip with DYN_LOG=1 (r and the mode at every decision): 8 leaders, epoch 1024, T = 0.15 / 0.25 / 0.4, h = 0, plus irrip and rrip. Every config is bit-identical to the matching task2b_sweep config, so the log does not change results. Only 7-13 decisions per trace after warmup, too few to show r over time; the report figure uses task2b_rtrace1 (epoch 128) instead.

Last run 2026-10-15 14:19, tree at commit a001cbf. `dyn_irrip.l2c_repl.ran` is the policy source that ran (committed when saved).

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2b_epochlog.toml`: the experiment file used, if there was one.
