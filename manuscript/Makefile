MAIN ?= main
PDFLATEX ?= pdflatex
BIBTEX ?= bibtex
TEXFLAGS ?= -interaction=nonstopmode -halt-on-error

.PHONY: all paper quick clean cleanall

all: paper

paper: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex references.bib $(wildcard sections/*.tex)
	@if command -v latexmk >/dev/null 2>&1; then \
		latexmk -pdf $(TEXFLAGS) $(MAIN).tex; \
	else \
		$(PDFLATEX) $(TEXFLAGS) $(MAIN).tex; \
		$(BIBTEX) $(MAIN); \
		$(PDFLATEX) $(TEXFLAGS) $(MAIN).tex; \
		$(PDFLATEX) $(TEXFLAGS) $(MAIN).tex; \
	fi

quick:
	$(PDFLATEX) $(TEXFLAGS) $(MAIN).tex

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).fdb_latexmk $(MAIN).fls $(MAIN).log $(MAIN).out $(MAIN).toc $(MAIN).lof $(MAIN).lot

cleanall: clean
	rm -f $(MAIN).pdf
