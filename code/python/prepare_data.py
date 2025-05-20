import pandas as pd
import os
from utils import read_config, setup_logging

log = setup_logging()

def main():
    cfg = read_config('config/prepare_data_cfg.yaml')

    log.info("Loading raw Gapminder 2007 data ...")
    df = pd.read_parquet(cfg['input_path'])

    log.info("Checking for missing values ...")
    missing = df.isnull().sum()
    log.info(f"Missing values per column:\n{missing}")

    log.info("Rounding numeric columns to 0 decimal places ...")
    numeric_cols = df.select_dtypes(include='number').columns
    df[numeric_cols] = df[numeric_cols].round(0)

    os.makedirs(os.path.dirname(cfg['output_path']), exist_ok=True)
    df.to_parquet(cfg['output_path'])
    log.info("Prepared data saved.")

if __name__ == '__main__':
    main()