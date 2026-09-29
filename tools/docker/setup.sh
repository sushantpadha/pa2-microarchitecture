#!/bin/bash
# One-time: pull the gcc:7 image. Re-running is a harmless no-op.
# Only touches Docker's image cache - never the host's own gcc/g++.
set -euo pipefail
# Colors only on a terminal tput knows; any other terminal just gets plain text.
c=""; r=""
if [ -t 1 ] && tput sgr0 >/dev/null 2>&1; then c=$(tput setaf 6)$(tput bold); r=$(tput sgr0); fi

docker pull gcc:7
echo "${c}[setup] size:${r}     $(docker image inspect gcc:7 --format '{{.Size}}' | numfmt --to=iec)"
echo "${c}[setup] id:${r}       $(docker image inspect gcc:7 --format '{{.Id}}' | cut -c8-19)"
echo "${c}[setup] compiler:${r} $(docker run --rm gcc:7 g++ --version | head -1)"
