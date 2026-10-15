# task2b_hyst final run

Dynamic I-RRIP at T = 0.15, placement 0, with hysteresis h {0, 0.05, 0.1} (switch to I-RRIP when the ratio > T + h, to RRIP when <= T - h) x epoch {512, 1024} x leader sets {8, 16, 32, 64}, plus `irrip` and `rrip`. The h = 0 configs are bit-identical to the matching task2b_sweep configs.

`analysis/` is made by `tools/task2b_analysis.py`: `summary.csv`, `by_hysteresis.png`, and `rrip_decisions_h<h>.png`, one per hysteresis value with the same axes, and `rrip_decisions_summary_e<epoch>.png` (Trace3 only, 8/16/32 leaders; `_e512` has the most switching points) (per trace: speedup vs the number of post-warmup decisions that chose RRIP; mode switches are not logged, so a run with k >= 1 RRIP decisions switched between 1 and 2k times).

The loss is a step, not proportional to the RRIP decisions. On Trace2, one RRIP decision out of 48 (16 leaders, epoch 512, h = 0.05) costs 0.43% (0.9947 vs 0.9990 with none). If that one epoch ran at SRRIP's average speed on Trace2 (4.6% slower than I-RRIP), it would cost about 0.1%. From 2 decisions on, the loss levels off near 0.9% (0.991-0.992), even at 9-10 decisions. On Trace3, 2 decisions already cost 0.4-0.65%, against 0.84% for full SRRIP. So most of the cost comes after the switch back to I-RRIP. Why is not measured yet. Configs with no RRIP decision differ by up to 0.1% (Trace1, 64 leaders), because of decisions made during warmup; smaller differences are noise.

Findings: hysteresis raises speedup only by suppressing RRIP decisions. At h = 0.1 the policy switches to RRIP only when the ratio drops to 0.05 or below, and most configs then make no RRIP decision after warmup; the exceptions are 32 leaders at epoch 512 and 64 leaders at both epochs (Trace2, and Trace3 for 64 leaders at epoch 512). No configuration beats static I-RRIP; the best (8 leaders) is 0.9998 of it, the same as never switching.

Last run 2026-10-14 23:50, tree at commit c399fca. `dyn_irrip.l2c_repl.ran` is the policy source that ran (committed when saved).

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2b_hyst.toml`: the experiment file used, if there was one.
