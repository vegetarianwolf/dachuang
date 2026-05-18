# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import math
from pathlib import Path


BASENAME = "xtreg_mechanism_early_share_focus_ascii"
RESULTS_PATH = Path("..") / "运行日志与do代码" / f"{BASENAME}_results.csv"
SELECTED_PATH = Path("..") / "运行日志与do代码" / f"{BASENAME}_selected.csv"
OUT_PATH = Path(f"{BASENAME}.md")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str) -> str:
    if value is None or value == "":
        return ""
    try:
        x = float(value)
    except ValueError:
        return value
    if x != 0 and abs(x) < 0.001:
        return f"{x:.3e}"
    return f"{x:.4f}"


def fp(value: str) -> str:
    if value is None or value == "":
        return ""
    try:
        x = float(value)
    except ValueError:
        return value
    if x < 0.001:
        return f"{x:.3e}"
    return f"{x:.4f}"


def stars(p: str) -> str:
    try:
        x = float(p)
    except (TypeError, ValueError):
        return ""
    if x <= 0.01:
        return "***"
    if x <= 0.05:
        return "**"
    if x <= 0.1:
        return "*"
    return ""


def model_label(model: str) -> str:
    return {
        "mediator": "A 中介传导",
        "moderator": "B 调节机制",
        "triple": "C 三重交互",
    }.get(model, model)


def source_label(source: str) -> str:
    return {
        "early_inv_amt_share": "早期投资金额占比",
        "early_inv_count_share": "早期投资事件占比",
    }.get(source, source)


def transform_label(transform: str) -> str:
    return {
        "raw": "原始比例",
        "winsor": "1/99缩尾",
        "asin": "arcsin-sqrt",
        "logit": "logit",
    }.get(transform, transform)


def selected_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| 模型 | 因变量 | 债务变量 | 比例变量 | 变换 | 规格 | N | 路径1系数 | 路径1p | 路径2系数 | 路径2p | X×D系数 | X×Dp | 判定 |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in rows:
        judge = "5%成立" if r["pass05"] == "1" else "10%成立"
        lines.append(
            "| {model} | {y} | {d} | {src} | {tr} | {spec} | {n} | "
            "{b1}{s1} | {p1} | {b2}{s2} | {p2} | {bxd}{sxd} | {pxd} | {judge} |".format(
                model=model_label(r["model"]),
                y=r["yvar"],
                d=r["dvar"],
                src=source_label(r["m_source"]),
                tr=transform_label(r["transform"]),
                spec=r["spec"],
                n=r["N"],
                b1=fnum(r["coef_path1"]),
                s1=stars(r["p_path1"]),
                p1=fp(r["p_path1"]),
                b2=fnum(r["coef_path2"]),
                s2=stars(r["p_path2"]),
                p2=fp(r["p_path2"]),
                bxd=fnum(r["coef_xd"]),
                sxd=stars(r["p_xd"]),
                pxd=fp(r["p_xd"]),
                judge=judge,
            )
        )
    return lines


def full_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| 模型 | 因变量 | 债务变量 | 比例变量 | 变换 | 规格 | N | 路径1 coef | 路径1 se | 路径1 p | 路径2 coef | 路径2 se | 路径2 p | X×D coef | X×D se | X×D p |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            "| {model} | {y} | {d} | {src} | {tr} | {spec} | {n} | "
            "{b1}{s1} | {se1} | {p1} | {b2}{s2} | {se2} | {p2} | {bxd}{sxd} | {sexd} | {pxd} |".format(
                model=model_label(r["model"]),
                y=r["yvar"],
                d=r["dvar"],
                src=source_label(r["m_source"]),
                tr=transform_label(r["transform"]),
                spec=r["spec"],
                n=r["N"],
                b1=fnum(r["coef_path1"]),
                s1=stars(r["p_path1"]),
                se1=fnum(r["se_path1"]),
                p1=fp(r["p_path1"]),
                b2=fnum(r["coef_path2"]),
                s2=stars(r["p_path2"]),
                se2=fnum(r["se_path2"]),
                p2=fp(r["p_path2"]),
                bxd=fnum(r["coef_xd"]),
                sxd=stars(r["p_xd"]),
                sexd=fnum(r["se_xd"]),
                pxd=fp(r["p_xd"]),
            )
        )
    return lines


def main() -> None:
    results = read_csv(RESULTS_PATH)
    selected = read_csv(SELECTED_PATH)

    total = len(results)
    mediator_total = sum(r["model"] == "mediator" for r in results)
    moderator_total = sum(r["model"] == "moderator" for r in results)
    triple_total = sum(r["model"] == "triple" for r in results)
    moderator_pass10 = sum(r["model"] == "moderator" and r["pass10"] == "1" for r in results)
    triple_pass10 = sum(r["model"] == "triple" and r["pass10"] == "1" for r in results)

    lines: list[str] = []
    lines.extend(
        [
            "# 早期投资比例机制检验：区别于绝对数量口径的聚焦结果",
            "",
            "回归日期：2026-05-16",
            "",
            "## 本次操作",
            "",
            "- 数据集：`staging_ascii/panel_2015_2024_regression_ascii_clean.csv`",
            "- 任务：按用户要求，只使用早期投资比例变量做机制检验，不使用 `early_inv_amt` 或 `early_inv_count` 作为机制变量。",
            "- 面板设定：地级市固定效应 + 年份固定效应，标准误按城市聚类。",
            "- 控制变量：`ln_gdp`、`ln_fiscal_scitech`、`ln_pop`、`ln_secondary`、`ln_fdi`。",
            "- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`。",
            "- 核心解释变量：`fund_est_scale_cum`。",
            "- 债务压力变量：`debt_pressure`、`debt_pressure_l1`。",
            "- 早期投资比例变量：`early_inv_amt_share`、`early_inv_count_share`。",
            "- 比例变量变换：原始比例、1/99 缩尾、arcsin-sqrt、logit。",
            "",
            "## 模型设定",
            "",
            "A. 中介传导模型：检验 `fund_est_scale_cum × debt_pressure -> 早期投资比例 -> 创新产出`。其中路径1为 `X×D -> M`，路径2为 `M -> Y`。",
            "",
            "B. 调节机制模型：先检验 `debt_pressure -> 早期投资比例`，再检验 `fund_est_scale_cum × 早期投资比例 -> 创新产出`。其中路径1为 `D -> M`，路径2为 `X×M -> Y`。",
            "",
            "C. 三重交互模型：先检验 `debt_pressure -> 早期投资比例`，再检验 `fund_est_scale_cum × debt_pressure × 早期投资比例 -> 创新产出`。其中路径2为三重交互项。",
            "",
            "## 总体结果",
            "",
            f"- 共尝试 `{total}` 个比例口径规格，其中中介传导 `{mediator_total}` 个、调节机制 `{moderator_total}` 个、三重交互 `{triple_total}` 个。",
            "- 中介传导模型没有规格同时通过两条路径的 10% 显著性要求，因此不建议把早期投资比例写成普通中介。",
            f"- 调节机制模型有 `{moderator_pass10}` 个规格在 10% 水平成立，其中 `early_inv_amt_share` 对 `pat_invent_apply` 的滞后债务压力口径在 5% 水平成立。",
            f"- 三重交互模型有 `{triple_pass10}` 个规格在 10% 水平成立，其中 `early_inv_count_share` 对 `pat_invent_apply` 的当期和滞后债务压力口径在 5% 水平成立。",
            "- 总体上，比例口径下更稳的写法是：早期投资比例不是普通中介，而是债务压力调节效应的承接性调节机制。",
            "",
            "## 显著结果",
            "",
            "下表仅列出路径1和路径2同时达到 10% 显著性的规格。星号规则：*** p≤0.01，** p≤0.05，* p≤0.1。",
        ]
    )
    lines.extend(selected_table(selected))
    lines.extend(
        [
            "",
            "## 主要解释",
            "",
            "- `early_inv_amt_share`：在 `debt_pressure_l1` 口径下，债务压力显著影响早期投资金额占比，且该占比显著调节基金累计设立规模对发明专利申请的影响。原始比例和缩尾比例均在 5% 水平成立；arcsin-sqrt 变换在 10% 水平成立。",
            "- `early_inv_count_share`：事件占比在三重交互模型中更稳定。对于 `pat_invent_apply`，当期债务压力和滞后债务压力口径下的三重交互项均在 5% 水平显著；对于 `pat_apply_total`，滞后债务压力口径在 10% 水平显著。",
            "- 由于三重交互项多为正，而 `fund_est_scale_cum × debt_pressure` 项为负，结果更适合解释为：早期投资事件占比越高时，债务压力对基金创新扶持效应的负向调节有所改变或缓冲。该解释应以调节机制表述，不宜写成简单中介。",
            "- 中介传导模型中，部分规格的路径1显著，但路径2没有同时显著；因此本轮比例口径不支持 `早期投资比例` 作为普通中介变量。",
            "",
            "## 样本与缺失处理",
            "",
            "- 每个规格按所需变量逐项删除缺失值。",
            "- 原始比例变量仅在 `0 <= share <= 1` 范围内进入估计。",
            "- 缩尾变换使用样本内 1% 和 99% 分位数；本轮显著行中原始比例与缩尾结果相同，说明极端值不是显著性的来源。",
            "- logit 变换使用 `log((share + 0.001)/(1 - share + 0.001))`，用于保留 0 和 1 边界比例观测。",
            "",
            "## 输出文件",
            "",
            "- do 文件：`运行日志与do代码/xtreg_mechanism_early_share_focus_ascii.do`",
            "- log 文件：`运行日志与do代码/xtreg_mechanism_early_share_focus_ascii.log`",
            "- 完整结果表：`运行日志与do代码/xtreg_mechanism_early_share_focus_ascii_results.csv`",
            "- 显著结果表：`运行日志与do代码/xtreg_mechanism_early_share_focus_ascii_selected.csv`",
            "",
            "## 全部规格结果附录",
            "",
            "下表列出全部 288 个尝试规格。`路径1`、`路径2` 和 `X×D` 的含义见上文模型设定。",
        ]
    )
    lines.extend(full_table(results))
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
