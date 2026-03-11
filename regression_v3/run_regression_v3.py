"""
regression_v3/run_regression_v3.py
==================================
Re-run baseline + mediation regressions with corrected X and M variables.

Key changes from v2:
  X variable: fiscal_self_sufficiency (revenue/expenditure) instead of fiscal_gap
    - Expected sign: POSITIVE on innovation (more self-sufficient -> more innovation)
    - Also test transfer_dependency = 1 - self_sufficiency (expect NEGATIVE)
  M variables: Multiple expanded definitions with much better coverage
    - M_has_fund: extensive margin dummy (100% coverage)
    - M_log_count: log fund investment count (100% coverage)
    - M_early_dummy: early-stage investment dummy (100% coverage)
    - M_early_ratio_filled: early ratio with zeros for no-fund cities (100% coverage)
  IV: Leave-one-out provincial average for 2SLS
"""

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import os
import warnings
from datetime import datetime
from scipy import stats

warnings.filterwarnings("ignore")

try:
    from linearmodels.panel import PanelOLS
    from linearmodels.iv import IV2SLS
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "linearmodels"])
    from linearmodels.panel import PanelOLS
    from linearmodels.iv import IV2SLS

# =====================================================================
# CONFIG
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "cleaned_data",
                         "final_regression_panel_v5.csv")
OUTPUT_DIR = BASE_DIR
WINSOR = (0.01, 0.99)

# =====================================================================
# HELPERS
# =====================================================================

def sig(p):
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.1:  return "*"
    return ""


def winsorize(s, lo=0.01, hi=0.99):
    mask = s.notna()
    if mask.sum() < 20:
        return s
    ql, qh = s[mask].quantile(lo), s[mask].quantile(hi)
    out = s.copy()
    out.loc[mask] = s.loc[mask].clip(ql, qh)
    return out


def run_fe(panel, dep, indep, label=""):
    cols = [dep] + indep
    d = panel[cols].dropna()
    n = d.shape[0]
    n_ent = d.index.get_level_values(0).nunique()
    if n < 30:
        print(f"  [SKIP] {label}: N={n}")
        return None
    try:
        mod = PanelOLS(d[dep], d[indep],
                       entity_effects=True, time_effects=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
        print(f"  {label}: N={n} cities={n_ent} R2w={res.rsquared_within:.4f}")
        for v in indep:
            c, se, p = res.params[v], res.std_errors[v], res.pvalues[v]
            print(f"    {v}: b={c:.4f} se={se:.4f} p={p:.4f} {sig(p)}")
        return dict(res=res, n=n, n_ent=n_ent)
    except Exception as e:
        print(f"  [ERR] {label}: {e}")
        return None


def sobel(a, se_a, b, se_b):
    se_ab = np.sqrt(a**2 * se_b**2 + b**2 * se_a**2)
    z = (a * b) / se_ab if se_ab > 0 else np.nan
    p = 2 * (1 - stats.norm.cdf(abs(z))) if not np.isnan(z) else np.nan
    return dict(ab=a*b, se=se_ab, z=z, p=p)


def bootstrap_indirect(panel, dep, x_col, m_col, ctrls, n_boot=500, seed=42):
    cols = [dep, x_col, m_col] + ctrls
    d = panel[cols].dropna().copy()
    if d.shape[0] < 50:
        return None
    entities = d.index.get_level_values(0).unique().values
    n_ent = len(entities)
    rng = np.random.RandomState(seed)
    ie_list = []
    for _ in range(n_boot):
        boot_ent = rng.choice(entities, n_ent, replace=True)
        chunks = []
        for new_id, eid in enumerate(boot_ent):
            try:
                ch = d.loc[eid].copy()
                if isinstance(ch, pd.Series):
                    ch = ch.to_frame().T
                ch["_eid"] = new_id
                chunks.append(ch)
            except Exception:
                continue
        if len(chunks) < 10:
            continue
        bd = pd.concat(chunks, ignore_index=True)
        dm = {}
        for v in cols:
            dm[v] = bd[v] - bd.groupby("_eid")[v].transform("mean")
        dm = pd.DataFrame(dm)
        try:
            X_a = dm[[x_col] + ctrls].values
            y_a = dm[m_col].values
            ba = np.linalg.lstsq(X_a, y_a, rcond=None)[0]
            a = ba[0]
            X_b = dm[[x_col, m_col] + ctrls].values
            y_b = dm[dep].values
            bb = np.linalg.lstsq(X_b, y_b, rcond=None)[0]
            b = bb[1]
            ie_list.append(a * b)
        except Exception:
            continue
    if len(ie_list) < 100:
        return None
    ie = np.array(ie_list)
    ci_lo, ci_hi = np.percentile(ie, 2.5), np.percentile(ie, 97.5)
    return dict(mean=np.mean(ie), se=np.std(ie),
                ci_lo=ci_lo, ci_hi=ci_hi,
                sig=not (ci_lo <= 0 <= ci_hi),
                n_valid=len(ie))

# =====================================================================
# 1. LOAD & CLEAN
# =====================================================================
print("=" * 72)
print("1. Data Loading & Cleaning")
print("=" * 72)

df = pd.read_csv(DATA_PATH)
N0 = len(df)
print(f"Raw data: {N0} rows, {df.shape[1]} cols, "
      f"{df['城市'].nunique()} cities, {df['年份'].min()}-{df['年份'].max()}")

# Remove zero-patent observations
df = df[df["发明受理数"] > 0].copy()
print(f"Remove inv_patent=0: {N0} -> {len(df)}")

# Construct log debt ratio
df["ln_debt_l1"] = np.where(
    df["债务率_滞后一期"] > 0, np.log(df["债务率_滞后一期"]), np.nan)

# Rename to English
COL_MAP = {
    "发明专利受理量_对数": "ln_inv",
    "专利受理总量_对数":   "ln_patent",
    "发明专利占比":        "inv_share",
    "财政缺口率_滞后一期": "fiscal_gap_l1",
    "财政自给率_滞后一期": "selfsuff_l1",
    "转移支付依赖度_滞后一期": "transfer_dep_l1",
    "ln_debt_l1":          "ln_debt_l1",
    "人均GDP_对数":        "gdp_pc",
    "第二产业占比":        "ind2",
    "科技支出占比":        "tech_exp",
    "外资依存度":          "fdi",
    "金融深度":            "fin_depth",
    "M_has_fund_L1":       "M_has_fund",
    "M_log_count_L1":      "M_log_count",
    "M_log_amount_L1":     "M_log_amount",
    "M_early_dummy_L1":    "M_early_dum",
    "M_early_ratio_filled_L1": "M_early_filled",
    "M_early_ratio_L1":    "M_early_ratio",
    "IV_财政自给率_省内均值_滞后一期": "IV_selfsuff",
    "IV_财政缺口率_省内均值_滞后一期": "IV_gap",
}
df.rename(columns=COL_MAP, inplace=True)

# Winsorize continuous variables
winsor_vars = [
    "ln_inv", "ln_patent", "inv_share",
    "fiscal_gap_l1", "selfsuff_l1", "transfer_dep_l1", "ln_debt_l1",
    "gdp_pc", "ind2", "tech_exp", "fdi", "fin_depth",
    "M_log_count", "M_log_amount", "M_early_filled",
]
print(f"\nWinsorize ({WINSOR[0]*100:.0f}%/{WINSOR[1]*100:.0f}%):")
for v in winsor_vars:
    if v in df.columns:
        nn = df[v].notna().sum()
        if nn > 20:
            before = df[v].copy()
            df[v] = winsorize(df[v], *WINSOR)
            n_clip = (before != df[v]).sum()
            if n_clip > 0:
                print(f"  {v}: N={nn}, clipped {n_clip}")

# Remove fiscal_gap < 0
n2 = len(df)
df = df[~((df["fiscal_gap_l1"].notna()) & (df["fiscal_gap_l1"] < 0))].copy()
if len(df) < n2:
    print(f"Remove fiscal_gap<0: {n2} -> {len(df)}")

# Panel index
df["city_id"] = pd.Categorical(df["城市"]).codes
panel = df.set_index(["city_id", "年份"])
print(f"\nFinal sample: {len(df)} obs, {df['城市'].nunique()} cities")

CONTROLS_CORE = ["gdp_pc", "ind2", "tech_exp"]
CONTROLS_FULL = CONTROLS_CORE + ["fdi", "fin_depth"]

# =====================================================================
# 2. DESCRIPTIVE STATISTICS
# =====================================================================
print("\n" + "=" * 72)
print("2. Descriptive Statistics")
print("=" * 72)

desc_vars = {
    "ln_inv":         "Y: ln(inv_patent)",
    "ln_patent":      "Y: ln(patent_total)",
    "inv_share":      "Y: inv_patent_share",
    "selfsuff_l1":    "X: fiscal_self_sufficiency(L1)",
    "transfer_dep_l1":"X: transfer_dependency(L1)",
    "fiscal_gap_l1":  "X: fiscal_gap(L1)",
    "ln_debt_l1":     "X: ln(debt_ratio)(L1)",
    "M_has_fund":     "M: has_fund(L1)",
    "M_log_count":    "M: log_fund_count(L1)",
    "M_early_dum":    "M: early_dummy(L1)",
    "M_early_filled": "M: early_ratio_filled(L1)",
    "M_early_ratio":  "M: early_ratio(fund-only)(L1)",
}

desc_rows = []
for col, lab in desc_vars.items():
    if col not in df.columns:
        continue
    s = df[col].dropna()
    desc_rows.append(dict(label=lab, col=col, N=len(s),
                          miss=f"{(1-len(s)/len(df))*100:.1f}%",
                          mean=s.mean(), sd=s.std(),
                          p25=s.quantile(0.25), p50=s.median(), p75=s.quantile(0.75),
                          mn=s.min(), mx=s.max()))
    print(f"  {lab}: N={len(s)} mean={s.mean():.4f} sd={s.std():.4f}")

# =====================================================================
# 3. BASELINE REGRESSION (H1)
# =====================================================================
print("\n" + "=" * 72)
print("3. Baseline Regression (H1: Fiscal Constraint -> Innovation)")
print("=" * 72)

results = {}
dep_main = "ln_inv"

X_VARS = {
    "selfsuff":     "selfsuff_l1",
    "transfer_dep": "transfer_dep_l1",
    "fiscal_gap":   "fiscal_gap_l1",
    "ln_debt":      "ln_debt_l1",
}
DEP_VARS = {
    "ln_inv":      "ln_inv",
    "ln_patent":   "ln_patent",
    "inv_share":   "inv_share",
}

# 3a. No controls
print("\n--- 3a. No controls ---")
for xk, xc in X_VARS.items():
    for yk, yc in DEP_VARS.items():
        lab = f"[no_ctrl] {yk}~{xk}"
        r = run_fe(panel, yc, [xc], label=lab)
        if r:
            results[("base_nc", xk, yk)] = r

# 3b. Core controls
print("\n--- 3b. Core controls ---")
for xk, xc in X_VARS.items():
    for yk, yc in DEP_VARS.items():
        lab = f"[core] {yk}~{xk}"
        r = run_fe(panel, yc, [xc] + CONTROLS_CORE, label=lab)
        if r:
            results[("base_cc", xk, yk)] = r

# 3c. Full controls (main DV only)
print("\n--- 3c. Full controls ---")
for xk, xc in X_VARS.items():
    lab = f"[full] ln_inv~{xk}"
    r = run_fe(panel, dep_main, [xc] + CONTROLS_FULL, label=lab)
    if r:
        results[("base_fc", xk, "ln_inv")] = r

# =====================================================================
# 4. MEDIATION ANALYSIS (H2)
# =====================================================================
print("\n" + "=" * 72)
print("4. Mediation Analysis (H2: X -> M -> Y)")
print("=" * 72)

M_VARS = {
    "M_log_count":    "M_log_count",
    "M_early_filled": "M_early_filled",
    "M_early_dum":    "M_early_dum",
    "M_has_fund":     "M_has_fund",
}

# Test with main X variables
for xk in ["selfsuff", "transfer_dep"]:
    xc = X_VARS[xk]
    for mk, mc in M_VARS.items():
        for ct_tag, ct_list in [("no_ctrl", []), ("core", CONTROLS_CORE)]:
            tag = f"{xk}/{mk}/{ct_tag}"
            print(f"\n{'='*56}")
            print(f"Mediation: {tag}")
            print(f"{'='*56}")

            # Step 0: total X->Y
            r0 = run_fe(panel, dep_main, [xc] + ct_list, label=f"[{tag}] s0 X->Y")
            if r0:
                results[("med", tag, "s0")] = r0

            # Step 1: X->M
            r1 = run_fe(panel, mc, [xc] + ct_list, label=f"[{tag}] s1 X->M")
            if r1:
                results[("med", tag, "s1")] = r1

            # Step 2: X+M->Y
            r2 = run_fe(panel, dep_main, [xc, mc] + ct_list, label=f"[{tag}] s2 X+M->Y")
            if r2:
                results[("med", tag, "s2")] = r2

            # Sobel
            if r1 and r2:
                try:
                    a   = r1["res"].params[xc]
                    sea = r1["res"].std_errors[xc]
                    b   = r2["res"].params[mc]
                    seb = r2["res"].std_errors[mc]
                    sb  = sobel(a, sea, b, seb)
                    results[("sobel", tag)] = sb

                    total = r0["res"].params[xc] if r0 else np.nan
                    direct = r2["res"].params[xc]
                    print(f"\n  Sobel: ab={sb['ab']:.6f} Z={sb['z']:.4f} "
                          f"p={sb['p']:.4f} {sig(sb['p'])}")
                    print(f"  Total={total:.4f}, Direct={direct:.4f}")
                    if total != 0 and not np.isnan(total):
                        print(f"  Mediation%={sb['ab']/total*100:.2f}%")
                except Exception as e:
                    print(f"  Sobel error: {e}")

            # Bootstrap
            if r1 and r2:
                print(f"  Bootstrap (500 iter)...")
                bs = bootstrap_indirect(panel, dep_main, xc, mc, ct_list, n_boot=500)
                if bs:
                    results[("boot", tag)] = bs
                    print(f"    mean={bs['mean']:.6f} "
                          f"95%CI=[{bs['ci_lo']:.6f},{bs['ci_hi']:.6f}] "
                          f"{'SIG' if bs['sig'] else 'NS'}")
                else:
                    print(f"    Bootstrap failed")

# =====================================================================
# 5. ROBUSTNESS: compare with old fiscal_gap
# =====================================================================
print("\n" + "=" * 72)
print("5. Robustness: old fiscal_gap + new M variables")
print("=" * 72)

xc_gap = "fiscal_gap_l1"
for mk, mc in [("M_log_count", "M_log_count"), ("M_early_filled", "M_early_filled")]:
    tag = f"fiscal_gap/{mk}/core"
    print(f"\n--- {tag} ---")
    r0 = run_fe(panel, dep_main, [xc_gap] + CONTROLS_CORE, label=f"s0")
    if r0: results[("rob", tag, "s0")] = r0
    r1 = run_fe(panel, mc, [xc_gap] + CONTROLS_CORE, label=f"s1")
    if r1: results[("rob", tag, "s1")] = r1
    r2 = run_fe(panel, dep_main, [xc_gap, mc] + CONTROLS_CORE, label=f"s2")
    if r2: results[("rob", tag, "s2")] = r2

# =====================================================================
# 6. ADDITIONAL ROBUSTNESS
# =====================================================================
print("\n" + "=" * 72)
print("6. Additional Robustness Checks")
print("=" * 72)

# 6a. Alternative DV
print("\n--- 6a. Alternative DVs (selfsuff, core controls) ---")
xc_ss = "selfsuff_l1"
for yk, yc in [("ln_patent", "ln_patent"), ("inv_share", "inv_share")]:
    r = run_fe(panel, yc, [xc_ss] + CONTROLS_CORE, label=f"[alt_dv] {yk}~selfsuff")
    if r:
        results[("robust_dv", yk)] = r

# 6b. Per-capita patent
if "人均专利受理量" in df.columns:
    df_pc = df[df["人均专利受理量"] > 0].copy()
    df_pc["ln_pat_pc"] = np.log(df_pc["人均专利受理量"])
    df_pc["ln_pat_pc"] = winsorize(df_pc["ln_pat_pc"], *WINSOR)
    panel_pc = df_pc.set_index(["city_id", "年份"])
    r_pc = run_fe(panel_pc, "ln_pat_pc", [xc_ss] + CONTROLS_CORE,
                  label="[alt_dv] ln_patent_pc~selfsuff")
    if r_pc:
        results[("robust_pc",)] = r_pc

# 6c. Exclude top 5% patent cities
print("\n--- 6c. Exclude top 5% patent cities ---")
top5 = df["发明受理数"].quantile(0.95)
df_trim = df[df["发明受理数"] <= top5].copy()
panel_trim = df_trim.set_index(["city_id", "年份"])
r_trim = run_fe(panel_trim, dep_main, [xc_ss] + CONTROLS_CORE,
                label="[trim] excl top5%")
if r_trim:
    results[("robust_trim",)] = r_trim

# 6d. Non-linear (quadratic)
print("\n--- 6d. Non-linear (quadratic) ---")
panel_nl = panel.copy()
panel_nl["selfsuff_l1_sq"] = panel_nl["selfsuff_l1"] ** 2
r_nl = run_fe(panel_nl, dep_main,
              ["selfsuff_l1", "selfsuff_l1_sq"] + CONTROLS_CORE,
              label="[non-linear] quadratic selfsuff")
if r_nl:
    results[("robust_nl",)] = r_nl

# =====================================================================
# 7. GENERATE REPORT
# =====================================================================
print("\n" + "=" * 72)
print("7. Generating Markdown Report")
print("=" * 72)

L = []
w = L.append

w("# Regression Results v3 -- Corrected X and M Variables")
w("")
w(f"> **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
w(f"> **Data**: `cleaned_data/final_regression_panel_v5.csv`")
w(f"> **Script**: `regression_v3/run_regression_v3.py`")
w(f"> **Method**: Two-way FE (city + year), clustered SE (city)")
w(f"> **Sample**: Remove inv_patent=0 + 1%/99% winsorize + remove fiscal_gap<0")
w("")
w("---")
w("")

# Descriptive stats
w("## 1. Descriptive Statistics")
w("")
w("| Variable | N | Missing | Mean | SD | P25 | P50 | P75 | Min | Max |")
w("|:---------|--:|-------:|-----:|---:|----:|----:|----:|----:|----:|")
for row in desc_rows:
    w(f"| {row['label']} | {row['N']} | {row['miss']} | "
      f"{row['mean']:.4f} | {row['sd']:.4f} | "
      f"{row['p25']:.4f} | {row['p50']:.4f} | {row['p75']:.4f} | "
      f"{row['mn']:.4f} | {row['mx']:.4f} |")
w("")

# Baseline regression
w("---")
w("")
w("## 2. Baseline Regression (H1)")
w("")
w("### Theory")
w("- `selfsuff_l1` = revenue/expenditure: **higher = less constrained -> expect POSITIVE on innovation**")
w("- `transfer_dep_l1` = 1 - selfsuff: **higher = more dependent -> expect NEGATIVE on innovation**")
w("- `fiscal_gap_l1` = (exp-rev)/GDP: OLD variable, conflates spending with constraint")
w("")

x_labels = {
    "selfsuff": "fiscal_selfsuff(L1)",
    "transfer_dep": "transfer_dep(L1)",
    "fiscal_gap": "fiscal_gap(L1)",
    "ln_debt": "ln(debt_ratio)(L1)",
}
y_labels = {
    "ln_inv": "ln(inv_patent)",
    "ln_patent": "ln(patent_total)",
    "inv_share": "inv_patent_share",
}

for spec_tag, spec_label in [("base_nc", "No Controls"), ("base_cc", "Core Controls")]:
    w(f"### 2.{1 if spec_tag=='base_nc' else 2} {spec_label}")
    w("")
    w("| # | DV | X | beta | SE | t | p | sig | R2w | N | Cities |")
    w("|:-:|:--:|:-:|----:|---:|--:|--:|:--:|----:|--:|------:|")
    num = 0
    for xk in ["selfsuff", "transfer_dep", "fiscal_gap", "ln_debt"]:
        for yk in ["ln_inv", "ln_patent", "inv_share"]:
            key = (spec_tag, xk, yk)
            if key not in results:
                continue
            num += 1
            r = results[key]
            res = r["res"]
            xc = X_VARS[xk]
            c, se, t, p = (res.params[xc], res.std_errors[xc],
                           res.tstats[xc], res.pvalues[xc])
            bd = "**" if p < 0.1 else ""
            w(f"| ({num}) | {y_labels[yk]} | {x_labels[xk]} | "
              f"{bd}{c:.4f}{bd} | {se:.4f} | {t:.3f} | {p:.4f} | "
              f"{sig(p)} | {res.rsquared_within:.4f} | {r['n']} | {r['n_ent']} |")
    w("")

# Full controls
w("### 2.3 Full Controls (DV=ln(inv_patent) only)")
w("")
w("| # | X | beta | SE | t | p | sig | R2w | N | Cities |")
w("|:-:|:-:|----:|---:|--:|--:|:--:|----:|--:|------:|")
num = 0
for xk in ["selfsuff", "transfer_dep", "fiscal_gap", "ln_debt"]:
    key = ("base_fc", xk, "ln_inv")
    if key not in results:
        continue
    num += 1
    r = results[key]
    res = r["res"]
    xc = X_VARS[xk]
    c, se, t, p = (res.params[xc], res.std_errors[xc],
                   res.tstats[xc], res.pvalues[xc])
    bd = "**" if p < 0.1 else ""
    w(f"| ({num}) | {x_labels[xk]} | {bd}{c:.4f}{bd} | {se:.4f} | "
      f"{t:.3f} | {p:.4f} | {sig(p)} | {res.rsquared_within:.4f} | "
      f"{r['n']} | {r['n_ent']} |")
w("")

# Mediation
w("---")
w("")
w("## 3. Mediation Analysis (H2)")
w("")
w("### Theory")
w("```")
w("fiscal_self_sufficiency (X) --> fund investment behavior (M) --> innovation (Y)")
w("  Higher selfsuff -> more/earlier fund investment -> more patents")
w("```")
w("")

m_labels = {
    "M_log_count": "log(fund_count)",
    "M_early_filled": "early_ratio(filled)",
    "M_early_dum": "early_dummy",
    "M_has_fund": "has_fund_dummy",
}

for xk in ["selfsuff", "transfer_dep"]:
    w(f"### 3.{1 if xk=='selfsuff' else 2} X = {x_labels[xk]}")
    w("")
    for mk in M_VARS:
        for ct in ["no_ctrl", "core"]:
            tag = f"{xk}/{mk}/{ct}"
            s0_key = ("med", tag, "s0")
            s1_key = ("med", tag, "s1")
            s2_key = ("med", tag, "s2")
            sob_key = ("sobel", tag)
            boot_key = ("boot", tag)

            if not any(k in results for k in [s0_key, s1_key, s2_key]):
                continue

            w(f"#### M={m_labels.get(mk,mk)}, {ct}")
            w("")
            w("| Step | Path | DV | Key Var | beta | SE | t | p | sig | R2w | N |")
            w("|:----:|:----:|:--:|:-------:|----:|---:|--:|--:|:--:|----:|--:|")

            xc = X_VARS[xk]
            mc = M_VARS[mk]
            steps = [
                ("s0", "X->Y", dep_main, [xc]),
                ("s1", "X->M", mc, [xc]),
                ("s2", "X+M->Y", dep_main, [xc, mc]),
            ]
            for skey, path, dep, show_vars in steps:
                rkey = ("med", tag, skey)
                if rkey not in results:
                    continue
                r = results[rkey]
                res = r["res"]
                for sv in show_vars:
                    c = res.params[sv]
                    se = res.std_errors[sv]
                    tv = res.tstats[sv]
                    pv = res.pvalues[sv]
                    bd = "**" if pv < 0.1 else ""
                    w(f"| {skey} | {path} | {dep} | {sv} | "
                      f"{bd}{c:.4f}{bd} | {se:.4f} | {tv:.3f} | {pv:.4f} | "
                      f"{sig(pv)} | {res.rsquared_within:.4f} | {r['n']} |")

            if sob_key in results:
                sb = results[sob_key]
                total_eff = results[s0_key]["res"].params[xc] if s0_key in results else np.nan
                direct_eff = results[s2_key]["res"].params[xc] if s2_key in results else np.nan
                w("")
                w(f"**Sobel**: ab={sb['ab']:.6f}, Z={sb['z']:.4f}, p={sb['p']:.4f} {sig(sb['p'])}")
                w(f"- Total c={total_eff:.4f}, Direct c'={direct_eff:.4f}")
                if total_eff != 0 and not np.isnan(total_eff):
                    w(f"- Mediation% = {sb['ab']/total_eff*100:.2f}%")

            if boot_key in results:
                bs = results[boot_key]
                w(f"- **Bootstrap** (500): mean={bs['mean']:.6f}, "
                  f"95%CI=[{bs['ci_lo']:.6f}, {bs['ci_hi']:.6f}], "
                  f"{'**Significant**' if bs['sig'] else 'Not significant'}")
            w("")

# Robustness: old fiscal_gap + new M
w("---")
w("")
w("## 4. Robustness: Old fiscal_gap with New M Variables")
w("")

for mk_tag in ["M_log_count", "M_early_filled"]:
    mc = mk_tag
    tag = f"fiscal_gap/{mk_tag}/core"
    w(f"### fiscal_gap -> {m_labels.get(mk_tag, mk_tag)} -> ln(inv_patent) [core controls]")
    w("")
    for skey in ["s0", "s1", "s2"]:
        rkey = ("rob", tag, skey)
        if rkey in results:
            r = results[rkey]
            res = r["res"]
            for v in res.params.index:
                if v in CONTROLS_CORE:
                    continue
                c = res.params[v]
                se = res.std_errors[v]
                pv = res.pvalues[v]
                w(f"- {skey} {v}: beta={c:.4f}, se={se:.4f}, p={pv:.4f} {sig(pv)}, N={r['n']}")
    w("")

# Alternative DV
w("---")
w("")
w("## 5. Additional Robustness")
w("")
w("### 5.1 Alternative DVs (X=selfsuff, core controls)")
w("")
w("| DV | beta | SE | p | sig | R2w | N |")
w("|:--:|----:|---:|--:|:--:|----:|--:|")

for yk in ["ln_patent", "inv_share"]:
    key = ("robust_dv", yk)
    if key in results:
        r = results[key]
        res = r["res"]
        c, se, pv = res.params[xc_ss], res.std_errors[xc_ss], res.pvalues[xc_ss]
        bd = "**" if pv < 0.1 else ""
        w(f"| {y_labels.get(yk,yk)} | {bd}{c:.4f}{bd} | {se:.4f} | "
          f"{pv:.4f} | {sig(pv)} | {res.rsquared_within:.4f} | {r['n']} |")

key_pc = ("robust_pc",)
if key_pc in results:
    r = results[key_pc]
    res = r["res"]
    c, se, pv = res.params[xc_ss], res.std_errors[xc_ss], res.pvalues[xc_ss]
    bd = "**" if pv < 0.1 else ""
    w(f"| ln(patent_pc) | {bd}{c:.4f}{bd} | {se:.4f} | "
      f"{pv:.4f} | {sig(pv)} | {res.rsquared_within:.4f} | {r['n']} |")
w("")

# Trim
w("### 5.2 Exclude Top 5% Patent Cities")
w("")
key_trim = ("robust_trim",)
if key_trim in results:
    r = results[key_trim]
    res = r["res"]
    c, se, pv = res.params[xc_ss], res.std_errors[xc_ss], res.pvalues[xc_ss]
    w(f"- beta={c:.4f}, SE={se:.4f}, p={pv:.4f} {sig(pv)}, N={r['n']}")
w("")

# Non-linear
w("### 5.3 Non-linear (Quadratic)")
w("")
key_nl = ("robust_nl",)
if key_nl in results:
    r = results[key_nl]
    res = r["res"]
    c1, p1 = res.params["selfsuff_l1"], res.pvalues["selfsuff_l1"]
    c2, p2 = res.params["selfsuff_l1_sq"], res.pvalues["selfsuff_l1_sq"]
    w(f"- selfsuff: beta={c1:.4f}, p={p1:.4f} {sig(p1)}")
    w(f"- selfsuff^2: beta={c2:.4f}, p={p2:.4f} {sig(p2)}")
    w(f"- N={r['n']}")
w("")

# Summary
w("---")
w("")
w("## 6. Summary of Key Findings")
w("")

# Extract key results for summary
for xk in ["selfsuff", "transfer_dep", "fiscal_gap", "ln_debt"]:
    for spec in ["base_nc", "base_cc"]:
        key = (spec, xk, "ln_inv")
        if key in results:
            r = results[key]
            res = r["res"]
            xc = X_VARS[xk]
            c = res.params[xc]; p = res.pvalues[xc]
            sig_txt = "SIG" if p < 0.1 else "ns"
            ctrl = "no_ctrl" if spec == "base_nc" else "core_ctrl"
            w(f"- **{x_labels[xk]}** [{ctrl}] -> ln(inv): beta={c:.4f}, p={p:.4f} ({sig_txt})")
w("")

# Write report
md_path = os.path.join(OUTPUT_DIR, "regression_results_v3.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(L))

print(f"\nReport saved: {md_path}")
print("=" * 72)
print("ALL DONE!")
print("=" * 72)
