"""
run_regressions_v3.py  (v3 — 2010-2023 + 全部解释变量滞后一期)
===============================================================
相比 v2 的改动:
  1. 时间窗口限定为 2010-2023 (专利数据 2000-2023, PE 数据 2010 后才密集)
  2. 核心解释变量: 滞后一期财政缺口率 (已有)
  3. 机制变量也滞后一期: L1_早期投资事件占比, L1_加权风险偏好指数
  4. 输出与 v2 (README 中汇报的结果) 的对比表

所有面板回归: 双向固定效应 (城市FE + 年份FE), 聚类稳健标准误 (城市层面).
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS
import os

# ======================================================================
# 辅助函数
# ======================================================================

def load_data():
    """加载最终回归数据集"""
    df = pd.read_csv('cleaned_data/final_regression_dataset.csv', encoding='utf-8-sig')
    for col in df.columns:
        if col not in ['城市']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def prepare_lagged_vars(df):
    """
    生成机制变量的滞后一期:
      L1_早期投资事件占比  = 早期投资事件占比(t-1)
      L1_加权风险偏好指数  = 加权风险偏好指数(t-1)
      L1_早期投资金额占比  = 早期投资金额占比(t-1)
    """
    df = df.sort_values(['城市', '年份']).copy()
    for var in ['早期投资事件占比', '加权风险偏好指数', '早期投资金额占比']:
        if var in df.columns:
            df[f'L1_{var}'] = df.groupby('城市')[var].shift(1)
    return df


def prepare_panel(df, dep_var, indep_vars):
    """筛选有效行, 设置 MultiIndex(城市, 年份)"""
    cols = list(set([dep_var] + indep_vars + ['城市', '年份']))
    sub = df[cols].dropna().copy()
    sub = sub.set_index(['城市', '年份'])
    return sub


def run_panel_fe(df, dep_var, indep_vars, title=""):
    """双向固定效应面板回归, 城市层面聚类标准误"""
    sub = prepare_panel(df, dep_var, indep_vars)
    if len(sub) < 30:
        print(f"  [SKIP] {title}: only {len(sub)} obs after dropping NA")
        return None

    formula = f'{dep_var} ~ 1 + {" + ".join(indep_vars)} + EntityEffects + TimeEffects'
    mod = PanelOLS.from_formula(formula, data=sub)
    res = mod.fit(cov_type='clustered', cluster_entity=True)

    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")
    print(f"  Dep var:   {dep_var}")
    print(f"  Indep:     {', '.join(indep_vars)}")
    n_cities = sub.index.get_level_values(0).nunique()
    year_min = sub.index.get_level_values(1).min()
    year_max = sub.index.get_level_values(1).max()
    print(f"  N={res.nobs:.0f}, Cities={n_cities}, Years={year_min}-{year_max}")
    print(f"  R²(within)={res.rsquared_within:.4f}, "
          f"R²(between)={res.rsquared_between:.4f}, "
          f"R²(overall)={res.rsquared_overall:.4f}")
    print(f"  F-stat={res.f_statistic.stat:.3f}, p={res.f_statistic.pval:.4f}")
    print()
    print(f"  {'Variable':30s} {'Coef':>10s} {'Std.Err':>10s} {'t':>8s} {'p':>8s} {'Sig':>5s}")
    print(f"  {'-'*75}")
    for var in indep_vars:
        coef = res.params[var]
        se = res.std_errors[var]
        t = res.tstats[var]
        p = res.pvalues[var]
        sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
        print(f"  {var:30s} {coef:10.4f} {se:10.4f} {t:8.3f} {p:8.4f} {sig:>5s}")
    print()
    return res


def descriptive_stats(df, label=""):
    """输出关键变量的描述性统计"""
    key_vars = [
        'ln_发明专利申请数', 'ln_专利申请受理数', 'ln_专利授权数',
        '早期投资金额占比', '早期投资事件占比', '加权风险偏好指数',
        'L1_早期投资事件占比', 'L1_加权风险偏好指数',
        '当期财政缺口率', '滞后一期财政缺口率',
        'ln_人均GDP', '金融深度', '第二产业占比', '科技支出占比',
        '外资占比', '债务率', 'ln_人口',
    ]
    existing = [v for v in key_vars if v in df.columns]
    desc = df[existing].describe().T
    desc['missing'] = df[existing].isnull().sum()
    print(f"\n{'='*80}")
    print(f"  DESCRIPTIVE STATISTICS  {label}")
    print(f"{'='*80}")
    print(desc[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'missing']].round(4).to_string())
    print()


# ======================================================================
# 主回归
# ======================================================================

def main():
    print("=" * 75)
    print("  run_regressions_v3.py — 2010-2023, 解释变量全部滞后一期")
    print("=" * 75)

    # ---- 加载 & 筛选 ----
    df_full = load_data()
    print(f"\nFull dataset: {len(df_full)} obs, {df_full['城市'].nunique()} cities, "
          f"years {df_full['年份'].min()}-{df_full['年份'].max()}")

    # 生成滞后机制变量 (在筛选时间之前做, 保留 2009 年数据用于生成 2010 的滞后)
    df_full = prepare_lagged_vars(df_full)

    # 筛选时间窗口: 2010-2023
    df = df_full[(df_full['年份'] >= 2010) & (df_full['年份'] <= 2023)].copy()
    print(f"Filtered (2010-2023): {len(df)} obs, {df['城市'].nunique()} cities")

    # ---- 描述性统计 ----
    descriptive_stats(df, label="(2010-2023)")

    # ---- 变量定义 ----
    Y_main = 'ln_发明专利申请数'
    Y_alt1 = 'ln_专利申请受理数'
    Y_alt2 = 'ln_专利授权数'

    X_main = '滞后一期财政缺口率'         # 核心解释变量 (t-1)
    M_main = 'L1_早期投资事件占比'         # 机制变量 (t-1)
    M_alt  = 'L1_加权风险偏好指数'         # 替代机制变量 (t-1)

    CONTROLS = ['ln_人均GDP', '第二产业占比', '科技支出占比', 'ln_人口']

    # 检查覆盖情况
    print("\nVariable coverage (2010-2023):")
    for cv in [X_main, M_main, M_alt, Y_main] + CONTROLS:
        if cv in df.columns:
            nn = df[cv].notna().sum()
            print(f"  {cv}: {nn}/{len(df)} ({nn/len(df)*100:.0f}%)")

    # ==================================================================
    # A. 基准回归: 财政约束(t-1) → 地区创新产出(t)
    # ==================================================================
    print("\n" + "#" * 75)
    print("  PART A: 基准回归 — 财政约束(t-1) → 创新产出(t)")
    print("#" * 75)

    res_a1 = run_panel_fe(df, Y_main, [X_main],
        title="A1: L1_FiscalGapRate → ln_inv_patent (无控制)")
    res_a2 = run_panel_fe(df, Y_main, [X_main] + CONTROLS,
        title="A2: L1_FiscalGapRate → ln_inv_patent (含控制)")
    res_a3 = run_panel_fe(df, Y_alt1, [X_main] + CONTROLS,
        title="A3: L1_FiscalGapRate → ln_patent_apply (稳健性)")
    res_a4 = run_panel_fe(df, Y_alt2, [X_main] + CONTROLS,
        title="A4: L1_FiscalGapRate → ln_patent_grant (稳健性)")

    # ==================================================================
    # B. 机制检验 Step1: 财政约束(t-1) → 政府风险偏好(t-1)
    #    注意: 这里 M 也用滞后一期, 意味着我们检验的是前一期的关系
    #    或者理解为: 被解释变量是 L1_M, 解释变量是 L1_X
    #    但更合理的理解是: X(t-1) → M(t) 当期机制变量
    # ==================================================================
    # 用户要求: "解释变量全部滞后一期"
    # 在机制检验 B 中: M(t) = f(X(t-1)) — 仍用当期 M 作为被解释变量
    # 在机制检验 C/D 中: Y(t) = f(M(t-1)) — M 作为解释变量时滞后一期
    print("\n" + "#" * 75)
    print("  PART B: 机制检验 Step1 — 财政约束(t-1) → 风险偏好(t)")
    print("#" * 75)

    # B 步骤被解释变量仍用当期机制变量
    M_dep_main = '早期投资事件占比'
    M_dep_alt  = '加权风险偏好指数'

    res_b1 = run_panel_fe(df, M_dep_main, [X_main] + CONTROLS,
        title="B1: L1_FiscalGapRate → Early_Deal_Ratio(t) (含控制)")
    res_b2 = run_panel_fe(df, M_dep_alt, [X_main] + CONTROLS,
        title="B2: L1_FiscalGapRate → Risk_Index(t) (含控制)")

    # ==================================================================
    # C. 机制检验 Step2: 政府风险偏好(t-1) → 地区创新产出(t)
    # ==================================================================
    print("\n" + "#" * 75)
    print("  PART C: 机制检验 Step2 — 风险偏好(t-1) → 创新产出(t)")
    print("#" * 75)

    res_c1 = run_panel_fe(df, Y_main, [M_main] + CONTROLS,
        title="C1: L1_Early_Deal_Ratio → ln_inv_patent (含控制)")
    res_c2 = run_panel_fe(df, Y_main, [M_alt] + CONTROLS,
        title="C2: L1_Risk_Index → ln_inv_patent (含控制)")

    # ==================================================================
    # D. 机制检验 Step3: 同时加入 X(t-1) + M(t-1)
    # ==================================================================
    print("\n" + "#" * 75)
    print("  PART D: 机制检验 Step3 — 财政约束(t-1) + 风险偏好(t-1) → 创新(t)")
    print("#" * 75)

    res_d1 = run_panel_fe(df, Y_main, [X_main, M_main] + CONTROLS,
        title="D1: L1_FiscalGapRate + L1_Early_Deal_Ratio → ln_inv_patent")
    res_d2 = run_panel_fe(df, Y_main, [X_main, M_alt] + CONTROLS,
        title="D2: L1_FiscalGapRate + L1_Risk_Index → ln_inv_patent")

    # ==================================================================
    # E. 补充: 当期财政缺口率
    # ==================================================================
    print("\n" + "#" * 75)
    print("  PART E: 补充 — 当期财政缺口率")
    print("#" * 75)

    X_alt = '当期财政缺口率'
    res_e1 = run_panel_fe(df, Y_main, [X_alt] + CONTROLS,
        title="E1: Current FiscalGapRate → ln_inv_patent")

    # ==================================================================
    # 与 v2 (README) 结果对比
    # ==================================================================
    print("\n" + "=" * 75)
    print("  新旧结果对比 (v2 全样本 vs v3 2010-2023 + 解释变量滞后)")
    print("=" * 75)

    # v2 旧结果 (来自 README)
    old_results = {
        'A1': {'dep': 'ln_发明专利申请数', 'var': '滞后一期财政缺口率', 'coef': 1.773, 'sig': '**',  'note': '无控制, 全样本'},
        'A2': {'dep': 'ln_发明专利申请数', 'var': '滞后一期财政缺口率', 'coef': 1.701, 'sig': '**',  'note': '含控制, 全样本'},
        'A3': {'dep': 'ln_专利申请受理数', 'var': '滞后一期财政缺口率', 'coef': 0.164, 'sig': '',    'note': '稳健性, 全样本'},
        'A4': {'dep': 'ln_专利授权数',     'var': '滞后一期财政缺口率', 'coef': 1.406, 'sig': '*',   'note': '稳健性, 全样本'},
        'B1': {'dep': '早期投资事件占比',   'var': '滞后一期财政缺口率', 'coef': 1.596, 'sig': '',    'note': 'p=0.11, 全样本'},
        'B2': {'dep': '加权风险偏好指数',   'var': '滞后一期财政缺口率', 'coef': 3.639, 'sig': '',    'note': 'p=0.12, 全样本'},
        'C1': {'dep': 'ln_发明专利申请数', 'var': '早期投资事件占比',   'coef': 0.007, 'sig': '',    'note': '当期M, 全样本'},
        'C2': {'dep': 'ln_发明专利申请数', 'var': '加权风险偏好指数',   'coef': 0.004, 'sig': '',    'note': '当期M, 全样本'},
        'D1': {'dep': 'ln_发明专利申请数', 'var': '滞后一期财政缺口率', 'coef': 1.736, 'sig': '**',  'note': '+M, 全样本'},
    }

    # 收集 v3 新结果
    new_results = {}
    for label, res, var_name in [
        ('A1', res_a1, X_main), ('A2', res_a2, X_main),
        ('A3', res_a3, X_main), ('A4', res_a4, X_main),
        ('B1', res_b1, X_main), ('B2', res_b2, X_main),
        ('C1', res_c1, M_main), ('C2', res_c2, M_alt),
        ('D1', res_d1, X_main), ('D2', res_d2, X_main),
    ]:
        if res is not None:
            coef = res.params[var_name]
            p = res.pvalues[var_name]
            sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
            new_results[label] = {'coef': coef, 'pval': p, 'sig': sig, 'nobs': res.nobs,
                                  'r2w': res.rsquared_within}

    print(f"\n  {'Model':5s} | {'v2 (全样本)':>25s} | {'v3 (2010-2023, L1)':>30s} | {'变化':>10s}")
    print(f"  {'-'*80}")
    for label in ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'C1', 'C2', 'D1']:
        old = old_results.get(label, {})
        new = new_results.get(label, {})
        if old and new:
            old_str = f"{old['coef']:+.3f}{old['sig']:3s}"
            new_str = f"{new['coef']:+.4f}{new['sig']:3s} (N={new['nobs']:.0f})"
            delta = new['coef'] - old['coef']
            delta_str = f"{delta:+.3f}"
            print(f"  {label:5s} | {old_str:>25s} | {new_str:>30s} | {delta_str:>10s}")
        elif old:
            old_str = f"{old['coef']:+.3f}{old['sig']:3s}"
            print(f"  {label:5s} | {old_str:>25s} | {'N/A':>30s} | {'':>10s}")
        elif new:
            new_str = f"{new['coef']:+.4f}{new['sig']:3s} (N={new['nobs']:.0f})"
            print(f"  {label:5s} | {'N/A':>25s} | {new_str:>30s} | {'':>10s}")

    # D1 机制变量系数对比
    if 'D1' in new_results and res_d1 is not None:
        print(f"\n  D1 中机制变量 ({M_main}) 系数:")
        m_coef = res_d1.params[M_main]
        m_p = res_d1.pvalues[M_main]
        m_sig = '***' if m_p < 0.01 else '**' if m_p < 0.05 else '*' if m_p < 0.1 else ''
        print(f"    {M_main}: {m_coef:+.4f} (p={m_p:.4f}) {m_sig}")
    if res_d2 is not None:
        print(f"\n  D2 中机制变量 ({M_alt}) 系数:")
        m_coef = res_d2.params[M_alt]
        m_p = res_d2.pvalues[M_alt]
        m_sig = '***' if m_p < 0.01 else '**' if m_p < 0.05 else '*' if m_p < 0.1 else ''
        print(f"    {M_alt}: {m_coef:+.4f} (p={m_p:.4f}) {m_sig}")

    # 总结
    print(f"\n{'='*75}")
    print("  回归总结 (v3)")
    print(f"{'='*75}")
    print("""
    v3 变化要点:
      1. 时间窗口: 1991-2024 → 2010-2023 (PE数据密集区间)
      2. 机制变量滞后一期: M(t) → L1_M(t-1) 作为解释变量
      3. 核心解释变量: 仍用 滞后一期财政缺口率

    中介效应判断:
      若 B 中系数显著 (X(t-1) → M(t))
      且 C 中系数显著 (M(t-1) → Y(t))
      且 D 中 X(t-1) 的系数绝对值比 A 中减小 → 存在中介效应
    """)
    print("All regressions completed.")


if __name__ == "__main__":
    main()
