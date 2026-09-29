#!/bin/bash
# Undo setup.sh: remove the gcc:7 image and any leftover containers from
# it. Host gcc/g++ was never touched. Run setup.sh again to restore.
set -euo pipefail
# Colors only on a terminal tput knows; any other terminal just gets plain text.
c=""; r=""
if [ -t 1 ] && tput sgr0 >/dev/null 2>&1; then c=$(tput setaf 6)$(tput bold); r=$(tput sgr0); fi

containers="$(docker ps -aq --filter ancestor=gcc:7)"
if [ -n "$containers" ]; then
    echo "${c}[reset] removing $(echo "$containers" | wc -l) leftover container(s)${r}"
    docker rm -f $containers
fi

if docker image inspect gcc:7 >/dev/null 2>&1; then
    echo "${c}[reset] removing gcc:7 image${r}"
    docker rmi gcc:7
else
    echo "${c}[reset] gcc:7 image not present, nothing to remove${r}"
fi
