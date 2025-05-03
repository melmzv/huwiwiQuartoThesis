# --- Header -------------------------------------------------------------------
# Automates pulling data, preparing datasets, running analysis, and rendering the paper
# If you are new to Makefiles: https://makefiletutorial.com
# (C) Mel Mzv - See LICENSE file for details
# ------------------------------------------------------------------------------

PAPER := output/paper.pdf
PICKLE := output/figure1_replication.pickle
RESULTS := output/regression_results.csv
SUMMARY := output/summary_statistics.csv

TARGETS := $(PAPER) $(PICKLE) $(RESULTS) $(SUMMARY)

# Config Files
PULL_DATA_CFG := config/pull_data_cfg.yaml
PREPARE_DATA_CFG := config/prepare_data_cfg.yaml
DO_ANALYSIS_CFG := config/do_analysis_cfg.yaml

# Pulled Data (WRDS - CRSP/Compustat)
PULLED_CRSP := data/pulled/crsp_daily_stock_returns.csv
PULLED_COMPUSTAT := data/pulled/compustat_fundq_1972_2023.csv
PULLED_LINK := data/pulled/linkdata_compustat_crsp.parquet

# Pulled Data (Worldscope/Datastream)
PULLED_WS := data/pulled/wrds_ws_stock.csv
PULLED_DS := data/pulled/wrds_ds2dsf.csv
PULLED_LINK_DS_WS := data/pulled/wrds_link_ds_ws.csv

# Prepared Data
PREPARED_DATA := data/generated/prepared_data_wrds_ds2dsf.csv
BHR_EVENT_RESULTS := data/generated/bhr_event_results.csv
BHR_ANNUAL_RESULTS := data/generated/bhr_annual_results.csv

.PHONY: all clean very-clean dist-clean

all: $(TARGETS)

clean:
	rm -f $(TARGETS) $(PICKLE) $(RESULTS) $(SUMMARY) $(PREPARED_DATA) $(BHR_EVENT_RESULTS) $(BHR_ANNUAL_RESULTS)

very-clean: clean
	rm -f $(PULLED_CRSP) $(PULLED_COMPUSTAT) $(PULLED_LINK) $(PULLED_WS) $(PULLED_DS) $(PULLED_LINK_DS_WS)

dist-clean: very-clean
	rm -f config.csv

# Data Pulling Step (WRDS - CRSP/Compustat)
$(PULLED_CRSP) $(PULLED_COMPUSTAT) $(PULLED_LINK): code/python/pull_wrds_data-wscp.py $(PULL_DATA_CFG)
	python3 $<

# Data Pulling Step (Worldscope/Datastream)
$(PULLED_WS) $(PULLED_DS) $(PULLED_LINK_DS_WS): code/python/pull_wrds_data-wscp.py $(PULL_DATA_CFG)
	python3 $<

# Data Preparation Step
$(PREPARED_DATA): code/python/prepare_data-wscp.py $(PULLED_CRSP) $(PULLED_COMPUSTAT) $(PULLED_LINK) \
	$(PULLED_WS) $(PULLED_DS) $(PULLED_LINK_DS_WS) $(PREPARE_DATA_CFG)
	python3 $<

# Analysis Step
$(RESULTS) $(SUMMARY) $(PICKLE): code/python/do_analysis-wscp.py $(PREPARED_DATA) $(DO_ANALYSIS_CFG)
	python3 $<

# Paper Compilation Step
$(PAPER): doc/paper.qmd doc/references.bib $(RESULTS) $(PICKLE)
	quarto render $< --quiet
	mv doc/paper.pdf output
	rm -f doc/paper.ttt doc/paper.fff