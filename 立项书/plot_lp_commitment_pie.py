from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


TITLE = "2025 年第三季度中国 VC/PE 市场机构 LP 认缴出资数据"
SOURCE_TEXT = "来源：母基金研究中心、执中 ZERONE"

LABELS = [
    "国资",
    "企业投资者",
    "政府引导基金",
    "机构投资者",
    "GP出资主体",
    "其他",
    "家族办公室",
    "S基金",
    "市场化母基金",
]

VALUES = np.array([46.8, 16.8, 13.0, 9.7, 7.9, 4.9, 0.3, 0.3, 0.3])

COLORS = [
    "#4f78c4",
    "#f28a2b",
    "#f7c000",
    "#7fc241",
    "#39b8b6",
    "#eb4b63",
    "#4d5f87",
    "#8d5a3b",
    "#aa8a18",
]

OUTPUT_PATH = Path(__file__).resolve().parent / "2025年第三季度中国VCPE市场机构LP认缴出资数据.png"
PIE_CENTER = (0.0, -0.08)
PIE_RADIUS = 1.0


def annotate_wedges(ax, wedges, values):
    center_x, center_y = PIE_CENTER
    for index, (wedge, value) in enumerate(zip(wedges, values)):
        angle = (wedge.theta1 + wedge.theta2) / 2
        angle_rad = np.deg2rad(angle)

        x = np.cos(angle_rad)
        y = np.sin(angle_rad)

        label_radius = 1.18
        if value <= 0.5:
            label_radius = 1.28

        text_x = label_radius * x
        text_y = label_radius * y

        if index == 6:
            text_x = -0.24
            text_y = 1.12
        elif index == 7:
            text_x = 0.00
            text_y = 1.24
        elif index == 8:
            text_x = 0.22
            text_y = 1.10
        elif index == 5:
            text_x = -0.26
            text_y = 1.06

        ha = "left" if text_x >= 0 else "right"
        ax.annotate(
            f"{value:.1f}%",
            xy=(center_x + PIE_RADIUS * x, center_y + PIE_RADIUS * y),
            xytext=(text_x, text_y),
            ha=ha,
            va="center",
            fontsize=11,
            color="#444444",
            arrowprops={
                "arrowstyle": "-",
                "color": "#9a9a9a",
                "lw": 1.0,
                "shrinkA": 0,
                "shrinkB": 0,
                "connectionstyle": "arc3,rad=0",
            },
        )


def generate_chart(output_path: Path | str = OUTPUT_PATH) -> Path:
    output_path = Path(output_path)

    plt.style.use("seaborn-v0_8-white")
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(12, 7.6), dpi=200)

    wedges, _ = ax.pie(
        VALUES,
        colors=COLORS,
        startangle=90,
        counterclock=False,
        radius=PIE_RADIUS,
        center=PIE_CENTER,
        wedgeprops={"linewidth": 0.6, "edgecolor": "white"},
    )

    annotate_wedges(ax, wedges, VALUES)

    ax.legend(
        wedges,
        LABELS,
        loc="center left",
        bbox_to_anchor=(1.02, 0.52),
        frameon=False,
        fontsize=11,
        handlelength=0.9,
        handletextpad=0.55,
        labelspacing=0.7,
    )

    ax.set_title(TITLE, fontsize=17, y=1.08, pad=0)
    ax.set_aspect("equal")

    fig.text(0.055, 0.055, SOURCE_TEXT, fontsize=11, color="#555555")
    fig.subplots_adjust(left=0.04, right=0.80, top=0.94, bottom=0.10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    saved_path = generate_chart()
    print(f"Saved: {saved_path}")