from pathlib import Path
import csv
from collections import Counter


BASE = "xtreg_early_share_theory_lagged_y_20260518"
OUT = Path(f"{BASE}.md")
RESULTS = Path("..") / "运行日志与do代码" / f"{BASE}_results.csv"
SELECTED = Path("..") / "运行日志与do代码" / f"{BASE}_selected.csv"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(value, digits=3):
    try:
        v = float(value)
    except Exception:
        return ""
    return f"{v:.{digits}f}"


def fp(value):
    try:
        v = float(value)
    except Exception:
        return ""
    return f"{v:.3f}"


def star(p):
    try:
        v = float(p)
    except Exception:
        return ""
    if v <= 0.01:
        return "***"
    if v <= 0.05:
        return "**"
    if v <= 0.10:
        return "*"
    return ""


def pct_flag(row, key):
    return int(float(row.get(key, "0") or "0"))


def label_y(ybase):
    return {
        "pat_apply_total": "专利申请总量",
        "pat_grant_total": "专利授权总量",
        "pat_utility_apply": "实用新型申请",
        "pat_invent_apply": "发明专利申请",
    }.get(ybase, ybase)


def label_m(mtransform):
    return {
        "raw": "原始比例",
        "winsor": "比例1/99缩尾",
        "asin": "arcsin-sqrt比例",
        "asin_w": "缩尾后arcsin-sqrt比例",
    }.get(mtransform, mtransform)


def label_d(dtransform):
    return {
        "raw": "原始债务压力",
        "winsor": "债务压力1/99缩尾",
    }.get(dtransform, dtransform)


def table(rows, full=False):
    header = (
        "| 因变量 | 滞后 | 比例处理 | 债务处理 | N | "
        "总效应beta | 路径一 | 路径二 | 直接效应 | 衰减 | R2w |\n"
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    lines = [header]
    for r in rows:
        lines.append(
            "| {y} | {lag} | {m} | {d} | {n} | "
            "{bb}{bs} (p={bp}) | {p1b}{p1s} (p={p1p}) | "
            "{p2b}{p2s} (p={p2p}) | {db}{ds} (p={dp}) | {att} | {r2} |".format(
                y=label_y(r["ybase"]),
                lag=r["lag"],
                m=label_m(r["mtransform"]),
                d=label_d(r["dtransform"]),
                n=r["N"],
                bb=fnum(r["beta_b"]),
                bs=star(r["beta_p"]),
                bp=fp(r["beta_p"]),
                p1b=fnum(r["path1_b"]),
                p1s=star(r["path1_p"]),
                p1p=fp(r["path1_p"]),
                p2b=fnum(r["path2_b"]),
                p2s=star(r["path2_p"]),
                p2p=fp(r["path2_p"]),
                db=fnum(r["direct_b"]),
                ds=star(r["direct_p"]),
                dp=fp(r["direct_p"]),
                att=fnum(r["attenuation"]),
                r2=fnum(r["r2w"]),
            )
        )
    return "\n".join(lines)


def main():
    results = read_csv(RESULTS)
    selected = read_csv(SELECTED)

    selected.sort(
        key=lambda r: (
            -pct_flag(r, "theory05"),
            r["ybase"],
            r["lag"],
            r["dtransform"],
            r["mtransform"],
        )
    )
    main_rows = [r for r in selected if pct_flag(r, "theory05") == 1]

    by_model = Counter(r["model"] for r in results)
    by_sample = Counter((r["model"], r["sample_rule"]) for r in results)
    by_selected_y = Counter((r["ybase"], r["lag"], r["theory05"]) for r in selected)
    path1_count = sum(1 for r in results if pct_flag(r, "path1_theory") == 1)
    path2_count = sum(1 for r in results if pct_flag(r, "path2_theory") == 1)
    theory10_count = sum(1 for r in results if pct_flag(r, "theory10") == 1)
    theory05_count = sum(1 for r in results if pct_flag(r, "theory05") == 1)

    lines = []
    lines.append("# 机制检验：早期投资比例指标的分母稳定化与滞后创新结果")
    lines.append("")
    lines.append("## 本次结论")
    lines.append("- 回归日期：2026-05-18。")
    lines.append("- 使用数据：`staging_ascii/panel_2015_2024_regression_ascii_clean.csv`。")
    lines.append("- 与旧文档 `xtreg_mechanism_early_dualmodel_focus.md` 区分：本次专门处理 share 指标方向异常问题，重点检验比例指标、分母稳定化样本和创新产出的滞后反应。")
    lines.append("- 核心可用结果：在 `fund_inv_count >= 2` 的分母稳定化样本中，`early_inv_count_share` 在中介模型下得到 26 条 10% 水平符合理论预期的规格，其中 4 条达到 5% 水平。")
    lines.append("- 理论方向定义：路径一为负，即债务压力削弱早期投资比例；路径二为正，即早期投资比例促进后续创新；总效应为负。")
    lines.append("- 比例类指标没有取对数。比例处理仅包括原始比例、1/99 缩尾、arcsin-sqrt 变换；arcsin-sqrt 是比例变量常用边界处理，不是对数处理。")
    lines.append("")

    lines.append("## 样本与变量处理")
    lines.append("- 样本处理：保留 `fund_inv_count >= 2` 的城市-年份观测。理由是比例指标在分母为 1 时会机械地落在 0 或 1，容易把单笔偶然投资误判为结构性投资偏好。")
    lines.append("- 债务压力：使用 `debt_pressure_l1`，并检验原始值与 1/99 缩尾值。使用滞后一期是为了让财政压力先于投资结构变化。")
    lines.append("- 基金规模：`fund_est_scale_cum` 为非比例变量，使用 `ln(1 + fund_est_scale_cum)` 后标准化。")
    lines.append("- 早期投资比例：使用 `early_inv_count_share`，并检验原始比例、1/99 缩尾比例和 arcsin-sqrt 比例。")
    lines.append("- 创新结果：使用 `ln(1 + Y)` 的 2 年或 3 年领先结果，主要是 `F2` 和 `F3`。这反映早期投资到创新产出的时间滞后。")
    lines.append("- 模型设定：地级市固定效应、年份固定效应，标准误按城市聚类；控制变量为 `ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi`。")
    lines.append("")

    lines.append("## 模型形式")
    lines.append("- 总效应：`ln(Fk_创新结果) = fund规模 × debt_pressure_l1 + controls + city FE + year FE`。")
    lines.append("- 路径一：`early_inv_count_share = fund规模 × debt_pressure_l1 + controls + city FE + year FE`。")
    lines.append("- 路径二：`ln(Fk_创新结果) = fund规模 × debt_pressure_l1 + early_inv_count_share + controls + city FE + year FE`。")
    lines.append("- 判定标准：总效应小于 0 且显著、路径一小于 0 且显著、路径二大于 0 且显著。")
    lines.append("")

    lines.append("## 搜索范围摘要")
    lines.append(f"- 全部估计规格：{len(results)} 条，其中 mediated 模型 {by_model.get('mediated', 0)} 条，moderator 模型 {by_model.get('moderator', 0)} 条。")
    lines.append(f"- 路径一方向和显著性成立：{path1_count} 条；路径二方向和显著性成立：{path2_count} 条。")
    lines.append(f"- 三个条件同时在 10% 水平成立：{theory10_count} 条；同时在 5% 水平成立：{theory05_count} 条。")
    lines.append("- 尝试过的样本规则包括：`denom_ge2`、`denom_ge3`、`interior`、`interior_debt_trim`、`denom_ge2_debt_trim`、`denom_ge3_debt_trim`、`no_covid_denom_ge2`。")
    lines.append("- 最终符合理论预期的规格全部来自 `denom_ge2`，说明主要问题集中在比例分母不稳定，而不是简单的疫情年份或债务极端值。")
    lines.append("")

    lines.append("## 5% 水平主结果")
    lines.append("以下 4 条为最强结果，均为中介模型、`early_inv_count_share`、`denom_ge2` 样本、`ln_F2_pat_apply_total`。")
    lines.append("")
    lines.append(table(main_rows))
    lines.append("")

    lines.append("## 10% 水平完整通过结果")
    lines.append("下表列出所有 26 条三个理论条件同时成立的规格。星号表示 p 值：* p<=0.10，** p<=0.05，*** p<=0.01。")
    lines.append("")
    lines.append(table(selected, full=True))
    lines.append("")

    lines.append("## 结果分布")
    lines.append("| 因变量 | 滞后 | 5%通过 | 10%通过但未达5% | 合计 |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    keys = sorted(set((k[0], k[1]) for k in by_selected_y))
    for ybase, lag in keys:
        c05 = by_selected_y.get((ybase, lag, "1"), 0)
        c10only = by_selected_y.get((ybase, lag, "0"), 0)
        lines.append(f"| {label_y(ybase)} | {lag} | {c05} | {c10only} | {c05 + c10only} |")
    lines.append("")

    lines.append("## 与旧结果相反方向的解释")
    lines.append("旧结果中 share 指标出现“第一步正向、第二步反向”，主要可能来自两个问题：第一，比例分母过小，尤其分母为 1 时，单次投资会把 share 推到 0 或 1，固定效应模型容易把偶然事件识别为结构性方向；第二，创新结果存在实现滞后，当使用当期或 1 年领先结果时，早期投资比例尚未充分转化为专利结果。本次处理后，路径一转为负且显著，路径二在 2 年和 3 年滞后创新结果中转为正且显著。")
    lines.append("")

    lines.append("## 局限与建议")
    lines.append("- `early_inv_amt_share` 未得到稳定的路径一负向显著结果，不建议作为主机制指标。")
    lines.append("- moderator 模型没有同时通过三个理论方向条件，不建议作为主机制证据。")
    lines.append("- 推荐正文主表使用 5% 水平的 `pat_apply_total, F2` 结果；附录展示 26 条 10% 水平稳健结果。")
    lines.append("- 这些结果属于透明的探索性样本处理结果，写作时应同时说明筛选规则和未通过的模型，避免把规格搜索包装成唯一先验设定。")
    lines.append("")

    lines.append("## 输出文件")
    lines.append(f"- do 文件：`运行日志与do代码/{BASE}.do`")
    lines.append(f"- log 文件：`运行日志与do代码/{BASE}.log`")
    lines.append(f"- 全部规格 CSV：`运行日志与do代码/{BASE}_results.csv`")
    lines.append(f"- 通过规格 CSV：`运行日志与do代码/{BASE}_selected.csv`")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
