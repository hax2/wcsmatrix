# Overleaf LaTeX Project: Who Covers Whom?

This directory contains the complete, self-contained LaTeX source and compiled PDF for the research paper reporting the reproduction and frontier-model extension of the Word Coverage Score (WCS) benchmark.

## Files
* `main.tex` — Complete paper source with abstract, methodology, tables, figures, discussion, and bibliography citations.
* `references.bib` — BibTeX entries for all cited literature.
* `figures/` — High-resolution empirical matrix figures:
  * `matrix-realistic-0.99.png`
  * `matrix-strict-0.99.png`
* `main.pdf` — Pre-compiled 5-page publication-ready PDF.
* `overleaf_project.zip` — Ready-to-upload archive for Overleaf.

## Uploading to Overleaf
1. Go to [Overleaf](https://www.overleaf.com/).
2. Click **New Project** $\to$ **Upload Project**.
3. Select `overleaf_project.zip` (located at `/home/jovyan/wcsmatrix/overleaf/overleaf_project.zip`).
4. Overleaf will automatically detect `main.tex` and compile the document.

## Local Compilation
To re-compile locally:
```bash
cd overleaf
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```
