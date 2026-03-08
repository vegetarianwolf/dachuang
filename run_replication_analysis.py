"""
完整复现：财政压力对制造业企业创新的影响研究（李森, 王聪, 2024）
本脚本基于 replicate_lisen_final.py 生成的面板数据，运行全面的回归分析
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
print("=" * 70)
print("加载面板数据")
print("=" * 70)

df = pd.read_csv('cleaned_data/lisen_replication_panel.csv', encoding='utf-8-sig')
print(f"面板数据: {len(df)} obs, {df['Scode'].nunique()} firms, {df['city_matched'].nunique()} cities")
print(f"年份范围: {df['Year'].min()}-{df['Year'].max()}")

# ============================================================
# 获取上市公司基本信息 (注册地城市、行业、上市日期等)
# ============================================================
print("\n" + "=" * 70)
print("补充上市公司基本信息 (从CSMAR基本信息表)")
print("=" * 70)

try:
    stk = pd.read_excel(
        'CNRDS专利数据包/【赠品】上市公司基本信息年度表(csmar，2024)/STK_LISTEDCOINFOANL.xlsx',
        skiprows=[0, 1],  # skip header description rows
        engine='openpyxl',
        dtype=str
    )
    # Rename based on first row that has Chinese labels
    stk.columns = ['Symbol', 'ShortName', 'EndDate', 'ListedCoID', 'SecurityID',
                   'IndustryName', 'IndustryCode', 'IndustryNameC', 'IndustryCodeC',
                   'IndustryNameD', 'IndustryCodeD', 'RegisterAddress', 'OfficeAddress',
                   'Zipcode', 'Secretary', 'SecretaryTel', 'SecretaryFax', 'SecretaryEmail',
                   'SecurityConsultant', 'SocialCreditCode', 'Sigchange', 'Lng', 'Lat',
                   'ISIN', 'FullName', 'LegalRepresentative', 'EstablishDate', 'Crcd',
                   'RegisterCapital', 'Website', 'BusinessScope', 'RegisterLongitude',
                   'RegisterLatitude', 'EMAIL', 'LISTINGDATE', 'PROVINCECODE', 'PROVINCE',
                   'CITYCODE', 'CITY', 'MAINBUSSINESS', 'LISTINGSTATE']
    
    # Parse year from EndDate
    stk['EndDate'] = pd.to_datetime(stk['EndDate'], errors='coerce')
    stk['year_end'] = stk['EndDate'].dt.year
    
    # Parse Symbol as integer
    stk['Scode'] = pd.to_numeric(stk['Symbol'], errors='coerce')
    stk = stk.dropna(subset=['Scode', 'year_end'])
    stk['Scode'] = stk['Scode'].astype(int)
    stk['year_end'] = stk['year_end'].astype(int)
    
    # Parse listing date for age
    stk['LISTINGDATE'] = pd.to_datetime(stk['LISTINGDATE'], errors='coerce')
    stk['listing_year'] = stk['LISTINGDATE'].dt.year
    
    # Industry code from CSMAR (IndustryCodeC is CSRC)
    stk['csrc_ind'] = stk['IndustryCodeC'].astype(str).str.strip()
    
    # Register capital
    stk['reg_cap'] = pd.to_numeric(stk['RegisterCapital'], errors='coerce')
    
    # Keep latest year's info per firm per year
    stk_info = stk[['Scode', 'year_end', 'listing_year', 'csrc_ind', 'PROVINCE', 'CITY',
                     'IndustryName', 'LISTINGSTATE']].copy()
    stk_info = stk_info.rename(columns={'year_end': 'Year'})
    stk_info = stk_info.drop_duplicates(subset=['Scode', 'Year'], keep='last')
    
    # Check manufacturing firms (CSRC code starts with C)
    mfg_mask = stk_info['csrc_ind'].str.startswith('C', na=False)
    print(f"CSMAR中总企业-年: {len(stk_info)}, 制造业: {mfg_mask.sum()}")
    
    # 合并上市年份信息到面板
    listing_info = stk_info[['Scode', 'Year', 'listing_year']].drop_duplicates(subset=['Scode', 'Year'])
    df = df.merge(listing_info, on=['Scode', 'Year'], how='left')
    
    # 计算企业年龄
    df['firm_age'] = df['Year'] - df['listing_year']
    df['ln_age'] = np.log(df['firm_age'].clip(lower=1))
    print(f"成功合并上市年份, 有企业年龄: {df['ln_age'].notna().sum()}")
    
except Exception as e:
    print(f"读取CSMAR基本信息失败: {e}")
    df['ln_age'] = np.nan

# ============================================================
# 构建额外变量
# ============================================================
print("\n" + "=" * 70)
print("构建额外变量")
print("=" * 70)

# 省份分类（东中西）
east = ['北京', '天津', '河北', '辽宁', '上海', '江苏', '浙江', '福建', '山东', '广东', '海南']
central = ['山西', '吉林', '黑龙江', '安徽', '江西', '河南', '湖北', '湖南']
west = ['内蒙古', '广西', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']

df['region'] = '其他'
df.loc[df['prov'].isin(east), 'region'] = '东部'
df.loc[df['prov'].isin(central), 'region'] = '中部'
df.loc[df['prov'].isin(west), 'region'] = '西部'

print("地区分布:")
print(df['region'].value_counts())

# 发明专利加权 (3:2:1)
df['weighted_patent'] = 3 * df['Invia'] + 2 * df['Umia'] + 1 * df['Desia']
df['ln_weighted_patent'] = np.log(df['weighted_patent'] + 1)

# RD占比：如果RD_pct用的是R&D/总资产
# 论文中RD = 研发投入/总资产
df['RD'] = df['RD_pct']  # 已有

# 行业二级代码（已有ind2）
# 按行业-年计算HHI（用R&D支出近似市场份额）
# 这里只是粗略估计
if 'RD_exp' in df.columns:
    ind_yr_total = df.groupby(['ind2', 'Year'])['RD_exp'].transform('sum')
    df['share'] = df['RD_exp'] / ind_yr_total.replace(0, np.nan)
    df['share_sq'] = df['share'] ** 2
    hhi = df.groupby(['ind2', 'Year'])['share_sq'].sum().reset_index()
    hhi.columns = ['ind2', 'Year', 'HHI_approx']
    df = df.merge(hhi, on=['ind2', 'Year'], how='left')
    df.drop(columns=['share', 'share_sq'], inplace=True, errors='ignore')

# 构建工具变量：省内其他城市财政压力均值
city_yr_pressure = df[['city_matched', 'Year', 'prov', 'pressure']].drop_duplicates(subset=['city_matched', 'Year'])
def iv_pressure(row):
    mask = (city_yr_pressure['prov'] == row['prov']) & \
           (city_yr_pressure['Year'] == row['Year']) & \
           (city_yr_pressure['city_matched'] != row['city_matched'])
    others = city_yr_pressure.loc[mask, 'pressure']
    return others.mean() if len(others) > 0 else np.nan

city_yr_pressure['iv_pressure'] = city_yr_pressure.apply(iv_pressure, axis=1)
df = df.merge(city_yr_pressure[['city_matched', 'Year', 'iv_pressure']], 
              on=['city_matched', 'Year'], how='left')
print(f"IV (省内其他城市压力均值) 非空: {df['iv_pressure'].notna().sum()}")

# ============================================================
# 缩尾处理
# ============================================================
def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))

for col in ['pressure', 'RD', 'ln_pergdp', 'ln_age']:
    if col in df.columns and df[col].notna().sum() > 10:
        df.loc[df[col].notna(), col] = winsorize(df[col].dropna())

# ============================================================
# 描述性统计
# ============================================================
print("\n" + "=" * 70)
print("描述性统计")
print("=" * 70)

desc_vars = {
    'ln_Patent': ('创新数量(lnPatent)', 17279, 3.104, 0, 6.668, 1.527),
    'ln_inv_patent': ('发明专利(lnInv)', None, None, None, None, None),
    'pressure': ('财政压力', 17279, 0.559, -0.351, 13.24, 0.775),
    'ln_pergdp': ('人均GDP(ln)', 17279, 11.38, 9.957, 12.22, 0.513),
    'RD': ('研发投入强度', 17279, 0.023, 0.000, 0.089, 0.016),
    'is_soe': ('国有企业', 17279, 0.276, 0, 1, 0.447),
    'ln_age': ('企业年龄(ln)', 17279, 1.865, 0, 3.258, 0.940),
}

desc_results = {}
print(f"\n{'变量':<20s} {'N':>7s} {'均值':>9s} {'标准差':>8s} {'最小值':>8s} {'最大值':>8s} | {'论文N':>7s} {'论文均值':>9s} {'论文标准差':>8s}")
print("-" * 110)
for var, (name, pn, pm, pmin, pmax, pstd) in desc_vars.items():
    if var in df.columns:
        s = df[var].dropna()
        if len(s) > 0:
            pn_str = str(pn) if pn else 'N/A'
            pm_str = f'{pm:.3f}' if pm is not None else 'N/A'
            pstd_str = f'{pstd:.3f}' if pstd is not None else 'N/A'
            print(f"{name:<20s} {len(s):>7d} {s.mean():>9.3f} {s.std():>8.3f} {s.min():>8.3f} {s.max():>8.3f} | {pn_str:>7s} {pm_str:>9s} {pstd_str:>8s}")
            desc_results[var] = {
                'name': name, 'n': len(s), 'mean': float(s.mean()),
                'std': float(s.std()), 'min': float(s.min()), 'max': float(s.max()),
                'paper_n': pn, 'paper_mean': pm, 'paper_std': pstd
            }

# ============================================================
# 回归分析
# ============================================================
print("\n" + "=" * 70)
print("回归分析")
print("=" * 70)

panel_reg = df.copy()
panel_reg = panel_reg.set_index(['Scode', 'Year'])

results_store = {}

def run_fe(dep, exog, data, label, entity_effects=True, time_effects=True, 
           cluster='entity', other_effects=None):
    """运行面板FE回归"""
    cols = [dep] + exog
    if other_effects:
        cols += [other_effects]
    sub = data[cols].dropna().copy()
    if len(sub) < 100:
        print(f"  [{label}] 样本不足 ({len(sub)})")
        return None
    try:
        if other_effects:
            mod = PanelOLS(sub[dep], sub[exog],
                           entity_effects=entity_effects, time_effects=time_effects,
                           other_effects=sub[[other_effects]], check_rank=False)
        else:
            mod = PanelOLS(sub[dep], sub[exog],
                           entity_effects=entity_effects, time_effects=time_effects,
                           check_rank=False)
        if cluster == 'entity':
            res = mod.fit(cov_type='clustered', cluster_entity=True)
        else:
            res = mod.fit(cov_type='robust')
        return res
    except Exception as e:
        print(f"  [{label}] 错误: {e}")
        return None

def extract_result(res, var='pressure'):
    """提取回归结果"""
    if res is None:
        return {'coef': None, 'se': None, 'pvalue': None, 'sig': '', 'nobs': 0, 'r2': None}
    c = float(res.params[var])
    p = float(res.pvalues[var])
    se = float(res.std_errors[var])
    sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
    return {
        'coef': c, 'se': se, 'pvalue': p, 'sig': sig,
        'nobs': int(res.nobs), 'r2': float(res.rsquared_overall)
    }

def fmt(res, var='pressure'):
    """格式化输出"""
    r = extract_result(res, var) if not isinstance(res, dict) else res
    if r['coef'] is None:
        return 'N/A'
    return f"{r['coef']:+.4f}{r['sig']} ({r['se']:.4f})"

# ============================================================
# 表2: 基准回归
# ============================================================
print("\n" + "-" * 70)
print("表2: 基准回归")
print("-" * 70)

# (1) lnPatent ~ pressure, FE, 无控制变量
r1 = run_fe('ln_Patent', ['pressure'], panel_reg, 'T2(1)')
# (2) lnInvPatent ~ pressure, FE, 无控制变量
r2 = run_fe('ln_inv_patent', ['pressure'], panel_reg, 'T2(2)')

# (3) lnPatent ~ pressure + controls
ctrl_basic = ['pressure', 'ln_pergdp']
ctrl_with_rd = ['pressure', 'ln_pergdp', 'RD']
ctrl_with_age = ['pressure', 'ln_pergdp', 'RD', 'ln_age']
ctrl_with_soe = ['pressure', 'ln_pergdp', 'RD', 'ln_age', 'is_soe']

# 逐步加入控制变量
r3a = run_fe('ln_Patent', ctrl_basic, panel_reg, 'T2(3a): +pergdp')
r3b = run_fe('ln_Patent', ctrl_with_rd, panel_reg, 'T2(3b): +RD')
r3c = run_fe('ln_Patent', ctrl_with_age, panel_reg, 'T2(3c): +age')
r3d = run_fe('ln_Patent', ctrl_with_soe, panel_reg, 'T2(3d): +SOE')

r4a = run_fe('ln_inv_patent', ctrl_basic, panel_reg, 'T2(4a): +pergdp')
r4b = run_fe('ln_inv_patent', ctrl_with_rd, panel_reg, 'T2(4b): +RD')
r4c = run_fe('ln_inv_patent', ctrl_with_age, panel_reg, 'T2(4c): +age')
r4d = run_fe('ln_inv_patent', ctrl_with_soe, panel_reg, 'T2(4d): +SOE')

# 用最完整控制变量规格作为主要对比
r3 = r3d if r3d else r3c if r3c else r3b if r3b else r3a
r4 = r4d if r4d else r4c if r4c else r4b if r4b else r4a

print("\n表2 基准回归结果:")
print(f"{'':20s} | {'(1)lnPatent':>18s} | {'(2)lnInv':>18s} | {'(3)lnPatent':>18s} | {'(4)lnInv':>18s}")
print(f"{'':20s} | {'无控制':>18s} | {'无控制':>18s} | {'有控制':>18s} | {'有控制':>18s}")
print("-" * 100)
print(f"{'复现 pressure':20s} | {fmt(r1):>18s} | {fmt(r2):>18s} | {fmt(r3):>18s} | {fmt(r4):>18s}")
print(f"{'论文 pressure':20s} | {'-0.149***(0.040)':>18s} | {'-0.137***(0.044)':>18s} | {'-0.110***(0.036)':>18s} | {'-0.091** (0.042)':>18s}")

results_store['table2'] = {
    'col1': extract_result(r1), 'col2': extract_result(r2),
    'col3': extract_result(r3), 'col4': extract_result(r4),
    'col3_gradual': {
        'pergdp_only': extract_result(r3a),
        'plus_rd': extract_result(r3b),
        'plus_age': extract_result(r3c),
        'plus_soe': extract_result(r3d),
    }
}

# Print R2 and N
for lbl, r in [('(1)', r1), ('(2)', r2), ('(3)', r3), ('(4)', r4)]:
    if r:
        print(f"  {lbl}: N={r.nobs}, R²={r.rsquared_overall:.4f}")

# Print detailed results for key specifications
print("\n详细回归输出 (1):")
if r1: print(r1.summary)
print("\n详细回归输出 (3) with controls:")
if r3: print(r3.summary)

# ============================================================
# 表2 列3详细 - 逐步加入控制变量
# ============================================================
print("\n" + "-" * 70)
print("逐步加入控制变量 (lnPatent)")
print("-" * 70)
for lbl, r in [('仅pressure', r1), ('+pergdp', r3a), ('+RD', r3b), ('+age', r3c), ('+SOE', r3d)]:
    if r:
        print(f"  {lbl:15s}: pressure={fmt(r):>22s}, N={r.nobs:>6d}, R²={r.rsquared_overall:.4f}")

# ============================================================
# 稳健性检验1: 替换因变量 (加权专利)
# ============================================================
print("\n" + "-" * 70)
print("稳健性检验: 替换因变量(加权专利)")
print("-" * 70)

r_rob1 = run_fe('ln_weighted_patent', ['pressure'], panel_reg, 'Rob1: weighted_no_ctrl')
r_rob1c = run_fe('ln_weighted_patent', ctrl_with_rd if r3b else ctrl_basic, panel_reg, 'Rob1: weighted_ctrl')

print(f"  加权专利 无控制: {fmt(r_rob1)}")
print(f"  加权专利 有控制: {fmt(r_rob1c)}")
if r_rob1: print(f"  N={r_rob1.nobs}, R²={r_rob1.rsquared_overall:.4f}")

results_store['robustness_weighted'] = {
    'no_ctrl': extract_result(r_rob1),
    'with_ctrl': extract_result(r_rob1c)
}

# ============================================================
# 稳健性检验2: 剔除直辖市
# ============================================================
print("\n" + "-" * 70)
print("稳健性检验: 剔除直辖市")
print("-" * 70)

zhixia = ['北京', '天津', '上海', '重庆']
panel_no_zhixia = panel_reg[~panel_reg['prov'].isin(zhixia)].copy()

r_rob2a = run_fe('ln_Patent', ['pressure'], panel_no_zhixia, 'Rob2a: no_zhixia_noctrl')
r_rob2b = run_fe('ln_Patent', ctrl_with_rd if r3b else ctrl_basic, panel_no_zhixia, 'Rob2b: no_zhixia_ctrl')
r_rob2c = run_fe('ln_inv_patent', ['pressure'], panel_no_zhixia, 'Rob2c: inv_no_zhixia')

print(f"  lnPatent 无控制: {fmt(r_rob2a)}")
print(f"  lnPatent 有控制: {fmt(r_rob2b)}")
print(f"  lnInv    无控制: {fmt(r_rob2c)}")
if r_rob2a: print(f"  (lnPatent) N={r_rob2a.nobs}")

results_store['robustness_no_zhixia'] = {
    'patent_no_ctrl': extract_result(r_rob2a),
    'patent_with_ctrl': extract_result(r_rob2b),
    'inv_no_ctrl': extract_result(r_rob2c)
}

# ============================================================
# 工具变量法 (2SLS)
# ============================================================
print("\n" + "-" * 70)
print("工具变量法 (2SLS)")
print("-" * 70)

from linearmodels.iv import IV2SLS

try:
    iv_data = df[['Scode', 'Year', 'ln_Patent', 'ln_inv_patent', 'pressure', 
                   'iv_pressure', 'ln_pergdp']].dropna().copy()
    iv_data = iv_data.set_index(['Scode', 'Year'])
    
    if len(iv_data) > 100 and iv_data['iv_pressure'].notna().sum() > 100:
        # First stage
        from linearmodels.panel import PanelOLS as PanelOLS2
        fs = PanelOLS2(iv_data['pressure'], iv_data[['iv_pressure']],
                       entity_effects=True, time_effects=True, check_rank=False)
        fs_res = fs.fit(cov_type='clustered', cluster_entity=True)
        print(f"  第一阶段: iv_pressure -> pressure: {fmt(fs_res, 'iv_pressure')}")
        print(f"  第一阶段 R²: {fs_res.rsquared_overall:.4f}, F-stat: {fs_res.f_statistic.stat:.2f}")
        
        # Manual 2SLS: get fitted values and run second stage
        iv_data['pressure_hat'] = fs_res.fitted_values
        
        ss_patent = PanelOLS2(iv_data['ln_Patent'], iv_data[['pressure_hat']],
                               entity_effects=True, time_effects=True, check_rank=False)
        ss_patent_res = ss_patent.fit(cov_type='clustered', cluster_entity=True)
        
        ss_inv = PanelOLS2(iv_data['ln_inv_patent'], iv_data[['pressure_hat']],
                            entity_effects=True, time_effects=True, check_rank=False)
        ss_inv_res = ss_inv.fit(cov_type='clustered', cluster_entity=True)
        
        print(f"  IV二阶段 lnPatent: {fmt(ss_patent_res, 'pressure_hat')}, N={ss_patent_res.nobs}")
        print(f"  IV二阶段 lnInv:    {fmt(ss_inv_res, 'pressure_hat')}, N={ss_inv_res.nobs}")
        
        results_store['iv_2sls'] = {
            'first_stage': extract_result(fs_res, 'iv_pressure'),
            'second_stage_patent': extract_result(ss_patent_res, 'pressure_hat'),
            'second_stage_inv': extract_result(ss_inv_res, 'pressure_hat')
        }
    else:
        print("  IV数据不足")
        results_store['iv_2sls'] = None
except Exception as e:
    print(f"  IV回归失败: {e}")
    results_store['iv_2sls'] = None

# ============================================================
# 异质性分析1: 地区 (东/中/西)
# ============================================================
print("\n" + "-" * 70)
print("异质性分析: 地区")
print("-" * 70)

results_store['hetero_region'] = {}
for region in ['东部', '中部', '西部']:
    sub = panel_reg[panel_reg['region'] == region].copy()
    r_reg = run_fe('ln_Patent', ['pressure'], sub, f'Region: {region}')
    r_reg_inv = run_fe('ln_inv_patent', ['pressure'], sub, f'Region_inv: {region}')
    
    print(f"  {region}: lnPatent={fmt(r_reg):>22s}, lnInv={fmt(r_reg_inv):>22s}", end='')
    if r_reg: print(f", N={r_reg.nobs}", end='')
    print()
    
    results_store['hetero_region'][region] = {
        'patent': extract_result(r_reg),
        'inv': extract_result(r_reg_inv)
    }

# ============================================================
# 异质性分析2: SOE（注意数据限制）
# ============================================================
print("\n" + "-" * 70)
print("异质性分析: 所有制")
print("-" * 70)

soe_counts = df['is_soe'].value_counts()
print(f"  SOE分布: {dict(soe_counts)}")

if soe_counts.get(1, 0) > 50:
    for soe_val, soe_label in [(1, '国有'), (0, '非国有')]:
        sub = panel_reg[panel_reg['is_soe'] == soe_val].copy()
        r_soe = run_fe('ln_Patent', ['pressure'], sub, f'SOE={soe_val}')
        r_soe_inv = run_fe('ln_inv_patent', ['pressure'], sub, f'SOE_inv={soe_val}')
        print(f"  {soe_label}: lnPatent={fmt(r_soe):>22s}, lnInv={fmt(r_soe_inv):>22s}")
        results_store[f'hetero_soe_{soe_val}'] = {
            'patent': extract_result(r_soe), 'inv': extract_result(r_soe_inv)
        }
else:
    print("  ⚠ SOE=1样本极少，无法进行所有制异质性分析")
    print("  原因: 企业来源为专精特新(SRDI)数据库，SOE识别依赖EnterpriseNature字段")
    results_store['hetero_soe_note'] = 'SOE样本不足，无法分析'

# ============================================================
# 异质性分析3: 行业要素密集度
# ============================================================
print("\n" + "-" * 70)
print("异质性分析: 行业要素密集度")
print("-" * 70)

# 参考鲁桐和党印(2014)的分类
# 技术密集型: C26(化学), C27(医药), C35(专用设备), C36(汽车), C37(铁路航空), C38(电气机械), C39(计算机通信), C40(仪器仪表)
# 资本密集型: C17(纺织), C22(造纸), C25(石油), C28(化学纤维), C29(橡胶), C30(非金属矿), C31(黑色金属), C32(有色金属), C33(金属制品)
# 劳动密集型: C13(农副食品), C14(食品), C15(饮料), C18(纺织服装), C19(皮革), C20(木材), C21(家具), C23(印刷), C24(文教体育)

tech_intensive = ['C26', 'C27', 'C35', 'C36', 'C37', 'C38', 'C39', 'C40']
capital_intensive = ['C17', 'C22', 'C25', 'C28', 'C29', 'C30', 'C31', 'C32', 'C33']
labor_intensive = ['C13', 'C14', 'C15', 'C18', 'C19', 'C20', 'C21', 'C23', 'C24']

df['factor_type'] = '其他'
df.loc[df['ind2'].isin(tech_intensive), 'factor_type'] = '技术密集型'
df.loc[df['ind2'].isin(capital_intensive), 'factor_type'] = '资本密集型'
df.loc[df['ind2'].isin(labor_intensive), 'factor_type'] = '劳动密集型'

panel_reg_ft = df.set_index(['Scode', 'Year'])

results_store['hetero_factor'] = {}
for ft in ['技术密集型', '资本密集型', '劳动密集型']:
    sub = panel_reg_ft[panel_reg_ft['factor_type'] == ft].copy()
    r_ft = run_fe('ln_Patent', ['pressure'], sub, f'Factor: {ft}')
    r_ft_inv = run_fe('ln_inv_patent', ['pressure'], sub, f'Factor_inv: {ft}')
    
    print(f"  {ft}: lnPatent={fmt(r_ft):>22s}", end='')
    if r_ft: print(f", N={r_ft.nobs}", end='')
    print()
    
    results_store['hetero_factor'][ft] = {
        'patent': extract_result(r_ft),
        'inv': extract_result(r_ft_inv)
    }

# ============================================================
# Tobit模型（用截断回归近似）
# ============================================================
print("\n" + "-" * 70)
print("稳健性检验: Tobit模型 (OLS近似)")
print("-" * 70)

try:
    # 使用带有时间虚拟变量的pooled OLS作为近似
    tobit_data = df[['ln_Patent', 'ln_inv_patent', 'pressure', 'Year', 'Scode', 'ln_pergdp']].dropna().copy()
    tobit_data = pd.get_dummies(tobit_data, columns=['Year'], drop_first=True, dtype=float)
    
    year_cols = [c for c in tobit_data.columns if c.startswith('Year_')]
    X = tobit_data[['pressure'] + year_cols]
    X = sm.add_constant(X)
    
    # lnPatent
    model_tobit1 = sm.OLS(tobit_data['ln_Patent'], X).fit(cov_type='cluster',
                          cov_kwds={'groups': tobit_data['Scode']})
    # lnInv
    model_tobit2 = sm.OLS(tobit_data['ln_inv_patent'], X).fit(cov_type='cluster',
                          cov_kwds={'groups': tobit_data['Scode']})
    
    print(f"  Tobit(近似) lnPatent: pressure={model_tobit1.params['pressure']:+.4f} (SE={model_tobit1.bse['pressure']:.4f}, p={model_tobit1.pvalues['pressure']:.4f})")
    print(f"  Tobit(近似) lnInv:    pressure={model_tobit2.params['pressure']:+.4f} (SE={model_tobit2.bse['pressure']:.4f}, p={model_tobit2.pvalues['pressure']:.4f})")
    
    results_store['tobit_approx'] = {
        'patent': {'coef': float(model_tobit1.params['pressure']),
                   'se': float(model_tobit1.bse['pressure']),
                   'pvalue': float(model_tobit1.pvalues['pressure'])},
        'inv': {'coef': float(model_tobit2.params['pressure']),
                'se': float(model_tobit2.bse['pressure']),
                'pvalue': float(model_tobit2.pvalues['pressure'])}
    }
except Exception as e:
    print(f"  Tobit模型失败: {e}")

# ============================================================
# 加入行业固定效应
# ============================================================
print("\n" + "-" * 70)
print("加入行业固定效应")
print("-" * 70)

r_ind = run_fe('ln_Patent', ['pressure'], panel_reg, 'Industry FE', 
               other_effects='ind2')
r_ind_inv = run_fe('ln_inv_patent', ['pressure'], panel_reg, 'Industry FE inv',
                    other_effects='ind2')

print(f"  +行业FE lnPatent: {fmt(r_ind)}", end='')
if r_ind: print(f", N={r_ind.nobs}, R²={r_ind.rsquared_overall:.4f}")
print(f"  +行业FE lnInv:    {fmt(r_ind_inv)}", end='')
if r_ind_inv: print(f", N={r_ind_inv.nobs}, R²={r_ind_inv.rsquared_overall:.4f}")

results_store['ind_fe'] = {
    'patent': extract_result(r_ind),
    'inv': extract_result(r_ind_inv)
}

# ============================================================
# 保存所有结果到JSON
# ============================================================
# Convert numpy types for JSON serialization
def convert_for_json(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_for_json(v) for v in obj]
    return obj

results_json = convert_for_json(results_store)
results_json['desc_stats'] = convert_for_json(desc_results)

with open('cleaned_data/replication_results.json', 'w', encoding='utf-8') as f:
    json.dump(results_json, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print("所有结果已保存至 cleaned_data/replication_results.json")
print("=" * 70)

# ============================================================
# 最终总结
# ============================================================
print("\n" + "=" * 70)
print("复现总结")
print("=" * 70)

print(f"""
样本对比:
  论文: 沪深A股全部制造业上市公司, 2010-2020, ~17000 obs
  复现: 专精特新(SRDI)数据库中的制造业上市公司, {len(df)} obs, {df['Scode'].nunique()} firms

核心发现对比:
  论文 表2(1): pressure = -0.149*** (0.040), N=16937
  复现 (1):    pressure = {extract_result(r1)['coef']:+.4f}{extract_result(r1)['sig']} ({extract_result(r1)['se']:.4f}), N={extract_result(r1)['nobs']}

  论文 表2(3): pressure = -0.110*** (0.036), N=16926  
  复现 (3):    pressure = {extract_result(r3)['coef']:+.4f}{extract_result(r3)['sig']} ({extract_result(r3)['se']:.4f}), N={extract_result(r3)['nobs']}
""")

print("完成！")
