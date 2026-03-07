"""
run_regressions.py  (v2 — 含控制变量版)
===============================================
按照 新思路.md 2.5 节的实证模型设计, 运行:
  1. 基准回归: 财政约束 → 地区创新产出  (含控制变量)
  2. 机制检验 Step1: 财政约束 → 政府风险偏好
  3. 机制检验 Step2: 政府风险偏好 → 地区创新产出
  4. 机制检验 Step3: 同时加入财政约束+风险偏好
  5. 描述性统计表
所有面板回归使用双向固定效应 (城市FE + 年份FE), 聚类稳健标准误 (城市层面).
核心解释变量使用 '滞后一期财政缺口率' (已用GDP标准化).
控制变量: ln_人均GDP, 金融深度, 第二产业占比, 科技支出占比, 外资占比, ln_人口.
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
        '当期财政缺口率', '滞后一期财政缺口率',
        '全部基金投资总金额', '全部基金投资总次数',
        'ln_人均GDP', '金融深度', '第二产业占比', '科技支出占比',
        '外资占比', '债务率', 'ln_人口',
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
    X_main = '滞后一期财政缺口率'      # 核心解释变量 (t-1), 已用GDP标准化
    M_main = '早期投资事件占比'        # 机制变量 (early deal ratio)
    M_alt  = '加权风险偏好指数'        # 替代机制变量

    # ---- 控制变量 ----
    CONTROLS = ['ln_人均GDP', '第二产业占比', '科技支出占比', 'ln_人口']
    # 金融深度/外资占比覆盖率较低, 作为备选
    CONTROLS_FULL = CONTROLS + ['金融深度', '外资占比']

    # 检查控制变量覆盖情况
    for cv in CONTROLS_FULL:
        if cv in df.columns:
            nn = df[cv].notna().sum()
            print(f"  Control var '{cv}': {nn}/{len(df)} ({nn/len(df)*100:.0f}%)")

    # ==================================================================
    # A. 基准回归: 财政约束 → 地区创新产出  (不含控制变量 vs 含控制变量)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART A: 基准回归 — 财政约束对地区创新产出的影响")
    print("#" * 70)

    # A1: 无控制变量
    res_a1 = run_panel_fe(df, Y_main, [X_main],
                          title="A1: L1_FiscalGapRate → ln_inv_patent (无控制变量)")
    # A2: 含控制变量
    res_a2 = run_panel_fe(df, Y_main, [X_main] + CONTROLS,
                          title="A2: L1_FiscalGapRate → ln_inv_patent (含控制变量)")
    # A3-A4: 稳健性 (替换被解释变量)
    res_a3 = run_panel_fe(df, Y_alt1, [X_main] + CONTROLS,
                          title="A3: L1_FiscalGapRate → ln_patent_apply (稳健性)")
    res_a4 = run_panel_fe(df, Y_alt2, [X_main] + CONTROLS,
                          title="A4: L1_FiscalGapRate → ln_patent_grant (稳健性)")

    # ==================================================================
    # B. 机制检验 Step1: 财政约束 → 政府风险偏好  (H1)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART B: 机制检验 Step1 — 财政约束对政府风险偏好的影响")
    print("#" * 70)

    res_b1 = run_panel_fe(df, M_main, [X_main] + CONTROLS,
                          title="B1: L1_FiscalGapRate → Early_Deal_Ratio (含控制)")
    res_b2 = run_panel_fe(df, M_alt, [X_main] + CONTROLS,
                          title="B2: L1_FiscalGapRate → Risk_Index (含控制)")

    # ==================================================================
    # C. 机制检验 Step2: 政府风险偏好 → 地区创新产出  (H2)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART C: 机制检验 Step2 — 政府风险偏好对地区创新产出的影响")
    print("#" * 70)

    res_c1 = run_panel_fe(df, Y_main, [M_main] + CONTROLS,
                          title="C1: Early_Deal_Ratio → ln_inv_patent (含控制)")
    res_c2 = run_panel_fe(df, Y_main, [M_alt] + CONTROLS,
                          title="C2: Risk_Index → ln_inv_patent (含控制)")

    # ==================================================================
    # D. 机制检验 Step3: 同时加入财政约束 + 风险偏好  (H2中介判断)
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART D: 机制检验 Step3 — 同时加入财政约束与风险偏好")
    print("#" * 70)

    res_d1 = run_panel_fe(df, Y_main, [X_main, M_main] + CONTROLS,
                          title="D1: L1_FiscalGapRate + Early_Deal_Ratio → ln_inv_patent")
    res_d2 = run_panel_fe(df, Y_main, [X_main, M_alt] + CONTROLS,
                          title="D2: L1_FiscalGapRate + Risk_Index → ln_inv_patent")

    # ==================================================================
    # E. 补充: 使用当期财政缺口率 / 债务率
    # ==================================================================
    print("\n" + "#" * 70)
    print("  PART E: 补充回归 — 替代解释变量")
    print("#" * 70)

    X_alt = '当期财政缺口率'
    res_e1 = run_panel_fe(df, Y_main, [X_alt] + CONTROLS,
                          title="E1: Current FiscalGapRate → ln_inv_patent")
    res_e2 = run_panel_fe(df, M_main, [X_alt] + CONTROLS,
                          title="E2: Current FiscalGapRate → Early_Deal_Ratio")

    # 债务率 (如果有数据)
    if '债务率' in df.columns and df['债务率'].notna().sum() > 100:
        res_e3 = run_panel_fe(df, Y_main, ['债务率'] + CONTROLS,
                              title="E3: Debt_Rate → ln_inv_patent")
        res_e4 = run_panel_fe(df, M_main, ['债务率'] + CONTROLS,
                              title="E4: Debt_Rate → Early_Deal_Ratio")

    # ==================================================================
    # 总结
    # ==================================================================
    print("\n" + "=" * 70)
    print("  REGRESSION SUMMARY")
    print("=" * 70)
    print("""
    按照 新思路.md 的实证框架 (v2: 含控制变量):
      A  基准回归:     fiscal_gap_rate(t-1) → innovation(t) + Controls
      B  Step 1:      fiscal_gap_rate(t-1) → risk_preference(t) + Controls
      C  Step 2:      risk_preference(t) → innovation(t) + Controls
      D  Step 3:      fiscal_gap_rate(t-1) + risk_preference(t) → innovation(t) + Controls
      E  补充:        使用当期财政缺口率 / 债务率

    控制变量: ln_人均GDP, 第二产业占比, 科技支出占比, ln_人口

    核心解释变量: 滞后一期财政缺口率 = (财政支出 - 财政收入) / GDP (t-1)

    中介效应判断:
      若 B 中系数显著 (财政约束影响风险偏好)
      且 C 中系数显著 (风险偏好影响创新)
      且 D 中 fiscal_gap_rate 系数绝对值比 A 中减小 → 存在中介效应
    """)

    print("All regressions completed. Check results above for significance.")


if __name__ == "__main__":
    main()
