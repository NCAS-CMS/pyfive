# this does not build it like the JOSS paper, but it's good
# enough to test references etc
pandoc paper.md \
  --citeproc \
  --bibliography=paper.bib \
  --csl=apa \
  -o paper.pdf