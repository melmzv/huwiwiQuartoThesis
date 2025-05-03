# --- Header -------------------------------------------------------------------
# See LICENSE file for details
#
# This code pulls data from WRDS Databases 
# ------------------------------------------------------------------------------

import os
from getpass import getpass
import dotenv

import pandas as pd
from utils import read_config, setup_logging
import wrds

log = setup_logging()

def main():
    '''
    Main function to pull data from WRDS.

    This function reads the configuration file, gets the WRDS login credentials, and pulls the data from WRDS.

    The data is then saved to CSV and Parquet files.
    '''
    cfg = read_config('config/pull_data_cfg.yaml')
    wrds_login = get_wrds_login()
    
    # Pull CRSP and Compustat Data
    db = wrds.Connection(
        wrds_username=wrds_login['wrds_username'], 
        wrds_password=wrds_login['wrds_password']
    )
    
    log.info('Logged on to WRDS ...')
    
    pull_crsp_data(cfg, db)
    pull_compustat_data(cfg, db)
    pull_link_data(db)
    
    db.close()
    log.info("Disconnected from WRDS")

def get_wrds_login():
    '''
    Gets the WRDS login credentials.
    '''
    if os.path.exists('secrets.env'):
        dotenv.load_dotenv('secrets.env')
        wrds_username = os.getenv('WRDS_USERNAME')
        wrds_password = os.getenv('WRDS_PASSWORD')
        return {'wrds_username': wrds_username, 'wrds_password': wrds_password}
    else:
        wrds_username = input('Please provide a WRDS username: ')
        wrds_password = getpass(
            'Please provide a WRDS password (it will not show as you type): ')
        return {'wrds_username': wrds_username, 'wrds_password': wrds_password}

def pull_link_data(db):
    """
    Pulls the linking table between Compustat and CRSP from WRDS.
    """
    linkdata_df_wrds = db.get_table(library="crsp_a_ccm", table="ccmxpf_linktable")
    linkdata_df_wrds.to_parquet("data/pulled/linkdata_compustat_crsp.parquet")
    log.info("Pulling link data Compustat/CRSP... Done!")

def pull_crsp_data(cfg, db):
    """
    Pulls daily stock return data from the CRSP database on WRDS.
    """    
    # Prepare crsp_filter and crsp_vars
    crsp_vars = ', '.join(cfg['crsp_vars']) if cfg.get('crsp_vars') else "*"
    crsp_filter = ' AND '.join(cfg['crsp_filter']) if cfg.get('crsp_filter') else '1=1'
    
    crsp_query = f"SELECT {crsp_vars} FROM crsp_a_stock.dsf WHERE {crsp_filter}"
    log.info(f"Executing query: {crsp_query}")
    
    crsp_df_wrds = db.raw_sql(crsp_query)
    crsp_df_wrds.to_parquet(cfg['crsp_save_path'])
    crsp_df_wrds.to_csv(cfg['crsp_save_path_csv'], index=False)

    log.info("Pulling CRSP data ... Done!")

def pull_compustat_data(cfg, db):
    """
    Pulls quarterly fundamental data from the Compustat database on WRDS.
    """
    # Prepare fundq_filter and fundq_vars
    fundq_vars = ', '.join(cfg['fundq_vars']) if cfg.get('fundq_vars') else "*"
    fundq_filter = ' AND '.join(cfg['fundq_filter']) if cfg.get('fundq_filter') else '1=1'
    
    fundq_query = f"SELECT {fundq_vars} FROM comp_na_daily_all.fundq WHERE {fundq_filter}"
    log.info(f"Executing query: {fundq_query}")
    
    fundq_df_wrds = db.raw_sql(fundq_query)
    fundq_df_wrds.to_parquet(cfg['fundq_save_path'])
    fundq_df_wrds.to_csv(cfg['fundq_save_path_csv'], index=False)
   
    log.info("Pulling Compustat data ... Done!")

if __name__ == '__main__':
    main()