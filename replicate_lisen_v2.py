"""
复现：财政压力对制造业企业创新的影响研究（李森, 王聪, 2024）
优化版 - 使用向量化操作加速数据处理
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 第一步：构建企业-城市映射（制造业上市公司）
# ============================================================
print("=" * 60)
print("第一步：构建企业-城市映射")
print("=" * 60)

info = pd.read_csv('csmar_data_export/SRDI_EntInfo_Full.csv',
                   encoding='utf-8-sig', low_memory=False, on_bad_lines='skip')
ind_map = info[['InstitutionID', 'GBCode2017MainClass']].dropna() \
    .drop_duplicates(subset=['InstitutionID'])
del info  # free memory

ident = pd.read_csv('csmar_data_export/SRDI_EntIdentInfo.csv',
                    encoding='utf-8-sig', low_memory=False)
listed = ident[ident['IsListed'] == 1].copy()
listed_ind = listed.merge(ind_map, on='InstitutionID', how='left')
mfg = listed_ind[listed_ind['GBCode2017MainClass'].str.startswith('C', na=False)]
mfg_unique = mfg.drop_duplicates(subset=['Symbol'])
mapping = mfg_unique[['Symbol', 'InstitutionID', 'InstitutionName',
                       'CityName', 'ProvinceName', 'GBCode2017MainClass']].copy()
mapping = mapping[~mapping['Symbol'].astype(str).str.contains(',')]
mapping['Scode'] = mapping['Symbol'].astype(str).str.lstrip('0').astype(int)
mapping['city_clean'] = mapping['CityName'].astype(str).str.replace('市$', '', regex=True)
mapping['prov_clean'] = mapping['ProvinceName'].astype(str).str.replace('省$|市$', '', regex=True)
del ident, listed, listed_ind, mfg, mfg_unique, ind_map

print(f"制造业上市公司: {len(mapping)}家, 覆盖{mapping['city_clean'].nunique()}个城市")

# ============================================================
# 第二步：获取专利数据
# ============================================================
print("\n" + "=" * 60)
print("第二步：获取专利申请数据")
print("=" * 60)

patent = pd.read_csv(
    'CNRDS专利数据包/上市公司专利申请与获得/上市公司专利申请情况/上市公司专利申请情况.csv',
    skiprows=[1], encoding='utf-8-sig'
)
patent = patent[patent['Ftyp'] == '上市公司本身'].copy()
patent['Scode'] = pd.to_numeric(patent['Scode'], errors='coerce')
patent['Year'] = pd.to_numeric(patent['Year'], errors='coerce')
patent = patent.dropna(subset=['Scode', 'Year'])
patent['Scode'] = patent['Scode'].astype(int)
patent['Year'] = patent['Year'].astype(int)
patent = patent[(patent['Year'] >= 2010) & (patent['Year'] <= 2020)]
for col in ['Invia', 'Umia', 'Desia']:
    patent[col] = pd.to_numeric(patent[col], errors='coerce').fillna(0)
patent['total_patent'] = patent['Invia'] + patent['Umia'] + patent['Desia']
patent['ln_Patent'] = np.log(patent['total_patent'] + 1)
patent['ln_inv_patent'] = np.log(patent['Invia'] + 1)

print(f"专利数据: {len(patent)}条, {patent['Scode'].nunique()}家企业")

# ============================================================
# 第三步：构建城市级财政压力（优化版）
# ============================================================
print("\n" + "=" * 60)
print("第三步：构建城市级财政压力")
print("=" * 60)

def parse_ceic_fast(filepath, value_name):
    """快速解析CEIC宽格式→长格式"""
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    date_col = df.columns[0]
    df = df.rename(columns={date_col: 'date'})
    df['date'] = pd.to_numeric(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['year'] = df['date'].astype(int)

    # melt to long format
    id_vars = ['year']
    value_vars = [c for c in df.columns if c not in ['date', 'year']]
    long = df[['year'] + value_vars].melt(id_vars='year', var_name='col_name', value_name=value_name)
    long[value_name] = pd.to_numeric(long[value_name], errors='coerce')
    long = long.dropna(subset=[value_name])

    # 从列名提取城市
    def extract_city(col):
        parts = col.split(':')
        return parts[-1].strip()
    long['city'] = long['col_name'].apply(extract_city)
    return long[['year', 'city', value_name]]

print("解析财政收入...")
rev = parse_ceic_fast('地级市财政收入.csv', 'fiscal_revenue')
print(f"  {len(rev)}条")

print("解析财政支出...")
exp = parse_ceic_fast('地级市财政支出.csv', 'fiscal_expenditure')
print(f"  {len(exp)}条")

print("解析人均GDP...")
pgdp = parse_ceic_fast('地级市人均GDP.csv', 'pergdp')
print(f"  {len(pgdp)}条")

# 合并
fiscal = rev.merge(exp, on=['year', 'city'], how='inner')
fiscal = fiscal.merge(pgdp, on=['year', 'city'], how='left')
fiscal = fiscal[(fiscal['year'] >= 2010) & (fiscal['year'] <= 2020)]

# 财政压力 = (支出 - 收入) / 收入
fiscal['pressure'] = (fiscal['fiscal_expenditure'] - fiscal['fiscal_revenue']) / fiscal['fiscal_revenue']
fiscal['ln_pergdp'] = np.log(fiscal['pergdp'].replace(0, np.nan))

# 去除异常值
fiscal = fiscal[fiscal['pressure'].notna() & np.isfinite(fiscal['pressure'])]
print(f"\n财政数据: {len(fiscal)}条, {fiscal['city'].nunique()}个城市")
print(f"财政压力: mean={fiscal['pressure'].mean():.3f}, std={fiscal['pressure'].std():.3f}")

# ============================================================
# 第四步：获取R&D数据
# ============================================================
print("\n" + "=" * 60)
print("第四步：获取R&D数据")
print("=" * 60)

rd = pd.read_csv(
    'CNRDS专利数据包/上市公司研发费用/上市公司研发支出/上市公司研发支出.csv',
    skiprows=[1], encoding='utf-8-sig'
)
rd['Scode'] = pd.to_numeric(rd['Scode'], errors='coerce')
rd['Year'] = pd.to_numeric(rd['Year'], errors='coerce')
rd = rd.dropna(subset=['Scode', 'Year'])
rd['Scode'] = rd['Scode'].astype(int)
rd['Year'] = rd['Year'].astype(int)
rd['RD'] = pd.to_numeric(rd['R&Dpr'], errors='coerce')
rd = rd[['Scode', 'Year', 'RD']].dropna()
rd = rd[(rd['Year'] >= 2010) & (rd['Year'] <= 2020)]
print(f"R&D数据: {len(rd)}条, {rd['Scode'].nunique()}家企业")

# ============================================================
# 第五步：合并构建面板
# ============================================================
print("\n" + "=" * 60)
print("第五步：合并面板数据")
print("=" * 60)

panel = patent[['Scode', 'Year', 'total_patent', 'Invia', 'Umia', 'Desia',
                'ln_Patent', 'ln_inv_patent']].copy()
panel = panel.merge(mapping[['Scode', 'city_clean', 'prov_clean', 'InstitutionName',
                              'GBCode2017MainClass']],
                    on='Scode', how='inner')
print(f"专利+企业映射: {len(panel)}条, {panel['Scode'].nunique()}家")

panel = panel.merge(fiscal[['year', 'city', 'pressure', 'ln_pergdp']],
                    left_on=['Year', 'city_clean'],
                    right_on=['year', 'city'], how='inner')
print(f"合并财政数据: {len(panel)}条, {panel['Scode'].nunique()}家")

panel = panel.merge(rd, on=['Scode', 'Year'], how='left')
print(f"合并R&D数据后: {len(panel)}条")

# 缩尾处理
def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))

for col in ['pressure', 'ln_Patent', 'ln_inv_patent']:
    panel[col] = winsorize(panel[col])

panel = panel.dropna(subset=['ln_Patent', 'pressure'])

print(f"\n最终面板: {len(panel)}条, {panel['Scode'].nunique()}家企业, "
      f"{panel['Year'].min()}-{panel['Year'].max()}")

# 描述性统计
print("\n" + "-" * 60)
print("描述性统计（复现 vs 论文）")
print("-" * 60)
print(f"{'变量':12s} {'N':>6s}  {'Mean':>7s}  {'Std':>7s}  {'Min':>7s}  {'Max':>7s}  │ 论文Mean  论文N")
stats_compare = [
    ('ln_Patent', '创新数量', 3.104, 17279),
    ('ln_inv_patent', '发明专利', None, None),
    ('pressure', '财政压力', 0.559, 17279),
    ('ln_pergdp', 'ln人均GDP', 11.38, 17279),
]
for var, name, paper_mean, paper_n in stats_compare:
    if var in panel.columns:
        s = panel[var].dropna()
        pm = f"{paper_mean:.3f}" if paper_mean else "  N/A"
        pn = f"{paper_n}" if paper_n else " N/A"
        print(f"{name:12s} {len(s):>6d}  {s.mean():>7.3f}  {s.std():>7.3f}  "
              f"{s.min():>7.3f}  {s.max():>7.3f}  │ {pm:>8s}  {pn:>6s}")

# ============================================================
# 第六步：回归分析
# ============================================================
print("\n" + "=" * 60)
print("第六步：回归分析（复现表2）")
print("=" * 60)

from linearmodels.panel import PanelOLS

panel_reg = panel.set_index(['Scode', 'Year'])

def run_panel_fe(dep, exog_list, data, label):
    """运行面板固定效应回归"""
    sub = data[exog_list + [dep]].dropna().copy()
    if len(sub) < 50:
        print(f"  {label}: 样本不足 ({len(sub)})")
        return None
    mod = PanelOLS(sub[dep], sub[exog_list],
                   entity_effects=True, time_effects=True, check_rank=False)
    res = mod.fit(cov_type='clustered', cluster_entity=True)
    return res

def format_coef(res, var):
    if res is None:
        return "N/A"
    c = res.params[var]
    p = res.pvalues[var]
    se = res.std_errors[var]
    sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
    return f"{c:.4f}{sig} ({se:.4f})"

# (1) lnPatent ~ pressure, FE only
res1 = run_panel_fe('ln_Patent', ['pressure'], panel_reg, '(1)')
# (2) lnInvPatent ~ pressure, FE only
res2 = run_panel_fe('ln_inv_patent', ['pressure'], panel_reg, '(2)')
# (3) lnPatent ~ pressure + ln_pergdp
res3 = run_panel_fe('ln_Patent', ['pressure', 'ln_pergdp'], panel_reg, '(3)')
# (4) lnInvPatent ~ pressure + ln_pergdp
res4 = run_panel_fe('ln_inv_patent', ['pressure', 'ln_pergdp'], panel_reg, '(4)')
# (3b) with RD
res3b = run_panel_fe('ln_Patent', ['pressure', 'ln_pergdp', 'RD'], panel_reg, '(3b)')
# (4b) with RD
res4b = run_panel_fe('ln_inv_patent', ['pressure', 'ln_pergdp', 'RD'], panel_reg, '(4b)')

print("\n" + "=" * 60)
print("基准回归结果汇总")
print("=" * 60)

print(f"\n{'':15s} {'(1)lnPatent':>18s} {'(2)lnInv':>18s} {'(3)lnPatent':>18s} {'(4)lnInv':>18s}")
print(f"{'':15s} {'无控制':>18s} {'无控制':>18s} {'有控制':>18s} {'有控制':>18s}")
print("-" * 90)

# 复现结果
print(f"{'复现pressure':15s}", end="")
for r in [res1, res2, res3, res4]:
    print(f" {format_coef(r, 'pressure'):>18s}", end="")
print()

# ln_pergdp
if res3 and 'ln_pergdp' in res3.params:
    print(f"{'复现ln_pergdp':15s}", end="")
    print(f" {'':>18s} {'':>18s}", end="")
    print(f" {format_coef(res3, 'ln_pergdp'):>18s}", end="")
    print(f" {format_coef(res4, 'ln_pergdp'):>18s}")

# R² and N
print(f"\n{'复现R²':15s}", end="")
for r in [res1, res2, res3, res4]:
    if r:
        print(f" {r.rsquared_overall:>18.4f}", end="")
    else:
        print(f" {'N/A':>18s}", end="")
print()

print(f"{'复现N':15s}", end="")
for r in [res1, res2, res3, res4]:
    if r:
        print(f" {r.nobs:>18d}", end="")
    else:
        print(f" {'N/A':>18s}", end="")
print()

# 论文结果
print(f"\n{'─'*90}")
print(f"{'论文pressure':15s}  -0.149***(0.040)   -0.137***(0.044)   -0.110***(0.036)    -0.091**(0.042)")
print(f"{'论文R²':15s}             0.764              0.851              0.785              0.869")
print(f"{'论文N':15s}             16937              14097              16926              14093")
print(f"{'论文控制变量':15s}               否                 否  ln_Sale,ln_age等9个  ln_Sale,ln_age等9个")

# 加入RD控制的结果
if res3b is not None:
    print(f"\n{'─'*90}")
    print(f"加入RD控制后:")
    print(f"  (3b) lnPatent ~ pressure + ln_pergdp + RD: {format_coef(res3b, 'pressure')}")
    print(f"       R²={res3b.rsquared_overall:.4f}, N={res3b.nobs}")
if res4b is not None:
    print(f"  (4b) lnInv ~ pressure + ln_pergdp + RD: {format_coef(res4b, 'pressure')}")
    print(f"       R²={res4b.rsquared_overall:.4f}, N={res4b.nobs}")

# ============================================================
# 打印详细回归表
# ============================================================
print("\n" + "=" * 60)
print("详细回归结果")
print("=" * 60)

for i, (label, res) in enumerate([(f'(1) ln_Patent ~ pressure', res1),
                                   (f'(2) ln_inv ~ pressure', res2),
                                   (f'(3) ln_Patent ~ pressure + controls', res3),
                                   (f'(4) ln_inv ~ pressure + controls', res4)]):
    if res is not None:
        print(f"\n--- {label} ---")
        print(res.summary)

# ============================================================
# 结果分析
# ============================================================
print("\n" + "=" * 60)
print("复现结论与差异分析")
print("=" * 60)

if res1 is not None:
    c1 = res1.params['pressure']
    p1 = res1.pvalues['pressure']
    direction = "负向" if c1 < 0 else "正向"
    sig = "显著" if p1 < 0.1 else "不显著"

    print(f"""
1. 核心发现:
   - 论文: 财政压力对企业创新有显著负向影响 (β=-0.149***)
   - 复现: 财政压力系数为 {c1:.4f} ({sig}, p={p1:.4f})
   - 方向: {direction}

2. 样本差异:
   - 论文样本量约17,000条（全部A股制造业上市公司）
   - 复现样本量{res1.nobs}条（仅专精特新制造业上市公司）
   - 样本为论文的子集，偏向创新型企业

3. 控制变量缺失:
   - 缺少企业规模(ln_Sale)、杠杆率(lev)、企业年龄(ln_age)、
     SOE虚拟变量、资产结构(Tang)、行业集中度(HHI)、ROA
   - 这可能导致遗漏变量偏误

4. 复现评价:
   {'- 核心结论方向一致：财政压力抑制企业创新' if c1 < 0 else '- 方向与论文不一致，可能原因为样本差异'}
   - 由于数据限制，仅能做部分复现
   - 需要完整的CSMAR企业财务数据才能完全复现
""")

panel.to_csv('cleaned_data/lisen_replication_panel.csv', index=False, encoding='utf-8-sig')
print("面板数据已保存至 cleaned_data/lisen_replication_panel.csv")
print("\n复现完成！")
