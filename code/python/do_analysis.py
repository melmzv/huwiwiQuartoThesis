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
    with open(cfg["summary_statistics_pickle"], "wb") as f:
        pickle.dump(summary, f)
    log.info("Summary statistics saved.")

    # === Plot ===
    log.info("Creating and saving figure ...")
    fig = plot_figure(df)
    fig.savefig(cfg["gapminder_figure_png"])
    log.info("Figure saved as PNG.")


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

    # Round numeric columns to 0 decimal places
    numeric_cols = summary.select_dtypes(include="number").columns
    summary[numeric_cols] = summary[numeric_cols].round(2)

    return summary


def plot_figure(df):
    """Scatter plot: GDP per capita vs. Life Expectancy (bubble size = pop)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    continent_palette = {
        "Asia": "#1E90FF",
        "Europe": "#C71585",
        "Africa": "#32CD32",
        "Americas": "#FF4500",
        "Oceania": "#48D1CC"
    }

    sns.scatterplot(
        data=df,
        x="gdpPercap",
        y="lifeExp",
        size="pop",
        hue="continent",
        palette=continent_palette,
        sizes=(40, 800),
        alpha=0.7,
        ax=ax,
        legend="brief"
    )

    ax.set_xscale("log")
    ax.set_title("World Development in 2007")
    ax.set_xlabel("GDP per Capita [in USD] (log scale)")
    ax.set_ylabel("Life Expectancy [in years]")

    # Move legend outside the plot
    ax.legend(
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        borderaxespad=0.
    )

    plt.tight_layout(pad=2.5)

    return fig


if __name__ == "__main__":
    main()