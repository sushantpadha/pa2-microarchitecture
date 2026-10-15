# task2b_grid final run

Placement {0, 1, 2} x T {0, 0.15, 0.25, 0.4, 0.5, 0.6} x leaders {8, 16, 32, 64}, epoch = 32 leader accesses per leader set, plus irrip and rrip. The only run with placements 1 and 2; its placement-0 configs are bit-identical to task2b_sweep.

dyn_irrip here uses irrip lvl 8 rules in its I-RRIP branch (same as `irrip` at aac3749). Epoch = 32 leader accesses per leader set.

The binary ran was built at 01:55 from a version of dyn_irrip.l2c_repl that also had the Task 3 prefetch code (now in 3dyn_irrip.l2c_repl, off by default). The `.ran` copy is the later version without it. With no prefetcher both give identical results: n32.DYN_PLACE=0.DYN_THRESH=0.15 here matches dyn.DYN_EPOCH=1024 in task2b_epoch exactly.

Last run 2026-10-15 02:38, tree at commit fbca589. `dyn_irrip.l2c_repl.ran` is the policy source that ran (NOT committed when saved).

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2b_grid.toml`: the experiment file used, if there was one.
