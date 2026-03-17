# -*- coding: utf-8 -*-
"""
Generate publication-quality figures for regression_v3.
Figures:
  1. fig_h1_coef_plot.png   — H1 baseline coefficient plot (6 specs)
  2. fig_mechanism_coef.png — H2/H5 mechanism coefficient plot
  3. fig_scatter_fiscal_patent.png — binscatter fiscal_gap vs ln_invg
  4. fig_fund_trend.png     — government fund investment trend
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent

# --- Style setup ---
rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "SimSun"],
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# ============================================================================
# Figure 1: H1 Baseline Coefficient Plot
# ============================================================================
def fig_h1_coef_plot():
    """Plot coefficients from the 6-column H1 baseline regressions (Stata results)."""

    # From Stata output
    fg_specs = [
        ("(1) No ctrl",    -0.266, 0.243),
        ("(2) Core ctrl",   0.356, 0.211),
        ("(3) Full ctrl",   0.418, 0.211),
    ]
    dr_specs = [
        ("(4) No ctrl",    0.053, 0.032),
        ("(5) Core ctrl",  0.049, 0.033),
        ("(6) Full ctrl",  0.058, 0.041),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), sharey=False)

    # Panel A: fiscal_gap_L1
    labels_fg = [s[0] for s in fg_specs]
    coefs_fg = [s[1] for s in fg_specs]
    ses_fg = [s[2] for s in fg_specs]
    y_pos = np.arange(len(fg_specs))

    ax1.barh(y_pos, coefs_fg, height=0.5, color=["#4472C4", "#4472C4", "#4472C4"],
             alpha=0.7, edgecolor="black", linewidth=0.5)
    ax1.errorbar(coefs_fg, y_pos, xerr=[1.96*s for s in ses_fg],
                 fmt="none", ecolor="black", capsize=4, linewidth=1.2)
    ax1.axvline(x=0, color="grey", linestyle="--", linewidth=0.8)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels_fg)
    ax1.set_xlabel("Coefficient on fiscal_gap_L1")
    ax1.set_title("Panel A: Fiscal Gap Rate")

    # Panel B: ln_debt_ratio_L1
    labels_dr = [s[0] for s in dr_specs]
    coefs_dr = [s[1] for s in dr_specs]
    ses_dr = [s[2] for s in dr_specs]
    y_pos2 = np.arange(len(dr_specs))

    ax2.barh(y_pos2, coefs_dr, height=0.5, color=["#ED7D31", "#ED7D31", "#ED7D31"],
             alpha=0.7, edgecolor="black", linewidth=0.5)
    ax2.errorbar(coefs_dr, y_pos2, xerr=[1.96*s for s in ses_dr],
                 fmt="none", ecolor="black", capsize=4, linewidth=1.2)
    ax2.axvline(x=0, color="grey", linestyle="--", linewidth=0.8)
    ax2.set_yticks(y_pos2)
    ax2.set_yticklabels(labels_dr)
    ax2.set_xlabel("Coefficient on ln_debt_ratio_L1")
    ax2.set_title("Panel B: Debt Ratio")

    fig.suptitle("Figure 1: H1 Baseline — Fiscal Pressure and Innovation", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(OUTDIR / "fig_h1_coef_plot.png")
    plt.close(fig)
    print(f"Saved: {OUTDIR / 'fig_h1_coef_plot.png'}")


# ============================================================================
# Figure 2: Mechanism Coefficient Plot (H2 + H5)
# ============================================================================
def fig_mechanism_coef():
    """Plot key mechanism coefficients."""

    # H2 Two-step: fiscal_gap -> early_deal_ratio
    # H5 Two-step: fiscal_gap -> ln_invest_amt
    # H5 Interaction: FG_x_amt
    specs = [
        ("H2: FG→Early\n(two-step)", -0.455, 0.349, "#4472C4"),
        ("H5: FG→InvAmt\n(two-step)",  2.359, 0.703, "#4472C4"),
        ("H5: FG×Amt→Y\n(interaction)", 0.070, 0.030, "#ED7D31"),
        ("H5: DR×Amt→Y\n(interaction)", -0.018, 0.008, "#ED7D31"),
    ]

    fig, ax = plt.subplots(figsize=(8, 4))
    y_pos = np.arange(len(specs))
    labels = [s[0] for s in specs]
    coefs = [s[1] for s in specs]
    ses = [s[2] for s in specs]
    colors = [s[3] for s in specs]

    ax.barh(y_pos, coefs, height=0.55, color=colors, alpha=0.7,
            edgecolor="black", linewidth=0.5)
    ax.errorbar(coefs, y_pos, xerr=[1.96*s for s in ses],
                fmt="none", ecolor="black", capsize=4, linewidth=1.2)
    ax.axvline(x=0, color="grey", linestyle="--", linewidth=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Coefficient")
    ax.set_title("Figure 2: Mechanism Test Coefficients (H2 & H5)")

    # Add significance markers
    for i, (_, c, se, _) in enumerate(specs):
        pval_approx = 2 * (1 - 0.5 * (1 + np.sign(abs(c/se) - 1.96)))  # rough
        t = abs(c / se)
        if t > 2.576:
            star = "***"
        elif t > 1.96:
            star = "**"
        elif t > 1.645:
            star = "*"
        else:
            star = ""
        if star:
            x_offset = c + 1.96*se + 0.02*max(abs(cc) for cc in coefs) if c > 0 else c - 1.96*se - 0.02*max(abs(cc) for cc in coefs)
            ax.text(x_offset, i, star, ha="center", va="center", fontsize=12, fontweight="bold")

    fig.tight_layout()
    fig.savefig(OUTDIR / "fig_mechanism_coef.png")
    plt.close(fig)
    print(f"Saved: {OUTDIR / 'fig_mechanism_coef.png'}")


# ============================================================================
# Figure 3: Binscatter — Fiscal Gap vs Innovation
# ============================================================================
def fig_scatter_fiscal_patent():
    """Create binscatter-style plot of residualized fiscal_gap vs ln_invg."""
    df = pd.read_csv(OUTDIR / "panel_v3.csv", encoding="utf-8-sig")
    for c in ["ln_invg", "fiscal_gap_L1", "ln_pgdp", "sec_ratio", "sci_ratio"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    sub = df[["ln_invg", "fiscal_gap_L1"]].dropna()

    if len(sub) < 50:
        print("Not enough data for scatter plot")
        return

    # Create 20 equal-sized bins
    n_bins = 20
    sub = sub.sort_values("fiscal_gap_L1")
    sub["bin"] = pd.qcut(sub["fiscal_gap_L1"], n_bins, labels=False, duplicates="drop")
    binned = sub.groupby("bin").agg(
        fg_mean=("fiscal_gap_L1", "mean"),
        invg_mean=("ln_invg", "mean"),
        invg_se=("ln_invg", "sem"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(binned["fg_mean"], binned["invg_mean"], s=60, color="#4472C4",
               edgecolor="white", linewidth=0.5, zorder=3)

    # Fit line
    z = np.polyfit(binned["fg_mean"], binned["invg_mean"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(binned["fg_mean"].min(), binned["fg_mean"].max(), 100)
    ax.plot(x_line, p(x_line), color="#ED7D31", linewidth=2, linestyle="-",
            label=f"Slope = {z[0]:.3f}")

    ax.set_xlabel("Fiscal Gap Rate (L1)")
    ax.set_ylabel("ln(1 + Invention Grants)")
    ax.set_title("Figure 3: Fiscal Gap and Innovation (Binscatter)")
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTDIR / "fig_scatter_fiscal_patent.png")
    plt.close(fig)
    print(f"Saved: {OUTDIR / 'fig_scatter_fiscal_patent.png'}")


# ============================================================================
# Figure 4: Government Fund Investment Trend
# ============================================================================
def fig_fund_trend():
    """Plot aggregate fund investment trend over time."""
    df = pd.read_csv(OUTDIR / "panel_v3.csv", encoding="utf-8-sig")
    for c in ["ln_invest_amt_L1", "ln_invest_cnt_L1"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["year"] = df["year"].astype(int)

    # Use the raw investment stats file for actual amounts
    raw_path = Path(__file__).resolve().parents[1] / "政府引导基金整合数据" / "城市_投资统计_分年份_2000-2024.csv"
    raw = pd.read_csv(raw_path, encoding="utf-8-sig")
    for c in ["总投资次数", "总投资额_百万元"]:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    raw["年份"] = pd.to_numeric(raw["年份"], errors="coerce").astype(int)

    trend = raw.groupby("年份").agg(
        total_cnt=("总投资次数", "sum"),
        total_amt=("总投资额_百万元", "sum"),
        n_cities=("城市", "nunique"),
    ).reset_index()
    trend = trend[(trend["年份"] >= 2005) & (trend["年份"] <= 2024)]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color_bar = "#4472C4"
    color_line = "#ED7D31"

    bars = ax1.bar(trend["年份"], trend["total_cnt"], color=color_bar, alpha=0.6,
                   width=0.7, label="Investment Deals (left)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Number of Deals", color=color_bar)
    ax1.tick_params(axis="y", labelcolor=color_bar)

    ax2 = ax1.twinx()
    ax2.plot(trend["年份"], trend["total_amt"] / 1000, color=color_line, marker="o",
             linewidth=2, markersize=5, label="Investment Amount (right, bn RMB)")
    ax2.set_ylabel("Investment Amount (billion RMB)", color=color_line)
    ax2.tick_params(axis="y", labelcolor=color_line)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False)

    ax1.set_title("Figure 4: Government Guidance Fund Investment Trend (2005–2024)")
    ax1.set_xticks(trend["年份"])
    ax1.set_xticklabels(trend["年份"].astype(str), rotation=45, ha="right")

    fig.tight_layout()
    fig.savefig(OUTDIR / "fig_fund_trend.png")
    plt.close(fig)
    print(f"Saved: {OUTDIR / 'fig_fund_trend.png'}")


if __name__ == "__main__":
    fig_h1_coef_plot()
    fig_mechanism_coef()
    fig_scatter_fiscal_patent()
    fig_fund_trend()
    print("\nAll figures saved to:", OUTDIR)
