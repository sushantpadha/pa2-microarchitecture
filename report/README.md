# Summary report

LaTeX source of `Summary.pdf`.

```
report.tex          main file
common.tex          preamble, title page, listing styles
sections/*.tex      one file per task
figures/            plots, made from ../data/ by plots.py
tables/             LaTeX tables, made from ../data/ by tables.py
```

**Build:** `make -C report` writes `../Summary.pdf`. In VS Code (LaTeX Workshop), saving any `.tex` file runs the same build; view it live with Ctrl+Alt+V.

**Tables and figures:** run `python3 report/tables.py` and `python3 report/plots.py` after `data/` changes. Never edit `tables/*.tex` by hand; change the script instead.

**Writing:**
- New task: `\task{2B}{Dynamic I-RRIP}`. New section files need `% !TEX root = ../report.tex` on line 1.
- `\subsection` per deliverable. Tables: `booktabs`. Figures: `\includegraphics{name.png}` (from `figures/`).
- Code: `lstlisting`; trees and shell: `lstlisting[style=plain]`.
- Anything not yet verified: `\brt{...}` (bright red TODO). Remove all before submitting.
