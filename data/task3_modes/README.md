# task3_modes final run

Task 3 knobs with the duel switched off, team SPP: `irrip.*` pins every follower set to I-RRIP mode (DYN_THRESH=0), `rrip.*` pins RRIP mode (DYN_THRESH=1). Other DYN_* as Task 2B's choice. Policy is the working copy `3dyn_irrip` (PF_HIT, PF_INS, PF_TIE knobs).

I-RRIP mode: 1.0393-1.0398; PF_HIT=1 lowers L2C load MPKI 0.2%. RRIP mode: 1.0176-1.0180; PF_INS=1 lowers L2C and instruction load MPKI 0.7%, PF_HIT=1 + PF_INS=1 0.7% / 0.8%; PF_TIE similar. Speedup moves at most 0.05% in either mode.

## What this run is pinned to

If any of these no longer match the current code, the run is stale: rerun the toml and save again.

| What | Version that ran |
|---|---|
| Settings | 25M warmup + 25M sim, Trace1-3, one run per config and trace |
| Tree | commit `4f25a19` (branch `feat/task3-spp`) with `origin/dev` (`c4152ae`) merged, merge not yet committed |
| L1D prefetcher | `spp.l1d_pref.ran`, md5 `947d406b` (= `prefetcher/spp.l1d_pref` on `dev` `c4152ae`) |
| L2C policy | `3dyn_irrip.l2c_repl.ran`, md5 `0a2a32e3` (= `replacement/3dyn_irrip.l2c_repl`) |

Check a source with `md5sum`. Each log's first line records its binary and env.

## What is stored

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task3_modes.toml`: the experiment file used.

Last run 2026-10-15 12:30.
