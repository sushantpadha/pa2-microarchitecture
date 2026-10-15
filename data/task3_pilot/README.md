# task3_pilot final run

Task 3 pilot: SPP alone, Dynamic I-RRIP alone, and the combination, with the combination either prefetch-unaware (`spp_dyn`) or not promoting on prefetch hits (`hit`, `PF_HIT=1`). The prefetcher is a stand-in: `spp_test1` is the SPP from branch `origin/test1`, not the team's final 1B SPP. `dyn` ran `dyn_irrip.l2c_repl.ran`. The other configs ran `3dyn_irrip.l2c_repl.ran`, the same policy plus prefetch tracking and knobs.

Results (speedup over base, geomean of Trace1-3):

| config | speedup | L2C MPKI | L2 instr MPKI | L2 data MPKI |
|---|---|---|---|---|
| spp | 1.0164 | 15.56 | 10.15 | 5.41 |
| dyn | 1.0163 | 14.05 | 6.13 | 7.92 |
| spp_dyn | 1.0340 | 13.14 | 6.12 | 7.01 |
| hit | 1.0351 | 13.09 | 6.06 | 7.03 |

- The combination beats both alone on every trace. On Trace3 the margin over `spp` is small: 1.0253 vs 1.0242.
- 96-97% of L2C copies of prefetched lines are evicted without a demand hit (used / dead with `spp_dyn`: 2100 / 62247, 705 / 24930, 1276 / 30124). With LRU at L2C it is 92-95%.
- `PF_HIT=1` adds 0.1% on average: +0.3% on Trace2, -0.06% on Trace3.

## What this run is pinned to

If any of these no longer match the current code, this run is stale: ignore it and regenerate with `tools/exp.py run exp/task3_pilot.toml`.

| What | Version that ran |
|---|---|
| Settings | 25M warmup + 25M sim, Trace1-3, one run per config and trace |
| L1D prefetcher | `spp_test1.l1d_pref.ran` = `prefetcher/spp.l1d_pref` at `origin/test1` `ff8c8a6`, md5 `85e7f247`. A stand-in, not the team's 1B SPP. |
| `dyn` policy | `dyn_irrip.l2c_repl.ran`, md5 `dd01559d`. Uncommitted Task 2B working copy: lvl 8 I-RRIP, thresh 0.25, hyst 0, 32 leaders, place 0, epoch 1024. |
| Other configs | `3dyn_irrip.l2c_repl.ran`, md5 `2f9b40b1`. The same policy and defaults, plus prefetch tracking and the `PF_HIT`/`PF_INS`/`PF_TIE` knobs (defaults 0; `pf_ctr_max` 7). |
| Tree | commit `c399fca` (branch `feat/dyn-irrip`); none of the three files above was committed. |

Check a source with `md5sum`. Each log's first line records its binary and env, and its `Initialize Dynamic I-RRIP` line records the knob values.

## What is stored

- `stats.csv`: one row per config and trace. Columns: IPC, speedup, L1D accuracy (issued and resolved), coverage, L1D, L2C, L2 instr and L2 data load MPKI, and two pairs of L2C prefetch-copy counts:
  - `l2c_pf_useful` / `l2c_pf_useless`: ChampSim's own counts. They include translation prefetches.
  - `dyn_pf_used` / `dyn_pf_dead`: the policy's own counts, PREFETCH fills only. A copy is "used" if a demand hits it once; it is "dead" if it is evicted without one.
- `<config>/<trace>.log`: raw ChampSim output. The `3dyn_irrip` logs end with two more lines that are not in `stats.csv`:
  - `DYN_IRRIP`: duel epochs, the fraction of epochs in I-RRIP mode, and the min/mean/max instruction ratio.
  - `DYN_IRRIP_PF`: prefetch fills, prefetch hits, used and dead counts over all sets and over leader sets only (`ldr_used`, `ldr_dead`, which train `pf_ctr`), the number of dead inserts, and `pf_ctr` at the end. All counts cover the measured region only.
- `<metric>.png`: one bar chart per metric, from `tools/exp.py show --plot`.
- `task3_pilot.toml`: the experiment file.

Last run 2026-10-15 04:22.
