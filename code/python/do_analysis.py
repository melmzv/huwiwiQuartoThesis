import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from utils import read_config, setup_logging

log = setup_logging()


def main():
    cfg = read_config("config/do_analysis_cfg.yaml")

    # === Load prepared data ===
    log.info("Loading prepared Gapminder 2007 data ...")
    df = pd.read_parquet(cfg["gapminder_2007_input"])

    # === Summary statistics ===
    log.info("Computing summary statistics by continent ...")
    summary = compute_summary(df)
    summary.to_csv(cfg["summary_statistics_csv"], index=False)
    log.info("Summary statistics saved.")

    # === Plot ===
    log.info("Creating and saving figure ...")
    fig = plot_figure(df)
    fig.savefig(cfg["figure1_save_path"])
    with open(cfg["figure1_pickle_path"], "wb") as f:
        pickle.dump(fig, f)
    log.info("Figure saved as PNG and pickle.")


def compute_summary(df):
    """
    Compute mean/median for lifeExp & gdpPercap, total pop and count of countries by continent.
    """
    summary = (
        df.groupby("continent")
        .agg(
            Mean_LifeExp=("lifeExp", "mean"),
            Median_LifeExp=("lifeExp", "median"),
            Mean_GDPpc=("gdpPercap", "mean"),
            Median_GDPpc=("gdpPercap", "median"),
            Total_Pop=("pop", "sum"),
            Num_Countries=("country", "count")
        )
        .reset_index()
    )
    return summary


def plot_figure(df):
    """Scatter plot: GDP per capita vs. Life Expectancy (bubble size = pop)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=df,
        x="gdpPercap",
        y="lifeExp",
        size="pop",
        hue="continent",
        sizes=(40, 800),
        alpha=0.7,
        ax=ax,
        legend="full"
    )
    ax.set_xscale("log")
    ax.set_title("Gapminder 2007: Life Expectancy vs. GDP per Capita")
    ax.set_xlabel("GDP per Capita (log scale)")
    ax.set_ylabel("Life Expectancy")
    return fig


if __name__ == "__main__":
    main()