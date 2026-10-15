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
