# Published results

I ask claude to copy long-term `results/` into `data/` for report purposes :)

Final runs only: Trace1-3, 25M warmup + 25M simulation. Each folder has its own README with the commit, the experiment file and the raw logs.

| Folder | Last run | Contents | Learning |
|--------|----------|----------|----------|
| `task2a/` | 2026-10-15 | I-RRIP at L2C: base, RRIP and I-RRIP levels 1-8 (default 8) | Data evicted first and code aged slower cuts L2 instruction MPKI by 37% (lvl 1, 1.8% speedup). Inserting data at RRPV 3 and aging code 4x slower (lvl 8) cuts it by 43% for 2.2% speedup, at +31% data MPKI. |
