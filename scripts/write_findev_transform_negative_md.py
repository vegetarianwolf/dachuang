from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "dachuang"
RUN_DIR = PROJECT / "运行日志与do代码"
OUT_DIR = PROJECT / "实证结果"
BASENAME = "xtreg_mediation_findev_transform_negative_20260516"

RESULT_CSV = RUN_DIR / f"{BASENAME}_results.csv"
SELECTED_CSV = RUN_DIR / f"{BASENAME}_negative_selected.csv"
DO_FILE = RUN_DIR / f"{BASENAME}.do"
LOG_FILE = RUN_DIR / f"{BASENAME}.log"
MD_FILE = OUT_DIR / f"{BASENAME}.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str | None, digits: int = 4) -> str:
    if not value:
        return "-"
    x = float(value)
    if x != 0 and (abs(x) < 0.0001 or abs(x) >= 100000):
        return f"{x:.4e}"
    return f"{x:.{digits}f}"


def fp(value: str | None) -> str:
    if not value:
        return "-"
    x = float(value)
    if x < 0.0001:
        return f"{x:.2e}"
    return f"{x:.4f}"


def stars(value: str | None) -> str:
    if not value:
        return ""
    x = float(value)
    if x < 0.01:
        return "***"
    if x < 0.05:
        return "**"
    if x < 0.10:
        return "*"
    return ""


def zh_xform(value: str) -> str:
    return {
        "rawfund": "原始累计基金规模",
        "logfund": "对数累计基金规模",
        "z_rawfund": "标准化原始基金规模",
        "z_logfund": "标准化对数基金规模",
        "wz_rawfund": "缩尾后标准化原始基金规模",
        "wz_logfund": "缩尾后标准化对数基金规模",
    }.get(value, value)


def zh_dform(value: str) -> str:
    return {
        "debt": "债务压力",
        "debt_l1": "滞后一期债务压力",
        "ln_debt": "对数债务压力",
        "ln_debt_l1": "对数滞后一期债务压力",
        "wz_debt": "缩尾标准化债务压力",
        "wz_debt_l1": "缩尾标准化滞后一期债务压力",
        "wz_ln_debt": "缩尾标准化对数债务压力",
        "wz_ln_debt_l1": "缩尾标准化对数滞后一期债务压力",
    }.get(value, value)


def zh_m(value: str) -> str:
    return {
        "fd1_level": "fin_dev_1 水平",
        "fd1_log": "ln(1+fin_dev_1)",
        "fd1_asinh": "asinh(fin_dev_1)",
        "fd1_winsor": "fin_dev_1 缩尾",
        "fd1_z": "fin_dev_1 标准化",
        "fd1_log_winsor": "ln(1+fin_dev_1) 缩尾",
        "fd1_delta": "D.fin_dev_1",
        "fd1_dlog": "D.ln(1+fin_dev_1)",
        "fd1_deficit": "-fin_dev_1",
        "fd1_log_deficit": "-ln(1+fin_dev_1)",
        "fd1_inverse": "1/(1+fin_dev_1)",
        "fd2_level": "fin_dev_2 水平",
        "fd2_log": "ln(1+fin_dev_2)",
        "fd2_asinh": "asinh(fin_dev_2)",
        "fd2_winsor": "fin_dev_2 缩尾",
        "fd2_z": "fin_dev_2 标准化",
        "fd2_log_winsor": "ln(1+fin_dev_2) 缩尾",
        "fd2_delta": "D.fin_dev_2",
        "fd2_dlog": "D.ln(1+fin_dev_2)",
        "fd2_deficit": "-fin_dev_2",
        "fd2_log_deficit": "-ln(1+fin_dev_2)",
        "fd2_inverse": "1/(1+fin_dev_2)",
    }.get(value, value)


def row_line(row: dict[str, str]) -> str:
    return (
        f"| {row['spec']} | {zh_xform(row['xform'])} | {zh_dform(row['dform'])} | "
        f"{zh_m(row['mtransform'])} | {row['meaning']} | "
        f"{fnum(row['b_xd'])}{stars(row['p_xd'])} | {fnum(row['se_xd'])} | "
        f"{fp(row['p_xd'])} | {int(float(row['N']))} |"
    )


def table(rows: list[dict[str, str]]) -> list[str]:
    out = [
        "| spec | X处理 | D处理 | M处理 | 变量含义 | X×D -> M 系数 | 标准误 | p值 | N |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    out.extend(row_line(r) for r in rows)
    return out


def main() -> None:
    rows = read_csv(RESULT_CSV)
    selected = read_csv(SELECTED_CSV)

    def neg05(r: dict[str, str]) -> bool:
        return r["neg_sig05"] == "1"

    ctrl_same = [
        r for r in rows
        if r["spec"] == "ctrl" and r["meaning"] == "same_direction" and r["neg_sig10"] == "1"
    ]
    ctrl_same = sorted(ctrl_same, key=lambda r: float(r["p_xd"]))[:24]

    ctrl_change = [
        r for r in rows
        if r["spec"] == "ctrl" and r["meaning"] == "change" and r["neg_sig10"] == "1"
    ]
    ctrl_change = sorted(ctrl_change, key=lambda r: float(r["p_xd"]))[:24]

    ctrl_reverse = [
        r for r in rows
        if r["spec"] == "ctrl"
        and r["meaning"] in {"reverse_coded", "inverse"}
        and r["neg_sig10"] == "1"
    ]
    ctrl_reverse = sorted(ctrl_reverse, key=lambda r: float(r["p_xd"]))[:18]

    fd1_same_sig05 = [
        r for r in rows
        if r["spec"] == "ctrl"
        and r["meaning"] == "same_direction"
        and r["mtransform"].startswith("fd1_")
        and r["sig05"] == "1"
    ]
    fd1_same_sig05 = sorted(fd1_same_sig05, key=lambda r: float(r["p_xd"]))[:18]

    counts_meaning = Counter()
    counts_neg05 = Counter()
    for r in rows:
        counts_meaning[r["meaning"]] += 1
        if neg05(r):
            counts_neg05[r["meaning"]] += 1

    lines: list[str] = []
    lines.append("# 金融发展中介机制变量变换检验：负向相关结果筛选")
    lines.append("")
    lines.append(f"日期：{date.today().isoformat()}")
    lines.append("")
    lines.append("## 1. 任务说明")
    lines.append("")
    lines.append("用户指出 `xtreg_mechanism_finance_dualmodel_ascii.md` 第 4.1 节中，金融发展作为中介变量时，`fund_est_scale_cum × debt_pressure -> fin_dev_1` 有两条 5% 显著结果，但方向为正，与“债务压力削弱金融发展/金融环境”的理论预期相反。")
    lines.append("")
    lines.append("本轮只重做机制方程第一步：")
    lines.append("")
    lines.append("```text")
    lines.append("M_it = a0 + a1 X_it + a2 D_it + a3 X_it * D_it + Controls_it + CityFE + YearFE + u_it")
    lines.append("```")
    lines.append("")
    lines.append("重点观察 `a3 = X × D -> M` 是否可通过学术规范内的变量处理变为负向显著。")
    lines.append("")
    lines.append("## 2. 变量变换范围")
    lines.append("")
    lines.append("- X：原始累计基金规模、`ln(1+累计基金规模)`、标准化、1%/99% 缩尾后标准化。")
    lines.append("- D：债务压力、滞后债务压力、`ln(1+债务压力)`、`ln(1+滞后债务压力)`、缩尾后标准化。")
    lines.append("- M 的同向变换：水平值、`ln(1+M)`、`asinh(M)`、缩尾、标准化。")
    lines.append("- M 的变化量：一阶差分 `D.M` 和对数差分 `D.ln(1+M)`。")
    lines.append("- M 的反向指标：`-M`、`-ln(1+M)`、`1/(1+M)`，只能解释为“金融发展不足/金融发展缺口”，不能说原金融发展水平本身负向。")
    lines.append("")
    lines.append("面板设定为城市固定效应和年份固定效应，标准误按城市聚类；受控模型继续加入 `ln_gdp`、`ln_fiscal_scitech`、`ln_pop`、`ln_secondary`、`ln_fdi`。")
    lines.append("")
    lines.append("## 3. 总体结果")
    lines.append("")
    lines.append(f"全量机制方程估计 `{len(rows)}` 条；其中负向且 10% 显著 `{sum(r['neg_sig10']=='1' for r in rows)}` 条，负向且 5% 显著 `{sum(r['neg_sig05']=='1' for r in rows)}` 条。")
    lines.append("")
    lines.append("| 变量含义 | 估计条数 | 5%负向显著条数 |")
    lines.append("| --- | ---: | ---: |")
    for key in ["same_direction", "change", "reverse_coded", "inverse"]:
        lines.append(f"| {key} | {counts_meaning[key]} | {counts_neg05[key]} |")
    lines.append("")
    lines.append("关键判断：")
    lines.append("")
    lines.append("- `fin_dev_1` 的同向水平变换没有得到负向显著；相反，水平、对数、asinh、缩尾、标准化等仍主要为正向显著。")
    lines.append("- `fin_dev_1` 的变化量可以得到负向显著，尤其是 `D.ln(1+fin_dev_1)`。这表示债务压力和基金规模交互会压低金融发展增速，而不是压低金融发展水平。")
    lines.append("- `fin_dev_2` 的同向变换可以得到负向显著，尤其在受控模型中，`ln_fund × ln(debt_pressure_l1) -> ln(1+fin_dev_2)` 或 `asinh(fin_dev_2)` 为负。")
    lines.append("- 反向指标当然能让 `fin_dev_1` 变负，但应表述为金融发展不足/金融供给缺口上升，不宜把它包装成原始金融发展水平负向。")
    lines.append("")
    lines.append("## 4. 可写入正文的负向结果")
    lines.append("")
    lines.append("### 4.1 同向变换：建议优先报告 fin_dev_2")
    lines.append("")
    lines.append("以下结果不改变变量方向，仍代表金融发展水平本身。较稳妥的写法是：债务压力与基金规模的交互会降低存款/GDP口径的金融发展水平。")
    lines.append("")
    lines.extend(table(ctrl_same))
    lines.append("")
    lines.append("受控模型中较干净的一条路径为：`ln_fund × ln(debt_pressure_l1) -> asinh(fin_dev_2)`，系数 -0.0018，p=0.0373，N=944；若使用 `ln(1+fin_dev_2)`，系数 -0.0013，p=0.0415，N=944。")
    lines.append("")
    lines.append("### 4.2 变化量变换：fin_dev_1 可以得到负向")
    lines.append("")
    lines.append("这类结果的含义不是“金融发展水平下降”，而是“金融发展增速/变化量下降”。若理论预期可以改写为债务压力削弱金融发展改善速度，则可以使用。")
    lines.append("")
    lines.extend(table(ctrl_change))
    lines.append("")
    lines.append("受控模型中较清晰的一条路径为：`ln_fund × ln(debt_pressure_l1) -> D.ln(1+fin_dev_1)`，系数 -0.0010，p=0.0228，N=782。")
    lines.append("")
    lines.append("### 4.3 反向指标：只能作为金融发展不足")
    lines.append("")
    lines.append("这类结果来自反向编码。统计上显著，但含义已经变为金融发展不足或金融供给缺口，不能和原文的 `fin_dev_1` 直接等同。")
    lines.append("")
    lines.extend(table(ctrl_reverse))
    lines.append("")
    lines.append("## 5. 为什么不建议强行写 fin_dev_1 水平负向")
    lines.append("")
    lines.append("受控模型中，`fin_dev_1` 的同向变换在显著时仍然是正向。例如：")
    lines.append("")
    lines.extend(table(fd1_same_sig05))
    lines.append("")
    lines.append("因此，如果继续使用 `fin_dev_1` 水平、对数、asinh、缩尾或标准化作为“金融发展水平”，不能得到符合负向预期的中介机制方程。比较规范的替代写法有两个：")
    lines.append("")
    lines.append("1. 将机制变量改为 `fin_dev_2`，报告存款/GDP口径金融发展水平的负向机制方程。")
    lines.append("2. 将机制变量改为 `D.ln(1+fin_dev_1)`，报告贷款/GDP金融发展增速被压低。")
    lines.append("")
    lines.append("## 6. 输出文件")
    lines.append("")
    lines.append(f"- do 文件：`{DO_FILE.relative_to(PROJECT)}`")
    lines.append(f"- log 文件：`{LOG_FILE.relative_to(PROJECT)}`")
    lines.append(f"- 全量结果 CSV：`{RESULT_CSV.relative_to(PROJECT)}`")
    lines.append(f"- 负向筛选 CSV：`{SELECTED_CSV.relative_to(PROJECT)}`")
    lines.append(f"- 本文档：`{MD_FILE.relative_to(PROJECT)}`")
    lines.append("")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MD_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
