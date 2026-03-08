"""
run_risk_patent_regression_v2.py
==============================================
风险偏好(t-1) → 专利(t) 面板回归  (2010-2023)

变更说明 (对比 v1):
  1. 时间限定: 2010-2023 年
  2. 所有解释变量 (风险偏好 + 控制变量) 均取滞后一期 (t-1)
     被解释变量 (专利) 取当期 (t)
  3. 方便与 v1 全样本当期结果进行比较

模型:
  innovation_{c,t} = α₀ + α₁ risk_pref_{c,t-1} + γ X_{c,t-1} + μ_c + λ_t + ε_{c,t}
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS


# ======================================================================
# 辅助函数
# ======================================================================

def load_data():
    df = pd.read_csv('cleaned_data/final_regression_dataset.csv', encoding='utf-8-sig')
    for col in df.columns:
        if col not in ['城市']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def create_all_lags(df, var_list):
    """为所有指定变量创建滞后一期 (按城市分组, 按年份排序)."""
    df = df.sort_values(['城市', '年份']).copy()
    for var in var_list:
        if var in df.columns:
            lag_name = f'L1_{var}'
            if lag_name not in df.columns:
                df[lag_name] = df.groupby('城市')[var].shift(1)
    return df


def prepare_panel(df, dep_var, indep_vars):
    cols = list(set([dep_var] + indep_vars + ['城市', '年份']))
    sub = df[cols].dropna().copy()
    sub = sub.set_index(['城市', '年份'])
    return sub


def run_panel_fe(df, dep_var, indep_vars, title=""):
    sub = prepare_panel(df, dep_var, indep_vars)
    if len(sub) < 30:
        print(f"\n  [SKIP] {title}: only {len(sub)} obs after dropping NA")
        return None

    formula = f'{dep_var} ~ 1 + {" + ".join(indep_vars)} + EntityEffects + TimeEffects'
    mod = PanelOLS.from_formula(formula, data=sub)
    res = mod.fit(cov_type='clustered', cluster_entity=True)

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


def descriptive_stats(df, var_list, label=""):
    existing = [v for v in var_list if v in df.columns]
    desc = df[existing].describe().T
    desc['non_null'] = df[existing].notnull().sum()
    print(f"\n{'='*90}")
    print(f"  DESCRIPTIVE STATISTICS  {label}")
    print(f"{'='*90}")
    print(desc[['non_null', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']].round(4).to_string())
    print()


# ======================================================================
# 主回归流程
# ======================================================================

def main():
    print("=" * 78)
    print("  风险偏好(t-1) → 专利(t) 面板回归  [2010-2023]")
    print("  所有解释变量均取滞后一期")
    print("=" * 78)

    # ---- 加载数据 ----
    print("\nLoading data ...")
    df_full = load_data()
    print(f"  Full dataset: {len(df_full)} obs, {df_full['城市'].nunique()} cities, "
          f"years {int(df_full['年份'].min())}-{int(df_full['年份'].max())}")

    # ---- 构造所有变量的滞后项 (在筛选年份之前, 确保 lag 正确) ----
    vars_to_lag = [
        '早期投资事件占比', '加权风险偏好指数', '早期投资金额占比',
        'ln_人均GDP', '第二产业占比', '科技支出占比', 'ln_人口',
        '当期财政缺口率', '金融深度', '外资占比', '债务率',
    ]
    df_full = create_all_lags(df_full, vars_to_lag)

    # ---- 筛选 2010-2023 ----
    df = df_full[(df_full['年份'] >= 2010) & (df_full['年份'] <= 2023)].copy()
    print(f"  After filter [2010-2023]: {len(df)} obs, {df['城市'].nunique()} cities, "
          f"years {int(df['年份'].min())}-{int(df['年份'].max())}")

    # ---- 变量定义 ----
    # 被解释变量 (当期 t)
    Y_main = 'ln_发明专利申请数'
    Y_alt1 = 'ln_专利申请受理数'
    Y_alt2 = 'ln_专利授权数'
    Y_alt3 = 'ln_发明专利授权数'

    # 核心解释变量: 滞后一期 (t-1)
    X_main = 'L1_早期投资事件占比'
    X_alt1 = 'L1_加权风险偏好指数'
    X_alt2 = 'L1_早期投资金额占比'

    # 控制变量: 滞后一期 (t-1)
    CONTROLS = ['L1_ln_人均GDP', 'L1_第二产业占比', 'L1_科技支出占比', 'L1_ln_人口']

    # 财政变量: 滞后一期 (t-1) — 即滞后一期当期缺口率
    FISCAL = 'L1_当期财政缺口率'

    # ---- 描述性统计 (限定后的样本) ----
    desc_vars = [
        Y_main, Y_alt1, Y_alt2, Y_alt3,
        X_main, X_alt1, X_alt2, FISCAL,
    ] + CONTROLS
    descriptive_stats(df, desc_vars, label="[2010-2023, 滞后一期]")

    # ---- 覆盖情况 ----
    print("  Variable coverage (2010-2023):")
    for cv in [X_main, X_alt1, X_alt2, FISCAL] + CONTROLS:
        if cv in df.columns:
            nn = df[cv].notna().sum()
            print(f"    {cv}: {nn}/{len(df)} ({nn/len(df)*100:.0f}%)")

    # ==================================================================
    # PART A: 基准回归 — L1风险偏好 → 发明专利
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART A: 基准回归 — L1_风险偏好 → 发明专利 [2010-2023]")
    print("#" * 78)

    res_a1 = run_panel_fe(df, Y_main, [X_main],
        title="A1: L1_早期投资事件占比 → ln_发明专利申请数 (无控制)")

    res_a2 = run_panel_fe(df, Y_main, [X_main] + CONTROLS,
        title="A2: L1_早期投资事件占比 → ln_发明专利申请数 (有控制)")

    res_a3 = run_panel_fe(df, Y_main, [X_alt1],
        title="A3: L1_加权风险偏好指数 → ln_发明专利申请数 (无控制)")

    res_a4 = run_panel_fe(df, Y_main, [X_alt1] + CONTROLS,
        title="A4: L1_加权风险偏好指数 → ln_发明专利申请数 (有控制)")

    # ==================================================================
    # PART B: 替换被解释变量 (稳健性)
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART B: 替换被解释变量 (稳健性) [2010-2023]")
    print("#" * 78)

    for i, (y_var, y_label) in enumerate([
        (Y_alt1, '专利申请受理数'), (Y_alt2, '专利授权数'), (Y_alt3, '发明专利授权数'),
    ], start=1):
        run_panel_fe(df, y_var, [X_main] + CONTROLS,
            title=f"B{i}: L1_早期投资事件占比 → ln_{y_label} (有控制)")

    for i, (y_var, y_label) in enumerate([
        (Y_alt1, '专利申请受理数'), (Y_alt2, '专利授权数'), (Y_alt3, '发明专利授权数'),
    ], start=4):
        run_panel_fe(df, y_var, [X_alt1] + CONTROLS,
            title=f"B{i}: L1_加权风险偏好指数 → ln_{y_label} (有控制)")

    # ==================================================================
    # PART C: 替换核心解释变量 (早期投资金额占比)
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART C: 替换核心解释变量 — L1_早期投资金额占比 [2010-2023]")
    print("#" * 78)

    res_c1 = run_panel_fe(df, Y_main, [X_alt2] + CONTROLS,
        title="C1: L1_早期投资金额占比 → ln_发明专利申请数 (有控制)")
    res_c2 = run_panel_fe(df, Y_alt1, [X_alt2] + CONTROLS,
        title="C2: L1_早期投资金额占比 → ln_专利申请受理数 (有控制)")

    # ==================================================================
    # PART D: 加入财政缺口率作为额外控制
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART D: 加入L1财政缺口率作为额外控制 [2010-2023]")
    print("#" * 78)

    res_d1 = run_panel_fe(df, Y_main, [X_main, FISCAL] + CONTROLS,
        title="D1: L1_早期投资事件占比 + L1财政缺口率 → ln_发明专利申请数")
    res_d2 = run_panel_fe(df, Y_main, [X_alt1, FISCAL] + CONTROLS,
        title="D2: L1_加权风险偏好指数 + L1财政缺口率 → ln_发明专利申请数")
    res_d3 = run_panel_fe(df, Y_alt1, [X_main, FISCAL] + CONTROLS,
        title="D3: L1_早期投资事件占比 + L1财政缺口率 → ln_专利申请受理数")
    res_d4 = run_panel_fe(df, Y_alt2, [X_main, FISCAL] + CONTROLS,
        title="D4: L1_早期投资事件占比 + L1财政缺口率 → ln_专利授权数")
    res_d5 = run_panel_fe(df, Y_alt3, [X_main, FISCAL] + CONTROLS,
        title="D5: L1_早期投资事件占比 + L1财政缺口率 → ln_发明专利授权数")

    # ==================================================================
    # PART E: 对比 — 当期风险偏好 (不滞后) + 滞后控制 [2010-2023]
    # ==================================================================
    print("\n" + "#" * 78)
    print("  PART E: 对比 — 当期风险偏好 + 滞后控制 [2010-2023]")
    print("#" * 78)

    res_e1 = run_panel_fe(df, Y_main, ['早期投资事件占比'] + CONTROLS,
        title="E1: 当期早期投资事件占比 + L1控制 → ln_发明专利申请数")
    res_e2 = run_panel_fe(df, Y_main, ['加权风险偏好指数'] + CONTROLS,
        title="E2: 当期加权风险偏好指数 + L1控制 → ln_发明专利申请数")

    # ==================================================================
    # 总结对比
    # ==================================================================
    print("\n" + "=" * 78)
    print("  REGRESSION SUMMARY & COMPARISON")
    print("=" * 78)
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  v2 变更 (相对 v1):                                                ║
    ║    1. 样本时间: 全样本 → 2010-2023                                  ║
    ║    2. 解释变量: 当期 → 全部滞后一期 (t-1)                           ║
    ║       含风险偏好变量和控制变量均取 t-1                               ║
    ║    3. 模型: Y(t) = α + β·X(t-1) + γ·Controls(t-1) + FE + ε        ║
    ╚══════════════════════════════════════════════════════════════════════╝

    理论预期: β > 0 (风险偏好越高 → 更多早期投资 → t+1创新产出增加)

    PART A: 基准回归 (L1_早期投资事件占比 / L1_加权风险偏好指数 → 发明专利)
    PART B: 替换被解释变量 (稳健性)
    PART C: 替换核心解释变量 (L1_早期投资金额占比)
    PART D: 加入L1财政缺口率 (检验控制财政后风险偏好的独立效应)
    PART E: 对比当期风险偏好 (同样限定2010-2023, 但风险偏好不滞后)

    固定效应: 城市FE + 年份FE
    标准误:   城市层面聚类稳健标准误
    """)
    print("All regressions completed.")


if __name__ == "__main__":
    main()
