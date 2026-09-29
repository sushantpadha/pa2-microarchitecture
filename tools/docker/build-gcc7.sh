#!/bin/bash
# Build with GCC 7 inside the gcc:7 image, host compiler untouched.
# build_champsim.sh links -static, so the output is a plain ELF binary -
# Docker is only needed for this build step, never for running it.
# Usage: tools/docker/build-gcc7.sh <l1d_pref> <l2c_repl> <name>
set -euo pipefail
cd "$(dirname "$0")/../.."

# Colors only on a terminal tput knows; any other terminal just gets plain text.
c=""; r=""
if [ -t 1 ] && tput sgr0 >/dev/null 2>&1; then c=$(tput setaf 6)$(tput bold); r=$(tput sgr0); fi

if ! docker image inspect gcc:7 >/dev/null 2>&1; then
    echo "${c}[build-gcc7] gcc:7 image not found.${r} Run tools/docker/setup.sh first." >&2
    exit 1
fi

echo "${c}[build-gcc7] image:${r} gcc:7 ($(docker image inspect gcc:7 --format '{{.Id}}' | cut -c8-19))"
echo "${c}[build-gcc7] args:${r} $*"

# -t forces a tty inside the container so gcc/make emit color codes
# instead of detecting a pipe and going plain; only when our own
# stdout is a tty, so this still works fine when piped or logged.
# TERM is fixed to one the image knows; the host's (e.g. xterm-kitty) may not be.
tty_flag=""
[ -t 1 ] && tty_flag="-t"

docker run --rm $tty_flag \
    -u "$(id -u):$(id -g)" \
    -v "$PWD":/w \
    -w /w \
    -e TERM=xterm-256color \
    gcc:7 \
    bash -c 'echo "[build-gcc7] compiler: $(g++ --version | head -1)"; ./build_champsim.sh "$@"' -- "$@"
