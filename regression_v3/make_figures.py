# -*- coding: utf-8 -*-
"""
make_figures.py — Publication-quality figures for fiscal pressure & innovation paper.

Figures produced:
  fig_h1_coef_plot.png      — H1 baseline coefficient plot (2-panel)
  fig_mechanism_coef.png    — H2/H5 mechanism coefficient plots (2×2)
  fig_scatter_fiscal_patent.png — Binscatter: fiscal_gap_L1 vs ln_invg
  fig_fund_trend.png        — Government guidance fund investment trend 2010-2023
"""

import csv
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────
BASE   = Path(__file__).resolve().parents[1]
OUTDIR = Path(__file__).resolve().parent
PANEL  = OUTDIR / "panel_v3.csv"
FUND   = BASE / "政府引导基金整合数据" / "城市_投资统计_分年份_2000-2024.csv"

# ── Global style ───────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":      "serif",
    "font.serif":       ["Times New Roman", "DejaVu Serif", "serif"],
    "font.size":        11,
    "axes.titlesize":   12,
    "axes.labelsize":   11,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
    "legend.fontsize":  10,
    "figure.dpi":       150,
    "savefig.dpi":      300,
    "savefig.bbox":     "tight",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.linestyle":   "--",
    "grid.linewidth":   0.4,
    "grid.alpha":       0.5,
    "grid.color":       "#cccccc",
})

# Chinese font fallback — try to find a system CJK font
import matplotlib.font_manager as fm
_cjk_candidates = [
    "Microsoft YaHei", "SimSun", "SimHei", "Noto Sans CJK SC",
    "Source Han Sans CN", "WenQuanYi Micro Hei",
]
_available = {f.name for f in fm.fontManager.ttflist}
_cjk_font  = next((f for f in _cjk_candidates if f in _available), None)

def _set_chinese(ax_or_fig=None):
    """Apply CJK font to a specific axis or figure if available."""
    if _cjk_font is None:
        return
    prop = fm.FontProperties(family=_cjk_font, size=11)
    return prop   # caller applies it manually

CJK = fm.FontProperties(family=_cjk_font, size=11) if _cjk_font else None
CJK_title = fm.FontProperties(family=_cjk_font, size=12) if _cjk_font else None

def _maybe(text, fp=None):
    """Return (text, fontproperties) kwargs dict if CJK font available."""
    if fp and _cjk_font:
        return {"fontproperties": fp}
    return {}


# ═══════════════════════════════════════════════════════════════════════════
# Figure 1 — H1 baseline coefficient plot
# ═══════════════════════════════════════════════════════════════════════════
def fig1_h1_coef():
    # ── Data from Stata log ──
    fg_specs  = ["(1) No ctrl", "(2) Core", "(3) +Pop"]
    fg_coefs  = [-0.266, 0.356, 0.418]
    fg_ses    = [ 0.2427, 0.2105, 0.2111]
    fg_pvals  = [ 0.273,  0.092,  0.049]
    fg_ns     = [4111, 3894, 3519]

    dr_specs  = ["(4) No ctrl", "(5) Core", "(6) +Pop"]
    dr_coefs  = [0.053, 0.049, 0.058]
    dr_ses    = [0.0323, 0.0331, 0.0409]
    dr_pvals  = [0.100,  0.138,  0.154]
    dr_ns     = [1444, 1383, 1211]

    def stars(p):
        return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))

    for ax, specs, coefs, ses, pvals, ns, xvar, title_txt in [
        (axes[0], fg_specs, fg_coefs, fg_ses, fg_pvals, fg_ns,
         "fiscal_gap_L1",
         "Panel A: Fiscal Gap Rate → ln(1+Invention Grants)"),
        (axes[1], dr_specs, dr_coefs, dr_ses, dr_pvals, dr_ns,
         "ln_debt_ratio_L1",
         "Panel B: ln(Debt Ratio) → ln(1+Invention Grants)"),
    ]:
        y    = np.arange(len(specs))
        ci95 = [1.96 * s for s in ses]

        # Dots + horizontal CI bars
        ax.errorbar(coefs, y,
                    xerr=ci95,
                    fmt="o",
                    color="black",
                    markersize=7,
                    capsize=4,
                    linewidth=1.2,
                    elinewidth=1.2,
                    ecolor="black",
                    zorder=3)

        # Zero reference line
        ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)

        # Stars + N annotation
        x_max = max(c + e for c, e in zip(coefs, ci95))
        x_min = min(c - e for c, e in zip(coefs, ci95))
        pad   = (x_max - x_min) * 0.06

        for i, (c, p, n) in enumerate(zip(coefs, pvals, ns)):
            s = stars(p)
            label = f"{s}  N={n:,}"
            ax.text(x_max + pad, i, label,
                    va="center", ha="left", fontsize=9, color="#333333")

        ax.set_yticks(y)
        ax.set_yticklabels(specs, fontsize=10)
        ax.set_xlabel("Coefficient", fontsize=11)
        ax.set_title(title_txt, fontsize=11, pad=8)
        ax.invert_yaxis()

        # Extend xlim for annotations
        extra = (x_max - x_min) * 0.55
        ax.set_xlim(x_min - pad * 2, x_max + extra)

    fig.suptitle(
        "Table 2: Effect of Fiscal Pressure on Innovation Performance\n"
        "(Two-Way FE, City-Clustered SE, 2010–2023)",
        fontsize=11, y=1.01
    )
    fig.tight_layout()
    out = OUTDIR / "fig_h1_coef_plot.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════
# Figure 2 — Mechanism coefficient plots (2×2)
# ═══════════════════════════════════════════════════════════════════════════
def fig2_mechanism():
    # Each cell: (title, [(label, coef, se, pval), ...])
    cells = [
        # Top-left: H2 Two-step X → early_deal_ratio
        ("H2 Two-step: X → Early-Stage Investment Ratio\n(Dependent: early_deal_ratio_L1)",
         [("FG (fiscal_gap_L1)", -0.455, 0.349, 0.194),
          ("DR (ln_debt_ratio)", -0.014, 0.063, 0.824)]),
        # Top-right: H5 Two-step X → invest_amt
        ("H5 Two-step: X → Fund Investment Amount\n(Dependent: ln_invest_amt_L1)",
         [("FG (fiscal_gap_L1)",  2.359, 0.703, 0.001),
          ("DR (ln_debt_ratio)", -0.144, 0.104, 0.164)]),
        # Bottom-left: H2 Interaction FG_x_early / DR_x_early → ln_invg
        ("H2 Interaction: X×Early → ln_invg\n(Dependent: ln_invg)",
         [("FG×early_deal", -0.083, 0.172, 0.630),
          ("DR×early_deal", -0.090, 0.067, 0.180)]),
        # Bottom-right: H5 Interaction FG_x_amt / DR_x_amt → ln_invg
        ("H5 Interaction: X×Amount → ln_invg\n(Dependent: ln_invg)",
         [("FG×invest_amt",  0.070, 0.030, 0.022),
          ("DR×invest_amt", -0.018, 0.008, 0.026)]),
    ]

    def stars(p):
        return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""

    colors  = ["#111111", "#888888"]
    markers = ["o", "s"]

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))

    for idx, (title, items) in enumerate(cells):
        ax  = axes[idx // 2][idx % 2]
        ys  = np.arange(len(items))

        for j, (lbl, c, se, p) in enumerate(items):
            ci = 1.96 * se
            ax.errorbar([c], [j],
                        xerr=[[ci], [ci]],
                        fmt=markers[j],
                        color=colors[j],
                        markersize=8,
                        capsize=4,
                        linewidth=1.2,
                        elinewidth=1.2,
                        ecolor=colors[j],
                        label=lbl,
                        zorder=3)
            # Annotate
            s = stars(p)
            ax.text(c + ci * 0.15 + abs(ci) * 0.05,
                    j,
                    f" {s}",
                    va="center", ha="left",
                    fontsize=10, color=colors[j],
                    fontweight="bold")

        ax.axvline(0, color="black", linewidth=0.7, linestyle="--", alpha=0.6)
        ax.set_yticks(ys)
        ax.set_yticklabels([it[0] for it in items], fontsize=9.5)
        ax.set_xlabel("Coefficient", fontsize=10)
        ax.set_title(title, fontsize=9.5, pad=6)
        ax.invert_yaxis()

        # Pad xlim
        all_coefs = [it[1] for it in items]
        all_ci    = [1.96 * it[2] for it in items]
        xlo = min(c - e for c, e in zip(all_coefs, all_ci))
        xhi = max(c + e for c, e in zip(all_coefs, all_ci))
        span = max(xhi - xlo, 0.1)
        ax.set_xlim(xlo - span * 0.3, xhi + span * 0.5)

    fig.suptitle(
        "Table 3–4: Mechanism Tests — H2 (Risk Preference) & H5 (Investment Scale)\n"
        "Two-Way FE, City-Clustered SE",
        fontsize=11
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = OUTDIR / "fig_mechanism_coef.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════
# Figure 3 — Binscatter: fiscal_gap_L1 vs ln_invg (FE-partialled out)
# ═══════════════════════════════════════════════════════════════════════════
def fig3_binscatter():
    df = pd.read_csv(PANEL, encoding="utf-8-sig")
    df["fiscal_gap_L1"] = pd.to_numeric(df["fiscal_gap_L1"], errors="coerce")
    df["ln_invg"]       = pd.to_numeric(df["ln_invg"],       errors="coerce")
    df = df[["city", "year", "fiscal_gap_L1", "ln_invg"]].dropna()

    # ── Partial out city & year FE (within-transformation) ──
    df["x_dm"] = df["fiscal_gap_L1"] - df.groupby("city")["fiscal_gap_L1"].transform("mean")
    df["x_dm"] = df["x_dm"] - df.groupby("year")["x_dm"].transform("mean")
    df["y_dm"] = df["ln_invg"] - df.groupby("city")["ln_invg"].transform("mean")
    df["y_dm"] = df["y_dm"] - df.groupby("year")["y_dm"].transform("mean")

    df = df.dropna(subset=["x_dm", "y_dm"])

    # ── Binscatter: 20 equal-frequency bins ──
    n_bins = 20
    df["bin"] = pd.qcut(df["x_dm"], q=n_bins, labels=False, duplicates="drop")
    binned = df.groupby("bin")[["x_dm", "y_dm"]].mean().reset_index()

    # ── Regression line (from spec (2): 0.356) ──
    x_line = np.linspace(df["x_dm"].quantile(0.01), df["x_dm"].quantile(0.99), 200)
    slope  = 0.356          # from Stata H1-(2)
    intercept = binned["y_dm"].mean() - slope * binned["x_dm"].mean()
    y_line = slope * x_line + intercept

    # ── OLS on demeaned data for reference ──
    from numpy.polynomial import polynomial as P
    coeffs = np.polyfit(df["x_dm"], df["y_dm"], 1)
    y_ols  = np.polyval(coeffs, x_line)

    fig, ax = plt.subplots(figsize=(7, 4.8))

    ax.scatter(binned["x_dm"], binned["y_dm"],
               s=55, color="black", zorder=3, label="Bin means (N=20 bins)")
    ax.plot(x_line, y_ols, color="black", linewidth=1.5,
            label=f"OLS fit (β={coeffs[0]:.3f})")
    ax.plot(x_line, y_line, color="#666666", linewidth=1.2,
            linestyle="--", label="Stata FE coef (β=0.356*)")

    ax.axhline(0, color="#aaaaaa", linewidth=0.6, linestyle=":")
    ax.axvline(0, color="#aaaaaa", linewidth=0.6, linestyle=":")

    ax.set_xlabel("Fiscal Gap Rate L1 (de-meaned)", fontsize=11)
    ax.set_ylabel("ln(1+Invention Grants) (de-meaned)", fontsize=11)

    # Chinese title with fallback
    title_cn = "财政缺口率与创新绩效的相关关系"
    title_en = "Binscatter: Fiscal Gap Rate vs. Innovation Performance"
    if CJK_title:
        ax.set_title(title_en + "\n" + title_cn,
                     fontsize=11,
                     **_maybe(title_cn, CJK_title))
    else:
        ax.set_title(title_en, fontsize=11)

    ax.legend(fontsize=9.5, framealpha=0.7)
    note = ("Note: City and year FE partialled out. "
            "Bins are 20 equal-frequency groups of fiscal_gap_L1.")
    ax.annotate(note, xy=(0.01, 0.01), xycoords="axes fraction",
                fontsize=8, color="#555555",
                va="bottom", style="italic")

    fig.tight_layout()
    out = OUTDIR / "fig_scatter_fiscal_patent.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════
# Figure 4 — Government guidance fund investment trend 2010-2023
# ═══════════════════════════════════════════════════════════════════════════
def fig4_fund_trend():
    # Load raw investment data
    df = pd.read_csv(FUND, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    # Coerce numeric
    for col in ["年份", "总投资额_百万元", "总投资次数"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["年份"])
    df["年份"] = df["年份"].astype(int)
    df = df[(df["年份"] >= 2010) & (df["年份"] <= 2023)]

    # Aggregate
    annual = df.groupby("年份").agg(
        total_amt =("总投资额_百万元", "sum"),
        total_cnt =("总投资次数",    "sum"),
        n_cities  =("城市",         "nunique"),
    ).reset_index()

    annual["total_amt_bn"] = annual["total_amt"] / 1000   # convert to billion CNY

    years  = annual["年份"].values
    amt    = annual["total_amt_bn"].values
    cities = annual["n_cities"].values

    fig, ax1 = plt.subplots(figsize=(8.5, 4.5))

    color_amt  = "#111111"
    color_city = "#666666"

    lns1 = ax1.bar(years, amt,
                   color=color_amt, alpha=0.75,
                   width=0.6, label="Investment Amount (bn CNY)",
                   zorder=2)
    ax1.set_xlabel("Year", fontsize=11)
    ax1.set_ylabel("Total Investment Amount (billion CNY)", fontsize=11,
                   color=color_amt)
    ax1.tick_params(axis="y", labelcolor=color_amt)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:.0f}"))

    ax2 = ax1.twinx()
    lns2 = ax2.plot(years, cities,
                    color=color_city, linewidth=2, marker="o",
                    markersize=5, label="Active Cities (count)",
                    zorder=3)
    ax2.set_ylabel("Number of Active Cities", fontsize=11,
                   color=color_city)
    ax2.tick_params(axis="y", labelcolor=color_city)
    ax2.set_ylim(0, max(cities) * 1.35)

    # Combined legend
    handles  = [lns1, lns2[0]]
    labels_l = ["Investment Amount (bn CNY)", "Active Cities (count)"]
    ax1.legend(handles, labels_l, loc="upper left", fontsize=9.5,
               framealpha=0.8)

    # Title
    title_en = "Government Guidance Fund Investment Trend (2010–2023)"
    title_cn = "政府引导基金投资规模趋势 (2010–2023)"
    if CJK_title:
        ax1.set_title(title_en + "\n" + title_cn, fontsize=11)
    else:
        ax1.set_title(title_en, fontsize=11)

    ax1.set_xticks(years)
    ax1.set_xticklabels(years, rotation=45, ha="right")
    ax1.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax1.set_axisbelow(True)
    ax2.grid(False)

    # Annotate peak
    peak_year = years[np.argmax(amt)]
    peak_val  = amt.max()
    ax1.annotate(
        f"Peak: {peak_year}\n{peak_val:.0f} bn",
        xy=(peak_year, peak_val),
        xytext=(peak_year - 1.8, peak_val * 0.88),
        fontsize=8.5,
        arrowprops=dict(arrowstyle="->", color="#333333", lw=0.9),
        color="#333333",
    )

    fig.tight_layout()
    out = OUTDIR / "fig_fund_trend.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== Generating figures ===")
    print(f"Output dir: {OUTDIR}\n")

    print("[1/4] H1 coefficient plot...")
    fig1_h1_coef()

    print("[2/4] Mechanism coefficient plot...")
    fig2_mechanism()

    print("[3/4] Binscatter (fiscal gap vs patents)...")
    fig3_binscatter()

    print("[4/4] Fund investment trend...")
    fig4_fund_trend()

    print("\n=== All figures saved ===")
