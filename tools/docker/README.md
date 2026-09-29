# GCC 7 in Docker

All builds use GCC 7, the course's compiler, from the `gcc:7` Docker image. The host's own `gcc`/`g++` is never touched.

Don't build with the host compiler instead. A GCC 16 static build compiles fine but aborts at startup with `std::bad_cast`; the same code built with GCC 7 runs correctly.

`build_champsim.sh` links with `-static`, so the binary built in the container is a plain executable. Docker is only used for the build; the binary runs on the host.

`tools/exp.py` calls `build-gcc7.sh` itself. You only need these scripts directly for setup, reset, or a one-off build.

```bash
tools/docker/setup.sh                                     # once: pull gcc:7 (~1.6GB); rerunning is a no-op
tools/docker/build-gcc7.sh <l1d_pref> <l2c_repl> <name>   # same arguments as ./build_champsim.sh
tools/docker/reset.sh                                     # remove the gcc:7 image and leftover containers
```

`build-gcc7.sh` prints the image id and compiler version before building. It runs the container as your user, so `bin/` and `obj/` stay owned by you.

The scripts work from any terminal:
- The scripts color their own `[setup]`/`[build-gcc7]`/`[reset]` lines only if `tput` recognizes your terminal. Otherwise, or when output is piped, they print plain text.
- Inside the container, `TERM` is always `xterm-256color`, which the image knows. Your host's `TERM` (e.g. `xterm-kitty`) may not be in the image. Compiler colors come through when you run `build-gcc7.sh` directly in a terminal.
