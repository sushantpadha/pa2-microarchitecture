# task2b_sweep final run

Dynamic I-RRIP, placement 0, no hysteresis: threshold T {0, 0.15, 0.25, 0.4, 0.5} x leader sets {8, 16, 32, 64} x epoch {512, 1024, 2048} leader accesses, plus static I-RRIP (`irrip`, lvl 8, the same rules as dyn's I-RRIP mode) and SRRIP (`rrip`). Ran on a 24-core machine; base, irrip, rrip and every config shared with task2b_grid are bit-identical to the local runs.

`analysis/` is made by `tools/task2b_analysis.py`: `summary.csv` (one row per config: speedup and MPKI as ratios to irrip, per trace, plus `irrip_frac_<trace>`, the fraction of post-warmup decisions that chose I-RRIP) and the figures below. The `<metric>.png` charts from `exp.py show --plot` have 63 configs and are not readable; use `analysis/`.

Findings (speedup as a ratio to static I-RRIP, geomean over traces):
- No configuration beats static I-RRIP (speedup 1.0216 over LRU).
- With T = 0 the policy never switches, so the only cost is the leader sets running SRRIP: 0.9998 / 0.9996 / 0.9993 / 0.9983 for 8 / 16 / 32 / 64 leaders.
- At every leader count and epoch, speedup falls as T rises (`analysis/by_threshold.png`). A higher T sends more decisions to RRIP, which raises instruction MPKI more than it lowers data MPKI.
- Fewer leaders and longer epochs switch less: an epoch counted in leader accesses spans more instructions, so short dips in the ratio average out. 8 leaders make no RRIP decision after warmup at T <= 0.15 for any epoch, nor at T = 0.25 with epochs >= 1024.
- Switching costs more than the time spent in RRIP (`analysis/rrip_cost.png`). On Trace2, configs with 2-10% RRIP decisions lose 0.4-1.1%, against about 0.1-0.5% if the loss were linear. On Trace1 and Trace3, a small RRIP fraction already loses most of what full SRRIP loses. Not explained yet. Two candidate mechanisms, neither tested: lines left at RRPV 0 by SRRIP's promotion rules keep their place after the switch back to I-RRIP; or the RRIP decisions fall in the phases where I-RRIP matters most. The x axis counts decisions, not instructions, and epochs differ in length.

Last run 2026-10-14 23:36, tree at commit c399fca. `dyn_irrip.l2c_repl.ran` is the policy source that ran (committed when saved).

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2b_sweep.toml`: the experiment file used, if there was one.
