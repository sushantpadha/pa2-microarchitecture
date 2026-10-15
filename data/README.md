# Published results

I ask claude to copy long-term `results/` into `data/` for report purposes :)

Final runs only: Trace1-3, 25M warmup + 25M simulation. Each folder has its own README with the commit, the experiment file and the raw logs.

| Folder | Last run | Contents | Learning |
|--------|----------|----------|----------|
| `task2a/` | 2026-10-15 | I-RRIP at L2C: base, RRIP and I-RRIP levels 1-8 (default 8) | Data evicted first and code aged slower cuts L2 instruction MPKI by 37% (lvl 1, 1.8% speedup). Inserting data at RRPV 3 and aging code 4x slower (lvl 8) cuts it by 43% for 2.2% speedup, at +31% data MPKI. |
| `task2b_sweep/` | 2026-10-14 23:36 | Dynamic I-RRIP: T x leaders x epoch, placement 0 | No setting beats static I-RRIP; speedup falls as switching to RRIP rises |
| `task2b_hyst/` | 2026-10-14 23:50 | Dynamic I-RRIP: hysteresis x leaders x epoch, T = 0.15 | Hysteresis helps only by suppressing switches |
| `task2b_pilot_leaders/` | 2026-10-15 01:02 | Pilot: leaders 8-256 (old lvl 1 rules) | No noise penalty down to 8 leaders; 128+ only lose speedup |
| `task2b_pilot_epoch/` | 2026-10-15 01:35 | Pilot: epoch 128-8192 (old lvl 1 rules) | 128-1024 equal; 4096+ barely decides on Trace3 |
| `task2b_pilot_thresh/` | 2026-10-15 01:46 | Pilot: T 0-1 (old lvl 1 rules) | Nothing changes below 0.15; T >= 0.7 equals SRRIP |
| `task2b_grid/` | 2026-10-15 02:38 | Placement x T x leaders, epoch scaled with leaders | Placement changes speedup by < 0.1% at T <= 0.25 |
| `task2b_epochlog/` | 2026-10-15 14:19 | Per-decision r log, 8 leaders E1024 | Log does not change results; too few decisions for a time plot |
| `task2b_signal/` | 2026-10-15 14:49 | Weighted-miss set dueling (dyn_irrip2), W = 1-8, vs hint ratio | Unweighted misses pick SRRIP on Trace1 and lose; W >= 4 matches static I-RRIP |
| `task2b_rtrace1/` | 2026-10-15 14:56 | Trace1 only, r at every decision (8 leaders, E128), T 0.15/0.25/0.4 | r moves in slow waves; 2 SRRIP decisions of 52 cost 0.14-0.19% |
| `task3_pilot/` | 2026-10-15 04:22 | SUPERSEDED by task3 (stand-in SPP from origin/test1, 2B defaults before its sweep). spp, dyn, spp+dyn, spp+dyn with PF_HIT=1; stand-in SPP from origin/test1 | combination 1.0340 beats spp 1.0164 and dyn 1.0163; 96-97% of L2C prefetch copies die unused; PF_HIT=1 adds 0.1% |
| `task3_sweep/` | 2026-10-15 07:09 | STAND-IN SPP (Claude's from-scratch SPP, md5 6725d856), not the team SPP; not cited in the report. All 18 PF_HIT x PF_INS x PF_TIE combos with the duel on (3dyn_irrip) | 1.0353-1.0378; spread is Trace3 duel decision count, not the knobs |
| `task3/` | 2026-10-15 12:16 | team SPP (dev c4152ae): spp, dyn, spp+dyn unaware/aware | aware 1.0375 = unaware 1.0375, spp 1.0167, dyn 1.0191; combination beats both on every trace; the prefetch rule moves speedup by under 0.1% per trace |
| `task3_modes/` | 2026-10-15 12:30 | team SPP: knobs with the mode pinned to I-RRIP or RRIP | rule lowers L2C MPKI 0.2% (I-RRIP) and 0.7% (RRIP); speedup moves at most 0.05% |
