import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from utils import read_config, setup_logging

log = setup_logging()


def main():
    log.info("Running post-preparation analysis...")

    cfg = read_config("config/do_analysis_cfg.yaml")

    # === Load prepared data ===
    df_event = pd.read_csv(cfg["bhr_event_output_csv"])
    df_annual = pd.read_csv(cfg["bhr_annual_output_csv"])

    # === Summary Statistics ===
    summary = compute_summary(df_annual, df_event)
    summary.to_csv(cfg["summary_statistics_csv"], index=False)

    # === Regressions & Plot ===
    results = run_regressions(df_annual, df_event)
    results.to_csv(cfg["regression_results_csv"], index=False)
    plot_figure(results, cfg["figure1_save_path"], cfg["figure1_pickle_path"])

    log.info("Analysis complete.")


def compute_summary(df_annual, df_event):
    """Basic summary stats for annual and event-window returns."""
    def stats(series):  # Helper
        return {
            "Mean": series.mean(),
            "Median": series.median(),
            "Skew": series.skew(),
            "% = 0": (series == 0).mean() * 100,
            "% > 0": (series > 0).mean() * 100,
            "Obs": len(series)
        }

    summary = [{"Category": "Annual", **stats(df_annual["BHR_Annual"])}]
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        subset = df_event[df_event["quarter"] == q]["BHR_3day"]
        summary.append({"Category": f"3-day {q}", **stats(subset)})

    return pd.DataFrame(summary)


def run_regressions(df_annual, df_event):
    """Run annual regressions of annual returns on quarterly 3-day returns."""
    df_event["year_stock"] = pd.to_datetime(df_event["rdq"]).dt.year
    merged = df_annual.merge(df_event, on=["infocode", "year_stock"], how="inner")

    results = []
    for year in sorted(merged["year_stock"].unique()):
        year_df = merged[merged["year_stock"] == year]
        pivot = year_df.pivot_table(index=["infocode", "year_stock"], columns="quarter", values="BHR_3day").reset_index()
        pivot.columns.name = None
        pivot.rename(columns={f"Q{i}": f"BHR_Q{i}" for i in range(1, 5)}, inplace=True)

        X = pivot[[f"BHR_Q{i}" for i in range(1, 5)]].fillna(0)
        y = df_annual[df_annual["year_stock"] == year]["BHR_Annual"]
        if len(X) <= X.shape[1]:
            continue
        model = sm.OLS(y.reset_index(drop=True), sm.add_constant(X)).fit()
        results.append({
            "Year": year,
            **{f"Q{i}": model.params.get(f"BHR_Q{i}", float('nan')) for i in range(1, 5)},
            "Adj_R²": model.rsquared_adj,
            "Abnormal R²": model.rsquared_adj - 0.048
        })
    return pd.DataFrame(results)


def plot_figure(df, png_path, pkl_path):
    """Plot abnormal R² and slope coefficients over time."""
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))
    ax[0].plot(df["Year"], df["Abnormal R²"] * 100, marker="o")
    ax[0].set_title("Abnormal Adjusted R² (%)")

    for i, style in zip(range(1, 5), ["-", "--", "-.", ":"]):
        ax[1].plot(df["Year"], df[f"Q{i}"], label=f"Q{i}", linestyle=style)
    ax[1].set_title("Slope Coefficients per Quarter")
    ax[1].legend()

    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(png_path)
    with open(pkl_path, "wb") as f:
        pickle.dump(fig, f)


if __name__ == "__main__":
    main()