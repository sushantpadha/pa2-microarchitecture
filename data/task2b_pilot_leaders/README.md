# task2b_pilot_leaders final run

Pilot: leader sets 8-256 at T = 0.3, placement 0, epoch = 32 leader accesses per leader set, plus static I-RRIP (lvl 1 here) and SRRIP. Its I-RRIP branch used the older I-RRIP rules (irrip lvl 1, as of f171d26), so these numbers are only for choosing sweep ranges, not for the report.

Last run 2026-10-15 01:02, tree at commit 15a5533. `dyn_irrip.l2c_repl.ran` is the policy source that ran (NOT committed when saved).

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2b_pilot_leaders.toml`: the experiment file used, if there was one.
