# task2b_signal final run

A different decision signal (`dyn_irrip2.l2c_repl`, DYN_SIGNAL=1): set dueling with two leader groups of 16 sets each, one always SRRIP, one always I-RRIP. Each group counts demand misses per access, instruction misses weighted by W (DYN_IMISS_W = 1, 2, 4, 8); followers take the group with the lower weighted rate (switch to SRRIP when SRRIP's is more than 5% lower, back when I-RRIP's is). `ratio8` is the old hint ratio (DYN_SIGNAL=0) with dyn_irrip's defaults. Placement 0, epoch 1024, h = 0.05.

Checks: irrip, rrip and base are bit-identical to data/task2b_sweep; ratio8 is bit-identical to dyn_irrip's default config (data/task2b_hyst n8.DYN_EPOCH=1024.DYN_HYST=0.05).

Findings (speedup as a ratio to static I-RRIP; SRRIP decisions after warmup per trace):
- W = 1 and 2 pick SRRIP on all of Trace1 (14 of 14 decisions) and lose 0.74-0.76% there; 0.9971 overall. SRRIP has fewer L2 misses than I-RRIP on Trace1 but lower IPC, so counting misses (unweighted, or instruction misses x2) picks the wrong policy.
- W = 4 and 8 never pick SRRIP: 0.9996 (16 + 16 leader sets), against 0.9998 for the hint ratio with 8 leaders. The weighted-rate ratio I-RRIP/SRRIP averages 0.97 / 0.55 / 0.80 on Trace1/2/3 at W = 4, so Trace1 is close to the switching point (1.05).
- So the weighted duel agrees with the static ranking on all three traces once instruction misses count at least 4x; on these traces it ends up where the tuned hint ratio does, at static I-RRIP minus the leader cost.

Last run 2026-10-15 14:49, tree at commit a001cbf. `dyn_irrip2.l2c_repl.ran` is the policy source that ran (committed when saved).

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task2b_signal.toml`: the experiment file used, if there was one.
