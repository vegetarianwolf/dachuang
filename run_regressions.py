"""
run_regressions.py  (alternative_path branch)
===============================================
按照 新思路.md 2.5 节的实证模型设计, 运行:
  1. 基准回归: 财政约束 → 地区创新产出
  2. 机制检验 Step1: 财政约束 → 政府风险偏好
  3. 机制检验 Step2: 政府风险偏好 → 地区创新产出
  4. 机制检验 Step3: 同时加入财政约束+风险偏好
  5. 描述性统计表
所有面板回归使用双向固定效应 (城市FE + 年份FE), 聚类稳健标准误 (城市层面).
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS
from scipy import stats
import os

# ======================================================================
# 辅助函数
# ======================================================================

def load_data():
    """加载最终回归数据集, 设置面板索引"""
    df = pd.read_csv('cleaned_data/final_regression_dataset.csv', encoding='utf-8-sig')
    # 确保数值型
    for col in df.columns:
        if col not in ['城市']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def prepare_panel(df, dep_var, indep_vars, extra_controls=None):
    """
    准备面板数据: 筛选有效行, 设置 MultiIndex(城市, 年份).
    返回可直接用于 PanelOLS 的 DataFrame.
    """
    cols = [dep_var] + indep_vars + ['城市', '年份']
    if extra_controls:
        cols += extra_controls
    cols = list(set(cols))
    sub = df[cols].dropna().copy()
    sub = sub.set_index(['城市', '年份'])
    return sub


def run_panel_fe(df, dep_var, indep_vars, title="", cluster='城市'):
    """
    运行双向固定效应面板回归 (城市 + 年份 FE), 城市层面聚类标准误.
    """
    sub = prepare_panel(df, dep_var, indep_vars)
    if len(sub) < 30:
        print(f"  [SKIP] {title}: only {len(sub)} obs after dropping NA")
        return None

    formula = f'{dep_var} ~ 1 + {" + ".join(indep_vars)} + EntityEffects + TimeEffects'
    mod = PanelOLS.from_formula(formula, data=sub)
    res = mod.fit(cov_type='clustered', cluster_entity=True)

    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    print(f"  Dep var:   {dep_var}")
    print(f"  Indep:     {', '.join(indep_vars)}")
    print(f"  N={res.nobs:.0f}, R²(within)={res.rsquared_within:.4f}, "
          f"R²(between)={res.rsquared_between:.4f}, R²(overall)={res.rsquared_overall:.4f}")
    print(f"  F-stat={res.f_statistic.stat:.3f}, p={res.f_statistic.pval:.4f}")
    print()
    print(f"  {'Variable':30s} {'Coef':>10s} {'Std.Err':>10s} {'t':>8s} {'p':>8s} {'Sig':>5s}")
    print(f"  {'-'*72}")
    for var in indep_vars:
        coef = res.params[var]
        se = res.std_errors[var]
        t = res.tstats[var]
        p = res.pvalues[var]
        sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
        print(f"  {var:30s} {coef:10.4f} {se:10.4f} {t:8.3f} {p:8.4f} {sig:>5s}")
    print()
    return res


def descriptive_stats(df):
    """输出关键变量的描述性统计"""
    key_vars = [
        'ln_发明专利申请数', 'ln_专利申请受理数', 'ln_专利授权数',
        '早期投资金额占比', '早期投资事件占比', '加权风险偏好指数',
        '当期财政缺口', '滞后一期财政缺口',
        '全部基金投资总金额', '全部基金投资总次数',
    ]
    existing = [v for v in key_vars if v in df.columns]
    desc = df[existing].describe().T
    desc['missing'] = df[existing].isnull().sum()
    print("\n" + "=" * 80)
    print("  DESCRIPTIVE STATISTICS")
    print("=" * 80)
    print(desc[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'missing']].round(3).to_string())
    print()


# ======================================================================
# 主回归流程
# ======================================================================

def main():
    print("Loading data ...")
    df = load_data()
    print(f"  {len(df)} observations, {df['城市'].nunique()} cities, "
          f"years {df['年份'].min()}-{df['年份'].max()}")

    # ---- 描述性统计 ----
    descriptive_stats(df)

    # ---- 核心变量 ----
    Y_main = 'ln_发明专利申请数'      # 推荐主指标
    Y_alt1 = 'ln_专利申请受理数'      # 稳健性
    Y_alt2 = 'ln_专利授权数'          # 稳健性
    X_main = '滞后一期财政缺口'        # 核心解释变量 (t-1)
    M_main = '早期投资事件占比'        # 机制变量 (early deal ratio)
    M_alt  = '加权风险偏好指数'        # 替代机制变量

    # ==================================================================
    # A. 基准回归: 财政约束 → 地区创新产出  (H1直接效应的前提)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART A: 基准回归 — 财政约束对地区创新产出的影响")
    print("#" * 70)

    res_a1 = run_panel_fe(df, Y_main, [X_main],
                          title="A1: L1_Fiscal_Gap → ln_inv_patent (主指标)")
    res_a2 = run_panel_fe(df, Y_alt1, [X_main],
                          title="A2: L1_Fiscal_Gap → ln_patent_apply (稳健性)")
    res_a3 = run_panel_fe(df, Y_alt2, [X_main],
                          title="A3: L1_Fiscal_Gap → ln_patent_grant (稳健性)")

    # ==================================================================
    # B. 机制检验 Step1: 财政约束 → 政府风险偏好  (H1)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART B: 机制检验 Step1 — 财政约束对政府风险偏好的影响")
    print("#" * 70)

    res_b1 = run_panel_fe(df, M_main, [X_main],
                          title="B1: L1_Fiscal_Gap → Early_Deal_Ratio")
    res_b2 = run_panel_fe(df, M_alt, [X_main],
                          title="B2: L1_Fiscal_Gap → Risk_Index")

    # ==================================================================
    # C. 机制检验 Step2: 政府风险偏好 → 地区创新产出  (H2)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART C: 机制检验 Step2 — 政府风险偏好对地区创新产出的影响")
    print("#" * 70)

    res_c1 = run_panel_fe(df, Y_main, [M_main],
                          title="C1: Early_Deal_Ratio → ln_inv_patent")
    res_c2 = run_panel_fe(df, Y_main, [M_alt],
                          title="C2: Risk_Index → ln_inv_patent")

    # ==================================================================
    # D. 机制检验 Step3: 同时加入财政约束 + 风险偏好  (H2中介判断)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART D: 机制检验 Step3 — 同时加入财政约束与风险偏好")
    print("#" * 70)

    res_d1 = run_panel_fe(df, Y_main, [X_main, M_main],
                          title="D1: L1_Fiscal_Gap + Early_Deal_Ratio → ln_inv_patent")
    res_d2 = run_panel_fe(df, Y_main, [X_main, M_alt],
                          title="D2: L1_Fiscal_Gap + Risk_Index → ln_inv_patent")

    # ==================================================================
    # E. 使用当期财政缺口 (作为对比 / 补充)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART E: 补充回归 — 使用当期财政缺口")
    print("#" * 70)

    X_alt = '当期财政缺口'
    res_e1 = run_panel_fe(df, Y_main, [X_alt],
                          title="E1: Current Fiscal_Gap → ln_inv_patent")
    res_e2 = run_panel_fe(df, M_main, [X_alt],
                          title="E2: Current Fiscal_Gap → Early_Deal_Ratio")

    # ==================================================================
    # 总结
    # ==================================================================
    print("\n" + "=" * 70)
    print("  REGRESSION SUMMARY")
    print("=" * 70)
    print("""
    按照 新思路.md 的实证框架:
      A  基准回归:     fiscal_gap(t-1) → innovation(t)
      B  Step 1:      fiscal_gap(t-1) → risk_preference(t)
      C  Step 2:      risk_preference(t) → innovation(t)
      D  Step 3:      fiscal_gap(t-1) + risk_preference(t) → innovation(t)
      E  补充:        使用当期财政缺口

    中介效应判断:
      若 B 中系数显著 (财政约束影响风险偏好)
      且 C 中系数显著 (风险偏好影响创新)
      且 D 中 fiscal_gap 系数绝对值比 A 中减小 → 存在中介效应
    """)

    print("All regressions completed. Check results above for significance.")
    print("NOTE: 专利数据为省级/副省级城市数据, 非地级市完全匹配.")
    print("NOTE: 当前样本未包含控制变量(人均GDP/金融深度等), 需额外数据源补充.")


if __name__ == "__main__":
    main()
