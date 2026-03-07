"""
run_risk_patent_regression.py
==============================================
以风险偏好做核心解释变量, 专利做被解释变量, 进行面板回归.

模型设定:
  innovation_{c,t} = α₀ + α₁ risk_pref_{c,t} + γ X_{c,t} + μ_c + λ_t + ε_{c,t}

其中:
  被解释变量 (Y):  ln_发明专利申请数 / ln_专利申请受理数 / ln_专利授权数 / ln_发明专利授权数
  核心解释变量 (X): 早期投资事件占比 / 加权风险偏好指数 / 早期投资金额占比
  控制变量: ln_人均GDP, 第二产业占比, 科技支出占比, ln_人口
  固定效应: 城市 + 年份 双向固定效应
  标准误: 城市层面聚类稳健标准误

回归内容:
  PART A: 基准回归  — 风险偏好 → 专利 (无控制 vs 有控制)
  PART B: 替换被解释变量 (稳健性)
  PART C: 替换核心解释变量 (稳健性)
  PART D: 加入财政缺口率作为额外控制
  PART E: 使用滞后一期风险偏好
  PART F: 描述性统计
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS
import os
import sys


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


def create_lagged_vars(df, var_list):
    """
    为指定变量创建滞后一期版本.
    需要按城市分组, 按年份排序, 然后 shift(1).
    """
    df = df.sort_values(['城市', '年份']).copy()
    for var in var_list:
        if var in df.columns:
            lag_name = f'L1_{var}'
            df[lag_name] = df.groupby('城市')[var].shift(1)
    return df


def prepare_panel(df, dep_var, indep_vars):
    """筛选有效行, 设置面板索引 (城市, 年份)."""
    cols = list(set([dep_var] + indep_vars + ['城市', '年份']))
    sub = df[cols].dropna().copy()
    sub = sub.set_index(['城市', '年份'])
    return sub


def run_panel_fe(df, dep_var, indep_vars, title=""):
    """
    运行双向固定效应面板回归 (城市FE + 年份FE), 城市层面聚类标准误.
    返回回归结果对象.
    """
    sub = prepare_panel(df, dep_var, indep_vars)
    if len(sub) < 30:
        print(f"\n  [SKIP] {title}: only {len(sub)} obs after dropping NA")
        return None

    formula = f'{dep_var} ~ 1 + {" + ".join(indep_vars)} + EntityEffects + TimeEffects'
    mod = PanelOLS.from_formula(formula, data=sub)
    res = mod.fit(cov_type='clustered', cluster_entity=True)

    # ---- 打印结果 ----
    n_cities = sub.index.get_level_values(0).nunique()
    n_years  = sub.index.get_level_values(1).nunique()

    print(f"\n{'='*78}")
    print(f"  {title}")
    print(f"{'='*78}")
    print(f"  Dep var:   {dep_var}")
    print(f"  Indep:     {', '.join(indep_vars)}")
    print(f"  N={res.nobs:.0f}  (Cities={n_cities}, Years={n_years})")
    print(f"  R²(within)={res.rsquared_within:.4f}  "
          f"R²(between)={res.rsquared_between:.4f}  "
          f"R²(overall)={res.rsquared_overall:.4f}")
    print(f"  F-stat={res.f_statistic.stat:.3f}  p={res.f_statistic.pval:.6f}")
    print()
    print(f"  {'Variable':35s} {'Coef':>12s} {'Std.Err':>12s} {'t':>9s} {'p':>10s} {'Sig':>5s}")
    print(f"  {'-'*85}")
    for var in indep_vars:
        coef = res.params[var]
        se   = res.std_errors[var]
        t    = res.tstats[var]
        p    = res.pvalues[var]
        sig  = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
        print(f"  {var:35s} {coef:12.6f} {se:12.6f} {t:9.3f} {p:10.4f} {sig:>5s}")
    print()
    return res


def descriptive_stats(df, var_list):
    """输出关键变量的描述性统计"""
    existing = [v for v in var_list if v in df.columns]
    desc = df[existing].describe().T
    desc['missing'] = df[existing].isnull().sum()
    desc['non_null'] = df[existing].notnull().sum()
    print("\n" + "=" * 90)
    print("  DESCRIPTIVE STATISTICS")
    print("=" * 90)
    print(desc[['non_null', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']].round(4).to_string())
    print()


# ======================================================================
# 主回归流程
# ======================================================================

def main():
    print("=" * 78)
    print("  风险偏好 → 专利  面板回归")
    print("  (被解释变量: 专利, 核心解释变量: 风险偏好)")
    print("=" * 78)

    # ---- 加载数据 ----
    print("\nLoading data ...")
    df = load_data()
    print(f"  {len(df)} obs, {df['城市'].nunique()} cities, "
          f"years {int(df['年份'].min())}-{int(df['年份'].max())}")

    # ---- 构造滞后变量 ----
    risk_vars = ['早期投资事件占比', '加权风险偏好指数', '早期投资金额占比']
    df = create_lagged_vars(df, risk_vars)
    print("  Created lagged risk preference variables.")

    # ---- 变量定义 ----
    # 被解释变量 (专利)
    Y_main = 'ln_发明专利申请数'
    Y_alt1 = 'ln_专利申请受理数'
    Y_alt2 = 'ln_专利授权数'
    Y_alt3 = 'ln_发明专利授权数'

    # 核心解释变量 (风险偏好)
    X_main = '早期投资事件占比'
    X_alt1 = '加权风险偏好指数'
    X_alt2 = '早期投资金额占比'

    # 滞后一期风险偏好
    X_main_lag = 'L1_早期投资事件占比'
    X_alt1_lag = 'L1_加权风险偏好指数'

    # 控制变量
    CONTROLS = ['ln_人均GDP', '第二产业占比', '科技支出占比', 'ln_人口']

    # 财政变量 (额外控制)
    FISCAL = '滞后一期财政缺口率'

    # ---- PART F: 描述性统计 ----
    desc_vars = [
        Y_main, Y_alt1, Y_alt2, Y_alt3,
        X_main, X_alt1, X_alt2,
        FISCAL, '当期财政缺口率',
    ] + CONTROLS
    descriptive_stats(df, desc_vars)

    # ---- 控制变量覆盖情况 ----
    print("  Control variable coverage:")
    for cv in CONTROLS + [FISCAL]:
        if cv in df.columns:
            nn = df[cv].notna().sum()
            print(f"    {cv}: {nn}/{len(df)} ({nn/len(df)*100:.0f}%)")

    # ==================================================================
    # PART A: 基准回归 — 风险偏好 → 发明专利 (无控制 vs 有控制)
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART A: 基准回归 — 风险偏好 → 发明专利")
    print("#" * 78)

    # A1: 早期投资事件占比, 无控制
    res_a1 = run_panel_fe(df, Y_main, [X_main],
        title="A1: 早期投资事件占比 → ln_发明专利申请数 (无控制)")

    # A2: 早期投资事件占比, 有控制
    res_a2 = run_panel_fe(df, Y_main, [X_main] + CONTROLS,
        title="A2: 早期投资事件占比 → ln_发明专利申请数 (有控制)")

    # A3: 加权风险偏好指数, 无控制
    res_a3 = run_panel_fe(df, Y_main, [X_alt1],
        title="A3: 加权风险偏好指数 → ln_发明专利申请数 (无控制)")

    # A4: 加权风险偏好指数, 有控制
    res_a4 = run_panel_fe(df, Y_main, [X_alt1] + CONTROLS,
        title="A4: 加权风险偏好指数 → ln_发明专利申请数 (有控制)")

    # ==================================================================
    # PART B: 替换被解释变量 (稳健性)
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART B: 替换被解释变量 (稳健性)")
    print("#" * 78)

    for i, (y_var, y_label) in enumerate([
        (Y_alt1, '专利申请受理数'),
        (Y_alt2, '专利授权数'),
        (Y_alt3, '发明专利授权数'),
    ], start=1):
        run_panel_fe(df, y_var, [X_main] + CONTROLS,
            title=f"B{i}: 早期投资事件占比 → ln_{y_label} (有控制)")

    for i, (y_var, y_label) in enumerate([
        (Y_alt1, '专利申请受理数'),
        (Y_alt2, '专利授权数'),
        (Y_alt3, '发明专利授权数'),
    ], start=4):
        run_panel_fe(df, y_var, [X_alt1] + CONTROLS,
            title=f"B{i}: 加权风险偏好指数 → ln_{y_label} (有控制)")

    # ==================================================================
    # PART C: 替换核心解释变量 (早期投资金额占比)
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART C: 替换核心解释变量 — 早期投资金额占比")
    print("#" * 78)

    res_c1 = run_panel_fe(df, Y_main, [X_alt2] + CONTROLS,
        title="C1: 早期投资金额占比 → ln_发明专利申请数 (有控制)")

    res_c2 = run_panel_fe(df, Y_alt1, [X_alt2] + CONTROLS,
        title="C2: 早期投资金额占比 → ln_专利申请受理数 (有控制)")

    # ==================================================================
    # PART D: 加入财政缺口率作为额外控制变量
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART D: 加入滞后一期财政缺口率作为额外控制")
    print("#" * 78)

    res_d1 = run_panel_fe(df, Y_main, [X_main, FISCAL] + CONTROLS,
        title="D1: 早期投资事件占比 + L1财政缺口率 → ln_发明专利申请数")

    res_d2 = run_panel_fe(df, Y_main, [X_alt1, FISCAL] + CONTROLS,
        title="D2: 加权风险偏好指数 + L1财政缺口率 → ln_发明专利申请数")

    res_d3 = run_panel_fe(df, Y_alt1, [X_main, FISCAL] + CONTROLS,
        title="D3: 早期投资事件占比 + L1财政缺口率 → ln_专利申请受理数")

    res_d4 = run_panel_fe(df, Y_alt2, [X_main, FISCAL] + CONTROLS,
        title="D4: 早期投资事件占比 + L1财政缺口率 → ln_专利授权数")

    # ==================================================================
    # PART E: 使用滞后一期风险偏好 (缓解反向因果)
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART E: 滞后一期风险偏好 → 专利 (缓解反向因果)")
    print("#" * 78)

    res_e1 = run_panel_fe(df, Y_main, [X_main_lag] + CONTROLS,
        title="E1: L1_早期投资事件占比 → ln_发明专利申请数")

    res_e2 = run_panel_fe(df, Y_main, [X_alt1_lag] + CONTROLS,
        title="E2: L1_加权风险偏好指数 → ln_发明专利申请数")

    res_e3 = run_panel_fe(df, Y_alt1, [X_main_lag] + CONTROLS,
        title="E3: L1_早期投资事件占比 → ln_专利申请受理数")

    res_e4 = run_panel_fe(df, Y_alt2, [X_main_lag] + CONTROLS,
        title="E4: L1_早期投资事件占比 → ln_专利授权数")

    # 滞后一期 + 财政缺口率
    res_e5 = run_panel_fe(df, Y_main, [X_main_lag, FISCAL] + CONTROLS,
        title="E5: L1_早期投资事件占比 + L1财政缺口率 → ln_发明专利申请数")

    # ==================================================================
    # 总结
    # ==================================================================
    print("\n" + "=" * 78)
    print("  REGRESSION SUMMARY")
    print("=" * 78)
    print("""
    本次回归以风险偏好为核心解释变量, 专利为被解释变量:

      PART A: 基准回归 (早期投资事件占比 / 加权风险偏好指数 → 发明专利)
      PART B: 替换被解释变量 (专利申请受理数 / 专利授权数 / 发明专利授权数)
      PART C: 替换核心解释变量 (早期投资金额占比)
      PART D: 加入财政缺口率作为额外控制 (检验风险偏好独立效应)
      PART E: 滞后一期风险偏好 (缓解反向因果)

    理论预期: 风险偏好 → 专利 系数为正
      (风险偏好越高 = 更多早期投资 → 更高创新产出)

    控制变量: ln_人均GDP, 第二产业占比, 科技支出占比, ln_人口
    固定效应: 城市FE + 年份FE
    标准误:   城市层面聚类稳健标准误
    """)
    print("All regressions completed.")


if __name__ == "__main__":
    main()
