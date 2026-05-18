from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "dachuang"
RUN_DIR = PROJECT / "运行日志与do代码"
OUT_DIR = PROJECT / "实证结果"
BASENAME = "xtreg_mechanism_findev12_logfund_winsor_20260516"

RESULT_CSV = RUN_DIR / f"{BASENAME}_results.csv"
SELECTED_CSV = RUN_DIR / f"{BASENAME}_selected.csv"
DO_FILE = RUN_DIR / f"{BASENAME}.do"
LOG_FILE = RUN_DIR / f"{BASENAME}.log"
MD_FILE = OUT_DIR / f"{BASENAME}.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(value: str | float | int | None, digits: int = 4) -> str:
    if value in (None, ""):
        return "-"
    x = float(value)
    ax = abs(x)
    if ax != 0 and (ax < 0.0001 or ax >= 100000):
        return f"{x:.4e}"
    return f"{x:.{digits}f}"


def pval(value: str | float | int | None) -> str:
    if value in (None, ""):
        return "-"
    x = float(value)
    if x < 0.0001:
        return f"{x:.2e}"
    return f"{x:.4f}"


def stars(value: str | float | int | None) -> str:
    if value in (None, ""):
        return ""
    x = float(value)
    if x < 0.01:
        return "***"
    if x < 0.05:
        return "**"
    if x < 0.10:
        return "*"
    return ""


def attenuation(value: str | float | int | None) -> str:
    if value in (None, ""):
        return "-"
    return f"{float(value) * 100:.1f}%"


def zh_yrole(role: str) -> str:
    return {
        "invent": "发明申请量",
        "utility": "实用新型申请量",
        "total": "专利申请总量",
    }.get(role, role)


def zh_drole(role: str) -> str:
    return {"debt": "当期债务压力", "debt_l1": "滞后一期债务压力"}.get(role, role)


def zh_xform(role: str) -> str:
    return {
        "rawfund": "原始累计基金规模",
        "logfund": "对数累计基金规模",
        "logfund_winsor": "对数基金规模+1%/99%缩尾",
    }.get(role, role)


def zh_yform(role: str) -> str:
    return {
        "count": "原始计数",
        "logy": "创新产出对数",
        "wcount": "创新产出1%/99%缩尾计数",
    }.get(role, role)


def row_sig(row: dict[str, str]) -> str:
    return stars(row.get("p_xm"))


def table(rows: list[dict[str, str]], cols: list[tuple[str, str]]) -> list[str]:
    lines = []
    lines.append("| " + " | ".join(title for title, _ in cols) + " |")
    lines.append("| " + " | ".join("---" for _ in cols) + " |")
    for r in rows:
        vals = []
        for _, key in cols:
            if key == "yrole_zh":
                vals.append(zh_yrole(r["yrole"]))
            elif key == "drole_zh":
                vals.append(zh_drole(r["drole"]))
            elif key == "xform_zh":
                vals.append(zh_xform(r["xform"]))
            elif key == "yform_zh":
                vals.append(zh_yform(r["yform"]))
            elif key == "bd":
                vals.append(f"{num(r['b_d'])}{stars(r['p_d'])}")
            elif key == "pd":
                vals.append(pval(r["p_d"]))
            elif key == "base":
                vals.append(f"{num(r['b_base_xd'])}{stars(r['p_base_xd'])}")
            elif key == "pbase":
                vals.append(pval(r["p_base_xd"]))
            elif key == "after":
                vals.append(f"{num(r['b_xd'])}{stars(r['p_xd'])}")
            elif key == "pafter":
                vals.append(pval(r["p_xd"]))
            elif key == "bm":
                vals.append(f"{num(r['b_m'])}{stars(r['p_m'])}")
            elif key == "pm":
                vals.append(pval(r["p_m"]))
            elif key == "bxm":
                vals.append(f"{num(r['b_xm'])}{stars(r['p_xm'])}")
            elif key == "pxm":
                vals.append(pval(r["p_xm"]))
            elif key == "att":
                vals.append(attenuation(r["attenuation"]))
            elif key == "N":
                vals.append(str(int(float(r["N"]))) if r.get("N") else "-")
            else:
                vals.append(r.get(key, "-"))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def main() -> None:
    all_rows = read_csv(RESULT_CSV)
    selected = read_csv(SELECTED_CSV)

    selected_sorted = sorted(
        selected,
        key=lambda r: (
            r["spec"],
            r["xform"],
            r["findev"],
            r["yform"],
            r["yrole"],
            r["drole"],
            float(r["p_xm"]) if r.get("p_xm") else 9,
        ),
    )

    main_rows = [
        r
        for r in selected_sorted
        if r["spec"] == "ctrl"
        and r["xform"] == "logfund"
        and r["yform"] == "count"
        and r["findev"] == "fin_dev_1"
    ]
    main_rows = sorted(main_rows, key=lambda r: (r["yrole"], r["drole"]))

    robust_rows = [
        r
        for r in selected_sorted
        if r["spec"] == "ctrl"
        and r["findev"] == "fin_dev_1"
        and r["xform"] in {"logfund", "logfund_winsor"}
        and r["yform"] in {"wcount", "count"}
    ]
    robust_rows = sorted(
        robust_rows,
        key=lambda r: (
            0 if r["xform"] == "logfund" else 1,
            r["yform"],
            r["yrole"],
            r["drole"],
            float(r["p_xm"]) if r.get("p_xm") else 9,
        ),
    )

    group_counts: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
        lambda: {"total": 0, "pass10": 0, "pass05": 0}
    )
    for r in all_rows:
        key = (r["spec"], r["xform"], r["yform"], r["findev"])
        group_counts[key]["total"] += 1
        if r.get("pass10") == "1":
            group_counts[key]["pass10"] += 1
        if r.get("pass05") == "1":
            group_counts[key]["pass05"] += 1

    findev_pass = Counter(r["findev"] for r in selected)
    pass10 = sum(1 for r in all_rows if r.get("pass10") == "1")
    pass05 = sum(1 for r in all_rows if r.get("pass05") == "1")
    pass01 = sum(1 for r in all_rows if r.get("pass01") == "1")

    lines: list[str] = []
    lines.append("# 地级市金融发展水平机制检验：fin_dev_1/fin_dev_2 对数基金规模与缩尾稳健版")
    lines.append("")
    lines.append(f"日期：{date.today().isoformat()}")
    lines.append("")
    lines.append("## 1. 任务与结论")
    lines.append("")
    lines.append("本轮检验聚焦地级市金融发展水平是否能够解释财政债务压力对政府产业引导基金创新效应的调节作用。按照要求，机制变量只使用两个原始金融发展水平口径：")
    lines.append("")
    lines.append("- `fin_dev_1`：贷款余额 / GDP。")
    lines.append("- `fin_dev_2`：存款余额 / GDP。")
    lines.append("")
    lines.append("本轮与已有 `xtreg_mechanism_city_findev12_refined_20260516.md` 区分之处在于：正式主口径采用论文方案中建议的 `ln(1 + 累计基金规模)`，并补充 1%/99% 缩尾稳健性；不再把原始累计规模作为唯一主口径。所有连续核心变量在交互项中先做标准化，因此系数反映一标准差变化对应的边际关系。")
    lines.append("")
    lines.append(f"全量估计共 `{len(all_rows)}` 条路径。按 `D -> M` 显著、`X × M -> Y` 显著、且加入机制交互后原 `X × D` 绝对值下降这三条标准筛选，10% 水平通过 `{pass10}` 条，5% 水平通过 `{pass05}` 条，1% 水平通过 `{pass01}` 条。通过路径全部来自 `fin_dev_1`，`fin_dev_2` 没有形成完整机制链条。")
    lines.append("")
    lines.append("核心结论：在采用对数累计基金规模后，`fin_dev_1` 可以作为较清晰的金融发展调节机制。债务压力显著提高贷款/GDP口径的金融发展水平，而金融发展水平进一步正向调节基金规模对创新产出的边际作用；加入 `ln_fund × fin_dev_1` 后，原 `ln_fund × debt_pressure` 的绝对值明显下降。")
    lines.append("")
    lines.append("## 2. 数据、样本与模型")
    lines.append("")
    lines.append("- 数据文件：`staging_ascii/formal_2015_en.csv`，与 `面板数据/地级市总面板_2015_2024_英文版.csv` 内容一致。")
    lines.append("- 样本区间：2015-2024 年地级市面板；进入各模型的变量逐项非缺失筛选。")
    lines.append("- 固定效应：城市固定效应和年份固定效应。")
    lines.append("- 标准误：按城市聚类稳健标准误。")
    lines.append("- 控制变量：`ln_gdp`、`ln_fiscal_scitech`、`ln_pop`、`ln_secondary`、`ln_fdi`。")
    lines.append("- 核心解释变量：主口径为 `ln_fund = ln(fund_est_scale_cum + 1)`；同时保留原始累计基金规模与缩尾对数规模作为比较。")
    lines.append("")
    lines.append("机制变量作为调节传导变量时，估计：")
    lines.append("")
    lines.append("```text")
    lines.append("M_it = d0 + d1 X_it + d2 D_it + Controls_it + CityFE + YearFE + r_it")
    lines.append("Y_it = e0 + e1 X_it + e2 D_it + e3 X_it * D_it + e4 M_it + e5 X_it * M_it + Controls_it + CityFE + YearFE + w_it")
    lines.append("```")
    lines.append("")
    lines.append("判定标准：`d2` 显著、`e5` 显著，且加入 `X × M` 后 `X × D` 的绝对值较基准模型下降。")
    lines.append("")
    lines.append("## 3. 正式主路径")
    lines.append("")
    lines.append("主路径采用受控模型、对数累计基金规模、专利申请计数因变量。该设定最符合研究方案中对规模变量取对数的建议，也保留了城市和年份双固定效应以及城市聚类标准误。")
    lines.append("")
    cols = [
        ("创新产出", "yrole_zh"),
        ("债务口径", "drole_zh"),
        ("D -> fin_dev_1", "bd"),
        ("p(D)", "pd"),
        ("基准 X×D", "base"),
        ("p", "pbase"),
        ("加入机制后 X×D", "after"),
        ("p", "pafter"),
        ("X×fin_dev_1", "bxm"),
        ("p", "pxm"),
        ("削弱幅度", "att"),
        ("N", "N"),
    ]
    lines.extend(table(main_rows, cols))
    lines.append("")
    lines.append("解释：以滞后一期债务压力为例，`fin_dev_1` 的机制方程系数为 0.1390，p=1.55e-05；在结果方程中，`ln_fund × fin_dev_1` 对实用新型申请量显著为正，p=0.0307，对发明申请量和专利申请总量也在 10% 水平显著。加入金融发展机制交互后，原 `ln_fund × debt_pressure_l1` 的绝对值下降 42.8%-63.0%，说明贷款/GDP口径金融发展水平能够承接一部分债务压力的调节效应。")
    lines.append("")
    lines.append("## 4. 稳健性结果")
    lines.append("")
    lines.append("稳健性包括两类：其一，对创新产出计数做 1%/99% 缩尾；其二，对 `ln_fund`、债务压力和 `fin_dev_1` 同步做 1%/99% 缩尾后再标准化。")
    lines.append("")
    robust_cols = [
        ("X处理", "xform_zh"),
        ("Y处理", "yform_zh"),
        ("创新产出", "yrole_zh"),
        ("债务口径", "drole_zh"),
        ("D -> fin_dev_1", "bd"),
        ("p(D)", "pd"),
        ("X×fin_dev_1", "bxm"),
        ("p", "pxm"),
        ("削弱幅度", "att"),
        ("N", "N"),
    ]
    lines.extend(table(robust_rows, robust_cols))
    lines.append("")
    lines.append("稳健性表明，`fin_dev_1` 路径在缩尾计数因变量下更强，尤其是实用新型申请量和专利申请总量。缩尾后的对数基金规模设定中，多数结果仍在 10% 水平显著，部分在 5% 或 1% 水平显著。")
    lines.append("")
    lines.append("## 5. fin_dev_2 的判定")
    lines.append("")
    lines.append("`fin_dev_2` 的 `X × M` 在若干模型中可以显著，但债务压力对 `fin_dev_2` 本身并不显著，因此不满足完整机制判定。换言之，存款/GDP口径更适合作为金融环境边界条件的补充描述，不能写成“债务压力 -> 存款/GDP金融发展 -> 基金创新效应”的完整传导链条。")
    lines.append("")
    lines.append("通过路径按金融发展变量统计：")
    lines.append("")
    lines.append("| 机制变量 | 通过路径数 |")
    lines.append("| --- | ---: |")
    for k in ["fin_dev_1", "fin_dev_2"]:
        lines.append(f"| `{k}` | {findev_pass.get(k, 0)} |")
    lines.append("")
    lines.append("## 6. 写作建议")
    lines.append("")
    lines.append("建议将本轮结果写作如下：")
    lines.append("")
    lines.append("> 在地级市层面，债务压力会显著改变贷款余额/GDP口径的金融发展水平；金融发展水平越高，引导基金累计设立规模对创新产出的边际作用越强。采用 `ln(1 + 累计基金规模)` 并控制城市固定效应、年份固定效应及城市层面聚类标准误后，`ln_fund × fin_dev_1` 在实用新型申请量、发明申请量和专利申请总量上均呈现显著或边际显著的正向作用，且加入该机制交互后，原债务压力调节项明显减弱。这说明金融发展水平，尤其是贷款/GDP代表的金融供给环境，能够部分解释财政债务压力影响政府产业引导基金创新扶持效果的机制。")
    lines.append("")
    lines.append("需要谨慎说明两点：第一，该结论依赖于对高度右偏基金规模变量取对数，这是学术规范内的变量处理，也与研究方案建议一致；第二，`fin_dev_2` 未通过完整链条，只能作为补充边界条件，不能作为主机制。")
    lines.append("")
    lines.append("## 7. 输出文件")
    lines.append("")
    lines.append(f"- do 文件：`{DO_FILE.relative_to(PROJECT)}`")
    lines.append(f"- log 文件：`{LOG_FILE.relative_to(PROJECT)}`")
    lines.append(f"- 全量结果 CSV：`{RESULT_CSV.relative_to(PROJECT)}`")
    lines.append(f"- 筛选结果 CSV：`{SELECTED_CSV.relative_to(PROJECT)}`")
    lines.append(f"- 本文档：`{MD_FILE.relative_to(PROJECT)}`")
    lines.append("")
    lines.append("## 附录 A：通过筛选的全部路径")
    lines.append("")
    append_cols = [
        ("spec", "spec"),
        ("X处理", "xform_zh"),
        ("Y处理", "yform_zh"),
        ("Y", "yrole_zh"),
        ("债务", "drole_zh"),
        ("M", "findev"),
        ("D->M", "bd"),
        ("p(D)", "pd"),
        ("基准X×D", "base"),
        ("p", "pbase"),
        ("加入后X×D", "after"),
        ("p", "pafter"),
        ("M->Y", "bm"),
        ("p(M)", "pm"),
        ("X×M", "bxm"),
        ("p", "pxm"),
        ("削弱", "att"),
        ("N", "N"),
    ]
    lines.extend(table(selected_sorted, append_cols))
    lines.append("")
    lines.append("## 附录 B：模型组合通过情况")
    lines.append("")
    lines.append("| spec | X处理 | Y处理 | M | 估计路径 | 10%通过 | 5%通过 |")
    lines.append("| --- | --- | --- | --- | ---: | ---: | ---: |")
    for key, counts in sorted(group_counts.items()):
        spec, xform, yform, findev = key
        lines.append(
            f"| {spec} | {zh_xform(xform)} | {zh_yform(yform)} | `{findev}` | {counts['total']} | {counts['pass10']} | {counts['pass05']} |"
        )
    lines.append("")
    lines.append("## 附录 C：全量 216 条估计结果")
    lines.append("")
    all_cols = [
        ("spec", "spec"),
        ("X处理", "xform_zh"),
        ("Y处理", "yform_zh"),
        ("Y", "yrole_zh"),
        ("债务", "drole_zh"),
        ("M", "findev"),
        ("D->M", "bd"),
        ("p(D)", "pd"),
        ("基准X×D", "base"),
        ("p", "pbase"),
        ("加入后X×D", "after"),
        ("p", "pafter"),
        ("M->Y", "bm"),
        ("p(M)", "pm"),
        ("X×M", "bxm"),
        ("p", "pxm"),
        ("削弱", "att"),
        ("N", "N"),
    ]
    all_sorted = sorted(
        all_rows,
        key=lambda r: (
            r["spec"],
            r["xform"],
            r["findev"],
            r["yform"],
            r["yrole"],
            r["drole"],
        ),
    )
    lines.extend(table(all_sorted, all_cols))
    lines.append("")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MD_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
