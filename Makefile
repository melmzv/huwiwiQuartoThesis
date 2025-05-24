# --- Header -------------------------------------------------------------------
# Automates pulling data, preparing datasets, running analysis, and rendering the paper
# If you are new to Makefiles: https://makefiletutorial.com
# (C) Mel Mzv - See LICENSE file for details
# ------------------------------------------------------------------------------
PAPER          := output/paper.pdf

TARGETS        := $(PAPER)

# the prepared data your analysis uses
PREPARED_DATA  := data/generated/gapminder_2007_prepared.parquet

# the main output of do_analysis (it also writes the figure PNG)
RESULTS        := output/summary_statistics.pickle

.PHONY: all clean very-clean dist-clean

all: $(TARGETS)

clean:
	rm -f $(PAPER) $(RESULTS) output/gapminder_figure.png

very-clean: clean
	rm -rf data/pulled data/generated

dist-clean: very-clean

# 1) Pull raw 2007 data
data/pulled/gapminder_2007.parquet: code/python/pull_data.py config/pull_data_cfg.yaml
	mkdir -p data/pulled
	python $<

# 2) Prepare 
data/generated/gapminder_2007_prepared.parquet: code/python/prepare_data.py config/prepare_data_cfg.yaml data/pulled/gapminder_2007.parquet
	mkdir -p data/generated
	python $<

# 3) Analyze (summary + plot)
$(RESULTS): code/python/do_analysis.py config/do_analysis_cfg.yaml $(PREPARED_DATA)
	mkdir -p output
	python $<

# 4) Render paper.qmd → PDF, then move into output/
$(PAPER): doc/paper.qmd $(RESULTS)
	quarto render $< 
	mkdir -p output
	mv doc/paper.pdf output
	rm -f doc/paper.ttt doc/paper.fff