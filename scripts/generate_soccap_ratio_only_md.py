from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "运行日志与do代码"
RESULT_DIR = ROOT / "实证结果"
BASENAME = "xtreg_mechanism_soccap_ratio_only_20260516"
RESULT_CSV = LOG_DIR / f"{BASENAME}_results.csv"
DIAG_CSV = LOG_DIR / f"{BASENAME}_diagnostics.csv"
DO_FILE = LOG_DIR / f"{BASENAME}.do"
LOG_FILE = LOG_DIR / f"{BASENAME}.log"
MD_FILE = RESULT_DIR / f"{BASENAME}.md"


VAR_LABELS = {
    "z_scsh_w": "社会资本占总认缴比，非缺失口径，1%/99%缩尾后标准化",
    "z_scsh0_w": "社会资本占总认缴比，缺失填0，1%/99%缩尾后标准化",
    "L1_z_scsh0_w": "社会资本占总认缴比，缺失填0缩尾标准化后滞后一期",
    "z_matsh_w": "已匹配认缴额占比，非缺失口径，1%/99%缩尾后标准化",
    "z_matsh0_w": "已匹配认缴额占比，缺失填0，1%/99%缩尾后标准化",
    "L1_z_matsh0_w": "已匹配认缴额占比，缺失填0缩尾标准化后滞后一期",
    "z_govinv0_w": "非政府出资占比，等于 1-政府出资占总认缴比，缺失填0后缩尾标准化",
    "L1_z_govinv0_w": "非政府出资占比，缺失填0缩尾标准化后滞后一期",
    "z_lnlev_w": "社会资本撬动效率 ln(1+效率)，非缺失口径，缩尾后标准化",
    "z_lnlev0_w": "社会资本撬动效率 ln(1+效率)，缺失填0，缩尾后标准化",
    "L1_z_lnlev0_w": "社会资本撬动效率，缺失填0缩尾标准化后滞后一期",
}

FAMILY_LABELS = {
    "mediated": "模型A：中介式传导",
    "fund_x_ratio": "模型B：比例变量调节基金规模边际效应",
    "triple": "模型C：债务压力下的三重交互",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str, digits: int = 6) -> str:
    if value is None or value == "":
        return ""
    try:
        x = float(value)
    except ValueError:
        return str(value)
    if abs(x) >= 1000 or (abs(x) > 0 and abs(x) < 0.0001):
        return f"{x:.6g}"
    return f"{x:.{digits}f}".rstrip("0").rstrip(".")


def fp(value: str) -> str:
    if value is None or value == "":
        return ""
    try:
        x = float(value)
    except ValueError:
        return str(value)
    if x < 0.0001:
        return f"{x:.3g}"
    return f"{x:.5f}".rstrip("0").rstrip(".")


def sig_from_p(value: str) -> str:
    try:
        p = float(value)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        cleaned = [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        out.append("| " + " | ".join(cleaned) + " |")
    return out


def result_sort_key(row: dict[str, str]) -> tuple[float, str, str, str]:
    try:
        p = float(row.get("p", ""))
    except ValueError:
        p = 1.0
    return (p, row.get("family", ""), row.get("mvar", ""), row.get("yvar", ""))


def main() -> None:
    RESULT_DIR.mkdir(exist_ok=True)
    rows = read_csv(RESULT_CSV)
    diag = read_csv(DIAG_CSV)

    sig10 = [r for r in rows if r.get("p") and float(r["p"]) < 0.1]
    sig05 = [r for r in rows if r.get("p") and float(r["p"]) < 0.05]
    sig01 = [r for r in rows if r.get("p") and float(r["p"]) < 0.01]

    by_family_mvar: dict[tuple[str, str], int] = defaultdict(int)
    for r in sig05:
        by_family_mvar[(r["family"], r["mvar"])] += 1

    m_eq_sig = {
        (r["spec"], r["xvar"], r["dvar"], r["mvar"]): r
        for r in rows
        if r["family"] == "mediated" and r["step"] == "M_eq" and r.get("p") and float(r["p"]) < 0.1
    }
    mediated_pairs = []
    for r in rows:
        key = (r["spec"], r["xvar"], r["dvar"], r["mvar"])
        if (
            r["family"] == "mediated"
            and r["step"] == "Y_eq"
            and key in m_eq_sig
            and r.get("p_m")
            and float(r["p_m"]) < 0.1
        ):
            mediated_pairs.append((m_eq_sig[key], r))
    mediated_pairs.sort(key=lambda pair: float(pair[1]["p_m"]))

    lines: list[str] = []
    lines.append("# 机制检验：社会资本撬动效率（比例变量限定版）")
    lines.append("")
    lines.append("## 本次操作")
    lines.append("")
    lines.append("- 回归日期：2026-05-16")
    lines.append("- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`")
    lines.append("- 样本期：2015-2024 年地级市面板")
    lines.append("- 核心解释变量：`fund_est_scale_cum` 与 `ln_fund_est_scale_cum`")
    lines.append("- 债务调节变量：`debt_pressure`、`debt_pressure_l1`")
    lines.append("- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total` 及其对数口径")
    lines.append("- 回归方法：地级市固定效应 + 年份固定效应，标准误按城市聚类")
    lines.append("- 本版限定：机制变量只使用比例/效率口径，不使用 `soccap_amt`、`gov_amt`、`gp_amt`、`fund_commit_total`、`matched_commit_amt`、`soccap_fund_count` 等绝对数量变量。")
    lines.append("")
    lines.append("## 比例变量处理")
    lines.append("")
    lines.append("- 对比例变量限定合法区间：`soccap_share_total`、`gov_share_total`、`matched_share_total` 必须位于 `[0,1]`；`soccap_leverage` 必须非负。")
    lines.append("- 对比例变量做 1%/99% 缩尾并标准化；对社会资本撬动效率使用 `ln(1+soccap_leverage)` 后再缩尾标准化。")
    lines.append("- 同时报告非缺失口径、缺失填 0 口径和滞后一期口径。缺失填 0 用于刻画没有观测到社会资本撬动记录的城市年份，非缺失口径保留为对照。")
    lines.append("")
    lines.extend(
        md_table(
            ["变量", "含义"],
            [[name, label] for name, label in VAR_LABELS.items()],
        )
    )
    lines.append("")
    lines.append("## 变量诊断")
    lines.append("")
    lines.extend(
        md_table(
            ["变量", "N", "均值", "标准差", "最小值", "P1", "中位数", "P99", "最大值"],
            [
                [
                    d["variable"],
                    fnum(d["N"], 0),
                    fnum(d["mean"]),
                    fnum(d["sd"]),
                    fnum(d["min"]),
                    fnum(d["p1"]),
                    fnum(d["p50"]),
                    fnum(d["p99"]),
                    fnum(d["max"]),
                ]
                for d in diag
            ],
        )
    )
    lines.append("")
    lines.append("## 模型设定")
    lines.append("")
    lines.append("1. 模型A：`M = X + Debt + X*Debt + controls + city FE + year FE`；`Y = X + Debt + X*Debt + M + controls + city FE + year FE`。")
    lines.append("2. 模型B：`Y = X + Debt + X*Debt + X*M + M + controls + city FE + year FE`，检验比例变量是否改变基金规模的边际创新效应。")
    lines.append("3. 模型C：`Y = X*Debt*M + controls + city FE + year FE`，检验债务压力场景下比例变量是否改变基金规模作用。")
    lines.append("")
    lines.append("## 显著性概览")
    lines.append("")
    lines.append(f"- 共报告模型结果：`{len(rows)}` 行。")
    lines.append(f"- 焦点项在 10% 水平显著：`{len(sig10)}` 行；5% 水平显著：`{len(sig05)}` 行；1% 水平显著：`{len(sig01)}` 行。")
    lines.append("- 显著项主要集中在模型B和模型C；模型A的中介式第一步证据存在，但整体不如调节式证据稳定。")
    lines.append("")
    grouped_rows = []
    for (family, mvar), count in sorted(by_family_mvar.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))[:24]:
        grouped_rows.append([FAMILY_LABELS.get(family, family), mvar, VAR_LABELS.get(mvar, ""), str(count)])
    lines.extend(md_table(["模型", "比例变量", "变量说明", "5%显著项数"], grouped_rows))
    lines.append("")
    lines.append("## 代表性显著结果")
    lines.append("")
    top_rows = sorted(sig05, key=result_sort_key)[:30]
    lines.extend(
        md_table(
            ["模型", "规格", "因变量", "X", "债务变量", "比例变量", "焦点项", "系数", "标准误", "p值", "显著性", "N", "R2_w"],
            [
                [
                    FAMILY_LABELS.get(r["family"], r["family"]),
                    r["spec"],
                    r["yvar"],
                    r["xvar"],
                    r["dvar"],
                    r["mvar"],
                    r["focus_term"],
                    fnum(r["b"]),
                    fnum(r["se"]),
                    fp(r["p"]),
                    r["sig"],
                    fnum(r["N"], 0),
                    fnum(r["r2w"]),
                ]
                for r in top_rows
            ],
        )
    )
    lines.append("")
    lines.append("## 中介式结果补充")
    lines.append("")
    if mediated_pairs:
        lines.append("下表只列出模型A中同时满足第一步 `X*Debt -> M` 在 10% 水平显著，且第二步 `M -> Y` 在 10% 水平显著的组合。")
        lines.append("")
        lines.extend(
            md_table(
                ["规格", "因变量", "X", "债务变量", "比例变量", "第一步系数", "第一步p值", "第二步M系数", "第二步M p值", "N"],
                [
                    [
                        y["spec"],
                        y["yvar"],
                        y["xvar"],
                        y["dvar"],
                        y["mvar"],
                        fnum(m["b"]),
                        fp(m["p"]),
                        fnum(y["b_m"]),
                        fp(y["p_m"]),
                        fnum(y["N"], 0),
                    ]
                    for m, y in mediated_pairs[:30]
                ],
            )
        )
    else:
        lines.append("未发现第一步和第二步同时达到 10% 显著的中介式组合。")
    lines.append("")
    lines.append("## 简要解读")
    lines.append("")
    lines.append("- 在只使用比例变量的前提下，`matched_share_total` 的缺失填 0、缩尾标准化口径最稳定：在总专利、发明专利和实用新型专利上均出现显著的 `基金规模 × 已匹配认缴额占比` 项。")
    lines.append("- `soccap_share_total` 与 `1-gov_share_total` 也提供补充证据，说明社会资本或非政府出资占比越高，政府引导基金规模的边际创新效应越容易发生变化。")
    lines.append("- `soccap_leverage` 本身经 `ln(1+效率)` 处理后可以得到若干显著项，但强度弱于 `matched_share_total`；因此正文更适合把 `matched_share_total` 作为主比例机制，把 `soccap_leverage` 作为效率口径补充。")
    lines.append("- 三重交互项显著但方向并不完全一致，表示在债务压力约束下，比例变量会改变基金规模作用路径；这些结果适合作为机制存在的证据，不宜简单解释为单向促进。")
    lines.append("")
    lines.append("## 完整结果")
    lines.append("")
    lines.append("说明：`b/se/p/sig` 对应每行焦点项；`b_xd/se_xd/p_xd` 对应 `X*Debt`；`b_m/se_m/p_m` 对应比例变量主项。")
    lines.append("")
    lines.extend(
        md_table(
            [
                "family",
                "spec",
                "step",
                "yvar",
                "xvar",
                "dvar",
                "mvar",
                "focus_term",
                "b",
                "se",
                "p",
                "sig",
                "b_xd",
                "p_xd",
                "b_m",
                "p_m",
                "N",
                "r2w",
            ],
            [
                [
                    r["family"],
                    r["spec"],
                    r["step"],
                    r["yvar"],
                    r["xvar"],
                    r["dvar"],
                    r["mvar"],
                    r["focus_term"],
                    fnum(r["b"]),
                    fnum(r["se"]),
                    fp(r["p"]),
                    sig_from_p(r["p"]),
                    fnum(r["b_xd"]),
                    fp(r["p_xd"]),
                    fnum(r["b_m"]),
                    fp(r["p_m"]),
                    fnum(r["N"], 0),
                    fnum(r["r2w"]),
                ]
                for r in rows
            ],
        )
    )
    lines.append("")
    lines.append("## 输出文件")
    lines.append("")
    lines.append(f"- do 文件：`运行日志与do代码/{DO_FILE.name}`")
    lines.append(f"- log 文件：`运行日志与do代码/{LOG_FILE.name}`")
    lines.append(f"- 结果表：`运行日志与do代码/{RESULT_CSV.name}`")
    lines.append(f"- 诊断表：`运行日志与do代码/{DIAG_CSV.name}`")

    MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(MD_FILE)


if __name__ == "__main__":
    main()
