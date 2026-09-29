#!/usr/bin/env bash
# Build the PA2 Moodle submission tarball from an explicit list of files.
#
# Submission format, from PS/PS.md "Submission Instructions" (read 2026-09-29):
#   - One tar.gz of the repo, named <TeamName_LDAP1_LDAP2...>_pa2.tar.gz, uploaded on Moodle.
#   - Don't include trace files.
#   - It must contain the PA2 repository codebase, all tasks' implementations,
#     generated results, and Summary.pdf (data, plots, and explanations of the
#     logic used for each task).
#   - All deliverables must also be pushed to the GitHub repo, which must be
#     private, with a proper commit history (unclear or last-minute commits can
#     lose points).
#   - The code must have detailed comments explaining the logic; it is reviewed.
#   - Late: 20% per day (GitHub and Moodle), 0 after 5 days. Deadline: 15 October, 5 PM.
#
# What goes in: only files git tracks under the paths in INCLUDE, so build output
# (bin/, obj/), results/, traces and our tooling never slip in. Untracked files
# under INCLUDE stop the script: add and commit them first.
#
# Usage: ./submit.sh
set -euo pipefail
cd "$(dirname "$0")"

red=$'\e[1;31m' yellow=$'\e[1;33m' reset=$'\e[0m'
[ -t 1 ] || red="" yellow="" reset=""

cat <<EOF
${red}============================================================================
 WARNING: this script was generated automatically from PS/PS.md.
 Last updated: 2026-09-29.
 Review its output below, and update TEAM, LDAPS and INCLUDE in this script
 so that the tarball matches the current submission instructions.
============================================================================${reset}
EOF
read -r -p "Type 'yes' to continue: " answer
[ "$answer" = yes ] || { echo "aborted"; exit 1; }

TEAM=flipflops                           # team name
LDAPS=(24b0918 24b0945 24b1057 24b1071)  # LDAP IDs, in the order the tarball name should list them
TAR="${TEAM}_$(IFS=_; echo "${LDAPS[*]}")_pa2.tar.gz"
TOP=pa2-microarchitecture                # folder name inside the tarball

# Repository codebase + task implementations (prefetcher/, replacement/, and the
# core files changed for Task 2A), generated results (data/), and the report.
# This is enough to build with build_champsim.sh (GCC 7) and run the binary on a
# trace; tested 2026-09-29 by extracting the tarball, building and running once.
# Tuned parameters must be the code defaults for that run to match data/.
INCLUDE=(
  README.md LICENSE Makefile build_champsim.sh
  branch inc src prefetcher replacement
  data
  Summary.pdf
)

fail=0
for p in "${INCLUDE[@]}"; do
  [ -e "$p" ] || { echo "${red}MISSING${reset}  $p"; fail=1; }
done
untracked="$(git ls-files --others --exclude-standard -- "${INCLUDE[@]}")"
if [ -n "$untracked" ]; then
  echo "${red}UNTRACKED${reset} (git add + commit them, or they won't be submitted):"
  echo "$untracked" | sed 's/^/  /'
  fail=1
fi
[ "$fail" = 0 ] || exit 1

files="$(git ls-files -- "${INCLUDE[@]}")"
if echo "$files" | grep -qE '\.champsimtrace|\.xz$|\.gz$'; then
  echo "${red}ERROR${reset}  trace-like files would be included:"
  echo "$files" | grep -E '\.champsimtrace|\.xz$|\.gz$' | sed 's/^/  /'
  exit 1
fi
modified="$(git status --porcelain -- "${INCLUDE[@]}")"
if [ -n "$modified" ]; then
  echo "${yellow}NOTE${reset}  uncommitted changes in included files; the tarball uses the working copy:"
  echo "$modified" | sed 's/^/  /'
fi

echo "$files" | tar -czf "$TAR" --transform "s|^|$TOP/|" -T -
echo
echo "wrote $TAR ($(du -h "$TAR" | cut -f1), $(tar -tzf "$TAR" | wc -l) files):"
if command -v tree >/dev/null; then
  tar -tzf "$TAR" | tree --fromfile --noreport .
else
  tar -tzf "$TAR" | sort
fi
