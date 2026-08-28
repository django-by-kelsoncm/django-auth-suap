# Minimal makefile for Sphinx multi-language documentation

SPHINXOPTS    ?= -W
SPHINXBUILD   ?= sphinx-build
BUILDDIR      = _build

.PHONY: help html clean

help:
	@echo "Targets:"
	@echo "  html  Build HTML documentation for pt-br and en"
	@echo "  clean Clean build directory"

html:
	mkdir -p $(BUILDDIR)/html
	$(SPHINXBUILD) $(SPHINXOPTS) -b html pt-br/1.6.x $(BUILDDIR)/html/pt-br/1.6.x
	$(SPHINXBUILD) $(SPHINXOPTS) -b html en/1.6.x $(BUILDDIR)/html/en/1.6.x
	cp index.html $(BUILDDIR)/html/index.html

clean:
	rm -rf $(BUILDDIR)
