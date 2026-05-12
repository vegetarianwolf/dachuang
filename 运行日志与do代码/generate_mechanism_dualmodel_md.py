from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
RESULT_CSV = SCRIPT_DIR / "xtreg_mechanism_dualmodel_focus_ascii_results.csv"
RESULT_DIR = Path.cwd()


def fnum(value: str) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return f"{float(text):.10g}"
    except ValueError:
        return text


def is_sig(value: str, cutoff: float = 0.1) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        return float(text) < cutoff
    except ValueError:
        return False


def sig_star(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    p = float(text)
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def add_line(buf: list[str], text: str = "") -> None:
    buf.append(text)


def add_table(buf: list[str], rows: list[dict], headers: list[str], props: list[str]) -> None:
    add_line(buf, "| " + " | ".join(headers) + " |")
    add_line(buf, "| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        vals = [str(row.get(prop, "")).replace("\n", " ").replace("\r", " ") for prop in props]
        add_line(buf, "| " + " | ".join(vals) + " |")
    add_line(buf)


def load_rows() -> list[dict]:
    with RESULT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_summary(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_family"], row["mvar"])].append(row)

    items = []
    for (model_family, mvar), group in grouped.items():
        items.append(
            {
                "model_family": model_family,
                "mvar": mvar,
                "m_eq_sig": sum(
                    1
                    for r in group
                    if r["step"] == "M_eq"
                    and (is_sig(r["p1"]) or is_sig(r["p2"]) or is_sig(r["p3"]))
                ),
                "y_term1_sig": sum(1 for r in group if r["step"] == "Y_eq" and is_sig(r["p1"])),
                "y_term2_sig": sum(1 for r in group if r["step"] == "Y_eq" and is_sig(r["p2"])),
                "y_term3_sig": sum(1 for r in group if r["step"] == "Y_eq" and is_sig(r["p3"])),
                "total_rows": len(group),
            }
        )

    return sorted(
        items,
        key=lambda x: (
            x["model_family"],
            -x["m_eq_sig"],
            -x["y_term3_sig"],
            -x["y_term2_sig"],
            -x["y_term1_sig"],
            x["mvar"],
        ),
    )


def build_table_rows(rows: list[dict], model_family: str, step: str) -> list[dict]:
    subset = [
        row
        for row in rows
        if row["model_family"] == model_family and row["step"] == step
    ]
    subset.sort(key=lambda r: (r["mvar"], r["dvar"], r["spec"], r["yvar"]))

    out = []
    for r in subset:
        out.append(
            {
                "spec": r["spec"],
                "yvar": r["yvar"],
                "dvar": r["dvar"],
                "mvar": r["mvar"],
                "term1": r["term1"],
                "coef1": fnum(r["b1"]),
                "se1": fnum(r["se1"]),
                "p1": fnum(r["p1"]),
                "sig1": sig_star(r["p1"]),
                "term2": r["term2"],
                "coef2": fnum(r["b2"]),
                "se2": fnum(r["se2"]),
                "p2": fnum(r["p2"]),
                "sig2": sig_star(r["p2"]),
                "term3": r["term3"],
                "coef3": fnum(r["b3"]),
                "se3": fnum(r["se3"]),
                "p3": fnum(r["p3"]),
                "sig3": sig_star(r["p3"]),
                "N": fnum(r["N"]),
                "r2w": fnum(r["r2w"]),
            }
        )
    return out


def write_overview(all_rows: list[dict], category_map: dict[str, str]) -> None:
    buf: list[str] = []
    add_line(buf, "# 机制检验总览：早期投资、社会资本撬动效率与融资约束")
    add_line(buf)
    add_line(buf, "## 本次操作")
    add_line(buf, "- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`")
    add_line(buf, "- 基准主线：`fund_est_scale_cum × debt_pressure` 与 `fund_est_scale_cum × debt_pressure_l1`")
    add_line(buf, "- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`")
    add_line(buf, "- 机制模型 A：`X × N -> M -> Y`")
    add_line(buf, "- 机制模型 B：先检验 `N -> M`，再在结果方程中加入 `X × M`")
    add_line(buf, f"- 结果总行数：`{len(all_rows)}`")
    add_line(buf)
    add_line(buf, "## 各类别显著性概览")

    overview_rows: list[dict] = []
    for key, title in category_map.items():
        summary = build_summary([r for r in all_rows if r["category"] == key])
        for item in summary:
            overview_rows.append(
                {
                    "category": title,
                    "model": item["model_family"],
                    "mvar": item["mvar"],
                    "M_eq_sig": item["m_eq_sig"],
                    "Y_term1_sig": item["y_term1_sig"],
                    "Y_term2_sig": item["y_term2_sig"],
                    "Y_term3_sig": item["y_term3_sig"],
                    "total_rows": item["total_rows"],
                }
            )

    add_table(
        buf,
        overview_rows,
        ["category", "model", "mvar", "M_eq_sig", "Y_term1_sig", "Y_term2_sig", "Y_term3_sig", "total_rows"],
        ["category", "model", "mvar", "M_eq_sig", "Y_term1_sig", "Y_term2_sig", "Y_term3_sig", "total_rows"],
    )

    add_line(buf, "## 结论摘要")
    add_line(buf, "- 早期投资类中，`early_inv_amt`、`early_inv_amt_share` 在机制方程里更容易出现显著，`early_inv_count` 在结果方程里显著最多。")
    add_line(buf, "- 社会资本类中，`gov_amt`、`matched_commit_amt`、`fund_commit_total`、`gp_amt` 的信号相对更多，`soccap_leverage` 本身并不是最强口径。")
    add_line(buf, "- 融资约束类中，`fcity_fc_mean` 在机制方程里最稳定；若把机制变量视为调节变量，则 `fcity_fc_mean` 与 `fcity_sa_mean` 的 `X × M` 项显著最多。")
    add_line(buf, "- 大多数结果方程里，原始债务调节项 `fund_est_scale_cum × debt_pressure` 仍保持负向显著，说明债务压力削弱基金扶持创新效果这一主结论较稳。")
    add_line(buf)
    add_line(buf, "## 输出文件")
    add_line(buf, "- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`")
    add_line(buf, "- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`")
    add_line(buf, "- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`")

    (RESULT_DIR / "xtreg_mechanism_dualmodel_focus_overview.md").write_text(
        "\n".join(buf), encoding="utf-8"
    )


def write_category_docs(all_rows: list[dict], category_map: dict[str, str]) -> None:
    for key, title in category_map.items():
        rows = [r for r in all_rows if r["category"] == key]
        summary = build_summary(rows)
        buf: list[str] = []
        add_line(buf, f"# 机制检验：{title}")
        add_line(buf)
        add_line(buf, "## 本次操作")
        add_line(buf, "- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`")
        add_line(buf, "- 核心解释变量：`fund_est_scale_cum`")
        add_line(buf, "- 债务调节变量：`debt_pressure`、`debt_pressure_l1`")
        add_line(buf, "- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`")
        add_line(buf, "- 回归方法：地级市固定效应 + 年份固定效应，标准误按城市聚类")
        add_line(buf, "- 报告说明：以下表格完整记录该类别下所有已尝试规格的系数、标准误、p 值和显著性星号")
        add_line(buf)

        add_line(buf, "## 显著结果摘要")
        add_table(
            buf,
            [
                {
                    "model": item["model_family"],
                    "mvar": item["mvar"],
                    "M_eq_sig": item["m_eq_sig"],
                    "Y_term1_sig": item["y_term1_sig"],
                    "Y_term2_sig": item["y_term2_sig"],
                    "Y_term3_sig": item["y_term3_sig"],
                    "total_rows": item["total_rows"],
                }
                for item in summary
            ],
            ["model", "mvar", "M_eq_sig", "Y_term1_sig", "Y_term2_sig", "Y_term3_sig", "total_rows"],
            ["model", "mvar", "M_eq_sig", "Y_term1_sig", "Y_term2_sig", "Y_term3_sig", "total_rows"],
        )

        add_line(buf, "## 完整结果")
        add_line(buf, "### 模型 A：机制变量作为中介传导变量")
        add_line(buf, "#### A1. M_eq")
        add_table(
            buf,
            build_table_rows(rows, "mediated", "M_eq"),
            ["spec", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "N", "r2w"],
            ["spec", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "N", "r2w"],
        )
        add_line(buf, "#### A2. Y_eq")
        add_table(
            buf,
            build_table_rows(rows, "mediated", "Y_eq"),
            ["spec", "yvar", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "term2", "coef2", "se2", "p2", "sig2", "N", "r2w"],
            ["spec", "yvar", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "term2", "coef2", "se2", "p2", "sig2", "N", "r2w"],
        )

        add_line(buf, "### 模型 B：机制变量作为调节变量")
        add_line(buf, "#### B1. M_eq")
        add_table(
            buf,
            build_table_rows(rows, "moderator", "M_eq"),
            ["spec", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "term2", "coef2", "se2", "p2", "sig2", "N", "r2w"],
            ["spec", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "term2", "coef2", "se2", "p2", "sig2", "N", "r2w"],
        )
        add_line(buf, "#### B2. Y_eq")
        add_table(
            buf,
            build_table_rows(rows, "moderator", "Y_eq"),
            ["spec", "yvar", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "term2", "coef2", "se2", "p2", "sig2", "term3", "coef3", "se3", "p3", "sig3", "N", "r2w"],
            ["spec", "yvar", "dvar", "mvar", "term1", "coef1", "se1", "p1", "sig1", "term2", "coef2", "se2", "p2", "sig2", "term3", "coef3", "se3", "p3", "sig3", "N", "r2w"],
        )

        add_line(buf, "## 输出文件")
        add_line(buf, "- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`")
        add_line(buf, "- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`")
        add_line(buf, "- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`")

        filename = {
            "early": "xtreg_mechanism_early_dualmodel_focus.md",
            "soccap": "xtreg_mechanism_soccap_dualmodel_focus.md",
            "fc": "xtreg_mechanism_fc_dualmodel_focus.md",
        }[key]

        (RESULT_DIR / filename).write_text("\n".join(buf), encoding="utf-8")


def main() -> None:
    rows = load_rows()
    category_map = {
        "early": "早期投资",
        "soccap": "社会资本撬动效率",
        "fc": "融资约束",
    }
    write_overview(rows, category_map)
    write_category_docs(rows, category_map)


if __name__ == "__main__":
    main()
