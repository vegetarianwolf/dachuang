from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


# Data source: user-provided table in screenshot (2021-2025)
years = np.array([2021, 2022, 2023, 2024, 2025])
revenue = np.array([11.11, 10.88, 11.72, 11.93, 12.21])
expenditure = np.array([21.13, 22.50, 23.64, 24.39, 24.44])
revenue_growth = np.array([10.9, -2.1, 7.8, 1.7, 2.4])
expenditure_growth = np.array([0.3, 6.4, 5.1, 3.2, 0.2])

# Fiscal gap line uses the same unit as bars: trillion yuan.
fiscal_gap = expenditure - revenue

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax_amount = plt.subplots(figsize=(12, 7), dpi=200)

x = np.arange(len(years))
bar_width = 0.34
revenue_centers = x - bar_width / 2
expenditure_centers = x + bar_width / 2

bars_revenue = ax_amount.bar(
    x - bar_width / 2,
    revenue,
    width=bar_width,
    color="#8FAED1",
    label="地方本级收入（万亿元）",
)
bars_expenditure = ax_amount.bar(
    x + bar_width / 2,
    expenditure,
    width=bar_width,
    color="#E6B58F",
    label="地方本级支出（万亿元）",
)

line_gap = ax_amount.plot(
    x,
    fiscal_gap,
    color="#009E73",
    marker="D",
    markersize=7.5,
    markerfacecolor="white",
    markeredgewidth=2,
    linewidth=2.8,
    zorder=6,
    label="收支缺口（支出-收入，万亿元）",
)

ax_amount.set_xlabel("年份", fontsize=13)
ax_amount.set_ylabel("金额（万亿元）", fontsize=13)
ax_amount.set_xticks(x)
ax_amount.set_xticklabels(years)
ax_amount.set_ylim(8, 26)
ax_amount.grid(False)

ax_growth = ax_amount.twinx()
line_revenue_growth = ax_growth.plot(
    x,
    revenue_growth,
    color="#C62828",
    linestyle="--",
    linewidth=2.9,
    zorder=7,
    label="收入同比增长（%）",
)
line_expenditure_growth = ax_growth.plot(
    x,
    expenditure_growth,
    color="#4A3B8F",
    linestyle="-.",
    linewidth=2.9,
    zorder=7,
    label="支出同比增长（%）",
)
ax_growth.plot(
    x,
    revenue_growth,
    linestyle="None",
    marker="o",
    markersize=7.5,
    markerfacecolor="white",
    markeredgewidth=2,
    color="#C62828",
    zorder=8,
    label="_nolegend_",
)
ax_growth.plot(
    x,
    expenditure_growth,
    linestyle="None",
    marker="s",
    markersize=7.2,
    markerfacecolor="white",
    markeredgewidth=2,
    color="#4A3B8F",
    zorder=8,
    label="_nolegend_",
)
ax_growth.yaxis.set_label_position("right")
ax_growth.set_ylabel("增长率（%）", fontsize=16, labelpad=28, color="#333333")
ax_growth.set_ylim(-12, 20)
ax_growth.grid(False)

ax_amount.set_title("近五年地方一般公共预算收支与增长率（2021-2025）", fontsize=18, pad=14)

for i, bar in enumerate(bars_revenue):
    h = bar.get_height()
    rev_bbox = {"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.4}
    rev_zorder = 9
    if years[i] == 2025:
        rev_bbox = None
        rev_zorder = 40
    text_x = bar.get_x() + bar.get_width() / 2
    text_y = h + 0.15
    ax_amount.text(
        text_x,
        text_y,
        f"{h:.2f}",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#1E1E1E",
        bbox=rev_bbox,
        zorder=rev_zorder,
    )

for i, bar in enumerate(bars_expenditure):
    h = bar.get_height()
    exp_bbox = {"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.4}
    exp_zorder = 9
    if years[i] == 2021:
        exp_bbox = None
        exp_zorder = 40
    ax_amount.text(
        bar.get_x() + bar.get_width() / 2,
        h + 0.15,
        f"{h:.2f}",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#1E1E1E",
        bbox=exp_bbox,
        zorder=exp_zorder,
    )

for i, (xi, gi) in enumerate(zip(x, fiscal_gap)):
    gap_y = gi + 0.07
    gap_va = "bottom"
    if years[i] in (2021, 2023):
        gap_y = gi - 0.12
        gap_va = "top"
    ax_amount.text(
        xi,
        gap_y,
        f"{gi:.2f}",
        color="#007E5D",
        ha="center",
        va=gap_va,
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.25},
        zorder=15,
    )

for xi, rg in zip(x, revenue_growth):
    ax_growth.text(
        xi,
        rg + (0.35 if rg >= 0 else -0.9),
        f"{rg:.1f}%",
        color="#C62828",
        ha="center",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.2},
    )

for i, (xi, eg) in enumerate(zip(x, expenditure_growth)):
    eg_y = eg + 0.35
    eg_va = "bottom"
    if years[i] == 2025:
        eg_y = eg - 0.45
        eg_va = "top"
    ax_growth.text(
        xi,
        eg_y,
        f"{eg:.1f}%",
        color="#4A3B8F",
        ha="center",
        va=eg_va,
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.2},
        zorder=15,
    )

legend_gap = Line2D(
    [0], [0],
    color="#009E73",
    marker="D",
    markersize=7.5,
    markerfacecolor="white",
    markeredgewidth=2,
    linewidth=2.8,
)
legend_rev = Line2D(
    [0], [0],
    color="#C62828",
    linestyle="--",
    marker="o",
    markersize=7.5,
    markerfacecolor="white",
    markeredgewidth=2,
    linewidth=2.9,
)
legend_exp = Line2D(
    [0], [0],
    color="#4A3B8F",
    linestyle="-.",
    marker="s",
    markersize=7.2,
    markerfacecolor="white",
    markeredgewidth=2,
    linewidth=2.9,
)

handles = [bars_revenue, bars_expenditure, legend_gap, legend_rev, legend_exp]
labels = [
    "地方本级收入（万亿元）",
    "地方本级支出（万亿元）",
    "收支缺口（支出-收入，万亿元）",
    "收入同比增长（%）",
    "支出同比增长（%）",
]
ax_amount.legend(
    handles,
    labels,
    loc="upper left",
    bbox_to_anchor=(0.01, 0.99),
    ncol=2,
    frameon=True,
    handlelength=2.6,
)

fig.tight_layout(rect=(0, 0, 0.965, 0.96))

output_path = Path(__file__).resolve().parent / "近五年地方一般公共预算收支_可视化.png"
fig.savefig(output_path, bbox_inches="tight")
plt.close(fig)

print(f"Saved: {output_path}")
