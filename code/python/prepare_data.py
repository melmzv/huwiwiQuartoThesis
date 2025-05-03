# --- Header -------------------------------------------------------------------
# Prepare the pulled data for further analysis as per Analysis requirements
#
# (C) Mel Mzv - See LICENSE file for details
# ------------------------------------------------------------------------------

def main():
    log.info("Preparing data ...")
    cfg = read_config('config/prepare_data_cfg.yaml')

    ws = pd.read_csv(cfg['worldscope_sample_save_path_csv'])
    link = pd.read_csv(cfg['link_ds_ws_save_path_csv'])
    ds = pd.read_csv(cfg['datastream_sample_save_path_csv'])

    merged = merge_worldscope_link(ws, link)
    long = pivot_longer_earnings(merged)
    events = expand_event_window(long)
    with_ret = merge_with_datastream(events, ds)
    sample = select_firms_for_sample(with_ret)
    bhr_event = compute_and_save_eawr_bhr(sample, cfg)
    annual_data = extract_annual_stock_data(bhr_event, ds, cfg)
    bhr_annual = compute_and_save_annual_bhr(cfg)

    sample.to_csv(cfg['prepared_wrds_ds2dsf_path'], index=False)
    sample.to_parquet(cfg['prepared_wrds_ds2dsf_parquet'], index=False)
    log.info("Done.")

def merge_worldscope_link(ws, link):
    df = ws.merge(link, on="code", how="inner")
    return df[["year_", "item6105", "item5901", "item5902", "item5903", "item5904", "infocode"]]

def pivot_longer_earnings(df):
    df = df.melt(
        id_vars=["year_", "item6105", "infocode"],
        value_vars=["item5901", "item5902", "item5903", "item5904"],
        var_name="quarter", value_name="rdq"
    )
    qmap = {"item5901": "Q1", "item5902": "Q2", "item5903": "Q3", "item5904": "Q4"}
    df["quarter"] = df["quarter"].map(qmap)
    return df

def expand_event_window(df):
    df = df.dropna(subset=["rdq"]).copy()
    df["rdq"] = pd.to_datetime(df["rdq"], errors="coerce")
    offsets = [-3, -2, -1, 0, 1, 2, 3]
    df = df.loc[df.index.repeat(len(offsets))].reset_index(drop=True)
    df["event_window"] = offsets * (len(df) // len(offsets))
    df["event_date"] = df["rdq"] + pd.to_timedelta(df["event_window"], unit="D")
    return df

def merge_with_datastream(df, ds):
    ds["marketdate"] = pd.to_datetime(ds["marketdate"], errors="coerce")
    df = df.merge(ds, left_on=["infocode", "event_date"], right_on=["infocode", "marketdate"], how="left")
    df = df.dropna(subset=["ret"])
    df = df[df["event_window"].isin([-1, 0, 1])]
    return df.drop(columns=["region", "typecode", "dscode", "marketdate"], errors="ignore")

def select_firms_for_sample(df):
    df["rdq"] = pd.to_datetime(df["rdq"], errors="coerce")
    df["rdq_year"] = df["rdq"].dt.year
    df0 = df[df["event_window"] == 0]
    valid = df0.groupby(["infocode", "rdq_year"])["quarter"].nunique().reset_index()
    valid = valid[valid["quarter"] == 4]
    return df.merge(valid[["infocode", "rdq_year"]], on=["infocode", "rdq_year"], how="inner")

def compute_and_save_eawr_bhr(df, cfg):
    df = df.sort_values(by=["infocode", "rdq", "event_window"])
    rows = []
    for (i, r), g in df.groupby(["infocode", "rdq"]):
        if set(g["event_window"]) == {-1, 0, 1}:
            ret = g.set_index("event_window")["ret"]
            bhr = (1 + ret[-1]) * (1 + ret[0]) * (1 + ret[1]) - 1
            rows.append({"infocode": i, "rdq": r, "quarter": g["quarter"].iloc[0], "BHR_3day": bhr})
    out = pd.DataFrame(rows)
    out.to_csv(cfg["bhr_event_output_csv"], index=False)
    out.to_parquet(cfg["bhr_event_output_parquet"], index=False)
    return out

def extract_annual_stock_data(bhr, ds, cfg):
    ds["marketdate"] = pd.to_datetime(ds["marketdate"], errors="coerce")
    ds["year_stock"] = ds["marketdate"].dt.year
    bhr["year_bhr"] = pd.to_datetime(bhr["rdq"]).dt.year
    pairs = bhr.drop_duplicates(subset=["infocode", "year_bhr"])
    f = ds.merge(pairs, left_on=["infocode", "year_stock"], right_on=["infocode", "year_bhr"], how="inner")
    f[["marketdate", "infocode", "ret", "year_stock", "rdq"]].to_csv(cfg["annual_stock_data_csv"], index=False)
    f[["marketdate", "infocode", "ret", "year_stock", "rdq"]].to_parquet(cfg["annual_stock_data_parquet"], index=False)
    return f

def compute_and_save_annual_bhr(cfg):
    df = pd.read_csv(cfg["annual_stock_data_csv"])
    df["marketdate"] = pd.to_datetime(df["marketdate"], errors="coerce")
    df = df.sort_values(by=["infocode", "year_stock", "marketdate"])
    out = df.groupby(["infocode", "year_stock"])["ret"].apply(lambda x: (1 + x).prod() - 1).reset_index(name="BHR_Annual")
    out.to_csv(cfg["bhr_annual_output_csv"], index=False)
    out.to_parquet(cfg["bhr_annual_output_parquet"], index=False)
    return out

if __name__ == "__main__":
    main()