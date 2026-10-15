# task2b_rtrace1 final-length run (Trace1 only)

dyn_irrip with DYN_LOG=1 on Trace1 at the final instruction counts (25M warmup, 25M simulation), run through the `[test]` section of `task2b_rtrace1.toml` because final runs always use all three traces. 8 leaders, epoch 128 leader accesses (8x more decisions than the final E = 1024, about 95 per run), T = 0.15 / 0.25 / 0.4, h = 0, plus irrip and the LRU base.

`analysis/plot1.png` (made by `tools/task2b_analysis.py`): r at every decision, one panel per T, SRRIP decisions filled.

Findings: after warmup r moves between 0.36 and 0.60 in slow waves. T = 0.15 and 0.25 make no SRRIP decision after warmup (speedup over LRU 1.0073 and 1.0075, against 1.0068 for static I-RRIP; differences this small come from decisions made during warmup). T = 0.4 picks SRRIP in 2 of 52 decisions after warmup, at the bottom of two dips, and gets 1.0054. Full SRRIP on Trace1 costs 0.72% (data/task2b_sweep).

`dyn_irrip.l2c_repl.ran` is the policy source that ran (committed at fa16eaa, with DYN_LOG). Raw logs: `<config>/Trace1.log`; the first line records the command and env.
