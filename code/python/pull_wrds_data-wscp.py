# --- Header -------------------------------------------------------------------
# See LICENSE file for details
#
# This code pulls data from WRDS Worldscope and Datastream Databases and links them
# ------------------------------------------------------------------------------
import os
from getpass import getpass
import dotenv
import pandas as pd
from utils import read_config, setup_logging
import wrds

log = setup_logging()

def main():
    """
    Main function to pull data from WRDS.

    This function reads the configuration file, gets the WRDS login credentials, 
    and pulls the data from WRDS.

    The data is then saved to CSV and Parquet files.
    """
    cfg = read_config('config/pull_data_cfg.yaml')
    wrds_login = get_wrds_login()
    
    # Pull data from WRDS
    worldscope_df, ds_df, linkdata_df = pull_wrds_data(cfg, wrds_login)

    # Save pulled data
    worldscope_df.to_csv(cfg['worldscope_sample_save_path_csv'], index=False)
    worldscope_df.to_parquet(cfg['worldscope_sample_save_path'], index=False)

    ds_df.to_csv(cfg['datastream_sample_save_path_csv'], index=False)
    ds_df.to_parquet(cfg['datastream_sample_save_path'], index=False)

    linkdata_df.to_csv(cfg['link_ds_ws_save_path_csv'], index=False)
    linkdata_df.to_parquet(cfg['link_ds_ws_save_path'], index=False)


def get_wrds_login():
    """
    Gets the WRDS login credentials.
    """
    if os.path.exists('secrets.env'):
        dotenv.load_dotenv('secrets.env')
        wrds_username = os.getenv('WRDS_USERNAME')
        wrds_password = os.getenv('WRDS_PASSWORD')
    else:
        wrds_username = input("Please provide a WRDS username: ")
        wrds_password = getpass("Please provide a WRDS password (it will not show as you type): ")

    return {'wrds_username': wrds_username, 'wrds_password': wrds_password}


def pull_wrds_data(cfg, wrds_authentication):
    """
    Pulls data from WRDS (Worldscope, Datastream, and linking table).
    """
    db = wrds.Connection(
        wrds_username=wrds_authentication['wrds_username'], 
        wrds_password=wrds_authentication['wrds_password']
    )
    
    log.info("Logged on to WRDS ...")


    log.info("Pulling Worldscope data ... ")
    # Prepare the variables and filters for the WRDS Worldscope stock data query
    if cfg.get('wrds_ws_stock_vars'):
        wrds_ws_stock_vars = ', '.join(cfg['wrds_ws_stock_vars'])
    else:
        wrds_ws_stock_vars = '*'
    
    if cfg.get('wrds_ws_stock_filter'):
        wrds_ws_stock_filter = ' AND '.join(cfg['wrds_ws_stock_filter'])
    else:
        wrds_ws_stock_filter = '1=1' # To ensure the query is valid and can run even if no filters are specified.

    worldscope_query = f"SELECT {wrds_ws_stock_vars} FROM tr_worldscope.wrds_ws_stock WHERE {wrds_ws_stock_filter}"
    log.info(f"Executing query: {worldscope_query}")
    worldscope_df = db.raw_sql(worldscope_query)

    log.info("Pulling WSCP data ... Done!")



    log.info("Pulling DS data ... ")
    # Prepare the variables and filters likewise to pull from Datastream Daily Data
    if cfg.get('ds_vars'):
        ds_vars = ', '.join(cfg['ds_vars'])
    else:
        ds_vars = '*'
    
    if cfg.get('ds_filter'):
        ds_filter = ' AND '.join(cfg['ds_filter'])
    else:
        ds_filter = '1=1'

    ds_query = f"SELECT {ds_vars} FROM tr_ds_equities.wrds_ds2dsf WHERE {ds_filter}"
    log.info(f"Executing query: {ds_query}")
    ds_df = db.raw_sql(ds_query)
    log.info("Pulling DS data ... Done!")


    log.info("Pulling link data WSCP/DS... ") 
    linkdata_df = db.get_table(library="wrdsapps_link_datastream_wscope", table="ds2ws_linktable") # Pull link Data
    log.info("Pulling link data WSCP/DS... Done!")

    db.close()
    log.info("Disconnected from WRDS")


    return worldscope_df, ds_df, linkdata_df


if __name__ == '__main__':
    main()