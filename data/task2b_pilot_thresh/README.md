# task2b_pilot_thresh final run

Pilot: T from 0 to 1 (0.05 steps from 0.1 to 0.7) at 32 leaders, epoch 1024, placement 0. Its I-RRIP branch used the older I-RRIP rules (irrip lvl 1, as of f171d26), so these numbers are only for choosing sweep ranges, not for the report.

Note: the `irrip` reference config here ran `irrip.l2c_repl` at aac3749 (default lvl 8: age_k 4, data inserted at RRPV 3). The I-RRIP branch of `dyn_irrip` is still lvl 1 (as of f171d26), so `irrip` is not the same rules as dyn at T = 0.

Last run 2026-10-15 01:46, tree at commit aac3749. `dyn_irrip.l2c_repl.ran` is the policy source that ran (NOT committed when saved).

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2b_pilot_thresh.toml`: the experiment file used, if there was one.
