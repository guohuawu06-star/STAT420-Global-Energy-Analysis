import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.config import CATEGORIES, FIGURES, RESULTS, TOTAL

COLORS = ["#163a5f", "#ac501f", "#17766f", "#793e73", "#566b83"]


def make_figures():
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "axes.grid": True, "grid.alpha": 0.22,
                         "axes.axisbelow": True, "figure.dpi": 110})
    panel = pd.read_csv(RESULTS / "analysis_panel.csv")
    w = panel[panel.name.eq("World")].pivot(index="year", columns="indicator_id", values="value")
    countries = panel[panel.name.ne("World")].pivot(index="year", columns=["indicator_id", "name"], values="value")
    m = pd.read_csv(RESULTS / "model_diagnostics.csv")

    def save(fig, name):
        fig.supxlabel("Source: Energy Institute Statistical Review of World Energy (2026) and Our World in Data",
                      fontsize=8, color="#475569")
        fig.savefig(FIGURES / name, dpi=320, bbox_inches="tight", pad_inches=0.14, facecolor="white")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.15), layout="constrained")
    ax.plot(w.index, w[TOTAL], color=COLORS[0], linewidth=2.4)
    ax.set(title="World total energy supply", xlabel="Year", ylabel="Energy supply (TWh)")
    ax.ticklabel_format(axis="y", style="plain")
    save(fig, "01_world_total.png")

    fig, ax = plt.subplots(figsize=(8, 3.55), layout="constrained")
    ids = ["coal", "oil", "gas", "renewables", "nuclear"]
    for name, color in zip(ids, COLORS):
        indicator = f"{name}_energy_share_pct"
        ax.plot(w.index, w[indicator], label=CATEGORIES[indicator], color=color, linewidth=2.1)
    ax.set(title="Selected sources in world energy supply", xlabel="Year", ylabel="Share of total supply (%)")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.19), frameon=False)
    save(fig, "02_world_mix.png")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.45), layout="constrained")
    for name, color in zip(countries[TOTAL].columns, COLORS):
        ax1.plot(countries.index, countries[TOTAL][name], color=color, linewidth=2.0, label=name)
        ax2.plot(countries.index, countries["fossil_fuels_energy_share_pct"][name], color=color, linewidth=2.0, label=name)
    ax1.set(title="Total energy supply", xlabel="Year", ylabel="Energy supply (TWh)")
    ax2.set(title="Fossil fuel share", xlabel="Year", ylabel="Share of total supply (%)")
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc="outside upper center", frameon=False)
    save(fig, "03_countries.png")

    fig = plt.figure(figsize=(8, 5.7), layout="constrained")
    grid = fig.add_gridspec(2, 2)
    ax1 = fig.add_subplot(grid[0, :])
    ax2 = fig.add_subplot(grid[1, 0])
    ax3 = fig.add_subplot(grid[1, 1])
    ax1.plot(m.year, m.observed, "o-", label="Reported share", color=COLORS[0], markersize=3)
    ax1.plot(m.year, m.fitted, "--", label="OLS fit", color=COLORS[1], linewidth=2)
    ax1.legend(frameon=False)
    ax1.set(title="World renewable energy share and linear fit", ylabel="Supply share (%)")
    ax2.axhline(0, color="#586676", linewidth=1)
    ax2.plot(m.year, m.residual, "o-", color=COLORS[2], markersize=3)
    ax2.set(title="Residuals by year", xlabel="Year", ylabel="Residual (pp)")
    ax3.axhline(0, color="#586676", linewidth=1)
    ax3.scatter(m.fitted, m.residual, color=COLORS[2], s=15)
    ax3.set(title="Residuals vs. fitted values", xlabel="Fitted share (%)", ylabel="Residual (pp)")
    save(fig, "04_model_diagnostics.png")


if __name__ == "__main__":
    make_figures()
