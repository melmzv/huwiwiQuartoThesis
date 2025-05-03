# We start by loading the libraries that we will use in this analysis.
import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from utils import read_config, setup_logging

# Set up logging
log = setup_logging()

def main():
    log.info("Starting analysis ...")
    cfg = read_config('config/do_analysis_cfg.yaml')

    # Load datasets
    log.info("Loading computed BHR Event and BHR Annual datasets...")
    bhr_event_results = pd.read_csv(cfg["bhr_event_output_csv"])
    bhr_annual_results = pd.read_csv(cfg["bhr_annual_output_csv"])

    # Compute summary statistics
    df_summary = compute_summary_statistics(bhr_annual_results, bhr_event_results)

    # Save summary statistics
    summary_statistics_csv = cfg["summary_statistics_csv"]
    df_summary.to_csv(summary_statistics_csv, index=False)
    log.info(f"Summary statistics saved to {summary_statistics_csv}")

    # Run annual regressions
    df_regression = run_regressions(bhr_annual_results, bhr_event_results)

    # Save regression results (CSV)
    regression_results_csv = cfg["regression_results_csv"]
    df_regression.to_csv(regression_results_csv, index=False)
    log.info(f"Regression results saved to {regression_results_csv}")

    # Generate Figure 1 replication
    plot_figure1(df_regression, cfg["figure1_save_path"], cfg['figure1_pickle_path'])

    
    log.info("Analysis complete.")

def compute_summary_statistics(bhr_annual_results, bhr_event_results):
    """
    Computes summary statistics (Mean, Median, Skewness, % Obs = 0, % Obs > 0) 
    for annual returns and earnings-announcement window returns like in Table 1 by Ball(2008)
    to compare preliminary results.
    """
    log.info("Computing summary statistics for comparison with Table 1...")

    # **Annual Returns Summary**
    annual_stats = {
        "Category": "Calendar-Year Returns",
        "No. Obs.": len(bhr_annual_results),
        "Mean": np.mean(bhr_annual_results["BHR_Annual"]),
        "Median": np.median(bhr_annual_results["BHR_Annual"]),
        "Skewness": pd.Series(bhr_annual_results["BHR_Annual"]).skew(),
        "% Obs. = 0": np.mean(bhr_annual_results["BHR_Annual"] == 0) * 100,
        "% Obs. > 0": np.mean(bhr_annual_results["BHR_Annual"] > 0) * 100,
    }

    # **Earnings-Announcement Window Summary (for each quarter)**
    quarterly_stats = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        df_q = bhr_event_results[bhr_event_results["quarter"] == q]

        q_stats = {
            "Category": f"Earnings-Announcement Window Returns in {q}",
            "No. Obs.": len(df_q),
            "Mean": np.mean(df_q["BHR_3day"]),
            "Median": np.median(df_q["BHR_3day"]),
            "Skewness": pd.Series(df_q["BHR_3day"]).skew(),
            "% Obs. = 0": np.mean(df_q["BHR_3day"] == 0) * 100,
            "% Obs. > 0": np.mean(df_q["BHR_3day"] > 0) * 100,
        }

        quarterly_stats.append(q_stats)

    # Convert to DataFrame
    df_summary = pd.DataFrame([annual_stats] + quarterly_stats)

    log.info("Computed summary statistics:")
    log.info(df_summary.to_string())

    return df_summary

def run_regressions(bhr_annual, bhr_event):
    """
    Runs annual cross-sectional regressions of calendar-year returns on 
    the four earnings-announcement window returns in the calendar year.
    Computes Adjusted R² and Abnormal R², following Ball (2008).
    """

    log.info("Running annual regressions with Abnormal R² benchmarking...")

    # Ensure `year_stock` column exists in BHR Event dataset
    if "year_stock" not in bhr_event.columns:
        bhr_event["year_stock"] = pd.to_datetime(bhr_event["rdq"]).dt.year

    # Merge annual and event datasets
    merged_data = bhr_annual.merge(bhr_event, on=["infocode", "year_stock"], how="inner")

    # Run regressions for each year
    regression_results = []
    for year in sorted(merged_data["year_stock"].unique()):
        yearly_data = merged_data[merged_data["year_stock"] == year]

        # Pivot data to have Q1, Q2, Q3, Q4 as separate columns
        yearly_pivot = yearly_data.pivot_table(
            index=["infocode", "year_stock"], 
            columns="quarter", 
            values="BHR_3day"
        ).reset_index()

        # Rename columns for clarity
        yearly_pivot = yearly_pivot.rename(
            columns={"Q1": "BHR_Q1", "Q2": "BHR_Q2", "Q3": "BHR_Q3", "Q4": "BHR_Q4"}
        )

        # Merge back with annual returns
        final_data = yearly_pivot.merge(bhr_annual, on=["infocode", "year_stock"], how="inner")

        # Define Dependent and Independent Variables
        independent_vars = ["BHR_Q1", "BHR_Q2", "BHR_Q3", "BHR_Q4"]
        X = final_data[independent_vars]
        y = final_data["BHR_Annual"]

        # **Fix Missing Values in Independent Variables**
        X = X.fillna(0)  # Replace NaNs with 0
        X = sm.add_constant(X)  # Add intercept

        # **Check for NaNs or Infs in y or X**
        if X.isna().any().any() or y.isna().any():
            log.warning(f"Skipping year {year} due to NaNs in data.")
            continue

        if np.isinf(X).any().any() or np.isinf(y).any():
            log.warning(f"Skipping year {year} due to Inf values in data.")
            continue

        # **Ensure we have enough observations for valid regression**
        if X.shape[0] <= X.shape[1]:  
            log.warning(f"Skipping year {year} due to insufficient observations (n={X.shape[0]}, k={X.shape[1] - 1}).")
            continue

        # Fit Regression Model
        model = sm.OLS(y, X).fit()

        # Compute Adjusted R² & Abnormal R²
        adj_r2 = model.rsquared_adj if model.nobs > model.df_model + 1 else np.nan
        abnormal_r2 = adj_r2 - 0.048 if not np.isnan(adj_r2) else np.nan

        # Store results
        regression_results.append({
            "Year": year,
            "Intercept": model.params["const"],
            "Q1": model.params.get("BHR_Q1", np.nan),
            "Q2": model.params.get("BHR_Q2", np.nan),
            "Q3": model.params.get("BHR_Q3", np.nan),
            "Q4": model.params.get("BHR_Q4", np.nan),
            "Adj_R²": adj_r2,
            "Abnormal R²": abnormal_r2,  # New column
            "No. Obs.": len(final_data)
        })

    results_df = pd.DataFrame(regression_results)

    # **Fill NaN Adj_R² with a marker (-999) if needed**
    results_df["Adj_R²"] = results_df["Adj_R²"].fillna(-999)
    results_df["Abnormal R²"] = results_df["Abnormal R²"].fillna(-999)

    # Display the output
    print("\nRegression Results with Abnormal R²:\n", results_df.round(3).to_string(index=False))    

    return results_df

def plot_figure1(results_df, save_path, pickle_path):
    """Replicates Figure 1 from Ball (2008) and saves it as PNG and Pickle."""

    log.info("Generating Figure 1 replication...")

    # Create figure
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [1, 1]})

    # **Panel A: Abnormal Adjusted R²**
    abnormal_r2 = results_df["Abnormal R²"] * 100  
    axes[0].plot(results_df["Year"], abnormal_r2, marker="o", linestyle="-", color="black")
    axes[0].axhline(y=0, color="gray", linestyle="--")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Abnormal Adj. R² (%)")
    axes[0].set_title("Panel A: Abnormal adjusted R² values from annual cross-sectional regressions\n"
                      "calendar-year arithmetic returns on arithmetic returns\n"
                      "at the four quarterly earnings announcements")
    axes[0].grid(True)

    # **Panel B: Slope Coefficients**
    axes[1].plot(results_df["Year"], results_df["Q1"], label="Quarter 1", linestyle="solid", color="black", linewidth=2)  
    axes[1].plot(results_df["Year"], results_df["Q2"], label="Quarter 2", linestyle="dashed", color="black", linewidth=1.5)  
    axes[1].plot(results_df["Year"], results_df["Q3"], label="Quarter 3", linestyle="solid", color="black", linewidth=1)  
    axes[1].plot(results_df["Year"], results_df["Q4"], label="Quarter 4", linestyle=(0, (3, 1, 1, 1)), color="black", linewidth=1.5)  

    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Slope Coefficients")
    axes[1].set_title("Panel B: Slope coefficients from annual cross-sectional regressions\n"
                      "of calendar-year arithmetic returns on arithmetic returns\n"
                      "at the four quarterly earnings announcements in the calendar year")
    axes[1].grid(True)

    # **Move Legend Outside the Plot**
    legend = axes[1].legend(frameon=True, edgecolor="black", loc="upper left", bbox_to_anchor=(1.02, 1))


    # Ensure directory exists before saving
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    os.makedirs(os.path.dirname(pickle_path), exist_ok=True)

    # Save PNG
    plt.tight_layout()
    plt.savefig(save_path, bbox_extra_artists=(legend,), bbox_inches='tight')
    log.info(f"Figure saved to {save_path}")

    # Save as Pickle
    if fig is not None:
        with open(pickle_path, "wb") as f:
            pickle.dump(fig, f)
        log.info(f"Figure saved as pickle to {pickle_path}")



if __name__ == "__main__":
    main()
