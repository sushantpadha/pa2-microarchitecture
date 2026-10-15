# task3_sweep final run

Task 3 knob sweep: every combination of PF_HIT {0,1,2} x PF_INS {0,1,2} x PF_TIE {0,1} in `3dyn_irrip` (the Task 3 working copy of dyn_irrip with more knobs), plus spp, dyn and dyn3 (3dyn_irrip without a prefetcher, equal to dyn). DYN_* set by env to Task 2B's choice (8 / 256 / 0 / 0.15).

All knob combinations land in 1.0353-1.0378 (unaware 1.0365). Traces 1-2 vary by at most 0.03%. Trace3 depends strongly on the duel's epoch count (only 6-7 epochs per run): all runs with 7 epochs have IPC 0.3932-0.3934, runs with 6 epochs 0.3908-0.3922. So the ranking here mixes the duel's timing with the knobs; see task3_modes for the knobs without the duel. `pf.PF_HIT=1.PF_INS=1.PF_TIE=0` makes the same decisions as the final `dyn_irrip` and gives the same numbers.

## What this run is pinned to

If any of these no longer match the current code, the run is stale: rerun the toml and save again.

| What | Version that ran |
|---|---|
| Settings | 25M warmup + 25M sim, Trace1-3, one run per config and trace |
| Tree | commit `5de25ac` (branch `feat/task3-spp`) plus the uncommitted sources below |
| L1D prefetcher | `spp.l1d_pref.ran`, md5 `6725d856`: the 1B SPP before a comment-only fix, a storage-print change and a guard that only acts for a non-default knob. `spp` here equals `spp` in task3 exactly. |
| L2C policy (knobs) | `3dyn_irrip.l2c_repl.ran`, md5 `0a2a32e3` |
| L2C policy (`dyn`) | `dyn_irrip.l2c_repl.ran`, md5 `dd01559d` (Task 2B file before the Task 3 changes; DYN_* set by env) |

Check a source with `md5sum`. Each log's first line records its binary and env.

## What is stored

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task3_sweep.toml`: the experiment file used, if there was one.
- `3dyn_irrip` logs also have `DYN_IRRIP_PF` (prefetch fills and hits, used/dead in all sets and leaders, the adaptive counter's end value).

Last run 2026-10-15 07:09, tree at commit 5de25ac. `3dyn_irrip.l2c_repl.ran` is the policy source that ran (NOT committed when saved).
