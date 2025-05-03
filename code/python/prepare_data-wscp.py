# --- Header -------------------------------------------------------------------
# Prepare the pulled data for further analysis as per Task 3 requirements
#
# (C) Mel Mzv - See LICENSE file for details
# ------------------------------------------------------------------------------

import pandas as pd
from utils import read_config, setup_logging

log = setup_logging()

def main():
    log.info("Preparing data for analysis ...")
    cfg = read_config('config/prepare_data_cfg.yaml')

    # Load the pulled datasets
    ws_stock = pd.read_csv(cfg['worldscope_sample_save_path_csv'])
    link_ds_ws = pd.read_csv(cfg['link_ds_ws_save_path_csv'])
    ds2dsf = pd.read_csv(cfg['datastream_sample_save_path_csv'])

    # Step 1: Merge Worldscope with the Linking Table
    log.info("Merging Worldscope with Linking Table...")
    ws_link_merged = merge_worldscope_link(ws_stock, link_ds_ws)

    # Step 2: Pivot dataset to long format
    log.info("Pivoting merged dataset to long format...")
    ws_long = pivot_longer_earnings(ws_link_merged)

    # Step 3: Expand dataset for event windows (-1, 0, +1 days)
    log.info("Expanding dataset for event windows...")
    ws_expanded = expand_event_window(ws_long)

    # Step 4: Merge with Datastream stock returns
    log.info("Merging expanded dataset with Datastream stock returns...")
    merged_dataset = merge_with_datastream(ws_expanded, ds2dsf)

    # Step 5: Select firms that meet sample criteria
    log.info("Selecting firms that meet the sample criteria (4 announcements per year)...")
    final_dataset = select_firms_for_sample(merged_dataset)

    # Step 6: Compute and Save BHR (Event Window)
    bhr_event_results = compute_and_save_eawr_bhr(final_dataset, cfg)

    # Step 7: Extract annual stock return data for firms in BHR Event dataset
    annual_stock_data = extract_annual_stock_data(bhr_event_results, ds2dsf, cfg)

    # Step 8: Compute and Save BHR (Annual Return)
    bhr_annual_results = compute_and_save_annual_bhr(cfg)

    # Step 9: Save the final dataset (full dataset with event windows)
    final_dataset.to_csv(cfg['prepared_wrds_ds2dsf_path'], index=False)
    final_dataset.to_parquet(cfg['prepared_wrds_ds2dsf_parquet'], index=False)

    log.info(f"Final dataset saved to {cfg['prepared_wrds_ds2dsf_path']} (CSV) and {cfg['prepared_wrds_ds2dsf_parquet']} (Parquet)")

    log.info("Preparing data for analysis ... Done!")


def merge_worldscope_link(ws_stock, link_ds_ws):
    """
    Merge Worldscope stock data with the linking table.
    Uses `code` (QA ID for Worldscope) to join with the linking table.
    Keeps only the relevant columns: year_, item6105, item5901, item5902, item5903, item5904, infocode.
    """
    # Merge datasets
    ws_link_merged = ws_stock.merge(link_ds_ws, left_on="code", right_on="code", how="inner")
    log.info(f"Merged Worldscope and Linking Table. Observations: {len(ws_link_merged)}")

    # Keep only relevant columns
    selected_columns = ["year_", "item6105", "item5901", "item5902", "item5903", "item5904", "infocode"]
    ws_link_merged = ws_link_merged[selected_columns]
    log.info(f"Filtered merged dataset to keep only relevant columns: {selected_columns}")

    return ws_link_merged

def pivot_longer_earnings(ws_link_merged):
    """
    Transforms the dataset from wide to long format, making each earnings announcement its own row.
    """
    log.info("Pivoting dataset to longer format...")

    # Pivot longer to have one earnings announcement per row
    ws_long = ws_link_merged.melt(
        id_vars=["year_", "item6105", "infocode"],  # Keep these as identifiers
        value_vars=["item5901", "item5902", "item5903", "item5904"],  # Pivot these columns
        var_name="quarter", 
        value_name="rdq"
    )

    # Map quarter names for clarity
    quarter_mapping = {
        "item5901": "Q1",
        "item5902": "Q2",
        "item5903": "Q3",
        "item5904": "Q4"
    }
    ws_long["quarter"] = ws_long["quarter"].map(quarter_mapping)

    # Log transformation
    log.info(f"Pivoted dataset. New number of rows: {len(ws_long)}")

    return ws_long

def expand_event_window(df):
    """
    Expands dataset by adding -3 to +3 day event windows for each earnings announcement.
    If `ret = 0` on Day 0, shift `event_date` to the next available trading day.
    """
    log.info("Expanding dataset to include extended event windows (-3 to +3 days)...")

    # Ensure rdq is properly parsed as datetime
    df["rdq"] = pd.to_datetime(df["rdq"], format="%m/%d/%y", errors="coerce")

    # Log the number of NaT values before expansion
    num_nat = df["rdq"].isna().sum()
    if num_nat > 0:
        log.warning(f"Found {num_nat} missing or unconvertible 'rdq' values. Skipping these rows.")

    # Drop NaT values to avoid issues in expansion
    df = df.dropna(subset=["rdq"]).copy()

    # Define the extended event window offsets (-3 to +3)
    offsets = [-3, -2, -1, 0, 1, 2, 3]

    # Generate new rows efficiently using pandas repeat + offsets
    df_expanded = df.loc[df.index.repeat(len(offsets))].reset_index(drop=True)
    df_expanded["event_window"] = offsets * (len(df))  # Apply offsets
    df_expanded["event_date"] = df_expanded["rdq"] + pd.to_timedelta(df_expanded["event_window"], unit="D")

    log.info(f"Expanded dataset. New number of rows: {len(df_expanded)}")
    return df_expanded


def merge_with_datastream(df_expanded, ds2dsf):
    """
    Merge expanded dataset with Datastream stock returns using `infocode` and `event_date`,
    then adjust `event_date` for missing stock returns (`ret = 0`), ensuring continuous shifting.
    If no valid trading day is found for Day 0, the entire event window (-3 to +3) is dropped.
    Finally, removes event windows (-3, -2, +2, +3) as they are no longer needed.
    """
    log.info("Merging with Datastream stock returns...")

    # Ensure marketdate is in datetime format
    ds2dsf["marketdate"] = pd.to_datetime(ds2dsf["marketdate"], format="%m/%d/%y", errors="coerce")

    # Merge on `infocode` and `event_date` = `marketdate`
    df_final = df_expanded.merge(ds2dsf, left_on=["infocode", "event_date"], right_on=["infocode", "marketdate"], how="left")

    # Check for unmatched event dates (missing stock return data)
    missing_ret_count = df_final["ret"].isna().sum()
    log.warning(f"{missing_ret_count} rows have missing stock return data. These will be removed.")

    # Drop rows where `ret` is missing (i.e., the merge was not possible)
    df_final = df_final.dropna(subset=["ret"]).copy()

    # Identify where `ret = 0` for event windows -1, 0, +1
    zero_ret_rows = df_final[(df_final["event_window"].isin([-1, 0, 1])) & (df_final["ret"] == 0)]
    log.info(f"Identified {len(zero_ret_rows)} cases where `ret = 0` in key event windows (-1, 0, +1).")

    # List of infocode & year_ pairs where no valid trading day is found
    failed_rdq_infocode_pairs = []

    # **SHIFTING MECHANISM** - Adjusts Day 0 first, then Day -1 and Day +1 dynamically
    for index, row in zero_ret_rows.iterrows():
        new_date = row["event_date"]
        shifted = False  # Track if shifting was successful

        while True:
            # Get the next available trading date with `ret != 0`
            possible_dates = df_final[
                (df_final["infocode"] == row["infocode"]) & 
                (df_final["event_date"] > new_date) & 
                (df_final["ret"] != 0)
            ].sort_values(by="event_date")

            if not possible_dates.empty:
                new_date = possible_dates.iloc[0]["event_date"]  # Update event_date
                new_ret = possible_dates.iloc[0]["ret"]

                # Ensure `ret != 0`
                if new_ret != 0:
                    df_final.at[index, "event_date"] = new_date
                    df_final.at[index, "ret"] = new_ret
                    shifted = True  # Mark as shifted
                    break  # Exit loop once a valid date is found

            else:
                log.warning(f"No valid trading day found for infocode {row['infocode']} on {row['event_date']}. Marking for full window removal.")
                failed_rdq_infocode_pairs.append((row["infocode"], row["year_"]))
                break  # Exit loop if no more valid dates exist

    # **NEW STEP: Remove full event windows (-3 to +3) if no valid trading day was found**
    if failed_rdq_infocode_pairs:
        log.warning(f"Removing full event windows for {len(failed_rdq_infocode_pairs)} earnings announcements with no valid trading day.")

        # Convert list to DataFrame
        failed_rdq_df = pd.DataFrame(failed_rdq_infocode_pairs, columns=["infocode", "year_"]).drop_duplicates()

        # Remove all rows associated with these failed announcements
        df_final = df_final.merge(failed_rdq_df, on=["infocode", "year_"], how="left", indicator=True)
        df_final = df_final[df_final["_merge"] == "left_only"].drop(columns=["_merge"])

    # **DROP EVENT WINDOWS -3, -2, +2, +3**
    df_final = df_final[df_final["event_window"].isin([-1, 0, 1])]
    log.info("Dropped event windows (-3, -2, +2, +3) as they are no longer needed.")

    # Drop unnecessary variables after merging
    drop_columns = ["region", "typecode", "dscode", "marketdate"]
    df_final = df_final.drop(columns=drop_columns, errors="ignore")
    log.info(f"Dropped unnecessary columns: {drop_columns}")

    # **CHECK FOR DUPLICATES**
    duplicate_rows = df_final[df_final.duplicated()]
    num_duplicate_rows = len(duplicate_rows)

    if num_duplicate_rows > 0:
        log.warning(f"Found {num_duplicate_rows} duplicate rows in the dataset. Displaying the first 5 duplicate rows:")
        log.warning(f"\n{duplicate_rows.head(5)}")  # Display first 5 duplicate rows

        # Optional: Remove duplicates
        df_final = df_final.drop_duplicates().reset_index(drop=True)
        log.info(f"Removed duplicate rows. New dataset size: {len(df_final)}")

    log.info(f"Final merged dataset after adjusting `ret = 0`. Observations: {len(df_final)}")
    return df_final


def select_firms_for_sample(df):
    """
    Filters dataset to retain firms with exactly four earnings announcements per year.
    Ensures all four announcements fall within the same calendar year and belong to unique quarters (Q1, Q2, Q3, Q4).
    """
    log.info("Selecting firms that meet the sample criteria (4 earnings announcements per year)...")

    # Ensure `rdq` is in datetime format
    df["rdq"] = pd.to_datetime(df["rdq"], errors="coerce")

    # Extract the announcement year from `rdq`
    df["rdq_year"] = df["rdq"].dt.year

    # Keep only observations where event_window = 0 (earnings announcement day)
    df_event_0 = df[df["event_window"] == 0].copy()

    # Count unique quarters per firm-year where event_window == 0
    firm_rdq_counts = df_event_0.groupby(["infocode", "rdq_year"])["quarter"].nunique().reset_index()

    # Identify firms that have exactly 4 unique quarters (Q1, Q2, Q3, Q4)
    valid_firms = firm_rdq_counts[firm_rdq_counts["quarter"] == 4]


    # Merge back with the main dataset to keep only these firms
    df_filtered = df.merge(valid_firms[["infocode", "rdq_year"]], on=["infocode", "rdq_year"], how="inner")

    # Print the total number of unique firms after filtering
    unique_firms_after = df_filtered["infocode"].nunique()
    log.info(f"Total unique firms after filtering: {unique_firms_after}")

    log.info(f"Retained {unique_firms_after} firms meeting sample criteria.")

    return df_filtered

def compute_and_save_eawr_bhr(df, cfg):
    """
    Computes the Earnings Announcement Window Return (EAWR) as the 
    buy-and-hold return (BHR) over the three-day event window (-1,0,+1).
    Retains the `quarter` column and saves the output directly to CSV & Parquet.
    """
    log.info("Computing and saving Earnings Announcement Window Returns (3-day BHR)...")

    # Ensure dataset is sorted properly
    df = df.sort_values(by=["infocode", "rdq", "event_window"])

    # Group by firm and earnings announcement date
    bhr_results = []
    
    for (infocode, rdq), group in df.groupby(["infocode", "rdq"]):
        # Ensure all required event windows (-1, 0, +1) are present
        if set(group["event_window"]) == {-1, 0, 1}:  
            try:
                ret_neg1 = group.loc[group["event_window"] == -1, "ret"].values[0]
                ret_0 = group.loc[group["event_window"] == 0, "ret"].values[0]
                ret_1 = group.loc[group["event_window"] == 1, "ret"].values[0]

                # Retrieve quarter information (same across event window)
                quarter = group["quarter"].iloc[0]  

                # Compute BHR_3day
                bhr_3day = (1 + ret_neg1) * (1 + ret_0) * (1 + ret_1) - 1

                # Append results with quarter info
                bhr_results.append({
                    "infocode": infocode,
                    "rdq": rdq,
                    "quarter": quarter,  # Retain quarter for regression later
                    "BHR_3day": bhr_3day
                })
            except Exception as e:
                log.warning(f"Skipping {infocode} on {rdq} due to missing data: {e}")
    
    # Convert to DataFrame
    df_bhr = pd.DataFrame(bhr_results)

    log.info(f"Computed {len(df_bhr)} earnings announcement window returns. Quarter column is retained.")

    # SAVE THE OUTPUT
    # Keep only relevant columns (Include `quarter` for regression use)
    df_bhr_filtered = df_bhr[["infocode", "rdq", "quarter", "BHR_3day"]]

    # Save dataset paths from config
    bhr_csv_path = cfg["bhr_event_output_csv"]
    bhr_parquet_path = cfg["bhr_event_output_parquet"]

    # Save as CSV and Parquet
    df_bhr_filtered.to_csv(bhr_csv_path, index=False)
    df_bhr_filtered.to_parquet(bhr_parquet_path, index=False)

    log.info(f"BHR dataset saved to {bhr_csv_path} (CSV) and {bhr_parquet_path} (Parquet). Quarter column is retained.")

    return df_bhr

def extract_annual_stock_data(bhr_event_results, ds2dsf, cfg):
    """
    Extracts annual stock return data for firms present in the BHR Event dataset.
    Ensures that stock data only contains the same infocodes and years as in BHR Event.
    Saves the filtered dataset for computing annual buy-and-hold returns.
    """
    log.info("Extracting annual stock return data...")

    ## Extract Unique Firms & Years from BHR Event Dataset
    selected_firms = bhr_event_results[["infocode", "rdq"]].copy()
    selected_firms["year_bhr"] = pd.to_datetime(selected_firms["rdq"]).dt.year  # Extract year from `rdq`
    # Drop duplicates to ensure unique firm-year pairs
    selected_firms = selected_firms.drop_duplicates(subset=["infocode", "year_bhr"])  
    log.info(f"Selected {len(selected_firms)} unique firm-year pairs from BHR Event dataset.")
    log.info(f"Sample of firm-year pairs:\n{selected_firms.head(20).to_string()}")

    ## Load Full Stock Dataset (Unfiltered Datastream Data)
    ds2dsf["marketdate"] = pd.to_datetime(ds2dsf["marketdate"], errors="coerce")  # Ensure datetime format
    ds2dsf["year_stock"] = ds2dsf["marketdate"].dt.year  # Extract year for filtering
    log.info(f" Total records in stock return dataset: {len(ds2dsf)}")

    ## FILTER Stock Data (Strict Matching on infocode & year)
    filtered_stock_data = ds2dsf[
        ds2dsf["infocode"].isin(selected_firms["infocode"])
    ].copy()

    # Now filter the years based on firm-specific years from BHR Event dataset
    filtered_stock_data = filtered_stock_data.merge(
        selected_firms, 
        left_on=["infocode", "year_stock"], 
        right_on=["infocode", "year_bhr"], 
        how="inner"
    ).drop(columns=["year_bhr"])  # Remove duplicate column after merging

    log.info(f" Filtered stock data. Remaining records: {len(filtered_stock_data)}")
    log.info(f" Sample of filtered stock data:\n{filtered_stock_data.head(10).to_string()}")

    ## Ensure No Missing Firms/Years
    missing_firm_years = selected_firms[~selected_firms.set_index(["infocode", "year_bhr"]).index.isin(
        filtered_stock_data.set_index(["infocode", "year_stock"]).index
    )]

    if not missing_firm_years.empty:
        log.warning(f"⚠️ {len(missing_firm_years)} firm-year pairs are **missing** from the filtered stock dataset.")
        log.warning(f"⚠️ Sample missing firm-years:\n{missing_firm_years.head(10).to_string()}")

    else:
        log.info(f" All firm-year pairs from BHR Event dataset are fully covered in stock data.")

    ## 5️⃣ Keep Only Relevant Columns
    relevant_columns = ["marketdate", "infocode", "ret", "year_stock", "rdq"]
    filtered_stock_data = filtered_stock_data[relevant_columns]

    ## Save the Filtered Dataset
    annual_stock_csv_path = cfg["annual_stock_data_csv"]
    annual_stock_parquet_path = cfg["annual_stock_data_parquet"]

    filtered_stock_data.to_csv(annual_stock_csv_path, index=False)
    filtered_stock_data.to_parquet(annual_stock_parquet_path, index=False)

    log.info(f"Final row count of filtered annual stock data: {len(filtered_stock_data)}")
    log.info(f"Annual stock data saved to:\n- {annual_stock_csv_path} (CSV)\n- {annual_stock_parquet_path} (Parquet).")

    return filtered_stock_data

def compute_and_save_annual_bhr(cfg):
    """
    Computes the Annual Buy-and-Hold Return (BHR_Annual) using daily stock returns.
    Retains the `year_stock` column and saves the output directly to CSV & Parquet.
    """
    log.info("Computing and saving Annual Buy-and-Hold Returns (BHR_Annual)...")

    # Load the filtered annual stock data
    annual_stock_data = pd.read_csv(cfg["annual_stock_data_csv"])
    log.info(f"Loaded annual stock data. Total records: {len(annual_stock_data)}")

    # Ensure `marketdate` is in datetime format
    annual_stock_data["marketdate"] = pd.to_datetime(annual_stock_data["marketdate"], errors="coerce")

    # Sort data for correct computation order
    annual_stock_data = annual_stock_data.sort_values(by=["infocode", "year_stock", "marketdate"])

    # Verify available years
    log.info("Sample of available years in the dataset:")
    log.info(annual_stock_data["year_stock"].value_counts().sort_index())

    # Compute Buy-and-Hold Annual Return (BHR_Annual)
    bhr_annual_results = []

    for (infocode, year_stock), group in annual_stock_data.groupby(["infocode", "year_stock"]):
        try:
            # Ensure sorted data for proper calculation
            group = group.sort_values(by="marketdate")

            # Compute BHR_Annual using cumulative product of (1 + daily return) - 1
            bhr_annual = (group["ret"] + 1).prod() - 1

            # Append results
            bhr_annual_results.append({
                "infocode": infocode,
                "year_stock": year_stock,
                "BHR_Annual": bhr_annual
            })
        except Exception as e:
            log.warning(f"Skipping {infocode} for {year_stock} due to missing data: {e}")

    # Convert results to DataFrame
    df_bhr_annual = pd.DataFrame(bhr_annual_results)

    log.info(f"Computed {len(df_bhr_annual)} annual buy-and-hold returns.")

    # Save the output
    # Keep only relevant columns
    df_bhr_annual_filtered = df_bhr_annual[["infocode", "year_stock", "BHR_Annual"]]

    # Save dataset paths from config
    bhr_annual_csv_path = cfg["bhr_annual_output_csv"]
    bhr_annual_parquet_path = cfg["bhr_annual_output_parquet"]

    # Save as CSV and Parquet
    df_bhr_annual_filtered.to_csv(bhr_annual_csv_path, index=False)
    df_bhr_annual_filtered.to_parquet(bhr_annual_parquet_path, index=False)

    log.info(f"BHR Annual dataset saved to:\n- {bhr_annual_csv_path} (CSV)\n- {bhr_annual_parquet_path} (Parquet).")

    return df_bhr_annual

if __name__ == "__main__":
    main()