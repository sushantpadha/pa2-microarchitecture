# Published results

I ask claude to copy long-term `results/` into `data/` for report purposes :)

Final runs only: Trace1-3, 25M warmup + 25M simulation. Each folder has its own README with the commit, the experiment file and the raw logs.

| Folder | Last run | Contents | Learning |
|--------|----------|----------|----------|
| `task2a/` | 2026-10-15 | I-RRIP at L2C: base, RRIP and I-RRIP levels 1-8 (default 8) | Data evicted first and code aged slower cuts L2 instruction MPKI by 37% (lvl 1, 1.8% speedup). Inserting data at RRPV 3 and aging code 4x slower (lvl 8) cuts it by 43% for 2.2% speedup, at +31% data MPKI. |
| `task3_pilot/` | 2026-10-15 04:22 | SUPERSEDED by task3 (stand-in SPP from origin/test1, 2B defaults before its sweep). spp, dyn, spp+dyn, spp+dyn with PF_HIT=1; stand-in SPP from origin/test1 | combination 1.0340 beats spp 1.0164 and dyn 1.0163; 96-97% of L2C prefetch copies die unused; PF_HIT=1 adds 0.1% |
| `task3_sweep/` | 2026-10-15 07:09 | STAND-IN SPP (Claude's from-scratch SPP, md5 6725d856), not the team SPP; not cited in the report. All 18 PF_HIT x PF_INS x PF_TIE combos with the duel on (3dyn_irrip) | 1.0353-1.0378; spread is Trace3 duel decision count, not the knobs |
| `task3/` | 2026-10-15 12:16 | team SPP (dev c4152ae): spp, dyn, spp+dyn unaware/aware | aware 1.0375 = unaware 1.0375, spp 1.0167, dyn 1.0191; combination beats both on every trace; the prefetch rule moves speedup by under 0.1% per trace |
| `task3_modes/` | 2026-10-15 12:30 | team SPP: knobs with the mode pinned to I-RRIP or RRIP | rule lowers L2C MPKI 0.2% (I-RRIP) and 0.7% (RRIP); speedup moves at most 0.05% |
