# Build the PA2 summary: `make -C report` (or `make` inside report/).
#   make         -> ../Summary.pdf, the name PS.pdf asks for
#   make clean   -> remove build/ (Summary.pdf is kept)
# The repo root Makefile is ChampSim's, so this one lives here.
# VS Code (LaTeX Workshop) builds into the same build/ on save; see ../.vscode/settings.json.

LATEXMK := latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build

../Summary.pdf: report.tex common.tex $(wildcard sections/*.tex) $(wildcard figures/*)
	$(LATEXMK) report.tex
	cp build/report.pdf $@

.PHONY: clean
clean:
	rm -rf build
