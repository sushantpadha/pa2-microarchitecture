# CLAUDE.md

## Project

This is CS683 (Advanced Computer Architecture, IIT Bombay) Programming Assignment 2, built on ChampSim, a trace-driven microarchitecture simulator. There are four team members. The deadline is 15 Oct 2026, 5 PM. Each late day costs 20%, and anything more than 5 days late scores 0.

**`PS/PS.pdf` is the spec** (the problem statement). It defines the tasks, the required metrics and plots, and the submission format. If it disagrees with the README or anything else, `PS.pdf` wins.

**Read `PS/PS.md` (plus `PS/PS_images/`), not the PDF.** It's a Markdown copy of `PS.pdf` with the same text, the formulas as LaTeX, the links, and the example plots as images. It costs far fewer tokens. Open `PS.pdf` itself only for a final review (submission checks, checking a deliverable against the spec word for word) or when `PS.md` looks wrong. If `PS.pdf` changes, regenerate `PS.md` with `cd PS && pdf2md PS.pdf --images` and redo the hand fixes listed at its top.

| Task | File | What |
|------|------|------|
| 1A | `prefetcher/ip_stride.l1d_pref` | Read and understand the IP-stride prefetcher. |
| 1B | `prefetcher/spp.l1d_pref` | Stride Pattern Prefetcher at L1D: uniform strides first, a signature-based fallback for non-uniform ones, degree > 1, accuracy-based throttling, no page crossing. |
| 2A | `replacement/irrip.l2c_repl` | Instruction-conscious RRIP at L2C. First add `isInstruction` to the `update_replacement_state` signature in `inc/cache.h` and pass it at every call site. |
| 2B | `replacement/dyn_irrip.l2c_repl` | Set-dueling Dynamic I-RRIP, plus a sensitivity sweep over at least 5 values of the decision parameter. |
| 3 | `replacement/dyn_irrip.l2c_repl` | Make Dynamic I-RRIP aware of lines brought in by prefetches. It must beat both SPP alone and Dynamic I-RRIP alone on IPC. |

The baseline is no L1D prefetcher with LRU at L2C (`no`/`lru`). Speedup and coverage are measured against it.

## Layout

```
../traces/            the course traces Trace1.gz, Trace2.gz, Trace3.gz, outside the repo
branch/ inc/ src/     ChampSim core
prefetcher/           *.l1d_pref prefetchers (spp.l1d_pref is task 1B)
replacement/          *.l2c_repl policies (irrip, dyn_irrip for tasks 2 and 3)
build_champsim.sh     course build script, used as is
tools/docker/         GCC 7 in Docker: setup.sh (once), build-gcc7.sh, reset.sh
tools/exp.py          build + run + parse + show/plot; usage in tools/README.md
exp/task*.toml        one experiment file per task: configs, metrics, [test] settings
results/              experiment output, gitignored
data/                 results the team chooses to publish (committed); see "Published data"
report/               LaTeX source of Summary.pdf; `make -C report`, usage in report/README.md
Summary.pdf           the report deliverable, built from report/
.vscode/settings.json LaTeX Workshop: rebuild the report on save
submit.sh             builds the Moodle tarball from an explicit file list; review before submitting
PS/PS.pdf             the spec (original)
PS/PS.md, PS_images/  Markdown copy of the spec with its example plots; read this one
```

## Experimenting

The whole loop is one script and one file per task:

```bash
tools/exp.py run  exp/task1.toml --test      # quick: the file's [test] traces and instruction counts
tools/exp.py show exp/task1.toml --test --plot
tools/exp.py run  exp/task1.toml             # final: every trace, 25M warmup + 25M sim
```

- **Every number comes from `tools/exp.py`.** It builds with GCC 7 in Docker, runs the traces in parallel, parses the logs, and computes metrics against the baseline. Don't build or run binaries by hand for numbers that go in the report.
- **Test first, then final.** `--test` uses the file's `[test]` section (a few representative traces, smaller instruction counts) to check that a change builds, runs, and moves the metric the expected way. Final settings are fixed by `PS.pdf` and can't be changed in a file. Only final runs go in the report. Test settings are only useful if they behave like the final ones: check that the baseline has misses at the level the task measures (the start of a trace can have none; see tools/README.md), and check the subset against a final run.
- **A new experiment is a new config, not a new script.** Add a `[config.name]` with `pf`, `repl` and `env` to the task's toml. Commented lines in each file show the defaults.
- **Parameters are swept through environment variables.** Policy code reads a knob with `getenv()` and keeps a built-in default, so the TAs' plain build still works. A list in `env` is swept. Don't add compile-time flags or new ChampSim command-line options for sweeps.
- **One run per config and trace is enough.** ChampSim is deterministic (its seed comes from the trace path, see "Traces"), so repeats give identical numbers. The summary across traces is the `avg` row: geometric mean for speedup, arithmetic mean otherwise.
- **Read the plan `run` prints before waiting on it.** It lists every setting and where it came from, every config with defaults marked, and the builds and runs to do. A wrong trace set or instruction count shows up there.
- **Check the stats before trusting them.** A metric that looks too good, is NaN, or doesn't move usually means the stat or the code is wrong. Read the raw log in `results/<task>/<config>/` before explaining the number.
- **Final parameter values must be the code defaults.** The submission tarball has no `exp/` or `tools/`: graders build with `build_champsim.sh` and run the binary, so `getenv()` knobs fall back to their defaults. Once a sweep picks a value, make it the default in the code, so a plain build and run reproduces the reported results.
- **Keep the tooling small.** Extend `exp.py` (a regex in `METRICS`, a key in the toml) only when a task needs it.

## Published data

`results/` is scratch: gitignored, overwritten freely, never cited. `data/` holds the results the team decides to publish, and it is committed and submitted.
- Only final runs go in `data/`, never `--test` or quick runs.
- The team chooses what goes in. Don't copy results into `data/` unless asked.
- Keep each published result traceable: the `stats.csv` and the raw logs it came from, plus the experiment file and the commit it ran at.
- Report numbers and figures (`report/figures/`) come from `data/`, not from `results/`.

## Report

`Summary.pdf` is built from `report/` with `make -C report`, or by saving any `.tex` file in VS Code (LaTeX Workshop). The format copies PS.pdf's. Each task has one file in `report/sections/` with a subsection per deliverable. Figures go in `report/figures/`, made from `data/`. Numbers in the report come from final runs only, and every claim needs the mechanism behind it. See `report/README.md`.

**The report is submitted and graded. Be strict about what goes in it:**
- **Only what `PS.md` asks for.** Each task's deliverables, and the context needed to read them. Nothing else.
- **No environment or tooling details.** No local paths (e.g. where traces live), machine specs, Docker, `exp.py`, `results/`, or how we organize the repo. The graders don't need them, and every extra detail is something to be wrong about.
- **Only verified claims.** Every number, file path and statement must be checked against the code, a final run, or `PS.md` before it goes in. If it isn't verified, leave it out or leave a `% TODO` comment, not text.
- **Short.** Prefer a table or one sentence over a paragraph. Don't pad.

## Your role

The team writes the simulator code (prefetchers and replacement policies) by hand. Do not write or rewrite that code unless someone asks for a specific change.

Your job is logistics:

- Maintaining `tools/exp.py`, the `exp/*.toml` files and the Docker setup.
- Running experiments and sweeps, and reading their results.
- Keeping `submit.sh` in line with `PS.md`'s submission instructions: tarball name, contents, no traces, all deliverables present.
- Proofreading code: correctness bugs, page-boundary violations, off-by-one errors, stats that are wrong or misleading.
- Proofreading `Summary.pdf` and other writeups.

## How to work

- **Reason from fundamentals.** Every design choice, threshold, and claim in code or writing needs a mechanism behind it: what the hardware does, why the number is what it is. Do not hand over heuristics, magic constants, or explanations that only sound right. If you can't justify something from first principles, say so and don't write it.
- **Experiments are required for validation.** This is systems work, and intuition is often wrong. A claim is not settled until a run supports it. Experiments check reasoning; they do not replace it. Do not tune parameters blindly.
- **No autopilot.** Stop and think before producing anything. Read the relevant code and `PS.md` section first. Shorter correct output beats longer generic output.
- **Keep it simple.** Short scripts, few files, standard library first (bash, Python stdlib, pandas, matplotlib). Follow the `ponytail` skill for code, `plain-docs` for writing, and `caveman` for chat replies.
- **Branches.** `dev` is the working branch. `main` only mirrors the course repo (`upstream`); it is pulled and merged into `dev` by hand. Never commit to `main`. Work on `dev` or a branch off it. Always ask before committing.
- **Commit messages: one or two lines, nothing else.** A short conventional subject (`feat: ...`, `fix: ...`), at most one more line. No body paragraphs, no `Co-Authored-By` or other attribution lines. The commit history is graded.

## Traces

The course traces are `../traces/Trace1.gz`, `Trace2.gz` and `Trace3.gz` (gzip, 2.5-5.3 GB each), outside the repo. `exp.py` uses all three by default.
- **Never unzip them.** ChampSim reads them directly through `gunzip -c`.
- **Always pass a trace as `<dir>/TraceN.gz`, with the directory named `traces`.** ChampSim seeds `rand()` from the third-from-last token of the trace path, split on `/ . , -` (`src/main.cc`, around line 1130). For `../traces/Trace1.gz` that token is `traces`, the same for all three traces. `rand()` is used in physical page allocation, so a differently named directory can change the numbers. A bare `Trace1.gz` has only two tokens, and the code then reads before the start of an array. `exp.py` always passes `../traces/TraceN.gz`.
- The test settings (1M + 5M) were chosen on an earlier trace. Check that the baseline has misses on these traces at that length before relying on `--test`.

## Repo notes

- Traces live outside the repo (IITB Google Drive, LDAP login required). Never commit them.
- `results/` is gitignored. Never commit it; published results go in `data/`.
- `build_champsim.sh` rewrites tracked files on every build (`inc/champsim.h`, `prefetcher/*_prefetcher.cc`, `replacement/*_replacement.cc`, `branch/branch_predictor.cc`). Only stage the `.l1d_pref`/`.l2c_repl` files and anything you meant to change.
- Builds share one source tree, so two builds must never run at once. `exp.py` runs them one at a time.
- `irrip.l2c_repl` and `dyn_irrip.l2c_repl` do not exist yet, even though `PS.pdf` says templates are provided.
- `rrip.l2c_repl` does not build until the `isInstruction` signature change is done.
- Never build with the host compiler for anything that runs. A GCC 16 static build compiles fine but aborts at startup (`std::bad_cast`); GCC 7 builds of the same code run correctly.
- The usage text in `build_champsim.sh` is stale ("DCLIP", "PA2 Prefetcher"). The script accepts any name that has a matching `.l1d_pref` or `.l2c_repl` file.
