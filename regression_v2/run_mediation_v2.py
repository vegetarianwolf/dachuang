"""
regression_v2/run_mediation_v2.py
===================================================
中介效应模型回归分析（改进版 v2）

改进点（相比 regression_v1）:
  1. 数据: final_regression_panel_v4.csv（中介变量已内置且滞后一期）
  2. 样本处理: 去除发明专利=0的观测 + 连续变量1%/99%缩尾
  3. 中介变量: 使用滞后一期的早期投资占比（缓解内生性）
  4. 方法: Baron-Kenny三步法 + Sobel检验 + Bootstrap检验
  5. 中介样本: 区分全样本 / 有基金活动子样本

核心路径:
  财政约束(X) → 政府风险偏好(M) → 地区创新产出(Y)
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
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "linearmodels==4.17"])
    from linearmodels.panel import PanelOLS

# =====================================================================
# CONFIG
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "cleaned_data",
                         "final_regression_panel_v4.csv")
OUTPUT_DIR = BASE_DIR
WINSOR = (0.01, 0.99)

CONTROLS_CORE = ["人均GDP_对数", "第二产业占比", "科技支出占比"]
CONTROLS_FULL = CONTROLS_CORE + ["外资依存度", "金融深度"]

X_VARS = {
    "fiscal_gap": "财政缺口率_滞后一期",
    "ln_debt":    "ln_债务率_滞后一期",
}
DEP_VARS = {
    "ln_inv_patent":  "发明专利受理量_对数",
    "ln_patent_total": "专利受理总量_对数",
    "inv_share":       "发明专利占比",
}
M_VARS = {
    "deal_ratio":   "M_deal_ratio",
    "amount_ratio": "M_amount_ratio",
}

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def sig(p):
    if p < 0.01:  return "***"
    if p < 0.05:  return "**"
    if p < 0.1:   return "*"
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
    """Two-way FE with clustered SE at entity level."""
    cols = [dep] + indep
    d = panel[cols].dropna()
    n = d.shape[0]
    n_ent = d.index.get_level_values(0).nunique()
    n_t   = d.index.get_level_values(1).nunique()
    if n < 30:
        print(f"  [SKIP] {label}: N={n}")
        return None
    try:
        mod = PanelOLS(d[dep], d[indep],
                       entity_effects=True, time_effects=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
        print(f"  {label}: N={n} cities={n_ent} R²w={res.rsquared_within:.4f}")
        for v in indep:
            c, se, p = res.params[v], res.std_errors[v], res.pvalues[v]
            print(f"    {v}: β={c:.4f} se={se:.4f} p={p:.4f} {sig(p)}")
        return dict(res=res, n=n, n_ent=n_ent, n_t=n_t)
    except Exception as e:
        print(f"  [ERR] {label}: {e}")
        return None


def sobel(a, se_a, b, se_b):
    se_ab = np.sqrt(a**2 * se_b**2 + b**2 * se_a**2)
    z = (a * b) / se_ab if se_ab > 0 else np.nan
    p = 2 * (1 - stats.norm.cdf(abs(z))) if not np.isnan(z) else np.nan
    return dict(ab=a*b, se=se_ab, z=z, p=p)


def bootstrap_indirect(panel, dep, x_col, m_col, ctrls, n_boot=500, seed=42):
    """Cluster-bootstrap indirect effect (entity-FE only for speed)."""
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
# 1. LOAD & CLEAN DATA
# =====================================================================
print("=" * 72)
print("1. 数据加载与清洗")
print("=" * 72)

df = pd.read_csv(DATA_PATH)
N0 = len(df)
print(f"原始数据: {N0} 行, {df.shape[1]} 列, "
      f"{df['城市'].nunique()} 城市, {df['年份'].min()}-{df['年份'].max()}")

# 1a. 去除发明专利受理数=0
df = df[df["发明受理数"] > 0].copy()
print(f"去除发明受理数=0: {N0} → {len(df)} (删除 {N0 - len(df)})")

# 1b. 去除专利受理总数=0（如有）
n1 = len(df)
df = df[df["专利受理总数"] > 0].copy()
if len(df) < n1:
    print(f"去除专利受理总数=0: {n1} → {len(df)}")

# 1c. 构造 ln(债务率_滞后一期)
df["ln_债务率_滞后一期"] = np.where(
    df["债务率_滞后一期"] > 0, np.log(df["债务率_滞后一期"]), np.nan)

# 1d. 构造中介变量 —— 仅对有基金活动的城市-年份定义 M
df["M_deal_ratio"] = np.where(
    df["基金投资总次数_滞后一期"] > 0,
    df["早期投资次数占比_滞后一期"],
    np.nan)
df["M_amount_ratio"] = np.where(
    df["基金投资总金额_百万_滞后一期"] > 0,
    df["早期投资金额占比_滞后一期"],
    np.nan)

print(f"M_deal_ratio 有效: {df['M_deal_ratio'].notna().sum()} "
      f"({df['M_deal_ratio'].notna().mean()*100:.1f}%)")
print(f"M_amount_ratio 有效: {df['M_amount_ratio'].notna().sum()} "
      f"({df['M_amount_ratio'].notna().mean()*100:.1f}%)")

# 1e. 缩尾处理 1%/99%
winsor_vars = [
    "发明专利受理量_对数", "专利受理总量_对数", "发明专利占比",
    "财政缺口率_滞后一期", "ln_债务率_滞后一期",
    "M_deal_ratio", "M_amount_ratio",
    "人均GDP_对数", "第二产业占比", "科技支出占比", "外资依存度", "金融深度",
]
# NOTE: these are pre-rename Chinese names; winsorize before rename
print(f"\n缩尾处理 ({WINSOR[0]*100:.0f}%/{WINSOR[1]*100:.0f}%):")
for v in winsor_vars:
    if v in df.columns:
        nn = df[v].notna().sum()
        if nn > 20:
            before = df[v].copy()
            df[v] = winsorize(df[v], *WINSOR)
            n_clip = (before != df[v]).sum()
            print(f"  {v}: N={nn}, 截尾 {n_clip} 条")

# 1f. 额外去除异常样本：财政缺口率_滞后一期 < 0 的观测
n2 = len(df)
df = df[~((df["财政缺口率_滞后一期"].notna()) & (df["财政缺口率_滞后一期"] < 0))].copy()
if len(df) < n2:
    print(f"去除财政缺口率<0: {n2} → {len(df)}")

# 1g. Rename columns to English to avoid encoding issues in linearmodels
COL_RENAME = {
    "发明专利受理量_对数": "ln_inv_patent",
    "专利受理总量_对数":   "ln_patent_total",
    "发明专利占比":        "inv_share",
    "财政缺口率_滞后一期": "fiscal_gap_l1",
    "ln_债务率_滞后一期":  "ln_debt_l1",
    "M_deal_ratio":        "M_deal",
    "M_amount_ratio":      "M_amount",
    "人均GDP_对数":        "gdp_pc_ln",
    "第二产业占比":        "ind2_share",
    "科技支出占比":        "tech_exp",
    "外资依存度":          "fdi_ratio",
    "金融深度":            "fin_depth",
}
df.rename(columns=COL_RENAME, inplace=True)

# Update variable references
X_VARS = {"fiscal_gap": "fiscal_gap_l1", "ln_debt": "ln_debt_l1"}
DEP_VARS = {
    "ln_inv_patent":   "ln_inv_patent",
    "ln_patent_total": "ln_patent_total",
    "inv_share":       "inv_share",
}
M_VARS = {"deal_ratio": "M_deal", "amount_ratio": "M_amount"}
CONTROLS_CORE = ["gdp_pc_ln", "ind2_share", "tech_exp"]
CONTROLS_FULL = CONTROLS_CORE + ["fdi_ratio", "fin_depth"]

# 1h. 面板索引
df["city_id"] = pd.Categorical(df["城市"]).codes
panel = df.set_index(["city_id", "年份"])
print(f"\n最终分析样本: {len(df)} 观测, {df['城市'].nunique()} 城市")

# =====================================================================
# 2. DESCRIPTIVE STATISTICS
# =====================================================================
print("\n" + "=" * 72)
print("2. 描述性统计")
print("=" * 72)

desc_map = {
    "ln_inv_patent":   "Y: ln(发明专利)",
    "ln_patent_total": "Y: ln(专利总量)",
    "inv_share":       "Y: 发明专利占比",
    "fiscal_gap_l1":   "X1: 财政缺口率(L1)",
    "ln_debt_l1":      "X2: ln(债务率)(L1)",
    "M_deal":          "M1: 早期投资次数占比(L1)",
    "M_amount":        "M2: 早期投资金额占比(L1)",
}
ctrl_cn = {"gdp_pc_ln": "人均GDP_对数", "ind2_share": "第二产业占比",
           "tech_exp": "科技支出占比", "fdi_ratio": "外资依存度",
           "fin_depth": "金融深度"}
for c in CONTROLS_FULL:
    desc_map[c] = f"Control: {ctrl_cn.get(c, c)}"

desc_rows = []
for col, lab in desc_map.items():
    if col not in df.columns:
        continue
    s = df[col].dropna()
    desc_rows.append(dict(
        label=lab, col=col, N=len(s),
        miss=f"{(1-len(s)/len(df))*100:.1f}%",
        mean=s.mean(), sd=s.std(),
        p25=s.quantile(0.25), p50=s.median(), p75=s.quantile(0.75),
        mn=s.min(), mx=s.max()))
    print(f"  {lab}: N={len(s)} mean={s.mean():.4f} sd={s.std():.4f}")

desc_df = pd.DataFrame(desc_rows)

# =====================================================================
# 3. BASELINE REGRESSION (H1)
# =====================================================================
print("\n" + "=" * 72)
print("3. 基准回归 (H1: 财政约束 → 创新产出)")
print("=" * 72)

results = {}

# 3a. 无控制变量
print("\n--- 3a. 无控制变量 ---")
for xk, xc in X_VARS.items():
    for yk, yc in DEP_VARS.items():
        lab = f"[no_ctrl] {yk}~{xk}"
        r = run_fe(panel, yc, [xc], label=lab)
        if r:
            results[("base_nc", xk, yk)] = r

# 3b. 核心控制变量
print("\n--- 3b. 核心控制变量 ---")
for xk, xc in X_VARS.items():
    for yk, yc in DEP_VARS.items():
        lab = f"[core_ctrl] {yk}~{xk}"
        r = run_fe(panel, yc, [xc] + CONTROLS_CORE, label=lab)
        if r:
            results[("base_cc", xk, yk)] = r

# 3c. 完整控制变量
print("\n--- 3c. 完整控制变量 ---")
for xk, xc in X_VARS.items():
    for yk, yc in [("ln_inv_patent", "ln_inv_patent")]:
        lab = f"[full_ctrl] {yk}~{xk}"
        r = run_fe(panel, yc, [xc] + CONTROLS_FULL, label=lab)
        if r:
            results[("base_fc", xk, yk)] = r

# =====================================================================
# 4. MEDIATION ANALYSIS (H2)
# =====================================================================
print("\n" + "=" * 72)
print("4. 中介效应检验 (H2: X → M → Y)")
print("=" * 72)

dep_main = "ln_inv_patent"

for xk, xc in X_VARS.items():
    for mk, mc in M_VARS.items():
        for ctrl_tag, ctrl_list in [("no_ctrl", []),
                                    ("core_ctrl", CONTROLS_CORE)]:
            tag = f"{xk}/{mk}/{ctrl_tag}"
            print(f"\n{'='*56}")
            print(f"中介路径: {tag}")
            print(f"{'='*56}")

            # Step 0: total effect  X → Y
            lab0 = f"[{tag}] step0 X→Y"
            r0 = run_fe(panel, dep_main, [xc] + ctrl_list, label=lab0)
            if r0:
                results[("med", tag, "s0")] = r0

            # Step 1: X → M
            lab1 = f"[{tag}] step1 X→M"
            r1 = run_fe(panel, mc, [xc] + ctrl_list, label=lab1)
            if r1:
                results[("med", tag, "s1")] = r1

            # Step 2: X + M → Y
            lab2 = f"[{tag}] step2 X+M→Y"
            r2 = run_fe(panel, dep_main, [xc, mc] + ctrl_list, label=lab2)
            if r2:
                results[("med", tag, "s2")] = r2

            # Sobel test
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
                    print(f"  总效应={total:.4f}, 直接效应={direct:.4f}")
                    if total != 0 and not np.isnan(total):
                        print(f"  中介效应占比={sb['ab']/total*100:.2f}%")
                except Exception as e:
                    print(f"  Sobel error: {e}")

            # Bootstrap
            if r1 and r2:
                print(f"  Bootstrap (500 iter, entity-FE) ...")
                bs = bootstrap_indirect(panel, dep_main, xc, mc,
                                        ctrl_list, n_boot=500)
                if bs:
                    results[("boot", tag)] = bs
                    print(f"    mean={bs['mean']:.6f} "
                          f"95%CI=[{bs['ci_lo']:.6f}, {bs['ci_hi']:.6f}] "
                          f"{'SIG' if bs['sig'] else 'NS'}")
                else:
                    print(f"    Bootstrap 失败（样本不足）")

# =====================================================================
# 5. ROBUSTNESS CHECKS
# =====================================================================
print("\n" + "=" * 72)
print("5. 稳健性检验")
print("=" * 72)

# 5a. 替换被解释变量
print("\n--- 5a. 替换被解释变量（核心控制） ---")
for yk, yc in DEP_VARS.items():
    if yk == "ln_inv_patent":
        continue
    xc = "fiscal_gap_l1"
    lab = f"[robust_depvar] {yk}~fiscal_gap"
    r = run_fe(panel, yc, [xc] + CONTROLS_CORE, label=lab)
    if r:
        results[("robust_dv", yk)] = r

# 5b. 替换中介变量
print("\n--- 5b. 替换中介变量 (amount_ratio) ---")
alt_m = "M_amount"
xc = X_VARS["fiscal_gap"]
r_rob_m1 = run_fe(panel, alt_m, [xc] + CONTROLS_CORE,
                   label="[robust_m] X→M_amount")
if r_rob_m1:
    results[("robust_m", "s1")] = r_rob_m1
r_rob_m2 = run_fe(panel, dep_main, [xc, alt_m] + CONTROLS_CORE,
                   label="[robust_m] X+M_amount→Y")
if r_rob_m2:
    results[("robust_m", "s2")] = r_rob_m2

# 5c. 人均专利替代
print("\n--- 5c. 人均专利受理量 ---")
if "人均专利受理量" in df.columns:
    df_pc = df[df["人均专利受理量"] > 0].copy()
    df_pc["ln_patent_pc"] = np.log(df_pc["人均专利受理量"])
    df_pc["ln_patent_pc"] = winsorize(df_pc["ln_patent_pc"], *WINSOR)
    panel_pc = df_pc.set_index(["city_id", "年份"])
    xc = "fiscal_gap_l1"
    r_pc = run_fe(panel_pc, "ln_patent_pc", [xc] + CONTROLS_CORE,
                  label="[robust] ln(patent_pc)~fiscal_gap")
    if r_pc:
        results[("robust_pc",)] = r_pc

# 5d. 排除极端专利城市
print("\n--- 5d. 排除极端专利城市（top5%） ---")
top5 = df["发明受理数"].quantile(0.95)
df_trim = df[df["发明受理数"] <= top5].copy()
panel_trim = df_trim.set_index(["city_id", "年份"])
xc = "fiscal_gap_l1"
r_trim = run_fe(panel_trim, dep_main, [xc] + CONTROLS_CORE,
                label="[robust_trim] 去除top5%专利城市")
if r_trim:
    results[("robust_trim",)] = r_trim

# =====================================================================
# 6. GENERATE MARKDOWN REPORT
# =====================================================================
print("\n" + "=" * 72)
print("6. 生成 Markdown 报告")
print("=" * 72)

L = []
w = L.append

w(f"# 中介效应模型回归结果（v2）")
w(f"")
w(f"> **运行日期**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
w(f"> **数据源**：`cleaned_data/final_regression_panel_v4.csv`")
w(f"> **脚本**：`regression_v2/run_mediation_v2.py`")
w(f"> **方法**：双向固定效应（城市 FE + 年份 FE），聚类标准误（城市层面）")
w(f"> **样本处理**：去除发明专利=0 + 连续变量 {WINSOR[0]*100:.0f}%/{WINSOR[1]*100:.0f}% 缩尾")
w(f"")
w(f"---")
w(f"")

# ---------- Descriptive Stats ----------
w(f"## 一、描述性统计")
w(f"")
w(f"| 变量 | N | 缺失率 | 均值 | 标准差 | P25 | 中位数 | P75 | 最小值 | 最大值 |")
w(f"|------|--:|------:|-----:|------:|----:|------:|----:|------:|------:|")
for _, row in desc_df.iterrows():
    w(f"| {row['label']} | {row['N']} | {row['miss']} | "
      f"{row['mean']:.4f} | {row['sd']:.4f} | "
      f"{row['p25']:.4f} | {row['p50']:.4f} | {row['p75']:.4f} | "
      f"{row['mn']:.4f} | {row['mx']:.4f} |")
w(f"")

# ---------- Baseline ----------
w(f"---")
w(f"")
w(f"## 二、基准回归 (H1)")
w(f"")
w(r"$$Y_{c,t}=\alpha+\beta\, X_{c,t-1}+\gamma\,\mathbf{Z}_{c,t}+\mu_c+\lambda_t+\varepsilon_{c,t}$$")
w(f"")

x_cn = {"fiscal_gap": "财政缺口率(L1)", "ln_debt": "ln(债务率)(L1)"}
y_cn = {"ln_inv_patent": "ln(发明专利)", "ln_patent_total": "ln(专利总量)",
         "inv_share": "发明专利占比"}

for spec_tag, spec_cn, ctrl_cn in [
    ("base_nc", "无控制变量", "—"),
    ("base_cc", "核心控制变量", "人均GDP对数 / 第二产业占比 / 科技支出占比"),
]:
    w(f"### 2.{1 if spec_tag=='base_nc' else 2} {spec_cn}")
    w(f"")
    if ctrl_cn != "—":
        w(f"控制变量：{ctrl_cn}")
        w(f"")
    w(f"| # | 被解释变量 | 解释变量 | β | SE | t | p | sig | R²(w) | N | 城市 |")
    w(f"|:-:|:---------:|:-------:|--:|---:|--:|--:|:--:|-----:|--:|---:|")
    num = 0
    for xk in ["fiscal_gap", "ln_debt"]:
        for yk in ["ln_inv_patent", "ln_patent_total", "inv_share"]:
            key = (spec_tag, xk, yk)
            if key not in results:
                continue
            num += 1
            r = results[key]
            res = r["res"]
            xc = X_VARS[xk]
            c, se, t, p = (res.params[xc], res.std_errors[xc],
                           res.tstats[xc], res.pvalues[xc])
            b = "**" if p < 0.1 else ""
            w(f"| ({num}) | {y_cn[yk]} | {x_cn[xk]} | "
              f"{b}{c:.4f}{b} | {se:.4f} | {t:.3f} | {p:.4f} | "
              f"{sig(p)} | {res.rsquared_within:.4f} | {r['n']} | {r['n_ent']} |")
    w(f"")
    w(f"> \\*\\*\\* p<0.01, \\*\\* p<0.05, \\* p<0.1. 聚类标准误到城市层面.")
    w(f"")

# Full controls (only for main DV)
w(f"### 2.3 完整控制变量（仅主被解释变量 ln(发明专利)）")
w(f"")
w(f"控制变量：核心控制 + 外资依存度 + 金融深度")
w(f"")
w(f"| # | 解释变量 | β | SE | t | p | sig | R²(w) | N | 城市 |")
w(f"|:-:|:-------:|--:|---:|--:|--:|:--:|-----:|--:|---:|")
num = 0
for xk in ["fiscal_gap", "ln_debt"]:
    key = ("base_fc", xk, "ln_inv_patent")
    if key not in results:
        continue
    num += 1
    r = results[key]
    res = r["res"]
    xc = X_VARS[xk]
    c, se, t, p = (res.params[xc], res.std_errors[xc],
                   res.tstats[xc], res.pvalues[xc])
    b = "**" if p < 0.1 else ""
    w(f"| ({num}) | {x_cn[xk]} | {b}{c:.4f}{b} | {se:.4f} | "
      f"{t:.3f} | {p:.4f} | {sig(p)} | {res.rsquared_within:.4f} | "
      f"{r['n']} | {r['n_ent']} |")
w(f"")

# ---------- Mediation ----------
w(f"---")
w(f"")
w(f"## 三、中介效应检验 (H2)")
w(f"")
w(f"### 3.1 理论路径")
w(f"")
w(f"```")
w(f"财政约束 (X) ──→ 引导基金早期投资占比 (M) ──→ 发明专利 (Y)")
w(f"        (滞后一期)        (滞后一期)")
w(f"```")
w(f"")
w(f"- **M1**: 早期投资次数占比（滞后一期），仅限有基金活动的城市-年份")
w(f"- **M2**: 早期投资金额占比（滞后一期），仅限有基金活动的城市-年份")
w(f"")

m_cn = {"deal_ratio": "次数占比(M1)", "amount_ratio": "金额占比(M2)"}
ctrl_cn_map = {"no_ctrl": "无控制", "core_ctrl": "核心控制"}

for xk in ["fiscal_gap", "ln_debt"]:
    w(f"### 3.2 解释变量: {x_cn[xk]}")
    w(f"")
    for mk in ["deal_ratio", "amount_ratio"]:
        for ct in ["no_ctrl", "core_ctrl"]:
            tag = f"{xk}/{mk}/{ct}"
            s0_key = ("med", tag, "s0")
            s1_key = ("med", tag, "s1")
            s2_key = ("med", tag, "s2")
            sob_key = ("sobel", tag)
            boot_key = ("boot", tag)

            has_any = any(k in results for k in [s0_key, s1_key, s2_key])
            if not has_any:
                continue

            w(f"#### M={m_cn[mk]}, {ctrl_cn_map[ct]}")
            w(f"")
            w(f"| 步骤 | 路径 | 被解释 | 关键变量 | β | SE | t | p | sig | R²(w) | N |")
            w(f"|:----:|:---:|:-----:|:-------:|--:|---:|--:|--:|:--:|-----:|--:|")

            mc = M_VARS[mk]
            xc = X_VARS[xk]

            step_info = [
                ("s0", "X→Y", dep_main, [xc]),
                ("s1", "X→M", mc,       [xc]),
                ("s2", "X+M→Y", dep_main, [xc, mc]),
            ]
            for skey, path, dep, show_vars in step_info:
                rkey = ("med", tag, skey)
                if rkey not in results:
                    continue
                r = results[rkey]
                res = r["res"]
                for sv in show_vars:
                    c  = res.params[sv]
                    se = res.std_errors[sv]
                    tv = res.tstats[sv]
                    pv = res.pvalues[sv]
                    bd = "**" if pv < 0.1 else ""
                    short_map = {
                        "fiscal_gap_l1": "财政缺口率(L1)",
                        "ln_debt_l1": "ln(债务率)(L1)",
                        "M_deal": "M1(次数占比)",
                        "M_amount": "M2(金额占比)",
                    }
                    short = short_map.get(sv, sv)
                    dep_map = {
                        "ln_inv_patent": "ln(发明专利)",
                        "M_deal": "M1(次数占比)",
                        "M_amount": "M2(金额占比)",
                    }
                    dep_s = dep_map.get(dep, dep)
                    w(f"| {skey} | {path} | {dep_s} | {short} | "
                      f"{bd}{c:.4f}{bd} | {se:.4f} | {tv:.3f} | {pv:.4f} | "
                      f"{sig(pv)} | {res.rsquared_within:.4f} | {r['n']} |")

            # Sobel
            if sob_key in results:
                sb = results[sob_key]
                total_eff = (results[s0_key]["res"].params[xc]
                             if s0_key in results else np.nan)
                direct_eff = (results[s2_key]["res"].params[xc]
                              if s2_key in results else np.nan)
                w(f"")
                w(f"**Sobel 检验**：")
                w(f"- 间接效应 (a×b) = {sb['ab']:.6f}")
                w(f"- Sobel Z = {sb['z']:.4f}, p = {sb['p']:.4f} {sig(sb['p'])}")
                w(f"- 总效应 c = {total_eff:.4f}")
                w(f"- 直接效应 c' = {direct_eff:.4f}")
                if total_eff != 0 and not np.isnan(total_eff):
                    pct = sb["ab"] / total_eff * 100
                    w(f"- 中介效应占比 = {pct:.2f}%")

            # Bootstrap
            if boot_key in results:
                bs = results[boot_key]
                w(f"")
                w(f"**Bootstrap 检验** (500 次, cluster-entity)：")
                w(f"- 间接效应均值 = {bs['mean']:.6f}")
                w(f"- 标准误 = {bs['se']:.6f}")
                w(f"- 95% CI = [{bs['ci_lo']:.6f}, {bs['ci_hi']:.6f}]")
                w(f"- 结论: {'**显著**（置信区间不包含0）' if bs['sig'] else '不显著（置信区间包含0）'}")

            w(f"")

# ---------- Robustness ----------
w(f"---")
w(f"")
w(f"## 四、稳健性检验")
w(f"")

# 4a. Alternative DV
w(f"### 4.1 替换被解释变量")
w(f"")
w(f"| 被解释变量 | X=财政缺口率(L1) β | SE | p | sig | R²(w) | N |")
w(f"|:---------:|--:|---:|--:|:--:|-----:|--:|")
xc = X_VARS["fiscal_gap"]
for yk in ["ln_patent_total", "inv_share"]:
    key = ("robust_dv", yk)
    if key in results:
        r = results[key]
        res = r["res"]
        c, se, pv = res.params[xc], res.std_errors[xc], res.pvalues[xc]
        bd = "**" if pv < 0.1 else ""
        w(f"| {y_cn[yk]} | {bd}{c:.4f}{bd} | {se:.4f} | {pv:.4f} | "
          f"{sig(pv)} | {res.rsquared_within:.4f} | {r['n']} |")

# ln per capita
key_pc = ("robust_pc",)
if key_pc in results:
    r = results[key_pc]
    res = r["res"]
    c, se, pv = res.params[xc], res.std_errors[xc], res.pvalues[xc]
    bd = "**" if pv < 0.1 else ""
    w(f"| ln(人均专利) | {bd}{c:.4f}{bd} | {se:.4f} | {pv:.4f} | "
      f"{sig(pv)} | {res.rsquared_within:.4f} | {r['n']} |")
w(f"")

# 4b. Alternative M
w(f"### 4.2 替换中介变量 (M=早期投资金额占比)")
w(f"")
if ("robust_m", "s1") in results and ("robust_m", "s2") in results:
    r1 = results[("robust_m", "s1")]
    r2 = results[("robust_m", "s2")]
    res1 = r1["res"]; res2 = r2["res"]
    a_c  = res1.params[xc]; a_p = res1.pvalues[xc]
    b_c  = res2.params[alt_m]; b_p = res2.pvalues[alt_m]
    w(f"- X→M(金额): β={a_c:.4f}, p={a_p:.4f} {sig(a_p)}")
    w(f"- M(金额)→Y|X: β={b_c:.4f}, p={b_p:.4f} {sig(b_p)}")
    w(f"")

# 4c. Trim
w(f"### 4.3 排除极端专利城市（top 5%）")
w(f"")
key_trim = ("robust_trim",)
if key_trim in results:
    r = results[key_trim]
    res = r["res"]
    c, se, pv = res.params[xc], res.std_errors[xc], res.pvalues[xc]
    w(f"- 排除发明专利受理数前5%后: β={c:.4f}, SE={se:.4f}, p={pv:.4f} {sig(pv)}, "
      f"N={r['n']}, R²(w)={res.rsquared_within:.4f}")
w(f"")

# ---------- Comparison with v1 ----------
w(f"---")
w(f"")
w(f"## 五、与 regression_v1 结果对比")
w(f"")
w(f"| 对比维度 | regression_v1 | regression_v2 (本次) |")
w(f"|:--------|:-------------|:--------------------|")
w(f"| 数据版本 | v3 (final_regression_panel_v3_cityfiltered) | v4 (final_regression_panel_v4) |")
w(f"| 样本处理 | 无 | 去除发明专利=0 + 1%/99%缩尾 + 去除财政缺口率<0 |")
w(f"| 中介变量 | early_deal_ratio (当期，需手动匹配PE数据) | 早期投资次数占比_滞后一期 (已内置，滞后一期) |")
w(f"| 中介子样本 | 全部匹配到的观测 | 仅有基金活动的城市-年份 |")
w(f"| 检验方法 | BK三步法 + Sobel | BK三步法 + Sobel + Bootstrap |")
w(f"")

w(f"### 5.1 基准回归对比 (ln(发明专利) ~ 财政缺口率(L1), 核心控制)")
w(f"")

# v1 results (hardcoded from the report)
v1_base = {"coef": 1.0435, "se": 0.4821, "p": 0.0305, "n": 2575, "r2w": -0.0410}

key_v2 = ("base_cc", "fiscal_gap", "ln_inv_patent")
if key_v2 in results:
    r2 = results[key_v2]
    res2 = r2["res"]
    xc = X_VARS["fiscal_gap"]
    c2 = res2.params[xc]; se2 = res2.std_errors[xc]; p2 = res2.pvalues[xc]
    w(f"| 指标 | v1 | v2 |")
    w(f"|:-----|---:|---:|")
    w(f"| β | {v1_base['coef']:.4f}{sig(v1_base['p'])} | {c2:.4f}{sig(p2)} |")
    w(f"| SE | {v1_base['se']:.4f} | {se2:.4f} |")
    w(f"| p | {v1_base['p']:.4f} | {p2:.4f} |")
    w(f"| N | {v1_base['n']} | {r2['n']} |")
    w(f"| R²(within) | {v1_base['r2w']:.4f} | {res2.rsquared_within:.4f} |")
    w(f"")

w(f"### 5.2 中介效应对比 (fiscal_gap → M_deal_ratio → ln(发明专利), 核心控制)")
w(f"")

# v1 mediation results (hardcoded from report)
v1_med = {
    "total_p": 0.0305, "xm_p": 0.1253, "my_p": 0.3495,
    "sobel_z": -0.8859, "sobel_p": 0.3756,
    "indirect": -0.108696, "total": 1.0435,
}

tag_v2 = "fiscal_gap/deal_ratio/core_ctrl"
sob_v2 = results.get(("sobel", tag_v2))
s0_v2 = results.get(("med", tag_v2, "s0"))
s1_v2 = results.get(("med", tag_v2, "s1"))
s2_v2 = results.get(("med", tag_v2, "s2"))
boot_v2 = results.get(("boot", tag_v2))

w(f"| 检验步骤 | v1 | v2 |")
w(f"|:--------|---:|---:|")

if s0_v2:
    p0 = s0_v2["res"].pvalues[X_VARS["fiscal_gap"]]
    w(f"| 总效应 X→Y p值 | {v1_med['total_p']:.4f} | {p0:.4f} |")
if s1_v2:
    p1 = s1_v2["res"].pvalues[X_VARS["fiscal_gap"]]
    w(f"| X→M p值 | {v1_med['xm_p']:.4f} | {p1:.4f} |")
if s2_v2:
    p2_m = s2_v2["res"].pvalues[M_VARS["deal_ratio"]]
    w(f"| M→Y (控制X) p值 | {v1_med['my_p']:.4f} | {p2_m:.4f} |")
if sob_v2:
    w(f"| Sobel Z | {v1_med['sobel_z']:.4f} | {sob_v2['z']:.4f} |")
    w(f"| Sobel p | {v1_med['sobel_p']:.4f} | {sob_v2['p']:.4f} |")
    w(f"| 间接效应 | {v1_med['indirect']:.6f} | {sob_v2['ab']:.6f} |")
if boot_v2:
    w(f"| Bootstrap 95%CI | — | [{boot_v2['ci_lo']:.6f}, {boot_v2['ci_hi']:.6f}] |")
    w(f"| Bootstrap 结论 | — | {'显著' if boot_v2['sig'] else '不显著'} |")

w(f"")

# ---------- Interpretation ----------
w(f"---")
w(f"")
w(f"## 六、结果解读与结论")
w(f"")
w(f"### 6.1 基准回归 (H1)")
w(f"")

for xk in ["fiscal_gap", "ln_debt"]:
    for spec, spec_cn in [("base_nc", "无控制"), ("base_cc", "核心控制")]:
        key = (spec, xk, "ln_inv_patent")
        if key in results:
            r = results[key]
            res = r["res"]
            xc = X_VARS[xk]
            c = res.params[xc]; p = res.pvalues[xc]
            sig_txt = "显著" if p < 0.1 else "不显著"
            w(f"- **{x_cn[xk]}** [{spec_cn}] → ln(发明专利): "
              f"β={c:.4f}, p={p:.4f} ({sig_txt})")

w(f"")
w(f"### 6.2 中介效应 (H2)")
w(f"")

for xk in ["fiscal_gap", "ln_debt"]:
    for mk in ["deal_ratio"]:
        for ct in ["core_ctrl"]:
            tag = f"{xk}/{mk}/{ct}"
            sob_key = ("sobel", tag)
            boot_key = ("boot", tag)
            s1_key = ("med", tag, "s1")
            s2_key = ("med", tag, "s2")

            conditions = []
            if s1_key in results:
                p1 = results[s1_key]["res"].pvalues[X_VARS[xk]]
                conditions.append(f"X→M p={p1:.4f}({'✓' if p1<0.1 else '✗'})")
            if s2_key in results:
                mc = M_VARS[mk]
                p2m = results[s2_key]["res"].pvalues[mc]
                conditions.append(f"M→Y p={p2m:.4f}({'✓' if p2m<0.1 else '✗'})")
            if sob_key in results:
                sp = results[sob_key]["p"]
                conditions.append(f"Sobel p={sp:.4f}({'✓' if sp<0.1 else '✗'})")
            if boot_key in results:
                bs = results[boot_key]
                conditions.append(f"Boot {'显著' if bs['sig'] else '不显著'}")

            if conditions:
                w(f"- **{x_cn[xk]}→{m_cn[mk]}→Y** [{ctrl_cn_map[ct]}]: "
                  f"{', '.join(conditions)}")
w(f"")

w(f"### 6.3 与 v1 的主要变化")
w(f"")
w(f"1. **样本清洗**: 去除了发明专利=0的观测和极端值，提高了数据质量")
w(f"2. **中介变量时序**: v2使用滞后一期的中介变量（v1使用当期值），更好地缓解了内生性")
w("3. **中介子样本**: v2仅在有基金活动的城市-年份上检验中介，避免了将「无基金」与「有基金但不投早期」混淆")
w(f"4. **额外检验**: 新增Bootstrap置信区间，为间接效应提供更稳健的推断")
w(f"")

w(f"---")
w(f"")
w(f"## 七、方法说明")
w(f"")
w(f"1. **双向固定效应**: 控制城市和年份的不可观测异质性")
w(f"2. **聚类标准误**: 聚类到城市层面，允许城市内的序列相关和异方差")
w(f"3. **解释变量滞后一期**: 所有核心解释变量和中介变量均使用滞后一期值，缓解反向因果")
w(f"4. **缩尾处理**: 连续变量在1%和99%分位缩尾，降低极端值影响")
w(f"5. **中介效应检验**:")
w(f"   - Baron & Kenny三步法: 经典中介检验")
w(f"   - Sobel检验: 正态近似下间接效应的显著性检验")
w(f"   - Bootstrap检验: 不依赖正态假设的稳健推断 (cluster-entity, 500次)")
w(f"6. **Bootstrap注意**: Bootstrap仅使用城市固定效应（非双向FE），为近似检验")
w(f"")

# Write file
md_path = os.path.join(OUTPUT_DIR, "regression_results_v2.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(L))

print(f"\n报告已保存: {md_path}")
print("=" * 72)
print("全部完成!")
print("=" * 72)
