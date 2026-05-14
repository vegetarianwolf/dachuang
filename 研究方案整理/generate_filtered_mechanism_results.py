from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
RUN_DIR = ROOT.parent / "运行日志与do代码"
BASE_CSV = RUN_DIR / "xtreg_fe_moderation_fiscal_debt_combo_ascii_results.csv"
MECH_CSV = RUN_DIR / "xtreg_mechanism_dualmodel_focus_ascii_results.csv"
OUT_MD = ROOT / "README_按建模说明筛选后的机制结果.md"


def f(value: str | None) -> float | None:
    text = (value or "").strip()
    if not text:
        return None
    return float(text)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fobj:
        return list(csv.DictReader(fobj))


def main() -> None:
    base = load_csv(BASE_CSV)
    mech = load_csv(MECH_CSV)

    base_map: dict[tuple[str, str, str], dict[str, float]] = {}
    for row in base:
        if row["xvar"] == "fund_est_scale_cum" and row["mvar"] in ("debt_pressure", "debt_pressure_l1"):
            base_map[(row["yvar"], row["mvar"], row["spec"])] = {
                "bint": float(row["bint"]),
                "pint": float(row["pint"]),
            }

    mediated: list[dict] = []
    moderator: list[dict] = []

    for row in mech:
        if row["xvar"] != "fund_est_scale_cum":
            continue

        if row["model_family"] == "mediated" and row["step"] == "Y_eq":
            key = (row["yvar"], row["dvar"], row["spec"])
            if key not in base_map:
                continue
            m_eq = next(
                (
                    item
                    for item in mech
                    if item["model_family"] == "mediated"
                    and item["step"] == "M_eq"
                    and item["spec"] == row["spec"]
                    and item["dvar"] == row["dvar"]
                    and item["mvar"] == row["mvar"]
                    and item["xvar"] == row["xvar"]
                ),
                None,
            )
            if m_eq is None:
                continue

            a3_p = f(m_eq["p1"])
            c3_p = f(row["p1"])
            c4_p = f(row["p2"])
            if a3_p is None or c4_p is None:
                continue
            if a3_p < 0.1 and c4_p < 0.1:
                beta3_abs = abs(base_map[key]["bint"])
                c3_abs = abs(float(row["b1"]))
                if c3_abs < beta3_abs:
                    mediated.append(
                        {
                            "category": row["category"],
                            "mvar": row["mvar"],
                            "spec": row["spec"],
                            "yvar": row["yvar"],
                            "dvar": row["dvar"],
                            "base_b": base_map[key]["bint"],
                            "base_p": base_map[key]["pint"],
                            "a3_b": float(m_eq["b1"]),
                            "a3_p": a3_p,
                            "c3_b": float(row["b1"]),
                            "c3_p": c3_p,
                            "c4_b": float(row["b2"]),
                            "c4_p": c4_p,
                            "weaken": beta3_abs - c3_abs,
                            "mainly": (c3_p is not None and c3_p >= 0.1),
                        }
                    )

        if row["model_family"] == "moderator" and row["step"] == "Y_eq":
            key = (row["yvar"], row["dvar"], row["spec"])
            if key not in base_map:
                continue
            m_eq = next(
                (
                    item
                    for item in mech
                    if item["model_family"] == "moderator"
                    and item["step"] == "M_eq"
                    and item["spec"] == row["spec"]
                    and item["dvar"] == row["dvar"]
                    and item["mvar"] == row["mvar"]
                    and item["xvar"] == row["xvar"]
                ),
                None,
            )
            if m_eq is None:
                continue

            d2_p = f(m_eq["p1"])
            e3_p = f(row["p1"])
            e4_p = f(row["p2"])
            e5_p = f(row["p3"])
            if d2_p is None or e5_p is None:
                continue
            if d2_p < 0.1 and e5_p < 0.1:
                beta3_abs = abs(base_map[key]["bint"])
                e3_abs = abs(float(row["b1"]))
                if e3_abs < beta3_abs:
                    moderator.append(
                        {
                            "category": row["category"],
                            "mvar": row["mvar"],
                            "spec": row["spec"],
                            "yvar": row["yvar"],
                            "dvar": row["dvar"],
                            "base_b": base_map[key]["bint"],
                            "base_p": base_map[key]["pint"],
                            "d2_b": float(m_eq["b1"]),
                            "d2_p": d2_p,
                            "e3_b": float(row["b1"]),
                            "e3_p": e3_p,
                            "e4_b": float(row["b2"]) if (row["b2"] or "").strip() else None,
                            "e4_p": e4_p,
                            "e5_b": float(row["b3"]),
                            "e5_p": e5_p,
                            "weaken": beta3_abs - e3_abs,
                            "mainly": (e3_p is not None and e3_p >= 0.1),
                        }
                    )

    mediated.sort(key=lambda x: (x["category"], -x["weaken"], x["mvar"], x["yvar"], x["dvar"], x["spec"]))
    moderator.sort(key=lambda x: (x["category"], -x["weaken"], x["mvar"], x["yvar"], x["dvar"], x["spec"]))

    cat_name = {"early": "早期投资", "soccap": "社会资本撬动效率", "fc": "融资约束"}

    lines: list[str] = []
    lines.append("# 按建模说明筛选后的机制结果")
    lines.append("")
    lines.append("## 筛选标准")
    lines.append("- 方案一：中介传导模型，要求 `a3` 显著、`c4` 显著，且加入 `M` 后 `|c3| < |beta3|`。")
    lines.append("- 方案二：调节变量模型，要求 `d2` 显著、`e5` 显著，且加入 `X × M` 后 `|e3| < |beta3|`。")
    lines.append("- 基准调节项 `beta3` 来自既有的 `fund_est_scale_cum × debt_pressure / debt_pressure_l1` 调节效应回归。")
    lines.append("")
    lines.append("## 筛选结果概览")
    lines.append(f"- 符合方案一的结果数：`{len(mediated)}`")
    lines.append(f"- 符合方案二的结果数：`{len(moderator)}`")
    lines.append("")

    lines.append("## 方案一：机制变量作为中介变量")
    if not mediated:
        lines.append("没有组合同时满足 `a3` 显著、`c4` 显著且 `|c3| < |beta3|`。")
    else:
        for category in ("early", "soccap", "fc"):
            sub = [item for item in mediated if item["category"] == category]
            if not sub:
                continue
            lines.append(f"### {cat_name[category]}")
            for item in sub:
                verdict = "主要通过 M 传导" if item["mainly"] else "部分通过 M 传导"
                lines.append(f"- `{item['mvar']}` | `{item['yvar']}` | `{item['dvar']}` | `{item['spec']}`")
                lines.append(f"  - 基准调节项 `beta3={item['base_b']:.10g}`，`p={item['base_p']:.4g}`")
                lines.append(f"  - 机制方程 `a3={item['a3_b']:.10g}`，`p={item['a3_p']:.4g}`")
                lines.append(f"  - 结果方程 `c3={item['c3_b']:.10g}`，`p={item['c3_p']:.4g}`")
                lines.append(f"  - 结果方程 `c4={item['c4_b']:.10g}`，`p={item['c4_p']:.4g}`")
                lines.append(f"  - 判定：{verdict}；`|beta3|-|c3|={item['weaken']:.10g}`")
            lines.append("")

    lines.append("## 方案二：机制变量作为调节变量")
    if not moderator:
        lines.append("没有组合同时满足 `d2` 显著、`e5` 显著且 `|e3| < |beta3|`。")
    else:
        for category in ("early", "soccap", "fc"):
            sub = [item for item in moderator if item["category"] == category]
            if not sub:
                continue
            lines.append(f"### {cat_name[category]}")
            for item in sub:
                verdict = "主要通过 M 这种调节机制体现" if item["mainly"] else "部分通过 M 这种调节机制体现"
                lines.append(f"- `{item['mvar']}` | `{item['yvar']}` | `{item['dvar']}` | `{item['spec']}`")
                lines.append(f"  - 基准调节项 `beta3={item['base_b']:.10g}`，`p={item['base_p']:.4g}`")
                lines.append(f"  - 机制方程 `d2={item['d2_b']:.10g}`，`p={item['d2_p']:.4g}`")
                lines.append(f"  - 结果方程 `e3={item['e3_b']:.10g}`，`p={item['e3_p']:.4g}`")
                if item["e4_b"] is not None and item["e4_p"] is not None:
                    lines.append(f"  - 结果方程 `e4={item['e4_b']:.10g}`，`p={item['e4_p']:.4g}`")
                lines.append(f"  - 结果方程 `e5={item['e5_b']:.10g}`，`p={item['e5_p']:.4g}`")
                lines.append(f"  - 判定：{verdict}；`|beta3|-|e3|={item['weaken']:.10g}`")
            lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"mediated={len(mediated)} moderator={len(moderator)}")
    print(OUT_MD.name)


if __name__ == "__main__":
    main()
