# Summary report

LaTeX source of `Summary.pdf`.

```
report.tex          main file
common.tex          preamble, title page, listing styles
sections/*.tex      one file per task
figures/            plots, made from ../data/
```

**Build:** `make -C report` writes `../Summary.pdf`. In VS Code (LaTeX Workshop), saving any `.tex` file runs the same build; view it live with Ctrl+Alt+V.

**Writing:**
- New task: `\task{2B}{Dynamic I-RRIP}`. New section files need `% !TEX root = ../report.tex` on line 1.
- `\subsection` per deliverable. Tables: `booktabs`. Figures: `\includegraphics{name.png}` (from `figures/`).
- Code: `lstlisting`; trees and shell: `lstlisting[style=plain]`.
