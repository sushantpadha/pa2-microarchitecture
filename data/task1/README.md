# task1 final run

IP-stride and SPP at L1D against the no-prefetcher baseline (LRU at L2C), plus a sweep of SPP's IP table size. Final settings: 25M warmup + 25M simulation, all three traces. The SPP code is at commit 99b5e5a, where the IP table size is set by `SPP_IPT_SET_BITS` and `SPP_IPT_WAYS`.

- `stats.csv`: one row per config and trace. `report/task1.py` rebuilds it from the logs.
- `<config>/<trace>.log`: raw ChampSim output. The first line records the command and env.
- Figures: `report/figures/t1_*.png`, made by `python3 report/task1.py`.
- `plots/`: analysis plots, also from `report/task1.py`. One chart per `stats.csv` metric (every config, per trace and mean), plus `spp_classes.png` (uniform vs pattern prefetches and accuracy) and `spp_degree.png` (share of epochs at each degree), both for the default SPP.

The code default IP table is 32 sets x 4 ways, chosen from the sweep below, so "SPP" in the figures and tables is `ipt.SPP_IPT_SET_BITS=5.SPP_IPT_WAYS=4`. A plain build (no env) reproduces those logs exactly. The `spp` directory ran the earlier 64 x 4 default and matches `ipt.SPP_IPT_SET_BITS=6.SPP_IPT_WAYS=4` exactly.

## IP-stride vs SPP

Means over the three traces (geometric mean for speedup). Accuracy is ChampSim's own (useful / issued).

| Config | IPC | Speedup | L1D load MPKI | MPKI / baseline | Accuracy | Coverage |
|---|---|---|---|---|---|---|
| baseline | 0.2885 | 1.000 | 9.21 | 1.000 | - | - |
| ip_stride | 0.2892 | 1.002 | 8.96 | 0.973 | 35.6% | 2.8% |
| spp (32 x 4) | 0.2938 | 1.017 | 8.36 | 0.908 | 56.7% | 12.2% |

SPP beats IP-stride on every trace and every metric. Its speedup per trace is 1.010, 1.015 and 1.025 (Traces 1-3). IP-stride's speedup is between 1.000 and 1.005.

SPP removes 9% of L1D load misses but gains only 1.7% IPC. The cause is not measured yet. Candidates: how much of the run time L1D misses account for, late prefetches, and prefetches that fill only the L2.

## IP table size sweep

| Sets x ways | Entries | Speedup | Coverage | SPP storage |
|---|---|---|---|---|
| 16 x 4 | 64 | 1.0162 | 12.11% | 1970.75 B |
| 32 x 4 (default) | 128 | 1.0167 | 12.17% | 2386.75 B |
| 16 x 8 | 128 | 1.0166 | 12.23% | 2418.75 B |
| 64 x 4 (earlier default) | 256 | 1.0164 | 12.04% | 3202.75 B |
| 32 x 8 | 256 | 1.0164 | 12.03% | 3266.75 B |
| 64 x 8 | 512 | 1.0165 | 12.01% | 4930.75 B |

The table size barely matters. All six points are within 0.0005 speedup and 0.23 points of coverage, against a 0.016 gain over the baseline, and more entries do not help steadily. At 64 x 4 the IP table is 52% of SPP's storage. 32 x 4 is now the code default: it saves 25% of the storage (2386.75 B against 3202.75 B) at no measurable cost. The gaps between sizes are smaller than the run-to-run drift a size change causes (it changes which prefetches are sent, so the throttle's degree path differs), so the sweep does not rank the sizes.

A possible reason, not checked: SPP only allocates an IP on an L1D miss, so the IPs worth tracking may fit in 64 entries. Counting the distinct allocated IPs would test this.
