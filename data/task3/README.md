# task3 final run

Task 3 final run with the team SPP: SPP alone, Dynamic I-RRIP alone, and SPP + Dynamic I-RRIP with prefetch awareness off (`spp_dyn_unaware`: `PF_INS=0 PF_HIT=0`) and on (`spp_dyn`: code defaults). All DYN_* values are the code defaults (Task 2B's choice: 8 leaders, epoch 256, placement 0, threshold 0.15).

Speedup (geomean): spp 1.0167, dyn 1.0191, spp_dyn_unaware 1.0375, spp_dyn 1.0375. The combination beats both components on every trace. Aware vs unaware per trace: +0.03%, +0.05%, -0.08%; both make the same number of duel decisions on every trace.

## What this run is pinned to

If any of these no longer match the current code, the run is stale: rerun the toml and save again.

| What | Version that ran |
|---|---|
| Settings | 25M warmup + 25M sim, Trace1-3, one run per config and trace |
| Tree | commit `4f25a19` (branch `feat/task3-spp`) with `origin/dev` (`c4152ae`) merged, merge not yet committed |
| L1D prefetcher | `spp.l1d_pref.ran`, md5 `947d406b` (= `prefetcher/spp.l1d_pref` on `dev` `c4152ae`) |
| L2C policy | `dyn_irrip.l2c_repl.ran`, md5 `94f6dcbd`. Comments were trimmed afterwards (now md5 `71315226`); the code is identical with comments stripped |

Check a source with `md5sum`. Each log's first line records its binary and env.

## What is stored

- `stats.csv`: one row per config and trace.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `<config>/<trace>.log`: raw ChampSim output; the first line records the command and env.
- `task3.toml`: the experiment file used.
- Each `dyn_irrip` log ends with `DYN_IRRIP` (duel epochs, fraction in I-RRIP mode, ratio spread) and `DYN_IRRIP_DEAD` / `DYN_IRRIP_DEAD_LEADERS` (per fill kind: L2C lines evicted after at least one demand hit, and without one; all sets / leader sets only; ROI only).

Last run 2026-10-15 12:16.
