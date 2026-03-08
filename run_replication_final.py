"""
完整复现（最终版）：财政压力对制造业企业创新的影响研究
融合CSMAR行业代码 + 上市年份，全面对比论文结果
"""
import pandas as pd
import numpy as np
import warnings
import json
warnings.filterwarnings('ignore')
from linearmodels.panel import PanelOLS

# ============================================================
# 1. 加载并合并数据
# ============================================================
df = pd.read_csv('cleaned_data/lisen_replication_panel.csv', encoding='utf-8-sig')
ci = pd.read_csv('cleaned_data/csmar_firm_info.csv', encoding='utf-8-sig')

# 合并CSMAR行业代码和上市年份
ci_dedup = ci.drop_duplicates(subset=['Scode', 'Year'], keep='last')
df = df.merge(ci_dedup[['Scode', 'Year', 'ind2_csrc', 'listing_year', 'LISTINGSTATE']],
              on=['Scode', 'Year'], how='left')

# 剔除ST企业
st_mask = df['LISTINGSTATE'].astype(str).str.contains('ST|PT', na=False)
print(f"ST/PT企业-年: {st_mask.sum()}")
df = df[~st_mask].copy()

# 企业年龄
df['firm_age'] = df['Year'] - df['listing_year']
df['ln_age'] = np.log(df['firm_age'].clip(lower=1))

# 省份分类
east = ['北京', '天津', '河北', '辽宁', '上海', '江苏', '浙江', '福建', '山东', '广东', '海南']
central = ['山西', '吉林', '黑龙江', '安徽', '江西', '河南', '湖北', '湖南']
west = ['内蒙古', '广西', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']
df['region'] = '其他'
df.loc[df['prov'].isin(east), 'region'] = '东部'
df.loc[df['prov'].isin(central), 'region'] = '中部'
df.loc[df['prov'].isin(west), 'region'] = '西部'

# 加权专利
df['weighted_patent'] = 3 * df['Invia'] + 2 * df['Umia'] + 1 * df['Desia']
df['ln_weighted_patent'] = np.log(df['weighted_patent'] + 1)

# 行业要素密集度分类
tech = ['C26', 'C27', 'C35', 'C36', 'C37', 'C38', 'C39', 'C40']
capital = ['C17', 'C22', 'C25', 'C28', 'C29', 'C30', 'C31', 'C32', 'C33']
labor = ['C13', 'C14', 'C15', 'C18', 'C19', 'C20', 'C21', 'C23', 'C24']
df['factor_type'] = '其他'
df.loc[df['ind2_csrc'].isin(tech), 'factor_type'] = '技术密集型'
df.loc[df['ind2_csrc'].isin(capital), 'factor_type'] = '资本密集型'
df.loc[df['ind2_csrc'].isin(labor), 'factor_type'] = '劳动密集型'

# 行业二位代码 (用CSRC)
df['ind2_code'] = df['ind2_csrc'].fillna(df['ind2'])

# 缩尾处理
def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))
for col in ['pressure', 'ln_pergdp', 'ln_age', 'RD_pct']:
    if col in df.columns and df[col].notna().sum() > 10:
        valid = df[col].notna()
        df.loc[valid, col] = winsorize(df.loc[valid, col])

# IV: 省内其他城市均值
city_yr = df[['city_matched', 'Year', 'prov', 'pressure']].drop_duplicates(subset=['city_matched', 'Year'])
iv_map = {}
for _, row in city_yr.iterrows():
    key = (row['city_matched'], row['Year'])
    mask = (city_yr['prov'] == row['prov']) & (city_yr['Year'] == row['Year']) & (city_yr['city_matched'] != row['city_matched'])
    others = city_yr.loc[mask, 'pressure']
    iv_map[key] = others.mean() if len(others) > 0 else np.nan
df['iv_pressure'] = df.apply(lambda r: iv_map.get((r['city_matched'], r['Year']), np.nan), axis=1)

print(f"最终面板: {len(df)} obs, {df['Scode'].nunique()} firms")
print(f"地区: {dict(df['region'].value_counts())}")
print(f"行业: {dict(df['factor_type'].value_counts())}")
print(f"有CSRC行业代码: {df['ind2_csrc'].notna().sum()}")
print(f"有上市年份: {df['listing_year'].notna().sum()}")

# ============================================================
# 2. 描述性统计
# ============================================================
print("\n" + "=" * 70)
print("描述性统计")
print("=" * 70)

desc_paper = {
    'ln_Patent':    ('创新数量lnPatent',  17279, 3.104, 0, 6.668, 1.527),
    'ln_inv_patent':('发明专利lnInv',     None, None, None, None, None),
    'pressure':     ('财政压力',           17279, 0.559, -0.351, 13.24, 0.775),
    'ln_pergdp':    ('人均GDP(ln)',        17279, 11.38, 9.957, 12.22, 0.513),
    'RD_pct':       ('研发投入强度',       17279, 0.023, 0.000, 0.089, 0.016),
    'is_soe':       ('国有企业',           17279, 0.276, 0, 1, 0.447),
    'ln_age':       ('企业年龄(ln)',        17279, 1.865, 0, 3.258, 0.940),
}

desc_results = {}
for var, (name, pn, pm, pmin, pmax, pstd) in desc_paper.items():
    if var in df.columns:
        s = df[var].dropna()
        if len(s) > 0:
            desc_results[var] = {
                'name': name, 'n': int(len(s)),
                'mean': round(float(s.mean()), 4), 'std': round(float(s.std()), 4),
                'min': round(float(s.min()), 4), 'max': round(float(s.max()), 4),
                'paper_n': pn, 'paper_mean': pm, 'paper_std': pstd
            }
            pm_s = f'{pm:.3f}' if pm is not None else '-'
            print(f"  {name:<18s} N={len(s):>6d} mean={s.mean():.3f} std={s.std():.3f} | 论文: N={pn}, mean={pm_s}")

# ============================================================
# 3. 回归
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

def fmt(r, var='pressure'):
    if not isinstance(r, dict): r = ext(r, var)
    if r['coef'] is None: return 'N/A'
    return f"{r['coef']:+.4f}{r['sig']} ({r['se']:.4f})"

R = {}

# ---- 表2: 基准回归 ----
print("\n" + "=" * 70)
print("表2: 基准回归")
print("=" * 70)

# (1) lnPatent ~ pressure  (仅FE)
r1 = run_fe('ln_Patent', ['pressure'], panel_reg, '(1)')
# (2) lnInv ~ pressure (仅FE)
r2 = run_fe('ln_inv_patent', ['pressure'], panel_reg, '(2)')
# (3) lnPatent ~ pressure + controls
ctrl = ['pressure', 'ln_pergdp', 'RD_pct', 'ln_age', 'is_soe']
r3 = run_fe('ln_Patent', ctrl, panel_reg, '(3)')
# (4) lnInv ~ pressure + controls
r4 = run_fe('ln_inv_patent', ctrl, panel_reg, '(4)')

# 如果带全控制变量的不行，退回
if r3 is None:
    ctrl = ['pressure', 'ln_pergdp', 'RD_pct']
    r3 = run_fe('ln_Patent', ctrl, panel_reg, '(3b)')
    r4 = run_fe('ln_inv_patent', ctrl, panel_reg, '(4b)')
if r3 is None:
    ctrl = ['pressure', 'ln_pergdp']
    r3 = run_fe('ln_Patent', ctrl, panel_reg, '(3c)')
    r4 = run_fe('ln_inv_patent', ctrl, panel_reg, '(4c)')

R['t2'] = {'c1': ext(r1), 'c2': ext(r2), 'c3': ext(r3), 'c4': ext(r4)}

print(f"\n{'':15s} | {'(1)lnPatent':>20s} | {'(2)lnInv':>20s} | {'(3)lnPatent':>20s} | {'(4)lnInv':>20s}")
print("-" * 100)
print(f"{'复现':15s} | {fmt(r1):>20s} | {fmt(r2):>20s} | {fmt(r3):>20s} | {fmt(r4):>20s}")
print(f"{'论文':15s} | {'-0.149***(0.040)':>20s} | {'-0.137***(0.044)':>20s} | {'-0.110***(0.036)':>20s} | {'-0.091** (0.042)':>20s}")
for lbl, r in [('(1)',r1),('(2)',r2),('(3)',r3),('(4)',r4)]:
    if r: print(f"  {lbl}: N={r.nobs}, R²={r.rsquared_overall:.4f}")

# 控制变量系数
if r3:
    R['t2_ctrl_coefs'] = {}
    print("\n  控制变量系数 (列3):")
    for v in r3.params.index:
        c = float(r3.params[v])
        p = float(r3.pvalues[v])
        se = float(r3.std_errors[v])
        sig = '***' if p<0.01 else '**' if p<0.05 else '*' if p<0.1 else ''
        print(f"    {v}: {c:+.4f}{sig} ({se:.4f})")
        R['t2_ctrl_coefs'][v] = {'coef': round(c,4), 'se': round(se,4), 'pvalue': round(p,4), 'sig': sig}

# ---- 稳健性1: 加权专利 ----
print("\n" + "=" * 70)
print("稳健性: 替换因变量 (加权专利)")
print("=" * 70)
r_w1 = run_fe('ln_weighted_patent', ['pressure'], panel_reg, 'weighted')
r_w2 = run_fe('ln_weighted_patent', ctrl, panel_reg, 'weighted_ctrl') if r3 else None
print(f"  无控制: {fmt(r_w1)}", f"N={r_w1.nobs}" if r_w1 else "")
print(f"  有控制: {fmt(r_w2)}", f"N={r_w2.nobs}" if r_w2 else "")
R['rob_weighted'] = {'no_ctrl': ext(r_w1), 'ctrl': ext(r_w2)}

# ---- 稳健性2: 剔除直辖市 ----
print("\n" + "=" * 70)
print("稳健性: 剔除直辖市")
print("=" * 70)
pnz = panel_reg[~panel_reg['prov'].isin(['北京','天津','上海','重庆'])].copy()
r_nz1 = run_fe('ln_Patent', ['pressure'], pnz, 'no_zhixia')
r_nz2 = run_fe('ln_inv_patent', ['pressure'], pnz, 'no_zhixia_inv')
r_nz3 = run_fe('ln_Patent', ctrl, pnz, 'no_zhixia_ctrl') if r3 else None
print(f"  lnPatent无控制: {fmt(r_nz1)}", f"N={r_nz1.nobs}" if r_nz1 else "")
print(f"  lnInv无控制:    {fmt(r_nz2)}", f"N={r_nz2.nobs}" if r_nz2 else "")
print(f"  lnPatent有控制: {fmt(r_nz3)}", f"N={r_nz3.nobs}" if r_nz3 else "")
R['rob_no_zhixia'] = {'patent': ext(r_nz1), 'inv': ext(r_nz2), 'patent_ctrl': ext(r_nz3)}

# ---- 稳健性3: 行业FE (通过吸收进entity实现) ----
print("\n" + "=" * 70)
print("稳健性: 加入行业固定效应 (行业×年份交互)")
print("=" * 70)
# Create industry-year interaction for absorption
if df['ind2_csrc'].notna().sum() > 100:
    df['ind_year'] = df['ind2_csrc'].astype(str) + '_' + df['Year'].astype(str)
    pr_iy = df.set_index(['Scode', 'Year'])
    r_iy1 = run_fe('ln_Patent', ['pressure'], pr_iy, 'ind_yr_FE', other_effects_col='ind_year')
    r_iy2 = run_fe('ln_inv_patent', ['pressure'], pr_iy, 'ind_yr_FE_inv', other_effects_col='ind_year')
    print(f"  lnPatent: {fmt(r_iy1)}", f"N={r_iy1.nobs}, R²={r_iy1.rsquared_overall:.4f}" if r_iy1 else "")
    print(f"  lnInv:    {fmt(r_iy2)}", f"N={r_iy2.nobs}, R²={r_iy2.rsquared_overall:.4f}" if r_iy2 else "")
    R['rob_ind_fe'] = {'patent': ext(r_iy1), 'inv': ext(r_iy2)}
else:
    print("  行业代码缺失，跳过")
    R['rob_ind_fe'] = None

# ---- IV: 2SLS ----
print("\n" + "=" * 70)
print("工具变量法 (2SLS)")
print("=" * 70)
iv_cols = ['ln_Patent', 'ln_inv_patent', 'pressure', 'iv_pressure', 'ln_pergdp']
iv_data = panel_reg[iv_cols].dropna()
if len(iv_data) > 200:
    fs = PanelOLS(iv_data['pressure'], iv_data[['iv_pressure']], entity_effects=True, time_effects=True, check_rank=False)
    fs_r = fs.fit(cov_type='clustered', cluster_entity=True)
    fs_coef = float(fs_r.params['iv_pressure'])
    fs_f = float(fs_r.f_statistic.stat)
    print(f"  一阶段: IV -> pressure = {fmt(fs_r,'iv_pressure')}, F={fs_f:.1f}")
    
    iv_data = iv_data.copy()
    iv_data['p_hat'] = fs_r.fitted_values
    
    ss1 = PanelOLS(iv_data['ln_Patent'], iv_data[['p_hat']], entity_effects=True, time_effects=True, check_rank=False)
    ss1_r = ss1.fit(cov_type='clustered', cluster_entity=True)
    ss2 = PanelOLS(iv_data['ln_inv_patent'], iv_data[['p_hat']], entity_effects=True, time_effects=True, check_rank=False)
    ss2_r = ss2.fit(cov_type='clustered', cluster_entity=True)
    
    print(f"  二阶段 lnPatent: {fmt(ss1_r,'p_hat')}, N={ss1_r.nobs}")
    print(f"  二阶段 lnInv:    {fmt(ss2_r,'p_hat')}, N={ss2_r.nobs}")
    R['iv'] = {
        'first': ext(fs_r, 'iv_pressure'),
        'first_F': round(fs_f, 1),
        'patent': ext(ss1_r, 'p_hat'),
        'inv': ext(ss2_r, 'p_hat')
    }
else:
    R['iv'] = None

# ---- 异质性: 地区 ----
print("\n" + "=" * 70)
print("异质性: 地区")
print("=" * 70)
R['het_region'] = {}
for reg in ['东部', '中部', '西部']:
    sub = panel_reg[panel_reg['region'] == reg].copy()
    rr1 = run_fe('ln_Patent', ['pressure'], sub, f'{reg}')
    rr2 = run_fe('ln_inv_patent', ['pressure'], sub, f'{reg}_inv')
    n = rr1.nobs if rr1 else 0
    print(f"  {reg}: lnPatent={fmt(rr1):>22s}, lnInv={fmt(rr2):>22s}, N={n}")
    R['het_region'][reg] = {'patent': ext(rr1), 'inv': ext(rr2)}

# ---- 异质性: 行业要素密集度 ----
print("\n" + "=" * 70)
print("异质性: 行业要素密集度")
print("=" * 70)
pr_ft = df.set_index(['Scode', 'Year'])
R['het_factor'] = {}
for ft in ['技术密集型', '资本密集型', '劳动密集型']:
    sub = pr_ft[pr_ft['factor_type'] == ft].copy()
    rr1 = run_fe('ln_Patent', ['pressure'], sub, f'{ft}')
    rr2 = run_fe('ln_inv_patent', ['pressure'], sub, f'{ft}_inv')
    n = rr1.nobs if rr1 else 0
    print(f"  {ft}: lnPatent={fmt(rr1):>22s}, lnInv={fmt(rr2):>22s}, N={n}")
    R['het_factor'][ft] = {'patent': ext(rr1), 'inv': ext(rr2)}

# ---- 异质性: 所有制 ----
print("\n" + "=" * 70)  
print("异质性: 所有制")
print("=" * 70)
soe_dist = df['is_soe'].value_counts()
print(f"  SOE分布: {dict(soe_dist)}")
R['het_soe'] = {'distribution': {int(k):int(v) for k,v in soe_dist.items()}}
if soe_dist.get(1, 0) >= 50:
    for sv, sl in [(1,'国有'),(0,'非国有')]:
        sub = panel_reg[panel_reg['is_soe']==sv].copy()
        rr = run_fe('ln_Patent', ['pressure'], sub, f'SOE:{sl}')
        print(f"  {sl}: {fmt(rr)}, N={rr.nobs if rr else 0}")
        R['het_soe'][sl] = ext(rr)
else:
    print("  SOE=1 样本过少，无法进行分析")
    R['het_soe']['note'] = 'insufficient SOE=1 samples'

# ============================================================
# 保存
# ============================================================
R['desc'] = desc_results
R['sample'] = {
    'nobs': len(df), 'nfirms': int(df['Scode'].nunique()),
    'ncities': int(df['city_matched'].nunique()),
    'year_min': int(df['Year'].min()), 'year_max': int(df['Year'].max())
}

with open('cleaned_data/replication_results.json', 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2, default=str)

print("\n" + "=" * 70)
print("全部完成，结果已保存")
print("=" * 70)
