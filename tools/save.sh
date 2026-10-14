#!/bin/bash
# Publish a final run: copy results/<run> and the policy that produced it into data/<run>.
# Usage: tools/save.sh <policy> <run> [--force]    e.g. tools/save.sh irrip task2a
# --force replaces an existing data/<run>, including its hand-written README and index row.
set -euo pipefail
cd "$(dirname "$0")/.."

policy=$1 run=$2 force=${3:-}
src=replacement/$policy.l2c_repl res=results/$run dst=data/$run
[ -f "$src" ] || { echo "no $src"; exit 1; }
[ -f "$res/stats.csv" ] || { echo "no $res/stats.csv"; exit 1; }
[[ $run == *_w*_s* ]] && { echo "$run is a test run; only final runs go in data/"; exit 1; }

if [ -e "$dst" ] && [ "$force" != "--force" ]; then
    echo "$dst exists. Rerun with --force to replace it (its README and index row are reset to TODO)."
    exit 1
fi
rm -rf "$dst"   # data/ is tracked by git, so an old copy can be recovered
mkdir -p "$dst"
cp -r "$res"/. "$dst"/
rm -rf "$dst/_build"
cp "$src" "$dst/$policy.l2c_repl.ran"
[ -f "exp/$run.toml" ] && cp "exp/$run.toml" "$dst/"

stamp=$(date -r "$res/stats.csv" "+%Y-%m-%d %H:%M")
commit=$(git rev-parse --short HEAD)
git diff --quiet HEAD -- "$src" 2>/dev/null && state="committed when saved" || state="NOT committed when saved"

cat > "$dst/README.md" <<EOF
# $run final run

TODO: one or two lines on what this run compares.

Last run $stamp, tree at commit $commit. \`$policy.l2c_repl.ran\` is the policy source that ran ($state).

- \`stats.csv\`: one row per config and trace.
- \`<config>/<trace>.log\`: raw ChampSim output; the first line records the command and env.
- \`$run.toml\`: the experiment file used, if there was one.
EOF

# One row per run in the index: replace an existing row, or append a new one.
row="| \`$run/\` | $stamp | TODO contents | TODO learning |"
index=data/README.md
if grep -q "^| \`$run/\` |" "$index"; then
    grep -v "^| \`$run/\` |" "$index" > "$index.tmp" && mv "$index.tmp" "$index"
fi
echo "$row" >> "$index"

echo "Saved $res and $src to $dst (commit $commit, policy $state)."
echo "Please fill in by hand:"
echo "  $dst/README.md   the TODO line: what this run compares"
echo "  $index           the TODO contents and learning in the $run row"
