# --- Header -------------------------------------------------------------------
# Prepare the pulled data for further analysis as per Task 3 requirements
#
# (C) Mel Mzv - See LICENSE file for details
# ------------------------------------------------------------------------------

# --- Header -------------------------------------------------------------------
# Prepare the pulled data for further analysis as per Task 3 requirements
# ------------------------------------------------------------------------------

import pandas as pd
from utils import read_config, setup_logging

log = setup_logging()

def main():
    log.info("Preparing data for analysis ...")
    cfg = read_config('config/prepare_data_cfg.yaml')

    ws_stock = pd.read_csv(cfg['worldscope_sample_save_path_csv'])
    link_ds_ws = pd.read_csv(cfg['link_ds_ws_save_path_csv'])
    ds2dsf = pd.read_csv(cfg['datastream_sample_save_path_csv'])

    ws_link_merged = merge_worldscope_link(ws_stock, link_ds_ws)
    ws_long = pivot_longer_earnings(ws_link_merged)
    ws_expanded = expand_event_window(ws_long)
    merged_dataset = merge_with_datastream(ws_expanded, ds2dsf)
    final_dataset = select_firms_for_sample(merged_dataset)
    bhr_event_results = compute_and_save_eawr_bhr(final_dataset, cfg)
    annual_stock_data = extract_annual_stock_data(bhr_event_results, ds2dsf, cfg)
    bhr_annual_results = compute_and_save_annual_bhr(cfg)

    final_dataset.to_csv(cfg['prepared_wrds_ds2dsf_path'], index=False)
    final_dataset.to_parquet(cfg['prepared_wrds_ds2dsf_parquet'], index=False)
    log.info("Preparation complete.")

def merge_worldscope_link(ws_stock, link_ds_ws):
    merged = ws_stock.merge(link_ds_ws, on="code", how="inner")
    return merged[["year_", "item6105", "item5901", "item5902", "item5903", "item5904", "infocode"]]

def pivot_longer_earnings(ws_link_merged):
    df = ws_link_merged.melt(
        id_vars=["year_", "item6105", "infocode"],
        value_vars=["item5901", "item5902", "item5903", "item5904"],
        var_name="quarter", value_name="rdq"
    )
    quarter_map = {"item5901": "Q1", "item5902": "Q2", "item5903": "Q3", "item5904": "Q4"}
    df["quarter"] = df["quarter"].map(quarter_map)
    return df

def expand_event_window(df):
    df = df.dropna(subset=["rdq"]).copy()
    df["rdq"] = pd.to_datetime(df["rdq"], errors="coerce")
    offsets = [-3, -2, -1, 0, 1, 2, 3]
    df = df.loc[df.index.repeat(len(offsets))].reset_index(drop=True)
    df["event_window"] = offsets * (len(df) // len(offsets))
    df["event_date"] = df["rdq"] + pd.to_timedelta(df["event_window"], unit="D")
    return df

def merge_with_datastream(df_expanded, ds2dsf):
    ds2dsf["marketdate"] = pd.to_datetime(ds2dsf["marketdate"], errors="coerce")
    merged = df_expanded.merge(ds2dsf, left_on=["infocode", "event_date"], right_on=["infocode", "marketdate"], how="left")
    merged = merged.dropna(subset=["ret"])
    merged = merged[merged["event_window"].isin([-1, 0, 1])]
    return merged.drop(columns=["region", "typecode", "dscode", "marketdate"], errors="ignore")

def select_firms_for_sample(df):
    df["rdq"] = pd.to_datetime(df["rdq"], errors="coerce")
    df["rdq_year"] = df["rdq"].dt.year
    df_event_0 = df[df["event_window"] == 0]
    counts = df_event_0.groupby(["infocode", "rdq_year"])["quarter"].nunique().reset_index()
    valid = counts[counts["quarter"] == 4]
    return df.merge(valid[["infocode", "rdq_year"]], on=["infocode", "rdq_year"], how="inner")

def compute_and_save_eawr_bhr(df, cfg):
    df = df.sort_values(by=["infocode", "rdq", "event_window"])
    results = []
    for (infocode, rdq), group in df.groupby(["infocode", "rdq"]):
        if set(group["event_window"]) == {-1, 0, 1}:
            r = group.set_index("event_window")["ret"]
            bhr = (1 + r[-1]) * (1 + r[0]) * (1 + r[1]) - 1
            results.append({"infocode": infocode, "rdq": rdq, "quarter": group["quarter"].iloc[0], "BHR_3day": bhr})
    df_bhr = pd.DataFrame(results)
    df_bhr.to_csv(cfg["bhr_event_output_csv"], index=False)
    df_bhr.to_parquet(cfg["bhr_event_output_parquet"], index=False)
    return df_bhr

def extract_annual_stock_data(bhr_event_results, ds2dsf, cfg):
    ds2dsf["marketdate"] = pd.to_datetime(ds2dsf["marketdate"], errors="coerce")
    ds2dsf["year_stock"] = ds2dsf["marketdate"].dt.year
    bhr_event_results["year_bhr"] = pd.to_datetime(bhr_event_results["rdq"]).dt.year
    firm_years = bhr_event_results.drop_duplicates(subset=["infocode", "year_bhr"])
    filtered = ds2dsf.merge(firm_years, left_on=["infocode", "year_stock"], right_on=["infocode", "year_bhr"], how="inner")
    filtered[["marketdate", "infocode", "ret", "year_stock", "rdq"]].to_csv(cfg["annual_stock_data_csv"], index=False)
    filtered[["marketdate", "infocode", "ret", "year_stock", "rdq"]].to_parquet(cfg["annual_stock_data_parquet"], index=False)
    return filtered

def compute_and_save_annual_bhr(cfg):
    df = pd.read_csv(cfg["annual_stock_data_csv"])
    df["marketdate"] = pd.to_datetime(df["marketdate"], errors="coerce")
    df = df.sort_values(by=["infocode", "year_stock", "marketdate"])
    results = (
        df.groupby(["infocode", "year_stock"])["ret"]
        .apply(lambda x: (1 + x).prod() - 1)
        .reset_index(name="BHR_Annual")
    )
    results.to_csv(cfg["bhr_annual_output_csv"], index=False)
    results.to_parquet(cfg["bhr_annual_output_parquet"], index=False)
    return results

if __name__ == "__main__":
    main()