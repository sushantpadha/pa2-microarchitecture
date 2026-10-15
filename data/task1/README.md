# task1 final runs

IP-stride and SPP at L1D against the no-prefetcher baseline (LRU at L2C), plus a sweep of SPP's IP table size (sets x ways) and prefetch distance. Final settings: 25M warmup + 25M simulation, all three traces. Experiment file: `exp/task1.toml`. The SPP runs are from commit 724eb9e: 9-bit signature, 512-entry pattern table.

- `stats.csv`: one row per config and trace. `python3 report/task1.py` rebuilds it from the logs and makes `report/figures/t1_*.png`.
- `<config>/<trace>.log`: raw ChampSim output. The first line records the command and env.
- `ipt.SPP_IPT_SET_BITS=<b>.SPP_IPT_WAYS=<w>.DISTANCE=<d>`: the sweep, 2^b sets x w ways, d prefetch steps skipped.

SPP's code default is 16 sets x 6 ways with no distance, so "SPP" in the report is `ipt.SPP_IPT_SET_BITS=4.SPP_IPT_WAYS=6.DISTANCE=0`.

`spp/` is stale: it ran an earlier SPP (64 x 4 IP table, 1024-entry pattern table; see the `SPP storage bits` line in its logs). Do not use it. Its rows are still in `stats.csv`.
