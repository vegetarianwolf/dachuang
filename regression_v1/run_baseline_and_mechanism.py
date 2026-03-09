"""
基准回归 + 机制检验（完整版）
==============================
解释变量：
  (1) 财政缺口率_滞后一期
  (2) ln(债务率_滞后一期)

基准回归：
  A. 不加控制变量
  B. 加控制变量（人均GDP_对数、第二产业占比、科技支出占比、外资依存度、金融深度）

机制检验：
  Baron & Kenny 三步法 + Sobel 检验
  中介变量 M = early_deal_ratio（早期投资事件数占比）

固定效应：城市 + 年份双向固定效应
标准误：聚类到城市层面

输出：
  regression_v1/regression_results.md
"""

import pandas as pd
import numpy as np
import warnings
import os
import sys
from datetime import datetime

warnings.filterwarnings('ignore')

# ===================== 配置 =====================
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'cleaned_data',
                         'final_regression_panel_v3_cityfiltered.csv')
PE_PATH = os.path.join(os.path.dirname(__file__), '..', 'cleaned_data',
                       'PE_investment_events_cleaned.csv')
OUTPUT_DIR = os.path.dirname(__file__)

# 控制变量列表（按思路设计）
CONTROLS = ['人均GDP_对数', '第二产业占比', '科技支出占比', '外资依存度', '金融深度']

# 被解释变量
DEP_VARS = {
    'ln_inv_patent': '发明专利申请量_对数',
    'ln_patent_total': '专利申请总量_对数',
    'inv_share': '发明专利占比',
}

# ===================== 工具函数 =====================

def sig_stars(p):
    if p < 0.01: return '***'
    elif p < 0.05: return '**'
    elif p < 0.1: return '*'
    else: return ''


def format_coef(coef, se, p):
    """格式化系数：系数(标准误)显著性"""
    stars = sig_stars(p)
    return f"{coef:.4f}{stars}", f"({se:.4f})"


def run_panel_ols(panel_idx, dep_var, indep_vars, label=""):
    """运行双向固定效应面板 OLS 回归"""
    from linearmodels.panel import PanelOLS
    
    all_vars = [dep_var] + indep_vars
    reg_data = panel_idx[all_vars].dropna()
    
    n_obs = reg_data.shape[0]
    n_cities = reg_data.index.get_level_values(0).nunique()
    n_years = reg_data.index.get_level_values(1).nunique()
    
    if n_obs < 30:
        print(f"  [SKIP] {label}: 有效样本仅 {n_obs}，跳过")
        return None
    
    mod = PanelOLS(
        reg_data[dep_var], reg_data[indep_vars],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res = mod.fit(cov_type='clustered', cluster_entity=True)
    
    print(f"  {label}: N={n_obs}, 城市={n_cities}, R²w={res.rsquared_within:.4f}")
    for v in indep_vars:
        coef = res.params[v]
        se = res.std_errors[v]
        t = res.tstats[v]
        p = res.pvalues[v]
        print(f"    {v}: β={coef:.4f}, se={se:.4f}, t={t:.3f}, p={p:.4f} {sig_stars(p)}")
    
    return {
        'result': res,
        'n_obs': n_obs,
        'n_cities': n_cities,
        'n_years': n_years,
    }


# ===================== 1. 加载数据 =====================
print("=" * 70)
print("1. 加载与准备数据")
print("=" * 70)

panel = pd.read_csv(DATA_PATH)
print(f"面板数据: {panel.shape[0]} 行, {panel.shape[1]} 列")
print(f"城市数: {panel['城市'].nunique()}, 年份: {panel['年份'].min()}-{panel['年份'].max()}")

# ===================== 2. 构建 ln(债务率) =====================
print("\n--- 构建 ln(债务率) 变量 ---")
# 债务率 > 0 才取对数
panel['ln_债务率'] = np.where(panel['债务率'] > 0, np.log(panel['债务率']), np.nan)
panel['ln_债务率_滞后一期'] = np.where(
    panel['债务率_滞后一期'] > 0,
    np.log(panel['债务率_滞后一期']),
    np.nan
)
print(f"ln(债务率_滞后一期): 有效={panel['ln_债务率_滞后一期'].notna().sum()}, "
      f"均值={panel['ln_债务率_滞后一期'].dropna().mean():.4f}, "
      f"标准差={panel['ln_债务率_滞后一期'].dropna().std():.4f}")

# ===================== 3. 构建中介变量 =====================
print("\n--- 构建中介变量 (early_deal_ratio) ---")
pe = pd.read_csv(PE_PATH, low_memory=False)
valid_stages = ['种子期', '初创期', '扩张期', '成熟期']
pe_valid = pe[pe['投资阶段'].isin(valid_stages)].copy()
pe_valid['is_early'] = pe_valid['投资阶段'].isin(['种子期', '初创期']).astype(int)

panel['城市_match'] = panel['城市'].str.replace('市$', '', regex=True)

pe_agg = pe_valid.groupby(['City', 'Year']).agg(
    total_deals=('is_early', 'count'),
    early_deals=('is_early', 'sum'),
    total_amount=('Inv_Amount_RMB_M', lambda x: x.dropna().sum()),
    early_amount=('Inv_Amount_RMB_M', lambda x: x[pe_valid.loc[x.index, 'is_early'] == 1].dropna().sum())
).reset_index()

pe_agg['early_deal_ratio'] = pe_agg['early_deals'] / pe_agg['total_deals']
pe_agg['early_amount_ratio'] = np.where(
    pe_agg['total_amount'] > 0,
    pe_agg['early_amount'] / pe_agg['total_amount'],
    np.nan
)
pe_agg.rename(columns={'City': '城市_match', 'Year': '年份'}, inplace=True)
pe_agg['年份'] = pe_agg['年份'].astype(int)

panel = panel.merge(
    pe_agg[['城市_match', '年份', 'early_deal_ratio', 'early_amount_ratio',
            'total_deals', 'early_deals']],
    on=['城市_match', '年份'], how='left'
)
matched = panel['early_deal_ratio'].notna().sum()
print(f"中介变量匹配: {matched}/{panel.shape[0]} ({matched/panel.shape[0]*100:.1f}%)")

# ===================== 4. 安装 linearmodels =====================
try:
    import linearmodels
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'linearmodels'])
    import linearmodels

from linearmodels.panel import PanelOLS
from scipy import stats

# ===================== 5. 准备面板索引 =====================
panel['city_id'] = pd.Categorical(panel['城市']).codes
panel_idx = panel.set_index(['city_id', '年份'])

# ===================== 6. 描述性统计 =====================
print("\n" + "=" * 70)
print("2. 关键变量描述性统计")
print("=" * 70)

desc_vars = {
    '发明专利申请量_对数': 'Y: ln(发明专利)',
    '专利申请总量_对数': 'Y: ln(专利总量)',
    '发明专利占比': 'Y: 发明专利占比',
    '财政缺口率_滞后一期': 'X1: 财政缺口率(L1)',
    'ln_债务率_滞后一期': 'X2: ln(债务率)(L1)',
    'early_deal_ratio': 'M: 早期投资占比(事件)',
    'early_amount_ratio': 'M: 早期投资占比(金额)',
}
desc_vars.update({c: f'控制: {c}' for c in CONTROLS})

desc_rows = []
for var, label in desc_vars.items():
    if var in panel.columns:
        s = panel[var].dropna()
        desc_rows.append({
            '变量': label,
            '列名': var,
            'N': len(s),
            '缺失率': f"{(1 - len(s)/len(panel))*100:.1f}%",
            '均值': f"{s.mean():.4f}",
            '标准差': f"{s.std():.4f}",
            '最小值': f"{s.min():.4f}",
            '中位数': f"{s.median():.4f}",
            '最大值': f"{s.max():.4f}",
        })
        print(f"  {label}: N={len(s)}, mean={s.mean():.4f}, sd={s.std():.4f}")

desc_df = pd.DataFrame(desc_rows)

# ===================== 存储所有结果用于 MD 输出 =====================
all_results = {}  # 键: (模型名, 解释变量类型)

# ===================== 7. 基准回归 =====================
print("\n" + "=" * 70)
print("3. 基准回归")
print("=" * 70)

# 两个核心解释变量
X_VARS = {
    'fiscal_gap': '财政缺口率_滞后一期',
    'ln_debt': 'ln_债务率_滞后一期',
}

# ---------- A: 不加控制变量 ----------
print("\n========== A: 不加控制变量 ==========")
for x_key, x_col in X_VARS.items():
    for y_key, y_col in DEP_VARS.items():
        label = f"[无控制] {y_key} ~ {x_key}"
        res = run_panel_ols(panel_idx, y_col, [x_col], label=label)
        if res:
            all_results[('baseline_no_ctrl', x_key, y_key)] = res

# ---------- B: 加控制变量 ----------
print("\n========== B: 加控制变量 ==========")
# 先检查不含金融深度的控制子集（覆盖率更高）
CONTROLS_CORE = ['人均GDP_对数', '第二产业占比', '科技支出占比']
CONTROLS_FULL = CONTROLS.copy()

for ctrl_label, ctrl_list in [('core_ctrl', CONTROLS_CORE), ('full_ctrl', CONTROLS_FULL)]:
    print(f"\n--- 控制变量集: {ctrl_label} ({', '.join(ctrl_list)}) ---")
    for x_key, x_col in X_VARS.items():
        for y_key, y_col in [('ln_inv_patent', '发明专利申请量_对数')]:  # 主推荐被解释变量
            indep = [x_col] + ctrl_list
            label = f"[{ctrl_label}] {y_key} ~ {x_key}"
            res = run_panel_ols(panel_idx, y_col, indep, label=label)
            if res:
                all_results[('baseline_ctrl', ctrl_label, x_key, y_key)] = res

# 加控制变量对其他被解释变量也跑一下（用核心控制变量集）
print("\n--- 核心控制变量，其他被解释变量 ---")
for x_key, x_col in X_VARS.items():
    for y_key, y_col in DEP_VARS.items():
        if y_key == 'ln_inv_patent':
            continue  # 已经跑过
        indep = [x_col] + CONTROLS_CORE
        label = f"[core_ctrl] {y_key} ~ {x_key}"
        res = run_panel_ols(panel_idx, y_col, indep, label=label)
        if res:
            all_results[('baseline_ctrl', 'core_ctrl', x_key, y_key)] = res

# ===================== 8. 机制检验 =====================
print("\n" + "=" * 70)
print("4. 机制检验: Baron & Kenny 三步法")
print("=" * 70)

mediator_var = 'early_deal_ratio'
mediator_label = '早期投资占比(事件数)'

for x_key, x_col in X_VARS.items():
    print(f"\n{'='*50}")
    print(f"核心解释变量: {x_key} ({x_col})")
    print(f"{'='*50}")
    
    dep_main = '发明专利申请量_对数'
    
    # ---- 无控制变量的中介检验 ----
    for ctrl_label, ctrl_list in [('no_ctrl', []), ('core_ctrl', CONTROLS_CORE)]:
        print(f"\n--- 中介检验 [{ctrl_label}] ---")
        
        # 步骤0: 总效应 X → Y
        indep0 = [x_col] + ctrl_list
        res0 = run_panel_ols(panel_idx, dep_main, indep0,
                             label=f"步骤0 [{ctrl_label}]: X→Y")
        if res0:
            all_results[('mediation', ctrl_label, x_key, 'step0')] = res0
        
        # 步骤1: X → M
        indep1 = [x_col] + ctrl_list
        res1 = run_panel_ols(panel_idx, mediator_var, indep1,
                             label=f"步骤1 [{ctrl_label}]: X→M")
        if res1:
            all_results[('mediation', ctrl_label, x_key, 'step1')] = res1
        
        # 步骤2: M → Y
        indep2 = [mediator_var] + ctrl_list
        res2 = run_panel_ols(panel_idx, dep_main, indep2,
                             label=f"步骤2 [{ctrl_label}]: M→Y")
        if res2:
            all_results[('mediation', ctrl_label, x_key, 'step2')] = res2
        
        # 步骤3: X + M → Y
        indep3 = [x_col, mediator_var] + ctrl_list
        res3 = run_panel_ols(panel_idx, dep_main, indep3,
                             label=f"步骤3 [{ctrl_label}]: X+M→Y")
        if res3:
            all_results[('mediation', ctrl_label, x_key, 'step3')] = res3
        
        # Sobel 检验
        if res1 and res3:
            try:
                a = res1['result'].params[x_col]
                se_a = res1['result'].std_errors[x_col]
                b = res3['result'].params[mediator_var]
                se_b = res3['result'].std_errors[mediator_var]
                
                sobel_se = np.sqrt(a**2 * se_b**2 + b**2 * se_a**2)
                sobel_z = (a * b) / sobel_se if sobel_se > 0 else np.nan
                sobel_p = 2 * (1 - stats.norm.cdf(abs(sobel_z))) if not np.isnan(sobel_z) else np.nan
                
                total_effect = res0['result'].params[x_col] if res0 else np.nan
                direct_effect = res3['result'].params[x_col]
                indirect_effect = a * b
                
                sobel_info = {
                    'a': a, 'se_a': se_a,
                    'b': b, 'se_b': se_b,
                    'indirect': indirect_effect,
                    'sobel_z': sobel_z,
                    'sobel_p': sobel_p,
                    'total_effect': total_effect,
                    'direct_effect': direct_effect,
                }
                all_results[('sobel', ctrl_label, x_key)] = sobel_info
                
                print(f"\n  Sobel 检验 [{ctrl_label}]:")
                print(f"    间接效应 (a×b) = {indirect_effect:.6f}")
                print(f"    Sobel Z = {sobel_z:.4f}, p = {sobel_p:.4f} {sig_stars(sobel_p)}")
                print(f"    总效应 (c) = {total_effect:.4f}")
                print(f"    直接效应 (c') = {direct_effect:.4f}")
            except Exception as e:
                print(f"  Sobel检验出错: {e}")


# ===================== 9. 生成 Markdown 报告 =====================
print("\n" + "=" * 70)
print("5. 生成 Markdown 报告")
print("=" * 70)

md_lines = []
md = md_lines.append

md(f"# 基准回归与机制检验结果")
md(f"")
md(f"> **运行日期**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
md(f"> **数据源**：`cleaned_data/final_regression_panel_v3_cityfiltered.csv`")
md(f"> **回归脚本**：`regression_v1/run_baseline_and_mechanism.py`")
md(f"> **方法**：双向固定效应（城市 FE + 年份 FE），聚类标准误到城市层面")
md(f"")
md(f"---")
md(f"")

# ---- 描述性统计 ----
md(f"## 一、描述性统计")
md(f"")
md(f"| 变量 | N | 缺失率 | 均值 | 标准差 | 最小值 | 中位数 | 最大值 |")
md(f"|------|--:|-------:|-----:|-------:|-------:|-------:|-------:|")
for _, row in desc_df.iterrows():
    md(f"| {row['变量']} | {row['N']} | {row['缺失率']} | {row['均值']} | {row['标准差']} | {row['最小值']} | {row['中位数']} | {row['最大值']} |")
md(f"")

# ---- 基准回归 (无控制变量) ----
md(f"---")
md(f"")
md(f"## 二、基准回归结果")
md(f"")
md(f"### 2.1 不加控制变量")
md(f"")
md(f"$$")
md(f"Y_{{c,t}} = \\alpha + \\beta \\cdot X_{{c,t-1}} + \\mu_c + \\lambda_t + \\varepsilon_{{c,t}}")
md(f"$$")
md(f"")

# 构建表格
dep_names_cn = {'ln_inv_patent': 'ln(发明专利)', 'ln_patent_total': 'ln(专利总量)', 'inv_share': '发明专利占比'}
x_names_cn = {'fiscal_gap': '财政缺口率(L1)', 'ln_debt': 'ln(债务率)(L1)'}

md(f"| 模型 | 被解释变量 | 解释变量 | 系数 β | 标准误 | t 值 | p 值 | 显著性 | R²(within) | N | 城市数 |")
md(f"|:----:|:---------:|:-------:|------:|------:|-----:|-----:|:-----:|----------:|--:|------:|")

model_num = 0
for x_key in ['fiscal_gap', 'ln_debt']:
    for y_key in ['ln_inv_patent', 'ln_patent_total', 'inv_share']:
        key = ('baseline_no_ctrl', x_key, y_key)
        if key in all_results:
            model_num += 1
            r = all_results[key]
            res = r['result']
            x_col = X_VARS[x_key]
            coef = res.params[x_col]
            se = res.std_errors[x_col]
            t = res.tstats[x_col]
            p = res.pvalues[x_col]
            stars = sig_stars(p)
            bold = "**" if p < 0.1 else ""
            md(f"| ({model_num}) | {dep_names_cn[y_key]} | {x_names_cn[x_key]} | {bold}{coef:.4f}{bold} | {se:.4f} | {t:.3f} | {p:.4f} | {stars} | {res.rsquared_within:.4f} | {r['n_obs']} | {r['n_cities']} |")

md(f"")
md(f"> 注：\\*\\*\\* p<0.01, \\*\\* p<0.05, \\* p<0.1")
md(f"")

# ---- 基准回归 (加控制变量) ----
md(f"### 2.2 加控制变量")
md(f"")
md(f"$$")
md(f"Y_{{c,t}} = \\alpha + \\beta \\cdot X_{{c,t-1}} + \\gamma \\mathbf{{Z}}_{{c,t}} + \\mu_c + \\lambda_t + \\varepsilon_{{c,t}}")
md(f"$$")
md(f"")
md(f"控制变量 $\\mathbf{{Z}}$：")
md(f"- **核心控制 (core_ctrl)**：人均GDP(对数)、第二产业占比、科技支出占比")
md(f"- **完整控制 (full_ctrl)**：核心控制 + 外资依存度、金融深度")
md(f"")

# 对于主被解释变量 ln(发明专利)，列出核心和完整控制的结果对比
md(f"#### 被解释变量：ln(发明专利申请量)")
md(f"")

# 收集所有加控制的结果
ctrl_results_table = []
for ctrl_label in ['core_ctrl', 'full_ctrl']:
    for x_key in ['fiscal_gap', 'ln_debt']:
        key = ('baseline_ctrl', ctrl_label, x_key, 'ln_inv_patent')
        if key in all_results:
            r = all_results[key]
            res = r['result']
            x_col = X_VARS[x_key]
            ctrl_results_table.append({
                'ctrl': ctrl_label,
                'x_key': x_key,
                'res': res,
                'r': r,
            })

if ctrl_results_table:
    # 表头：各模型为列
    n_models = len(ctrl_results_table)
    header1 = "| 变量 |"
    header2 = "|:-----|"
    for i, item in enumerate(ctrl_results_table):
        header1 += f" ({i+1}) {item['ctrl']}/{x_names_cn[item['x_key']]} |"
        header2 += "------:|"
    md(header1)
    md(header2)
    
    # 核心解释变量行
    for var_name in ['核心解释变量']:
        row = f"| **{var_name}** |"
        for item in ctrl_results_table:
            x_col = X_VARS[item['x_key']]
            res = item['res']
            coef = res.params[x_col]
            p = res.pvalues[x_col]
            se = res.std_errors[x_col]
            stars = sig_stars(p)
            row += f" {coef:.4f}{stars} |"
        md(row)
        # 标准误行
        row_se = f"|  |"
        for item in ctrl_results_table:
            x_col = X_VARS[item['x_key']]
            se = item['res'].std_errors[x_col]
            row_se += f" ({se:.4f}) |"
        md(row_se)
    
    # 控制变量行
    all_ctrl_names = set()
    for item in ctrl_results_table:
        all_ctrl_names.update([v for v in item['res'].params.index if v != X_VARS[item['x_key']]])
    
    for ctrl_name in sorted(all_ctrl_names):
        row = f"| {ctrl_name} |"
        for item in ctrl_results_table:
            res = item['res']
            if ctrl_name in res.params.index:
                coef = res.params[ctrl_name]
                p = res.pvalues[ctrl_name]
                se = res.std_errors[ctrl_name]
                stars = sig_stars(p)
                row += f" {coef:.4f}{stars} |"
            else:
                row += f" — |"
        md(row)
        row_se = f"|  |"
        for item in ctrl_results_table:
            res = item['res']
            if ctrl_name in res.params.index:
                se = res.std_errors[ctrl_name]
                row_se += f" ({se:.4f}) |"
            else:
                row_se += f" — |"
        md(row_se)
    
    # 统计量
    row_r2 = "| R²(within) |"
    row_n = "| N |"
    row_city = "| 城市数 |"
    row_fe = "| 固定效应 |"
    for item in ctrl_results_table:
        row_r2 += f" {item['res'].rsquared_within:.4f} |"
        row_n += f" {item['r']['n_obs']} |"
        row_city += f" {item['r']['n_cities']} |"
        row_fe += f" 城市+年份 |"
    md(row_r2)
    md(row_n)
    md(row_city)
    md(row_fe)
    md(f"")

# 其他被解释变量的核心控制结果
md(f"#### 其他被解释变量（核心控制）")
md(f"")
md(f"| 模型 | 被解释变量 | 解释变量 | 系数 β | 标准误 | t 值 | p 值 | 显著性 | R²(within) | N | 城市数 |")
md(f"|:----:|:---------:|:-------:|------:|------:|-----:|-----:|:-----:|----------:|--:|------:|")

model_num = 0
for x_key in ['fiscal_gap', 'ln_debt']:
    for y_key in ['ln_patent_total', 'inv_share']:
        key = ('baseline_ctrl', 'core_ctrl', x_key, y_key)
        if key in all_results:
            model_num += 1
            r = all_results[key]
            res = r['result']
            x_col = X_VARS[x_key]
            coef = res.params[x_col]
            se = res.std_errors[x_col]
            t = res.tstats[x_col]
            p = res.pvalues[x_col]
            stars = sig_stars(p)
            bold = "**" if p < 0.1 else ""
            md(f"| ({model_num}) | {dep_names_cn[y_key]} | {x_names_cn[x_key]} | {bold}{coef:.4f}{bold} | {se:.4f} | {t:.3f} | {p:.4f} | {stars} | {res.rsquared_within:.4f} | {r['n_obs']} | {r['n_cities']} |")

md(f"")

# ---- 机制检验 ----
md(f"---")
md(f"")
md(f"## 三、机制检验：中介效应")
md(f"")
md(f"### 3.1 理论路径")
md(f"")
md(f"```")
md(f"财政约束 (X) ──→ 政府引导基金早期投资占比 (M) ──→ 发明专利申请量 (Y)")
md(f"```")
md(f"")
md(f"中介变量 M = `early_deal_ratio`（种子期 + 初创期投资事件数 / 总投资事件数）")
md(f"")

for x_key in ['fiscal_gap', 'ln_debt']:
    md(f"### 3.2 解释变量：{x_names_cn[x_key]}")
    md(f"")
    
    for ctrl_label, ctrl_cn in [('no_ctrl', '无控制变量'), ('core_ctrl', '核心控制变量')]:
        md(f"#### {ctrl_cn}")
        md(f"")
        md(f"| 步骤 | 路径 | 被解释变量 | 关键变量 | 系数 | 标准误 | t 值 | p 值 | 显著性 | R²(w) | N |")
        md(f"|:----:|:----:|:---------:|:-------:|-----:|------:|-----:|-----:|:-----:|------:|--:|")
        
        steps = [
            ('step0', 'X→Y', '发明专利申请量_对数'),
            ('step1', 'X→M', 'early_deal_ratio'),
            ('step2', 'M→Y', '发明专利申请量_对数'),
            ('step3', 'X+M→Y', '发明专利申请量_对数'),
        ]
        
        for step_key, path, dep in steps:
            key = ('mediation', ctrl_label, x_key, step_key)
            if key in all_results:
                r = all_results[key]
                res = r['result']
                
                # 显示每个解释变量
                for vname in res.params.index:
                    # 跳过控制变量（只显示核心变量和中介变量）
                    if vname in CONTROLS_CORE or vname in CONTROLS_FULL:
                        continue
                    coef = res.params[vname]
                    se = res.std_errors[vname]
                    t = res.tstats[vname]
                    p = res.pvalues[vname]
                    stars = sig_stars(p)
                    bold = "**" if p < 0.1 else ""
                    short_name = vname.replace('_滞后一期', '(L1)').replace('early_deal_ratio', 'M')
                    md(f"| {step_key} | {path} | {dep.replace('_对数', '(ln)').replace('发明专利申请量', '发明专利')} | {short_name} | {bold}{coef:.4f}{bold} | {se:.4f} | {t:.3f} | {p:.4f} | {stars} | {res.rsquared_within:.4f} | {r['n_obs']} |")
        
        # Sobel
        sobel_key = ('sobel', ctrl_label, x_key)
        if sobel_key in all_results:
            s = all_results[sobel_key]
            md(f"")
            md(f"**Sobel 检验**：")
            md(f"- 间接效应 (a×b) = {s['indirect']:.6f}")
            md(f"- Sobel Z = {s['sobel_z']:.4f}, p = {s['sobel_p']:.4f} {sig_stars(s['sobel_p'])}")
            md(f"- 总效应 (c) = {s['total_effect']:.4f}")
            md(f"- 直接效应 (c') = {s['direct_effect']:.4f}")
            
            if s['total_effect'] != 0 and not np.isnan(s['total_effect']):
                med_pct = s['indirect'] / s['total_effect'] * 100
                md(f"- 中介效应占比 = {med_pct:.2f}%")
        
        md(f"")

# ---- 结果解读 ----
md(f"---")
md(f"")
md(f"## 四、结果解读")
md(f"")
md(f"### 4.1 基准回归")
md(f"")
md(f"#### 不加控制变量")
md(f"")

# 动态生成解读
for x_key in ['fiscal_gap', 'ln_debt']:
    key_main = ('baseline_no_ctrl', x_key, 'ln_inv_patent')
    if key_main in all_results:
        r = all_results[key_main]
        res = r['result']
        x_col = X_VARS[x_key]
        coef = res.params[x_col]
        p = res.pvalues[x_col]
        stars = sig_stars(p)
        sig_text = "显著" if p < 0.1 else "不显著"
        md(f"- **{x_names_cn[x_key]}**→ln(发明专利)：系数={coef:.4f}, p={p:.4f} ({sig_text})")

md(f"")
md(f"#### 加控制变量")
md(f"")

for ctrl_label in ['core_ctrl', 'full_ctrl']:
    for x_key in ['fiscal_gap', 'ln_debt']:
        key_main = ('baseline_ctrl', ctrl_label, x_key, 'ln_inv_patent')
        if key_main in all_results:
            r = all_results[key_main]
            res = r['result']
            x_col = X_VARS[x_key]
            coef = res.params[x_col]
            p = res.pvalues[x_col]
            stars = sig_stars(p)
            sig_text = "显著" if p < 0.1 else "不显著"
            md(f"- **{x_names_cn[x_key]}**[{ctrl_label}]→ln(发明专利)：β={coef:.4f}, p={p:.4f} ({sig_text})")

md(f"")
md(f"### 4.2 机制检验")
md(f"")

for x_key in ['fiscal_gap', 'ln_debt']:
    md(f"#### 解释变量：{x_names_cn[x_key]}")
    md(f"")
    
    for ctrl_label, ctrl_cn in [('no_ctrl', '无控制变量'), ('core_ctrl', '核心控制')]:
        step0_key = ('mediation', ctrl_label, x_key, 'step0')
        step1_key = ('mediation', ctrl_label, x_key, 'step1')
        step2_key = ('mediation', ctrl_label, x_key, 'step2')
        sobel_key = ('sobel', ctrl_label, x_key)
        
        conditions = []
        if step0_key in all_results:
            r0 = all_results[step0_key]['result']
            p0 = r0.pvalues[X_VARS[x_key]]
            conditions.append(f"总效应p={p0:.4f} ({'√' if p0<0.1 else '×'})")
        if step1_key in all_results:
            r1 = all_results[step1_key]['result']
            p1 = r1.pvalues[X_VARS[x_key]]
            conditions.append(f"X→M p={p1:.4f} ({'√' if p1<0.1 else '×'})")
        if step2_key in all_results:
            r2 = all_results[step2_key]['result']
            p2 = r2.pvalues[mediator_var]
            conditions.append(f"M→Y p={p2:.4f} ({'√' if p2<0.1 else '×'})")
        if sobel_key in all_results:
            sp = all_results[sobel_key]['sobel_p']
            conditions.append(f"Sobel p={sp:.4f} ({'√' if sp<0.1 else '×'})")
        
        if conditions:
            md(f"- [{ctrl_cn}]：{', '.join(conditions)}")
    
    md(f"")

md(f"")
md(f"### 4.3 初步判断")
md(f"")
md(f"*（以下判断将依据实际回归结果自动填写，请查看上方具体数值）*")
md(f"")
md(f"1. **假说 H1**（财政约束抑制创新）：检查基准回归中核心解释变量系数的符号和显著性")
md(f"2. **假说 H2**（中介效应）：检查 Baron & Kenny 三步法的各步骤是否满足条件")
md(f"")

md(f"---")
md(f"")
md(f"## 五、注意事项")
md(f"")
md(f"1. **债务率取对数**：本报告中债务率解释变量使用 ln(债务率)，系数可解释为弹性")
md(f"2. **滞后一期**：所有核心解释变量均使用滞后一期值，缓解反向因果")
md(f"3. **聚类标准误**：标准误聚类到城市层面，控制组内自相关")
md(f"4. **中介变量覆盖率较低**：政府引导基金投资数据仅覆盖约 30% 的城市-年份观测")
md(f"5. **金融深度缺失较多**：full_ctrl 规格中因金融深度覆盖率仅 44.9%，样本量大幅缩减")
md(f"")

# 写入文件
md_path = os.path.join(OUTPUT_DIR, 'regression_results.md')
with open(md_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print(f"\n报告已保存到: {md_path}")
print("\n========== 全部完成 ==========")
