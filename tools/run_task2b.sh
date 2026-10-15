#!/bin/bash
# Run the Task 2B sweep and hysteresis experiments at final settings, publish each
# complete one to data/ with tools/save.sh, and commit the result (no push).
# Usage: tools/run_task2b.sh [jobs]      jobs: parallel runs, default nproc - 1
# Experiments: exp/task2b_sweep.toml, exp/task2b_hyst.toml (in that order).
# Prints what happened at each step; a run log goes to data/<run>/run.log.
set -uo pipefail
cd "$(dirname "$0")/.."

jobs=${1:-$(( $(nproc) - 1 ))}
runs=(task2b_sweep task2b_hyst)
log() { echo "[run_task2b $(date +%T)] $*"; }
die() { log "STOP: $*"; exit 1; }

# --- preflight: everything the runs need, checked before any build ---
log "host $(hostname), $(nproc) cores, jobs $jobs, repo $(pwd)"
branch=$(git branch --show-current)
[ "$branch" = feat/dyn-irrip ] || die "on branch '$branch', expected feat/dyn-irrip"
log "branch $branch at $(git rev-parse --short HEAD)"
git diff --quiet HEAD -- replacement exp tools build_champsim.sh src inc \
    || die "uncommitted changes in the simulator, exp/ or tools/; the published data would not match a commit"
for t in 1 2 3; do
    [ -f ../traces/Trace$t.gz ] || die "missing ../traces/Trace$t.gz"
done
log "traces: $(ls ../traces/Trace?.gz | tr '\n' ' ')"
docker image inspect gcc:7 >/dev/null 2>&1 || die "no gcc:7 Docker image; run tools/docker/setup.sh once"
python3 -c "import pandas, numpy, matplotlib" 2>/dev/null || die "python3 needs pandas, numpy, matplotlib"
for r in "${runs[@]}"; do
    [ -f exp/$r.toml ] || die "missing exp/$r.toml"
    [ -e data/$r ] && die "data/$r already exists; move it away or delete it first"
done
log "preflight ok"

# --- run, check, publish ---
ok=() bad=()
for r in "${runs[@]}"; do
    mkdir -p results
    rlog=results/$r.run.log
    log "$r: running (log: $rlog)"
    NO_COLOR=1 tools/exp.py run exp/$r.toml -j "$jobs" > "$rlog" 2>&1
    code=$?
    grep -E "^\[plan\] runs:|^\[summary\] [0-9]+ build" "$rlog" | sed "s/^/    /"
    summary=$(grep -E "^\[summary\] [0-9]+ build" "$rlog")
    if [ $code -ne 0 ] || [ -z "$summary" ]; then
        log "$r: FAILED (exit $code), last lines of $rlog:"; tail -15 "$rlog" | sed "s/^/    /"
        bad+=("$r"); continue
    fi
    if ! grep -q " 0 failed" <<< "$summary"; then
        log "$r: some runs FAILED; see [run] lines in $rlog"; grep -i "fail" "$rlog" | head -10 | sed "s/^/    /"
        bad+=("$r"); continue
    fi
    # every config must have all 3 traces and a speedup
    if ! python3 - "$r" <<'EOF'
import sys, pandas as pd
df = pd.read_csv(f"results/{sys.argv[1]}/stats.csv")
n = df.groupby("config").trace.count()
short, nan = list(n[n != 3].index), list(df[df.speedup.isna()].config.unique())
print(f"    stats.csv: {len(n)} configs, {len(df)} rows; incomplete: {short or 'none'}; NaN speedup: {nan or 'none'}")
sys.exit(1 if short or nan else 0)
EOF
    then
        log "$r: stats.csv incomplete, not publishing"; bad+=("$r"); continue
    fi
    log "$r: saving to data/$r"
    tools/save.sh dyn_irrip "$r" 2>&1 | grep -v -i warning | sed "s/^/    /"
    if [ ! -f data/$r/stats.csv ]; then
        log "$r: save.sh did not write data/$r"; bad+=("$r"); continue
    fi
    cp "$rlog" data/$r/run.log
    log "$r: averages, MPKI as ratios to irrip:"
    NO_COLOR=1 tools/exp.py show exp/$r.toml --ratios irrip 2>&1 | grep -E "avg|ratio to" | sed "s/^/    /"
    ok+=("$r")
done

# --- commit what was published ---
log "published: ${ok[*]:-none}; not published: ${bad[*]:-none}"
if [ ${#ok[@]} -eq 0 ]; then
    log "nothing to commit"; exit 1
fi
paths=(data/README.md); for r in "${ok[@]}"; do paths+=("data/$r"); done
git add "${paths[@]}"
git commit -q -m "data: publish ${ok[*]} final runs" || die "git commit failed"
log "committed $(git rev-parse --short HEAD) (not pushed):"
git show --stat --oneline HEAD | head -5 | sed "s/^/    /"
log "fill in by hand: the TODO line in data/<run>/README.md and the data/README.md rows"
[ ${#bad[@]} -eq 0 ] || exit 1
