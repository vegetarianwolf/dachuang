# -*- coding: utf-8 -*-
"""
Run all regressions specified in 实证方案.md using panel_v3.csv.

Outputs:
- regression_v3/reg_results.csv (coefficient table)
- regression_v3/reg_results.dta (Stata-compatible)
- regression_v3/descriptive_stats.csv
"""

from __future__ import annotations

import csv
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

OUTDIR = Path(__file__).resolve().parent
PANEL = OUTDIR / "panel_v3.csv"


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(PANEL, encoding="utf-8-sig")
    # Convert numeric columns
    num_cols = [
        "ln_invg", "ln_umg", "ln_inva", "ln_total_grant", "inv_share",
        "fiscal_gap_L1", "ln_debt_ratio_L1",
        "ln_invest_amt_L1", "ln_invest_cnt_L1",
        "early_deal_ratio_L1", "early_amt_ratio_L1", "broad_early_ratio_L1",
        "ln_pgdp", "sec_ratio", "sci_ratio", "fdi_dep", "fin_depth", "ln_pop",
        "market_index", "fiscal_trans",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df["city_id"] = df["city_id"].astype(int)
    df["year"] = df["year"].astype(int)
    df = df.set_index(["city_id", "year"])
    return df


def run_panel_fe(df: pd.DataFrame, y_col: str, x_cols: list[str], label: str) -> dict:
    """Run two-way FE panel regression with clustered SE at city level."""
    cols = [y_col] + x_cols
    sub = df[cols].dropna()
    if len(sub) < 30:
        return {"label": label, "N": len(sub), "note": "too few obs"}

    y = sub[y_col]
    X = sub[x_cols]

    try:
        mod = PanelOLS(y, X, entity_effects=True, time_effects=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
    except Exception as e:
        return {"label": label, "N": len(sub), "note": str(e)[:100]}

    result = {"label": label, "N": int(res.nobs), "R2_within": round(res.rsquared_within, 4)}
    for var in x_cols:
        result[f"coef_{var}"] = round(res.params[var], 6)
        result[f"se_{var}"] = round(res.std_errors[var], 6)
        result[f"pval_{var}"] = round(res.pvalues[var], 6)
        pv = res.pvalues[var]
        stars = "***" if pv < 0.01 else "**" if pv < 0.05 else "*" if pv < 0.1 else ""
        result[f"stars_{var}"] = stars
    return result


def main():
    print("Loading panel...")
    df = load_panel()
    print(f"Panel shape: {df.shape}")

    # ====================================================================
    # Descriptive Statistics
    # ====================================================================
    print("\n=== Descriptive Statistics ===")
    desc_vars = [
        "ln_invg", "ln_umg", "ln_inva", "ln_total_grant", "inv_share",
        "fiscal_gap_L1", "ln_debt_ratio_L1",
        "ln_invest_amt_L1", "ln_invest_cnt_L1",
        "early_deal_ratio_L1", "broad_early_ratio_L1",
        "ln_pgdp", "sec_ratio", "sci_ratio", "fdi_dep", "fin_depth", "ln_pop",
        "market_index", "fiscal_trans",
    ]
    desc = df[desc_vars].describe().T
    desc["count"] = desc["count"].astype(int)
    desc.to_csv(OUTDIR / "descriptive_stats.csv", encoding="utf-8-sig")
    print(desc[["count", "mean", "std", "min", "max"]].to_string())

    # ====================================================================
    # H1 Baseline Regression: 6-column matrix
    # ====================================================================
    print("\n=== H1 Baseline Regressions ===")
    core_controls = ["ln_pgdp", "sec_ratio", "sci_ratio"]
    ext_controls = ["fdi_dep", "fin_depth", "ln_pop"]

    results = []

    # (1) fiscal_gap_L1, no controls
    results.append(run_panel_fe(df, "ln_invg", ["fiscal_gap_L1"], "H1-(1) FG, no ctrl"))
    # (2) fiscal_gap_L1, core controls
    results.append(run_panel_fe(df, "ln_invg", ["fiscal_gap_L1"] + core_controls, "H1-(2) FG, core"))
    # (3) fiscal_gap_L1, full controls
    results.append(run_panel_fe(df, "ln_invg", ["fiscal_gap_L1"] + core_controls + ext_controls, "H1-(3) FG, full"))
    # (4) ln_debt_ratio_L1, no controls
    results.append(run_panel_fe(df, "ln_invg", ["ln_debt_ratio_L1"], "H1-(4) DR, no ctrl"))
    # (5) ln_debt_ratio_L1, core controls
    results.append(run_panel_fe(df, "ln_invg", ["ln_debt_ratio_L1"] + core_controls, "H1-(5) DR, core"))
    # (6) ln_debt_ratio_L1, full controls
    results.append(run_panel_fe(df, "ln_invg", ["ln_debt_ratio_L1"] + core_controls + ext_controls, "H1-(6) DR, full"))

    for r in results:
        print(f"  {r['label']}: N={r.get('N','?')}, R2w={r.get('R2_within','?')}")
        for key in r:
            if key.startswith("coef_"):
                var = key.replace("coef_", "")
                print(f"    {var}: {r[key]} ({r.get(f'se_{var}','?')}) {r.get(f'stars_{var}','')}")

    # ====================================================================
    # H2 Mechanism: Two-step (X -> M)
    # ====================================================================
    print("\n=== H2 Mechanism: Fiscal Pressure -> Early Investment Ratio ===")

    # Two-step: X -> early_deal_ratio_L1
    results.append(run_panel_fe(df, "early_deal_ratio_L1", ["fiscal_gap_L1"] + core_controls, "H2-2step FG->early_deal"))
    results.append(run_panel_fe(df, "early_deal_ratio_L1", ["ln_debt_ratio_L1"] + core_controls, "H2-2step DR->early_deal"))

    # Interaction: X * M -> Y
    df_inter = df.copy()
    df_inter["FG_x_early"] = df_inter["fiscal_gap_L1"] * df_inter["early_deal_ratio_L1"]
    results.append(run_panel_fe(
        df_inter, "ln_invg",
        ["fiscal_gap_L1", "early_deal_ratio_L1", "FG_x_early"] + core_controls,
        "H2-interact FG*early->Y"
    ))

    df_inter["DR_x_early"] = df_inter["ln_debt_ratio_L1"] * df_inter["early_deal_ratio_L1"]
    results.append(run_panel_fe(
        df_inter, "ln_invg",
        ["ln_debt_ratio_L1", "early_deal_ratio_L1", "DR_x_early"] + core_controls,
        "H2-interact DR*early->Y"
    ))

    for r in results[-4:]:
        print(f"  {r['label']}: N={r.get('N','?')}, R2w={r.get('R2_within','?')}")

    # ====================================================================
    # H5 Mechanism: Fiscal Pressure -> Investment Amount
    # ====================================================================
    print("\n=== H5 Mechanism: Fiscal Pressure -> Investment Amount ===")

    results.append(run_panel_fe(df, "ln_invest_amt_L1", ["fiscal_gap_L1"] + core_controls, "H5-2step FG->invest_amt"))
    results.append(run_panel_fe(df, "ln_invest_amt_L1", ["ln_debt_ratio_L1"] + core_controls, "H5-2step DR->invest_amt"))

    df_inter["FG_x_amt"] = df_inter["fiscal_gap_L1"] * df_inter["ln_invest_amt_L1"]
    results.append(run_panel_fe(
        df_inter, "ln_invg",
        ["fiscal_gap_L1", "ln_invest_amt_L1", "FG_x_amt"] + core_controls,
        "H5-interact FG*amt->Y"
    ))

    df_inter["DR_x_amt"] = df_inter["ln_debt_ratio_L1"] * df_inter["ln_invest_amt_L1"]
    results.append(run_panel_fe(
        df_inter, "ln_invg",
        ["ln_debt_ratio_L1", "ln_invest_amt_L1", "DR_x_amt"] + core_controls,
        "H5-interact DR*amt->Y"
    ))

    for r in results[-4:]:
        print(f"  {r['label']}: N={r.get('N','?')}, R2w={r.get('R2_within','?')}")

    # ====================================================================
    # Save all results
    # ====================================================================
    print("\nSaving results...")
    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    all_keys = sorted(all_keys)

    with (OUTDIR / "reg_results.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)

    # Save as Stata .dta
    try:
        res_df = pd.DataFrame(results)
        res_df.to_stata(OUTDIR / "reg_results.dta", write_index=False, version=118)
        print(f"Stata file saved: {OUTDIR / 'reg_results.dta'}")
    except Exception as e:
        print(f"Could not save .dta: {e}")

    # Also export the panel itself as .dta for Stata use
    try:
        panel_export = df.reset_index()
        # Encode string columns for Stata
        for col in ["city", "province", "region"]:
            if col in panel_export.columns:
                panel_export[col] = panel_export[col].astype(str)
        panel_export.to_stata(OUTDIR / "panel_v3.dta", write_index=False, version=118)
        print(f"Panel .dta saved: {OUTDIR / 'panel_v3.dta'}")
    except Exception as e:
        print(f"Could not save panel .dta: {e}")

    print("\n=== All regressions complete ===")
    print(f"Results: {OUTDIR / 'reg_results.csv'}")

    # Print summary table
    print("\n" + "=" * 80)
    print("REGRESSION RESULTS SUMMARY")
    print("=" * 80)
    for r in results:
        lbl = r.get("label", "?")
        n = r.get("N", "?")
        r2 = r.get("R2_within", "?")
        note = r.get("note", "")
        if note:
            print(f"{lbl:45s}  N={n:>6}  {note}")
            continue
        line = f"{lbl:45s}  N={n:>6}  R2w={r2}"
        coef_parts = []
        for key in sorted(r.keys()):
            if key.startswith("coef_"):
                var = key.replace("coef_", "")
                coef_parts.append(f"{var}={r[key]}{r.get(f'stars_{var}','')}")
        if coef_parts:
            line += "  " + ", ".join(coef_parts)
        print(line)


if __name__ == "__main__":
    main()
