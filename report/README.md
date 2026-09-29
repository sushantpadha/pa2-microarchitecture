# Summary report

`PS.pdf` asks for a `Summary.pdf` with data, plots and explanations for each task. It's built from LaTeX here.

```
report.tex        main file: title page, contents, one \input per task
common.tex        preamble: PS.pdf's layout (letter, 1in margins, "Task N" headings), PA1's font, code listings
sections/task*.tex  one file per task, with a subsection per deliverable
figures/          plots used in the report, made from the published results in ../data/
build/            latexmk output, gitignored
```

**Build:** `make -C report` writes `../Summary.pdf` at the repo root. `make -C report clean` removes `build/`. The repo root `Makefile` is ChampSim's, so this one lives in `report/`.

**VS Code:** with the LaTeX Workshop extension, saving any `.tex` file rebuilds the report. The workspace settings in `.vscode/settings.json` use the same latexmk flags and `build/` directory as the Makefile. Every section file starts with `% !TEX root = ../report.tex`, so saving a section builds the whole report. Keep that line in new section files.

**Writing:**
- Start a task with `\task{2B}{Dynamic I-RRIP}`. It starts a new page with the italic "Task 2B" label and a large bold title, like PS.pdf.
- Use `\subsection` for each deliverable. Headings are unnumbered, like PS.pdf.
- Tables use `booktabs` (`\toprule`, `\midrule`, `\bottomrule`). Figures: `\includegraphics[width=\textwidth]{name.png}` finds files in `figures/`.
- Code: `\begin{lstlisting} ... \end{lstlisting}` (C++ style, line numbers). Directory trees and shell commands: `\begin{lstlisting}[style=plain]`.
- The team table on the title page is in `common.tex` (`\reporttitle`).
