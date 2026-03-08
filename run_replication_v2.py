"""
完整复现：财政压力对制造业企业创新的影响研究（李森, 王聪, 2024）
精简版 - 基于已有面板数据直接运行回归
"""
import pandas as pd
import numpy as np
import warnings
import json
warnings.filterwarnings('ignore')

from linearmodels.panel import PanelOLS
import statsmodels.api as sm

# ============================================================
# 加载数据
# ============================================================
df = pd.read_csv('cleaned_data/lisen_replication_panel.csv', encoding='utf-8-sig')
print(f"面板: {len(df)} obs, {df['Scode'].nunique()} firms, {df['city_matched'].nunique()} cities, {df['Year'].min()}-{df['Year'].max()}")

# ============================================================
# 构建额外变量
# ============================================================
# 省份分类
east = ['北京', '天津', '河北', '辽宁', '上海', '江苏', '浙江', '福建', '山东', '广东', '海南']
central = ['山西', '吉林', '黑龙江', '安徽', '江西', '河南', '湖北', '湖南']
west = ['内蒙古', '广西', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']
df['region'] = '其他'
df.loc[df['prov'].isin(east), 'region'] = '东部'
df.loc[df['prov'].isin(central), 'region'] = '中部'
df.loc[df['prov'].isin(west), 'region'] = '西部'

# 加权专利 (3:2:1)
df['weighted_patent'] = 3 * df['Invia'] + 2 * df['Umia'] + 1 * df['Desia']
df['ln_weighted_patent'] = np.log(df['weighted_patent'] + 1)

# RD
df['RD'] = df['RD_pct']

# 行业要素密集度
tech_intensive = ['C26', 'C27', 'C35', 'C36', 'C37', 'C38', 'C39', 'C40']
capital_intensive = ['C17', 'C22', 'C25', 'C28', 'C29', 'C30', 'C31', 'C32', 'C33']
labor_intensive = ['C13', 'C14', 'C15', 'C18', 'C19', 'C20', 'C21', 'C23', 'C24']
df['factor_type'] = '其他'
df.loc[df['ind2'].isin(tech_intensive), 'factor_type'] = '技术密集型'
df.loc[df['ind2'].isin(capital_intensive), 'factor_type'] = '资本密集型'
df.loc[df['ind2'].isin(labor_intensive), 'factor_type'] = '劳动密集型'

# 工具变量：省内其他城市财政压力均值 (预先计算)
city_yr = df[['city_matched', 'Year', 'prov', 'pressure']].drop_duplicates(subset=['city_matched', 'Year'])
iv_list = []
for _, row in city_yr.iterrows():
    mask = (city_yr['prov'] == row['prov']) & (city_yr['Year'] == row['Year']) & (city_yr['city_matched'] != row['city_matched'])
    others = city_yr.loc[mask, 'pressure']
    iv_list.append({'city_matched': row['city_matched'], 'Year': row['Year'],
                    'iv_pressure': others.mean() if len(others) > 0 else np.nan})
iv_df = pd.DataFrame(iv_list)
df = df.merge(iv_df, on=['city_matched', 'Year'], how='left')

print(f"地区分布: {dict(df['region'].value_counts())}")
print(f"行业类型: {dict(df['factor_type'].value_counts())}")
print(f"IV非空: {df['iv_pressure'].notna().sum()}")

# ============================================================
# 描述性统计
# ============================================================
print("\n" + "=" * 70)
print("描述性统计对比")
print("=" * 70)

desc_vars = {
    'ln_Patent': ('创新数量', 17279, 3.104, 0, 6.668, 1.527),
    'ln_inv_patent': ('发明专利', None, None, None, None, None),
    'pressure': ('财政压力', 17279, 0.559, -0.351, 13.24, 0.775),
    'ln_pergdp': ('人均GDP(ln)', 17279, 11.38, 9.957, 12.22, 0.513),
    'RD': ('研发投入', 17279, 0.023, 0.000, 0.089, 0.016),
    'is_soe': ('国企虚拟', 17279, 0.276, 0, 1, 0.447),
}

desc_results = {}
print(f"{'变量':<15s} {'N':>7s} {'均值':>9s} {'标准差':>8s} {'最小':>8s} {'最大':>8s} | {'论文N':>7s} {'论文均值':>9s}")
for var, (name, pn, pm, pmin, pmax, pstd) in desc_vars.items():
    if var in df.columns:
        s = df[var].dropna()
        if len(s) > 0:
            pn_s = str(pn) if pn else '-'
            pm_s = f'{pm:.3f}' if pm is not None else '-'
            print(f"{name:<15s} {len(s):>7d} {s.mean():>9.3f} {s.std():>8.3f} {s.min():>8.3f} {s.max():>8.3f} | {pn_s:>7s} {pm_s:>9s}")
            desc_results[var] = {'name': name, 'n': int(len(s)), 'mean': round(float(s.mean()),4),
                                 'std': round(float(s.std()),4), 'min': round(float(s.min()),4), 
                                 'max': round(float(s.max()),4)}

# ============================================================
# 回归函数
# ============================================================
panel_reg = df.set_index(['Scode', 'Year'])

def run_fe(dep, exog, data, label, entity_effects=True, time_effects=True,
           cluster='entity', other_effects_col=None):
    cols = [dep] + exog
    if other_effects_col: cols.append(other_effects_col)
    sub = data[cols].dropna().copy()
    if len(sub) < 100:
        print(f"  [{label}] 样本不足 ({len(sub)})")
        return None
    try:
        kw = dict(entity_effects=entity_effects, time_effects=time_effects, check_rank=False)
        if other_effects_col:
            kw['other_effects'] = sub[[other_effects_col]]
        mod = PanelOLS(sub[dep], sub[exog], **kw)
        res = mod.fit(cov_type='clustered', cluster_entity=True)
        return res
    except Exception as e:
        print(f"  [{label}] 错误: {e}")
        return None

def ext(res, var='pressure'):
    if res is None: return {'coef':None,'se':None,'pvalue':None,'sig':'','nobs':0,'r2':None}
    c,p,se = float(res.params[var]),float(res.pvalues[var]),float(res.std_errors[var])
    sig = '***' if p<0.01 else '**' if p<0.05 else '*' if p<0.1 else ''
    return {'coef':round(c,4),'se':round(se,4),'pvalue':round(p,4),'sig':sig,
            'nobs':int(res.nobs),'r2':round(float(res.rsquared_overall),4)}

def fmt(res, var='pressure'):
    r = ext(res,var) if not isinstance(res,dict) else res
    if r['coef'] is None: return 'N/A'
    return f"{r['coef']:+.4f}{r['sig']} ({r['se']:.4f})"

R = {}

# ============================================================
# 表2: 基准回归
# ============================================================
print("\n" + "=" * 70)
print("表2: 基准回归")
print("=" * 70)

r1 = run_fe('ln_Patent', ['pressure'], panel_reg, '(1)')
r2 = run_fe('ln_inv_patent', ['pressure'], panel_reg, '(2)')

ctrl1 = ['pressure', 'ln_pergdp']
ctrl2 = ['pressure', 'ln_pergdp', 'RD']
ctrl3 = ['pressure', 'ln_pergdp', 'RD', 'is_soe']

r3a = run_fe('ln_Patent', ctrl1, panel_reg, '(3a)')
r3b = run_fe('ln_Patent', ctrl2, panel_reg, '(3b)')
r4a = run_fe('ln_inv_patent', ctrl1, panel_reg, '(4a)')
r4b = run_fe('ln_inv_patent', ctrl2, panel_reg, '(4b)')

r3 = r3b if r3b else r3a
r4 = r4b if r4b else r4a

R['t2'] = {'c1': ext(r1), 'c2': ext(r2), 'c3': ext(r3), 'c4': ext(r4),
           'c3a': ext(r3a), 'c4a': ext(r4a)}

print(f"\n{'':15s} | {'(1)lnPatent':>20s} | {'(2)lnInv':>20s} | {'(3)lnPatent':>20s} | {'(4)lnInv':>20s}")
print(f"{'':15s} | {'无控制':>20s} | {'无控制':>20s} | {'有控制':>20s} | {'有控制':>20s}")
print("-" * 100)
print(f"{'复现pressure':15s} | {fmt(r1):>20s} | {fmt(r2):>20s} | {fmt(r3):>20s} | {fmt(r4):>20s}")
print(f"{'论文pressure':15s} | {'-0.149***(0.040)':>20s} | {'-0.137***(0.044)':>20s} | {'-0.110***(0.036)':>20s} | {'-0.091** (0.042)':>20s}")
print()
for lbl, r in [('(1)', r1),('(2)', r2),('(3)', r3),('(4)', r4)]:
    if r: print(f"  {lbl}: N={r.nobs}, R²={r.rsquared_overall:.4f}")

# 详细输出
for lbl, r in [('(1)', r1), ('(3)', r3)]:
    if r:
        print(f"\n--- 详细 {lbl} ---")
        print(r.summary)

# 控制变量效果
if r3:
    print("\n控制变量系数 (列3):")
    for v in r3.params.index:
        print(f"  {v}: {r3.params[v]:+.4f} (SE={r3.std_errors[v]:.4f}, p={r3.pvalues[v]:.4f})")

# ============================================================
# 稳健性1: 替换因变量(加权专利)
# ============================================================
print("\n" + "=" * 70)
print("稳健性: 替换因变量(加权专利)")
print("=" * 70)

r_w1 = run_fe('ln_weighted_patent', ['pressure'], panel_reg, 'weighted_no_ctrl')
r_w2 = run_fe('ln_weighted_patent', ctrl2 if r3b else ctrl1, panel_reg, 'weighted_ctrl')
print(f"  无控制: {fmt(r_w1)}", f"N={r_w1.nobs}" if r_w1 else "")
print(f"  有控制: {fmt(r_w2)}", f"N={r_w2.nobs}" if r_w2 else "")
R['rob_weighted'] = {'no_ctrl': ext(r_w1), 'ctrl': ext(r_w2)}

# ============================================================
# 稳健性2: 剔除直辖市
# ============================================================
print("\n" + "=" * 70)
print("稳健性: 剔除直辖市")
print("=" * 70)

panel_nz = panel_reg[~panel_reg['prov'].isin(['北京','天津','上海','重庆'])].copy()
r_nz1 = run_fe('ln_Patent', ['pressure'], panel_nz, 'no_zhixia')
r_nz2 = run_fe('ln_inv_patent', ['pressure'], panel_nz, 'no_zhixia_inv')
print(f"  lnPatent: {fmt(r_nz1)}", f"N={r_nz1.nobs}" if r_nz1 else "")
print(f"  lnInv:    {fmt(r_nz2)}", f"N={r_nz2.nobs}" if r_nz2 else "")
R['rob_no_zhixia'] = {'patent': ext(r_nz1), 'inv': ext(r_nz2)}

# ============================================================
# 稳健性3: 加行业FE
# ============================================================
print("\n" + "=" * 70)
print("稳健性: 加行业固定效应")
print("=" * 70)

r_if1 = run_fe('ln_Patent', ['pressure'], panel_reg, 'indFE', other_effects_col='ind2')
r_if2 = run_fe('ln_inv_patent', ['pressure'], panel_reg, 'indFE_inv', other_effects_col='ind2')
print(f"  lnPatent: {fmt(r_if1)}", f"N={r_if1.nobs}, R²={r_if1.rsquared_overall:.4f}" if r_if1 else "")
print(f"  lnInv:    {fmt(r_if2)}", f"N={r_if2.nobs}, R²={r_if2.rsquared_overall:.4f}" if r_if2 else "")
R['rob_ind_fe'] = {'patent': ext(r_if1), 'inv': ext(r_if2)}

# ============================================================
# 工具变量 (2SLS)
# ============================================================
print("\n" + "=" * 70)
print("工具变量法 (2SLS)")
print("=" * 70)

iv_data = panel_reg[['ln_Patent','ln_inv_patent','pressure','iv_pressure','ln_pergdp']].dropna()
if len(iv_data) > 200:
    # First stage
    fs = PanelOLS(iv_data['pressure'], iv_data[['iv_pressure']], entity_effects=True, time_effects=True, check_rank=False)
    fs_r = fs.fit(cov_type='clustered', cluster_entity=True)
    print(f"  一阶段: iv -> pressure = {fmt(fs_r,'iv_pressure')}, F={fs_r.f_statistic.stat:.1f}")
    
    # Second stage (manual)
    iv_data = iv_data.copy()
    iv_data['p_hat'] = fs_r.fitted_values
    ss1 = PanelOLS(iv_data['ln_Patent'], iv_data[['p_hat']], entity_effects=True, time_effects=True, check_rank=False)
    ss1_r = ss1.fit(cov_type='clustered', cluster_entity=True)
    ss2 = PanelOLS(iv_data['ln_inv_patent'], iv_data[['p_hat']], entity_effects=True, time_effects=True, check_rank=False)
    ss2_r = ss2.fit(cov_type='clustered', cluster_entity=True)
    print(f"  二阶段 lnPatent: {fmt(ss1_r,'p_hat')}, N={ss1_r.nobs}")
    print(f"  二阶段 lnInv:    {fmt(ss2_r,'p_hat')}, N={ss2_r.nobs}")
    R['iv'] = {'first': ext(fs_r,'iv_pressure'), 'patent': ext(ss1_r,'p_hat'), 'inv': ext(ss2_r,'p_hat')}
else:
    print("  IV数据不足")
    R['iv'] = None

# ============================================================
# 异质性: 地区
# ============================================================
print("\n" + "=" * 70)
print("异质性: 地区(东/中/西)")
print("=" * 70)

R['het_region'] = {}
for reg in ['东部', '中部', '西部']:
    sub = panel_reg[panel_reg['region'] == reg].copy()
    rr1 = run_fe('ln_Patent', ['pressure'], sub, f'R:{reg}')
    rr2 = run_fe('ln_inv_patent', ['pressure'], sub, f'R:{reg}_inv')
    n = rr1.nobs if rr1 else 0
    print(f"  {reg}: lnPatent={fmt(rr1):>22s}, lnInv={fmt(rr2):>22s}, N={n}")
    R['het_region'][reg] = {'patent': ext(rr1), 'inv': ext(rr2)}

# ============================================================
# 异质性: 行业要素密集度
# ============================================================
print("\n" + "=" * 70)
print("异质性: 行业要素密集度")
print("=" * 70)

panel_reg2 = df.set_index(['Scode', 'Year'])
R['het_factor'] = {}
for ft in ['技术密集型', '资本密集型', '劳动密集型']:
    sub = panel_reg2[panel_reg2['factor_type'] == ft].copy()
    rr1 = run_fe('ln_Patent', ['pressure'], sub, f'F:{ft}')
    rr2 = run_fe('ln_inv_patent', ['pressure'], sub, f'F:{ft}_inv')
    n = rr1.nobs if rr1 else 0
    print(f"  {ft}: lnPatent={fmt(rr1):>22s}, lnInv={fmt(rr2):>22s}, N={n}")
    R['het_factor'][ft] = {'patent': ext(rr1), 'inv': ext(rr2)}

# ============================================================
# 异质性: 所有制 (如果数据支持)
# ============================================================
print("\n" + "=" * 70)
print("异质性: 所有制")
print("=" * 70)

soe_dist = df['is_soe'].value_counts()
print(f"  SOE分布: {dict(soe_dist)}")
R['het_soe'] = {}
if soe_dist.get(1, 0) >= 50:
    for sv, sl in [(1,'国有'),(0,'非国有')]:
        sub = panel_reg[panel_reg['is_soe']==sv].copy()
        rr = run_fe('ln_Patent', ['pressure'], sub, f'SOE:{sl}')
        print(f"  {sl}: {fmt(rr)}, N={rr.nobs if rr else 0}")
        R['het_soe'][sl] = ext(rr)
else:
    print("  ⚠ SOE=1 样本过少，无法做所有制异质性分析")
    R['het_soe']['note'] = f"SOE=1仅{soe_dist.get(1,0)}个, 无法分析"

# ============================================================
# 保存结果
# ============================================================
R['desc'] = desc_results
R['sample'] = {'nobs': len(df), 'nfirms': int(df['Scode'].nunique()), 
               'ncities': int(df['city_matched'].nunique()),
               'year_min': int(df['Year'].min()), 'year_max': int(df['Year'].max())}

with open('cleaned_data/replication_results.json', 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2, default=str)

print("\n结果已保存至 cleaned_data/replication_results.json")
print("完成！")
