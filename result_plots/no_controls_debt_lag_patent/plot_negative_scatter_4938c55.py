import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = "result_plots/no_controls_debt_lag_patent/historical_data_4938c55/final_regression_panel_v3_cityfiltered.csv"
OUT_PATH = "result_plots/no_controls_debt_lag_patent/debt_lag_vs_ln_invention_scatter_4938c55.png"

X_COL = "债务率_滞后一期"
Y_COL = "发明专利申请量_对数"


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    sub = df[[X_COL, Y_COL]].replace([np.inf, -np.inf], np.nan).dropna().copy()

    x = sub[X_COL].to_numpy(dtype=float)
    y = sub[Y_COL].to_numpy(dtype=float)

    # Linear fit on the same usable sample as the bivariate scatter
    slope, intercept = np.polyfit(x, y, 1)
    corr = np.corrcoef(x, y)[0, 1]

    x_line = np.linspace(x.min(), x.max(), 300)
    y_line = slope * x_line + intercept

    # Add quantile-binned means to make the negative pattern easier to see
    sub["bin"] = pd.qcut(sub[X_COL], q=20, duplicates="drop")
    binned = sub.groupby("bin", observed=False).agg(
        x_mean=(X_COL, "mean"),
        y_mean=(Y_COL, "mean"),
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(x, y, s=12, alpha=0.18, color="#3A6EA5", label="City-year observations")
    ax.plot(x_line, y_line, color="#D1495B", linewidth=2.2, label="OLS fit")
    ax.plot(
        binned["x_mean"],
        binned["y_mean"],
        color="#2A9D8F",
        marker="o",
        linewidth=1.8,
        markersize=4,
        label="20-quantile means",
    )

    ax.set_title("Negative Relationship: Debt Ratio (L1) vs ln(Invention Patent Applications)")
    ax.set_xlabel("Debt ratio (lagged one period)")
    ax.set_ylabel("ln(Invention patent applications)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)

    note = (
        f"N = {len(sub):,}\n"
        f"corr = {corr:.4f}\n"
        f"slope = {slope:.4f}"
    )
    ax.text(
        0.98,
        0.03,
        note,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.85},
    )

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=320)
    plt.close(fig)

    print(f"Saved: {OUT_PATH}")
    print(f"N={len(sub)}, corr={corr:.6f}, slope={slope:.6f}")


if __name__ == "__main__":
    main()
