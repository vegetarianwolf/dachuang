from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
RUN_DIR = ROOT.parent / "运行日志与do代码"
BASE_CSV = RUN_DIR / "xtreg_fe_moderation_fiscal_debt_combo_ascii_results.csv"
MECH_CSV = RUN_DIR / "xtreg_mechanism_dualmodel_focus_ascii_results.csv"
OUT_MD = ROOT / "README_符合理论预期的机制结果筛选.md"


def f(value: str | None) -> float | None:
    text = (value or "").strip()
    if not text:
        return None
    return float(text)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fobj:
        return list(csv.DictReader(fobj))


def sign_ok(val: float | None, expected: str) -> bool:
    if val is None:
        return False
    if expected == "pos":
        return val > 0
    if expected == "neg":
        return val < 0
    return False


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

    theory_map = {
        "early": {"debt_to_m": "neg", "m_to_y": "pos"},
        "fc": {"debt_to_m": "pos", "m_to_y": "neg"},
    }

    soccap_positive = {
        "soccap_fund_count",
        "soccap_amt",
        "gp_amt",
        "fund_commit_total",
        "matched_commit_amt",
        "soccap_share_total",
        "soccap_leverage",
        "matched_share_total",
    }
    soccap_inverse = {
        "gov_amt",
        "gov_share_total",
    }

    mediated_ok: list[dict] = []
    moderator_ok: list[dict] = []
    soccap_inverse_hits: list[dict] = []

    for row in mech:
        if row["xvar"] != "fund_est_scale_cum":
            continue
        key = (row["yvar"], row["dvar"], row["spec"])
        if key not in base_map:
            continue

        cat = row["category"]
        mvar = row["mvar"]

        if cat == "soccap":
            if mvar in soccap_positive:
                debt_sign = "neg"
                y_sign = "pos"
                soccap_mode = "positive"
            elif mvar in soccap_inverse:
                debt_sign = "pos"
                y_sign = "neg"
                soccap_mode = "inverse"
            else:
                continue
        else:
            if cat not in theory_map:
                continue
            debt_sign = theory_map[cat]["debt_to_m"]
            y_sign = theory_map[cat]["m_to_y"]
            soccap_mode = ""

        if row["model_family"] == "mediated" and row["step"] == "Y_eq":
            m_eq = next(
                (
                    item
                    for item in mech
                    if item["model_family"] == "mediated"
                    and item["step"] == "M_eq"
                    and item["spec"] == row["spec"]
                    and item["dvar"] == row["dvar"]
                    and item["mvar"] == mvar
                    and item["xvar"] == row["xvar"]
                ),
                None,
            )
            if m_eq is None:
                continue
            a3_b = f(m_eq["b1"])
            a3_p = f(m_eq["p1"])
            c3_b = f(row["b1"])
            c3_p = f(row["p1"])
            c4_b = f(row["b2"])
            c4_p = f(row["p2"])
            if None in (a3_b, a3_p, c3_b, c3_p, c4_b, c4_p):
                continue
            if a3_p < 0.1 and c4_p < 0.1 and abs(c3_b) < abs(base_map[key]["bint"]):
                if sign_ok(a3_b, debt_sign) and sign_ok(c4_b, y_sign):
                    item = {
                        "category": cat,
                        "mvar": mvar,
                        "spec": row["spec"],
                        "yvar": row["yvar"],
                        "dvar": row["dvar"],
                        "base_b": base_map[key]["bint"],
                        "base_p": base_map[key]["pint"],
                        "a3_b": a3_b,
                        "a3_p": a3_p,
                        "c3_b": c3_b,
                        "c3_p": c3_p,
                        "c4_b": c4_b,
                        "c4_p": c4_p,
                        "mainly": c3_p >= 0.1,
                        "soccap_mode": soccap_mode,
                    }
                    if cat == "soccap" and soccap_mode == "inverse":
                        soccap_inverse_hits.append({"model": "mediated", **item})
                    else:
                        mediated_ok.append(item)

        if row["model_family"] == "moderator" and row["step"] == "Y_eq":
            m_eq = next(
                (
                    item
                    for item in mech
                    if item["model_family"] == "moderator"
                    and item["step"] == "M_eq"
                    and item["spec"] == row["spec"]
                    and item["dvar"] == row["dvar"]
                    and item["mvar"] == mvar
                    and item["xvar"] == row["xvar"]
                ),
                None,
            )
            if m_eq is None:
                continue
            d2_b = f(m_eq["b1"])
            d2_p = f(m_eq["p1"])
            e3_b = f(row["b1"])
            e3_p = f(row["p1"])
            e4_b = f(row["b2"])
            e4_p = f(row["p2"])
            e5_b = f(row["b3"])
            e5_p = f(row["p3"])
            if None in (d2_b, d2_p, e3_b, e3_p, e5_b, e5_p):
                continue
            if d2_p < 0.1 and e5_p < 0.1 and abs(e3_b) < abs(base_map[key]["bint"]):
                if sign_ok(d2_b, debt_sign) and sign_ok(e5_b, y_sign):
                    item = {
                        "category": cat,
                        "mvar": mvar,
                        "spec": row["spec"],
                        "yvar": row["yvar"],
                        "dvar": row["dvar"],
                        "base_b": base_map[key]["bint"],
                        "base_p": base_map[key]["pint"],
                        "d2_b": d2_b,
                        "d2_p": d2_p,
                        "e3_b": e3_b,
                        "e3_p": e3_p,
                        "e4_b": e4_b,
                        "e4_p": e4_p,
                        "e5_b": e5_b,
                        "e5_p": e5_p,
                        "mainly": e3_p >= 0.1,
                        "soccap_mode": soccap_mode,
                    }
                    if cat == "soccap" and soccap_mode == "inverse":
                        soccap_inverse_hits.append({"model": "moderator", **item})
                    else:
                        moderator_ok.append(item)

    cat_name = {"early": "早期投资", "soccap": "社会资本撬动效率", "fc": "融资约束"}

    lines: list[str] = []
    lines.append("# 符合理论预期的机制结果筛选")
    lines.append("")
    lines.append("## 理论方向标准")
    lines.append("- 早期投资：债务作用方向预期为负；早期投资对基金促进创新的作用预期为正。")
    lines.append("- 社会资本撬动效率：债务作用方向预期为负；撬动效率对基金促进创新的作用预期为正。")
    lines.append("- 融资约束（KZ）：债务作用方向预期为正；KZ 对基金促进创新的作用预期为负。")
    lines.append("- 对于 `gov_amt`、`gov_share_total`，由于它们更接近“政府出资比重/规模”的逆向指标，不直接当作正向效率指标纳入主筛选，只在文末单独备注。")
    lines.append("")
    lines.append("## 主筛选结果概览")
    lines.append(f"- 符合理论预期的方案一结果数：`{len(mediated_ok)}`")
    lines.append(f"- 符合理论预期的方案二结果数：`{len(moderator_ok)}`")
    lines.append("")

    lines.append("## 方案一：机制变量作为中介变量")
    if not mediated_ok:
        lines.append("没有结果同时满足“显著性条件 + 理论方向条件”。")
    else:
        for cat in ("early", "soccap", "fc"):
            sub = [x for x in mediated_ok if x["category"] == cat]
            if not sub:
                continue
            lines.append(f"### {cat_name[cat]}")
            for item in sub:
                verdict = "主要通过 M 传导" if item["mainly"] else "部分通过 M 传导"
                lines.append(f"- `{item['mvar']}` | `{item['yvar']}` | `{item['dvar']}` | `{item['spec']}`")
                lines.append(f"  - `beta3={item['base_b']:.10g}`，`p={item['base_p']:.4g}`")
                lines.append(f"  - `a3={item['a3_b']:.10g}`，`p={item['a3_p']:.4g}`")
                lines.append(f"  - `c3={item['c3_b']:.10g}`，`p={item['c3_p']:.4g}`")
                lines.append(f"  - `c4={item['c4_b']:.10g}`，`p={item['c4_p']:.4g}`")
                lines.append(f"  - 判定：{verdict}")
            lines.append("")

    lines.append("## 方案二：机制变量作为调节变量")
    if not moderator_ok:
        lines.append("没有结果同时满足“显著性条件 + 理论方向条件”。")
    else:
        for cat in ("early", "soccap", "fc"):
            sub = [x for x in moderator_ok if x["category"] == cat]
            if not sub:
                continue
            lines.append(f"### {cat_name[cat]}")
            for item in sub:
                verdict = "主要通过 M 这种调节机制体现" if item["mainly"] else "部分通过 M 这种调节机制体现"
                lines.append(f"- `{item['mvar']}` | `{item['yvar']}` | `{item['dvar']}` | `{item['spec']}`")
                lines.append(f"  - `beta3={item['base_b']:.10g}`，`p={item['base_p']:.4g}`")
                lines.append(f"  - `d2={item['d2_b']:.10g}`，`p={item['d2_p']:.4g}`")
                lines.append(f"  - `e3={item['e3_b']:.10g}`，`p={item['e3_p']:.4g}`")
                if item["e4_b"] is not None and item["e4_p"] is not None:
                    lines.append(f"  - `e4={item['e4_b']:.10g}`，`p={item['e4_p']:.4g}`")
                lines.append(f"  - `e5={item['e5_b']:.10g}`，`p={item['e5_p']:.4g}`")
                lines.append(f"  - 判定：{verdict}")
            lines.append("")

    lines.append("## 关于社会资本变量的备注")
    lines.append("- 按照“效率越高越好”的正向指标理解，本轮主筛选中社会资本变量没有留下结果。")
    lines.append("- 若把 `gov_amt`、`gov_share_total` 理解为效率的逆向指标，则需要使用相反的方向标准。")
    lines.append("- 但即便按逆向指标处理，本轮结果也不足以得出稳定结论，因此不作为主筛选结果写入。")
    lines.append("")
    if soccap_inverse_hits:
        lines.append("### 逆向指标下的社会资本结果（仅供参考）")
        for item in soccap_inverse_hits:
            if item["model"] == "mediated":
                lines.append(f"- `{item['mvar']}` | `{item['yvar']}` | `{item['dvar']}` | `{item['spec']}` | `a3={item['a3_b']:.10g}` (`p={item['a3_p']:.4g}`), `c4={item['c4_b']:.10g}` (`p={item['c4_p']:.4g}`)")
            else:
                lines.append(f"- `{item['mvar']}` | `{item['yvar']}` | `{item['dvar']}` | `{item['spec']}` | `d2={item['d2_b']:.10g}` (`p={item['d2_p']:.4g}`), `e5={item['e5_b']:.10g}` (`p={item['e5_p']:.4g}`)")
        lines.append("")

    lines.append("## 简要结论")
    lines.append("- 早期投资：按你给定的方向标准，没有结果同时满足“显著 + 方向正确”。")
    lines.append("- 社会资本撬动效率：按正向效率指标理解，没有结果进入主筛选；`gov_amt` 等逆向指标也不足以支持稳定结论。")
    lines.append("- 融资约束：只有 `fcity_kz_mean` 在“机制变量作为调节变量”的设定下符合理论预期。")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"mediated_ok={len(mediated_ok)} moderator_ok={len(moderator_ok)} inverse_soccap={len(soccap_inverse_hits)}")
    print(OUT_MD.name)


if __name__ == "__main__":
    main()
