import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import FIGURES, TOTAL
from src.extended_analysis import HISTORICAL_COLORS, HISTORICAL_SOURCES, MAP_END, MAP_START


def make_extension_figures(coverage, history):
    output = FIGURES / "extended"
    output.mkdir(parents=True, exist_ok=True)
    counts = coverage.loc[coverage.year.between(MAP_START, MAP_END)]
    fig, ax = plt.subplots(figsize=(8, 2.35), layout="constrained")
    ax.plot(counts.year, counts.total_reported, color="#163a5f", label="Total energy supply", linewidth=2)
    ax.plot(counts.year, counts.renewable_reported, color="#087f71", label="Renewable share", linewidth=2)
    ax.set(xlabel="Year", ylabel="ISO-coded locations", xlim=(MAP_START, MAP_END + 0.6), ylim=(0, 235))
    ax.set_xticks([1965, 1980, 1995, 2010, 2024])
    ax.legend(loc="lower right", frameon=False)
    ax.grid(axis="y", alpha=0.23)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "coverage.png", dpi=320, facecolor="white")
    plt.close(fig)

    observed = history.dropna(subset=["component_sum_twh", TOTAL])
    fig, ax = plt.subplots(figsize=(8, 3.1), layout="constrained")
    bottom = observed[TOTAL] * 0
    for (label, column), color in zip(HISTORICAL_SOURCES.items(), HISTORICAL_COLORS):
        ax.bar(observed.index, observed[column], bottom=bottom, width=0.86, label=label, color=color)
        bottom += observed[column]
    ax.scatter(observed.index, observed[TOTAL], color="#172331", label="Published total", s=6, zorder=3)
    ax.set(xlabel="Observed year", ylabel="Energy supply (TWh)")
    ax.ticklabel_format(axis="y", style="plain")
    ax.legend(loc="upper left", ncol=2, fontsize=8, frameon=False)
    ax.grid(axis="y", alpha=0.23)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "historical_supply.png", dpi=320, facecolor="white")
    plt.close(fig)
