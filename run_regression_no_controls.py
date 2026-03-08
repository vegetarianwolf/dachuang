"""
无控制变量的双向固定效应回归 + 中介效应检验
===============================================
基准回归: Y = α + β*X + μ_city + λ_year + ε
中介效应: Baron & Kenny (1986) 三步法
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# =============================================================
# 1. 加载并准备面板数据
# =============================================================
print("=" * 70)
print("1. 加载数据")
print("=" * 70)

panel = pd.read_csv('cleaned_data/final_regression_panel_v3_cityfiltered.csv')
print(f"面板数据: {panel.shape[0]} 行, {panel.shape[1]} 列")
print(f"城市数: {panel['城市'].nunique()}, 年份范围: {panel['年份'].min()}-{panel['年份'].max()}")

# =============================================================
# 2. 构建中介变量: 早期投资占比 (从PE投资事件数据)
# =============================================================
print("\n" + "=" * 70)
print("2. 构建中介变量 (early_deal_ratio)")
print("=" * 70)

pe = pd.read_csv('cleaned_data/PE_investment_events_cleaned.csv', low_memory=False)
# 仅保留有效投资阶段
valid_stages = ['种子期', '初创期', '扩张期', '成熟期']
pe_valid = pe[pe['投资阶段'].isin(valid_stages)].copy()
pe_valid['is_early'] = pe_valid['投资阶段'].isin(['种子期', '初创期']).astype(int)

# 城市名标准化 - 去掉面板数据中的"市"后缀来匹配PE数据
panel['城市_match'] = panel['城市'].str.replace('市$', '', regex=True)

# 按城市-年份聚合
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

print(f"PE聚合: {pe_agg.shape[0]} 个城市-年份观测")
print(f"早期投资占比(事件数) 均值: {pe_agg['early_deal_ratio'].mean():.4f}")
print(f"早期投资占比(金额) 均值: {pe_agg['early_amount_ratio'].dropna().mean():.4f}")

# 合并到面板
panel = panel.merge(
    pe_agg[['城市_match', '年份', 'early_deal_ratio', 'early_amount_ratio', 'total_deals', 'early_deals']],
    on=['城市_match', '年份'], how='left'
)

matched = panel['early_deal_ratio'].notna().sum()
print(f"成功匹配: {matched} / {panel.shape[0]} 观测值 ({matched/panel.shape[0]*100:.1f}%)")
print(f"匹配到的城市数: {panel[panel['early_deal_ratio'].notna()]['城市'].nunique()}")

# =============================================================
# 3. 数据质量检查
# =============================================================
print("\n" + "=" * 70)
print("3. 数据质量诊断")
print("=" * 70)

# 关键变量
key_vars = {
    '发明专利申请量_对数': '被解释变量 Y',
    '专利申请总量_对数': '被解释变量 Y (替代)',
    '财政缺口率': '核心解释变量 X (当期)',
    '财政缺口率_滞后一期': '核心解释变量 X (滞后一期)',
    '债务率': '核心解释变量 X (替代)',
    '债务率_滞后一期': '核心解释变量 X (替代, 滞后一期)',
    'early_deal_ratio': '中介变量 M (事件数占比)',
    'early_amount_ratio': '中介变量 M (金额占比)',
}

print(f"\n{'变量':<25} {'含义':<30} {'非缺失':>8} {'缺失':>8} {'缺失率':>8} {'均值':>10} {'标准差':>10} {'最小值':>10} {'最大值':>10}")
print("-" * 140)
for var, desc in key_vars.items():
    if var in panel.columns:
        s = panel[var]
        n_valid = s.notna().sum()
        n_miss = s.isna().sum()
        miss_pct = n_miss / len(s) * 100
        if n_valid > 0:
            print(f"{var:<25} {desc:<30} {n_valid:>8} {n_miss:>8} {miss_pct:>7.1f}% {s.mean():>10.4f} {s.std():>10.4f} {s.min():>10.4f} {s.max():>10.4f}")
        else:
            print(f"{var:<25} {desc:<30} {n_valid:>8} {n_miss:>8} {miss_pct:>7.1f}%")

# 异常值检查
print("\n--- 异常值检查 (超过 3 倍标准差) ---")
for var in ['财政缺口率', '财政缺口率_滞后一期', '发明专利申请量_对数', 'early_deal_ratio']:
    if var in panel.columns:
        s = panel[var].dropna()
        mu, sigma = s.mean(), s.std()
        outliers = ((s < mu - 3*sigma) | (s > mu + 3*sigma)).sum()
        if outliers > 0:
            print(f"  {var}: {outliers} 个异常值 (>{mu+3*sigma:.4f} 或 <{mu-3*sigma:.4f})")
            outlier_cities = panel.loc[((panel[var] < mu - 3*sigma) | (panel[var] > mu + 3*sigma)) & panel[var].notna(), ['城市', '年份', var]]
            print(f"    异常城市:")
            for _, row in outlier_cities.head(10).iterrows():
                print(f"      {row['城市']} ({int(row['年份'])}): {row[var]:.4f}")

# 各年份观测数
print("\n--- 各年份有效观测数 ---")
year_stats = panel.groupby('年份').agg(
    总观测数=('城市', 'count'),
    有财政缺口率=('财政缺口率', lambda x: x.notna().sum()),
    有滞后财政缺口率=('财政缺口率_滞后一期', lambda x: x.notna().sum()),
    有债务率=('债务率', lambda x: x.notna().sum()),
    有中介变量=('early_deal_ratio', lambda x: x.notna().sum()),
).reset_index()
print(year_stats.to_string(index=False))

# =============================================================
# 4. 安装/导入回归所需包
# =============================================================
try:
    import linearmodels
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'linearmodels'])
    import linearmodels

from linearmodels.panel import PanelOLS
from linearmodels.panel.results import compare
import statsmodels.api as sm

# =============================================================
# 5. 准备回归数据
# =============================================================
print("\n" + "=" * 70)
print("4. 准备回归数据 (双向固定效应)")
print("=" * 70)

# 创建城市编码
panel['city_id'] = pd.Categorical(panel['城市']).codes

# 设置多重索引 (city, year)
panel_idx = panel.set_index(['city_id', '年份'])

# =============================================================
# 6. 基准回归: Y = β*X + city_FE + year_FE
# =============================================================
print("\n" + "=" * 70)
print("5. 基准回归: 双向固定效应")
print("=" * 70)

results_store = {}

# --- 模型1: 发明专利 ~ 财政缺口率(滞后一期) ---
print("\n--- 模型1: ln(发明专利) ~ 财政缺口率_滞后一期 ---")
try:
    dep_var = '发明专利申请量_对数'
    indep_var = '财政缺口率_滞后一期'
    reg_data = panel_idx[[dep_var, indep_var]].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    mod1 = PanelOLS(
        reg_data[dep_var], reg_data[[indep_var]],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res1 = mod1.fit(cov_type='clustered', cluster_entity=True)
    results_store['model1'] = res1
    print(res1.summary)
except Exception as e:
    print(f"模型1出错: {e}")

# --- 模型2: ln(专利总量) ~ 财政缺口率_滞后一期 ---
print("\n--- 模型2: ln(专利总量) ~ 财政缺口率_滞后一期 ---")
try:
    dep_var = '专利申请总量_对数'
    indep_var = '财政缺口率_滞后一期'
    reg_data = panel_idx[[dep_var, indep_var]].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    mod2 = PanelOLS(
        reg_data[dep_var], reg_data[[indep_var]],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res2 = mod2.fit(cov_type='clustered', cluster_entity=True)
    results_store['model2'] = res2
    print(res2.summary)
except Exception as e:
    print(f"模型2出错: {e}")

# --- 模型3: 发明专利占比 ~ 财政缺口率_滞后一期 ---
print("\n--- 模型3: 发明专利占比 ~ 财政缺口率_滞后一期 ---")
try:
    dep_var = '发明专利占比'
    indep_var = '财政缺口率_滞后一期'
    reg_data = panel_idx[[dep_var, indep_var]].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    mod3 = PanelOLS(
        reg_data[dep_var], reg_data[[indep_var]],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res3 = mod3.fit(cov_type='clustered', cluster_entity=True)
    results_store['model3'] = res3
    print(res3.summary)
except Exception as e:
    print(f"模型3出错: {e}")

# --- 模型4: 发明专利 ~ 债务率_滞后一期 ---
print("\n--- 模型4: ln(发明专利) ~ 债务率_滞后一期 ---")
try:
    dep_var = '发明专利申请量_对数'
    indep_var = '债务率_滞后一期'
    reg_data = panel_idx[[dep_var, indep_var]].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    mod4 = PanelOLS(
        reg_data[dep_var], reg_data[[indep_var]],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res4 = mod4.fit(cov_type='clustered', cluster_entity=True)
    results_store['model4'] = res4
    print(res4.summary)
except Exception as e:
    print(f"模型4出错: {e}")

# =============================================================
# 7. 中介效应检验: Baron & Kenny 三步法
# =============================================================
print("\n" + "=" * 70)
print("6. 中介效应检验: Baron & Kenny 三步法")
print("=" * 70)

# 使用 early_deal_ratio (事件数占比) 作为中介变量
# 步骤0 (基准): X → Y  已在模型1中完成

# --- 步骤1: X → M (财政约束 → 早期投资占比) ---
print("\n--- 步骤1 (中介): 财政缺口率_滞后一期 → early_deal_ratio ---")
try:
    dep_var = 'early_deal_ratio'
    indep_var = '财政缺口率_滞后一期'
    reg_data = panel_idx[[dep_var, indep_var]].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    med_step1 = PanelOLS(
        reg_data[dep_var], reg_data[[indep_var]],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res_med1 = med_step1.fit(cov_type='clustered', cluster_entity=True)
    results_store['med_step1'] = res_med1
    print(res_med1.summary)
except Exception as e:
    print(f"步骤1出错: {e}")

# --- 步骤2: M → Y (早期投资占比 → 发明专利) ---
print("\n--- 步骤2 (中介): early_deal_ratio → ln(发明专利) ---")
try:
    dep_var = '发明专利申请量_对数'
    indep_var = 'early_deal_ratio'
    reg_data = panel_idx[[dep_var, indep_var]].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    med_step2 = PanelOLS(
        reg_data[dep_var], reg_data[[indep_var]],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res_med2 = med_step2.fit(cov_type='clustered', cluster_entity=True)
    results_store['med_step2'] = res_med2
    print(res_med2.summary)
except Exception as e:
    print(f"步骤2出错: {e}")

# --- 步骤3: X + M → Y (同时加入财政约束和早期投资占比) ---
print("\n--- 步骤3 (中介): 财政缺口率_滞后一期 + early_deal_ratio → ln(发明专利) ---")
try:
    dep_var = '发明专利申请量_对数'
    indep_vars = ['财政缺口率_滞后一期', 'early_deal_ratio']
    reg_data = panel_idx[[dep_var] + indep_vars].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    med_step3 = PanelOLS(
        reg_data[dep_var], reg_data[indep_vars],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res_med3 = med_step3.fit(cov_type='clustered', cluster_entity=True)
    results_store['med_step3'] = res_med3
    print(res_med3.summary)
except Exception as e:
    print(f"步骤3出错: {e}")

# =============================================================
# 8. 使用 early_amount_ratio (金额占比) 重复中介检验
# =============================================================
print("\n" + "=" * 70)
print("7. 中介效应检验 (金额占比替代)")
print("=" * 70)

# 步骤1: X → M (金额)
print("\n--- 步骤1 (金额中介): 财政缺口率_滞后一期 → early_amount_ratio ---")
try:
    dep_var = 'early_amount_ratio'
    indep_var = '财政缺口率_滞后一期'
    reg_data = panel_idx[[dep_var, indep_var]].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    med_amt1 = PanelOLS(
        reg_data[dep_var], reg_data[[indep_var]],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res_amt1 = med_amt1.fit(cov_type='clustered', cluster_entity=True)
    results_store['med_amt_step1'] = res_amt1
    print(res_amt1.summary)
except Exception as e:
    print(f"金额中介步骤1出错: {e}")

# 步骤3: X + M(金额) → Y
print("\n--- 步骤3 (金额中介): 财政缺口率_滞后一期 + early_amount_ratio → ln(发明专利) ---")
try:
    dep_var = '发明专利申请量_对数'
    indep_vars = ['财政缺口率_滞后一期', 'early_amount_ratio']
    reg_data = panel_idx[[dep_var] + indep_vars].dropna()
    print(f"有效样本: {reg_data.shape[0]} (城市: {reg_data.index.get_level_values(0).nunique()}, 年份: {reg_data.index.get_level_values(1).nunique()})")
    
    med_amt3 = PanelOLS(
        reg_data[dep_var], reg_data[indep_vars],
        entity_effects=True, time_effects=True,
        check_rank=False
    )
    res_amt3 = med_amt3.fit(cov_type='clustered', cluster_entity=True)
    results_store['med_amt_step3'] = res_amt3
    print(res_amt3.summary)
except Exception as e:
    print(f"金额中介步骤3出错: {e}")

# =============================================================
# 9. 输出汇总表格 (easy to read)
# =============================================================
print("\n" + "=" * 70)
print("8. 结果汇总")
print("=" * 70)

def extract_result(res, var_name=None):
    """提取回归结果的关键信息"""
    info = {
        'nobs': res.nobs,
        'r2_within': res.rsquared_within,
        'r2_overall': res.rsquared_overall if hasattr(res, 'rsquared_overall') else None,
        'r2_between': res.rsquared_between if hasattr(res, 'rsquared_between') else None,
        'n_entities': res.entity_info.total if hasattr(res, 'entity_info') else None,
        'f_stat': res.f_statistic.stat if hasattr(res, 'f_statistic') and res.f_statistic is not None else None,
        'f_pval': res.f_statistic.pval if hasattr(res, 'f_statistic') and res.f_statistic is not None else None,
    }
    
    for name in res.params.index:
        info[f'coef_{name}'] = res.params[name]
        info[f'se_{name}'] = res.std_errors[name]
        info[f'tstat_{name}'] = res.tstats[name]
        info[f'pval_{name}'] = res.pvalues[name]
    
    return info

print("\n--- 基准回归结果汇总 ---")
print(f"{'模型':>6} | {'被解释变量':>20} | {'解释变量':>20} | {'系数':>10} | {'聚类标准误':>10} | {'t值':>8} | {'p值':>8} | {'显著性':>5} | {'组内R²':>8} | {'样本量':>6} | {'城市数':>5}")
print("-" * 150)

def sig_stars(p):
    if p < 0.01: return '***'
    elif p < 0.05: return '**'
    elif p < 0.1: return '*'
    else: return ''

# 基准回归
baseline_models = [
    ('model1', 'ln(发明专利)', '财政缺口率_滞后一期'),
    ('model2', 'ln(专利总量)', '财政缺口率_滞后一期'),
    ('model3', '发明专利占比', '财政缺口率_滞后一期'),
    ('model4', 'ln(发明专利)', '债务率_滞后一期'),
]

for key, dep_name, indep_name in baseline_models:
    if key in results_store:
        r = results_store[key]
        info = extract_result(r)
        for vname in r.params.index:
            coef = r.params[vname]
            se = r.std_errors[vname]
            t = r.tstats[vname]
            p = r.pvalues[vname]
            stars = sig_stars(p)
            n_ent = r.entity_info.total if hasattr(r, 'entity_info') else 'N/A'
            print(f"{key:>6} | {dep_name:>20} | {indep_name:>20} | {coef:>10.4f} | {se:>10.4f} | {t:>8.3f} | {p:>8.4f} | {stars:>5} | {r.rsquared_within:>8.4f} | {r.nobs:>6} | {n_ent:>5}")

# 中介效应
print("\n--- 中介效应结果汇总 (事件数占比) ---")
med_models = [
    ('model1', '步骤0: X→Y', 'ln(发明专利)', '财政缺口率_滞后一期'),
    ('med_step1', '步骤1: X→M', 'early_deal_ratio', '财政缺口率_滞后一期'),
    ('med_step2', '步骤2: M→Y', 'ln(发明专利)', 'early_deal_ratio'),
    ('med_step3', '步骤3: X+M→Y', 'ln(发明专利)', '财政缺口率_滞后一期 + early_deal_ratio'),
]

for key, step_name, dep_name, indep_name in med_models:
    if key in results_store:
        r = results_store[key]
        for vname in r.params.index:
            coef = r.params[vname]
            se = r.std_errors[vname]
            t = r.tstats[vname]
            p = r.pvalues[vname]
            stars = sig_stars(p)
            n_ent = r.entity_info.total if hasattr(r, 'entity_info') else 'N/A'
            print(f"{step_name:>12} | {dep_name:>20} | {vname:>25} | {coef:>10.4f} | {se:>10.4f} | {t:>8.3f} | {p:>8.4f} | {stars:>5} | R²w={r.rsquared_within:.4f} | N={r.nobs} | 城市={n_ent}")

print("\n--- 中介效应结果汇总 (金额占比) ---")
amt_models = [
    ('med_amt_step1', '步骤1: X→M', 'early_amount_ratio', '财政缺口率_滞后一期'),
    ('med_amt_step3', '步骤3: X+M→Y', 'ln(发明专利)', '财政缺口率_滞后一期 + early_amount_ratio'),
]

for key, step_name, dep_name, indep_name in amt_models:
    if key in results_store:
        r = results_store[key]
        for vname in r.params.index:
            coef = r.params[vname]
            se = r.std_errors[vname]
            t = r.tstats[vname]
            p = r.pvalues[vname]
            stars = sig_stars(p)
            n_ent = r.entity_info.total if hasattr(r, 'entity_info') else 'N/A'
            print(f"{step_name:>12} | {dep_name:>20} | {vname:>25} | {coef:>10.4f} | {se:>10.4f} | {t:>8.3f} | {p:>8.4f} | {stars:>5} | R²w={r.rsquared_within:.4f} | N={r.nobs} | 城市={n_ent}")

# Sobel 检验 (如果中介效应步骤1和步骤2显著)
print("\n--- Sobel 检验 ---")
try:
    if 'med_step1' in results_store and 'med_step3' in results_store:
        # a = X→M的系数, b = M→Y的系数(联合模型), se_a, se_b
        a = results_store['med_step1'].params['财政缺口率_滞后一期']
        se_a = results_store['med_step1'].std_errors['财政缺口率_滞后一期']
        b = results_store['med_step3'].params['early_deal_ratio']
        se_b = results_store['med_step3'].std_errors['early_deal_ratio']
        
        # Sobel test statistic
        sobel_se = np.sqrt(a**2 * se_b**2 + b**2 * se_a**2)
        sobel_z = (a * b) / sobel_se
        sobel_p = 2 * (1 - pd.Series([abs(sobel_z)]).apply(lambda x: __import__('scipy').stats.norm.cdf(x)).values[0])
        
        print(f"  间接效应 (a*b): {a*b:.6f}")
        print(f"  Sobel Z统计量: {sobel_z:.4f}")
        print(f"  Sobel p值: {sobel_p:.4f}")
        print(f"  显著性: {sig_stars(sobel_p)}")
        
        # 中介效应占比
        total_effect = results_store['model1'].params['财政缺口率_滞后一期']
        direct_effect = results_store['med_step3'].params['财政缺口率_滞后一期']
        indirect_effect = a * b
        mediation_ratio = indirect_effect / total_effect if total_effect != 0 else np.nan
        print(f"\n  总效应 (c): {total_effect:.6f}")
        print(f"  直接效应 (c'): {direct_effect:.6f}")
        print(f"  间接效应 (a*b): {indirect_effect:.6f}")
        print(f"  中介效应占比: {mediation_ratio*100:.2f}%")
except Exception as e:
    print(f"  Sobel检验出错: {e}")

print("\n\n========== 回归完成 ==========")
