# --- Header -------------------------------------------------------------------
# See LICENSE file for details
#
# This code pulls 2007 data from the Gapminder Database
# ------------------------------------------------------------------------------

import pandas as pd
from utils import read_config, setup_logging
from gapminder import gapminder

log = setup_logging()

def main():
    cfg = read_config('config/pull_data_cfg.yaml')

    # 1. Pull
    log.info("Loading Gapminder dataset from package ...")
    df = gapminder.copy()
    log.info("Done loading.")

    # 2. Subset for 2007 only
    df_2007 = df[df['year'] == 2007].copy()
    df_2007.to_parquet(cfg['save_path_2007_parquet'])
    log.info("Saved 2007 subset as Parquet data.")

if __name__ == '__main__':
    main()