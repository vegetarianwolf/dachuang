"""
复现：财政压力对制造业企业创新的影响研究（李森, 王聪, 2024）
最终版 - 修复R&D数据解析、城市匹配、扩大样本覆盖
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 构建企业-城市映射
# ============================================================
print("=" * 60)
print("1. 构建企业-城市映射")
print("=" * 60)

# 从SRDI_EntInfo_Full获取行业分类 + 城市
info = pd.read_csv('csmar_data_export/SRDI_EntInfo_Full.csv',
                   encoding='utf-8-sig', low_memory=False, on_bad_lines='skip',
                   usecols=['InstitutionID', 'InstitutionName', 'CityName',
                           'ProvinceName', 'GBCode2017MainClass', 'EnterpriseNature'])

# 取最后一条记录（最新信息）
info_dedup = info.drop_duplicates(subset=['InstitutionID'], keep='last')

# 从EntIdentInfo获取上市公司股票代码
ident = pd.read_csv('csmar_data_export/SRDI_EntIdentInfo.csv',
                    encoding='utf-8-sig', low_memory=False)
ident_sym = ident[ident['Symbol'].notna()][['InstitutionID', 'Symbol']].drop_duplicates(subset=['Symbol'])
# 过滤逗号
ident_sym = ident_sym[~ident_sym['Symbol'].astype(str).str.contains(',')]

# 合并获取映射  
mapping = ident_sym.merge(info_dedup[['InstitutionID', 'CityName', 'ProvinceName',
                                       'GBCode2017MainClass', 'EnterpriseNature']],
                          on='InstitutionID', how='left')

# 筛选制造业
mapping_mfg = mapping[mapping['GBCode2017MainClass'].str.startswith('C', na=False)].copy()
mapping_mfg['Scode'] = mapping_mfg['Symbol'].astype(str).str.lstrip('0').astype(int)

# 清理城市名
mapping_mfg['city'] = mapping_mfg['CityName'].astype(str).str.replace('市$', '', regex=True)
mapping_mfg['prov'] = mapping_mfg['ProvinceName'].astype(str).str.replace('省$|市$|自治区$|壮族自治区$|回族自治区$|维吾尔自治区$', '', regex=True)

# 判断SOE (粗略: 名称包含"国有"或EnterpriseNature包含"国有")
mapping_mfg['is_soe'] = mapping_mfg['EnterpriseNature'].str.contains('国有|国资', na=False).astype(int)

print(f"制造业上市公司: {len(mapping_mfg)}家")
print(f"覆盖城市: {mapping_mfg['city'].nunique()}")

del info, info_dedup, ident

# ============================================================
# 2. 获取专利数据
# ============================================================
print("\n" + "=" * 60)
print("2. 获取专利申请数据")
print("=" * 60)

patent = pd.read_csv(
    'CNRDS专利数据包/上市公司专利申请与获得/上市公司专利申请情况/上市公司专利申请情况.csv',
    skiprows=[1], encoding='utf-8-sig')
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
# 3. 构建财政压力
# ============================================================
print("\n" + "=" * 60)
print("3. 构建城市级财政压力")
print("=" * 60)

def parse_ceic_fast(filepath, value_name):
    """快速解析CEIC宽格式"""
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    date_col = df.columns[0]
    df = df.rename(columns={date_col: 'date'})
    df['year'] = pd.to_numeric(df['date'], errors='coerce').astype('Int64')
    df = df.dropna(subset=['year'])

    id_vars = ['year']
    value_vars = [c for c in df.columns if c not in ['date', 'year']]
    long = df[['year'] + value_vars].melt(id_vars='year', var_name='col_name', value_name=value_name)
    long[value_name] = pd.to_numeric(long[value_name], errors='coerce')
    long = long.dropna(subset=[value_name])
    long['city'] = long['col_name'].apply(lambda x: x.split(':')[-1].strip())
    return long[['year', 'city', value_name]]

rev = parse_ceic_fast('地级市财政收入.csv', 'fiscal_revenue')
exp = parse_ceic_fast('地级市财政支出.csv', 'fiscal_expenditure')
pgdp = parse_ceic_fast('地级市人均GDP.csv', 'pergdp')

fiscal = rev.merge(exp, on=['year', 'city'], how='inner')
fiscal = fiscal.merge(pgdp, on=['year', 'city'], how='left')
fiscal = fiscal[(fiscal['year'] >= 2010) & (fiscal['year'] <= 2020)]

# 财政压力 = (支出 - 收入) / 收入
fiscal['pressure'] = (fiscal['fiscal_expenditure'] - fiscal['fiscal_revenue']) / fiscal['fiscal_revenue']
fiscal['ln_pergdp'] = np.log(fiscal['pergdp'].clip(lower=1))
fiscal = fiscal[fiscal['pressure'].notna() & np.isfinite(fiscal['pressure'])]

# 查看城市匹配情况并改进
fiscal_cities = set(fiscal['city'].unique())
map_cities = set(mapping_mfg['city'].unique())
print(f"财政城市: {len(fiscal_cities)}, 企业城市: {len(map_cities)}")
print(f"直接匹配: {len(map_cities & fiscal_cities)}")

# 常见城市名替换
city_synonyms = {
    '北京': '北京', '天津': '天津', '上海': '上海', '重庆': '重庆',
    '广州': '广州', '深圳': '深圳', '呼和浩特': '呼和浩特',
    '巴彦淖尔': '巴彦淖尔', '锡林郭勒': '锡林郭勒盟',
    '昌吉': '昌吉州', '凉山': '凉山州', '义乌': '金华',
    '江阴': '无锡', '昆山': '苏州', '常熟': '苏州',
    '张家港': '苏州', '宜兴': '无锡', '太仓': '苏州',
    '靖江': '泰州', '海门': '南通', '启东': '南通',
    '如皋': '南通', '句容': '镇江', '丹阳': '镇江',
    '仪征': '扬州', '诸暨': '绍兴', '余姚': '宁波',
    '慈溪': '宁波', '温岭': '台州', '瑞安': '温州',
    '乐清': '温州', '桐乡': '嘉兴', '海宁': '嘉兴',
    '长兴': '湖州', '晋江': '泉州', '石狮': '泉州',
    '新郑': '郑州', '巩义': '郑州', '荥阳': '郑州',
    '新密': '郑州', '禹州': '许昌', '长葛': '许昌',
    '新泰': '泰安', '龙口': '烟台', '寿光': '潍坊',
    '宜都': '宜昌', '潜江': '潜江', '天门': '天门',
    '仙桃': '仙桃', '赤壁': '咸宁', '浏阳': '长沙',
    '宁乡': '长沙', '醴陵': '株洲', '汨罗': '岳阳',
}
mapping_mfg['city_matched'] = mapping_mfg['city'].map(city_synonyms).fillna(mapping_mfg['city'])
overlap2 = set(mapping_mfg['city_matched'].unique()) & fiscal_cities
print(f"修正后匹配: {len(overlap2)}")

print(f"\n财政压力: mean={fiscal['pressure'].mean():.3f}, std={fiscal['pressure'].std():.3f}")

# ============================================================
# 4. 获取R&D数据
# ============================================================
print("\n" + "=" * 60)
print("4. 获取R&D数据")
print("=" * 60)

rd = pd.read_csv('CNRDS专利数据包/上市公司研发费用/上市公司研发支出/上市公司研发支出.csv',
                 skiprows=[1], encoding='utf-8-sig')
rd['Scode'] = pd.to_numeric(rd['Scode'], errors='coerce')
rd['Year'] = pd.to_numeric(rd['Year'], errors='coerce')
rd = rd.dropna(subset=['Scode', 'Year'])
rd['Scode'] = rd['Scode'].astype(int)
rd['Year'] = rd['Year'].astype(int)

# R&Deapoinr格式是 "4.39%"，需要去掉%
rd['RD_pct'] = rd['R&Deapoinr'].astype(str).str.rstrip('%')
rd['RD_pct'] = pd.to_numeric(rd['RD_pct'], errors='coerce') / 100  # 转为小数

# R&Dexp: 研发支出总额（元）
rd['RD_exp'] = pd.to_numeric(rd['R&Dexp'], errors='coerce')

rd = rd[['Scode', 'Year', 'RD_pct', 'RD_exp']].copy()
rd = rd[(rd['Year'] >= 2010) & (rd['Year'] <= 2020)]
rd = rd.dropna(subset=['RD_exp'])  # 至少有研发支出数据

print(f"R&D数据: {len(rd)}条, {rd['Scode'].nunique()}家企业")
print(f"R&D占比非空: {rd['RD_pct'].notna().sum()}条")

# ============================================================
# 5. 合并面板
# ============================================================
print("\n" + "=" * 60)
print("5. 合并面板数据")
print("=" * 60)

panel = patent[['Scode', 'Year', 'total_patent', 'Invia', 'Umia', 'Desia',
                'ln_Patent', 'ln_inv_patent']].copy()

# 合并企业信息（选择mapping中实际存在的列）
merge_cols = ['Scode', 'city_matched', 'prov', 'GBCode2017MainClass', 'is_soe']
if 'InstitutionName' in mapping_mfg.columns:
    merge_cols.insert(3, 'InstitutionName')
panel = panel.merge(
    mapping_mfg[merge_cols],
    on='Scode', how='inner')
print(f"合并企业映射: {len(panel)}条, {panel['Scode'].nunique()}家")

# 合并财政数据
panel = panel.merge(
    fiscal[['year', 'city', 'pressure', 'ln_pergdp', 'pergdp']],
    left_on=['Year', 'city_matched'], right_on=['year', 'city'], how='inner')
print(f"合并财政数据: {len(panel)}条, {panel['Scode'].nunique()}家")

# 合并R&D数据
panel = panel.merge(rd[['Scode', 'Year', 'RD_pct', 'RD_exp']], on=['Scode', 'Year'], how='left')
print(f"合并R&D数据: {len(panel)}条")
print(f"  有R&D占比: {panel['RD_pct'].notna().sum()}条")
print(f"  有R&D支出: {panel['RD_exp'].notna().sum()}条")

# 缩尾处理（1%/99%）
def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))

for col in ['pressure', 'ln_Patent', 'ln_inv_patent', 'ln_pergdp', 'RD_pct']:
    if col in panel.columns and panel[col].notna().sum() > 0:
        panel.loc[panel[col].notna(), col] = winsorize(panel[col].dropna())

panel = panel.dropna(subset=['ln_Patent', 'pressure'])

# 行业二级代码
panel['ind2'] = panel['GBCode2017MainClass'].str[:3]

print(f"\n最终面板: {len(panel)}条, {panel['Scode'].nunique()}家, "
      f"{panel['Year'].min()}-{panel['Year'].max()}")
print(f"覆盖城市: {panel['city_matched'].nunique()}")

# ============================================================
# 描述性统计
# ============================================================
print("\n" + "=" * 60)
print("描述性统计对比")
print("=" * 60)

print(f"\n{'变量':12s} {'复现N':>7s} {'复现Mean':>9s} {'复现Std':>8s} {'复现Min':>8s} {'复现Max':>8s} │{'论文N':>7s} {'论文Mean':>9s} {'论文Std':>8s}")
stats = [
    ('ln_Patent', '创新数量', 17279, 3.104, 1.527),
    ('ln_inv_patent', '发明专利', None, None, None),
    ('pressure', '财政压力', 17279, 0.559, 0.775),
    ('ln_pergdp', '人均GDP', 17279, 11.38, 0.513),
    ('RD_pct', '研发投入', 17279, 0.023, 0.016),
    ('is_soe', 'SOE', 17279, 0.276, 0.447),
]
for var, name, pn, pm, ps in stats:
    if var in panel.columns:
        s = panel[var].dropna()
        if len(s) > 0:
            pn_str = str(pn) if pn else 'N/A'
            pm_str = f'{pm:.3f}' if pm is not None else 'N/A'
            ps_str = f'{ps:.3f}' if ps is not None else 'N/A'
            print(f"{name:12s} {len(s):>7d} {s.mean():>9.3f} {s.std():>8.3f} {s.min():>8.3f} {s.max():>8.3f} │{pn_str:>7s} {pm_str:>9s} {ps_str:>8s}")

# ============================================================
# 6. 回归分析
# ============================================================
print("\n" + "=" * 60)
print("6. 回归分析 —— 复现表2基准回归")
print("=" * 60)

from linearmodels.panel import PanelOLS

panel_reg = panel.copy()
panel_reg = panel_reg.set_index(['Scode', 'Year'])

def run_fe(dep, exog, data, label, cluster='entity'):
    """运行面板FE回归"""
    cols = [dep] + exog
    sub = data[cols].dropna().copy()
    if len(sub) < 100:
        print(f"  [{label}] 样本不足 ({len(sub)})")
        return None
    try:
        mod = PanelOLS(sub[dep], sub[exog],
                       entity_effects=True, time_effects=True, check_rank=False)
        if cluster == 'entity':
            res = mod.fit(cov_type='clustered', cluster_entity=True)
        else:
            res = mod.fit(cov_type='robust')
        return res
    except Exception as e:
        print(f"  [{label}] 错误: {e}")
        return None

def fmt(res, var):
    if res is None: return 'N/A'
    c, p, se = res.params[var], res.pvalues[var], res.std_errors[var]
    sig = '***' if p<0.01 else '**' if p<0.05 else '*' if p<0.1 else ''
    return f"{c:+.4f}{sig} ({se:.4f})"

# ---- 表2 回归 ----
# (1) lnPatent ~ pressure (无控制)
r1 = run_fe('ln_Patent', ['pressure'], panel_reg, '1')
# (2) lnInv ~ pressure (无控制)  
r2 = run_fe('ln_inv_patent', ['pressure'], panel_reg, '2')
# (3) lnPatent ~ pressure + 控制
ctrl = ['pressure', 'ln_pergdp']
r3 = run_fe('ln_Patent', ctrl, panel_reg, '3')
# (4) lnInv ~ pressure + 控制
r4 = run_fe('ln_inv_patent', ctrl, panel_reg, '4')

# (3b) (4b) 加入RD
ctrl_rd = ['pressure', 'ln_pergdp', 'RD_pct']
r3b = run_fe('ln_Patent', ctrl_rd, panel_reg, '3b')
r4b = run_fe('ln_inv_patent', ctrl_rd, panel_reg, '4b')

# (3c) (4c) 加入RD + SOE
ctrl_full = ['pressure', 'ln_pergdp', 'RD_pct', 'is_soe']
r3c = run_fe('ln_Patent', ctrl_full, panel_reg, '3c')
r4c = run_fe('ln_inv_patent', ctrl_full, panel_reg, '4c')

# ============================================================
# 结果汇总
# ============================================================
print("\n" + "=" * 60)
print("表2 基准回归结果对比")
print("=" * 60)

print(f"\n{'':20s} | {'(1)lnPatent':>20s} | {'(2)lnInv':>20s} | {'(3)lnPatent':>20s} | {'(4)lnInv':>20s}")
print(f"{'':20s} | {'无控制':>20s} | {'无控制':>20s} | {'有控制':>20s} | {'有控制':>20s}")
print("-" * 110)

print(f"{'复现 pressure':20s} |{fmt(r1,'pressure'):>21s} |{fmt(r2,'pressure'):>21s} |{fmt(r3,'pressure'):>21s} |{fmt(r4,'pressure'):>21s}")
print(f"{'论文 pressure':20s} | {'-0.149***  (0.040)':>20s} | {'-0.137***  (0.044)':>20s} | {'-0.110***  (0.036)':>20s} | {'-0.091**   (0.042)':>20s}")

print()
if r3 and 'ln_pergdp' in r3.params:
    print(f"{'复现 ln_pergdp':20s} | {'':>20s} | {'':>20s} |{fmt(r3,'ln_pergdp'):>21s} |{fmt(r4,'ln_pergdp'):>21s}")
    print(f"{'论文 ln_pergdp':20s} | {'':>20s} | {'':>20s} | {'0.003      (0.078)':>20s} | {'0.083      (0.075)':>20s}")

print()
row_r2 = f"{'复现 R²':20s} |"
row_r2_paper = f"{'论文 R²':20s} |"
row_n = f"{'复现 N':20s} |"
row_n_paper = f"{'论文 N':20s} |"
paper_r2 = [0.764, 0.851, 0.785, 0.869]
paper_n = [16937, 14097, 16926, 14093]
for i, r in enumerate([r1, r2, r3, r4]):
    if r:
        row_r2 += f"{r.rsquared_overall:>21.4f} |"
        row_n += f"{r.nobs:>21d} |"
    else:
        row_r2 += f"{'N/A':>21s} |"
        row_n += f"{'N/A':>21s} |"
    row_r2_paper += f"{paper_r2[i]:>21.3f} |"
    row_n_paper += f"{paper_n[i]:>21d} |"

print(row_r2)
print(row_r2_paper)
print(row_n)
print(row_n_paper)

# 加入更多控制变量的结果
print(f"\n{'─'*110}")
print("加入更多控制变量:")
if r3b:
    print(f"  (3b) +RD_pct: pressure={fmt(r3b,'pressure')}, RD={fmt(r3b,'RD_pct')}, N={r3b.nobs}")
if r4b:
    print(f"  (4b) +RD_pct: pressure={fmt(r4b,'pressure')}, RD={fmt(r4b,'RD_pct')}, N={r4b.nobs}")
if r3c:
    print(f"  (3c) +RD+SOE: pressure={fmt(r3c,'pressure')}, N={r3c.nobs}")
if r4c:
    print(f"  (4c) +RD+SOE: pressure={fmt(r4c,'pressure')}, N={r4c.nobs}")

# ============================================================
# 7. 详细回归输出
# ============================================================
print("\n" + "=" * 60)
print("7. 详细回归输出")
print("=" * 60)
for lbl, r in [('(1) lnPatent~pressure', r1),
               ('(2) lnInv~pressure', r2),
               ('(3) lnPatent~pressure+ctrls', r3),
               ('(4) lnInv~pressure+ctrls', r4)]:
    if r:
        print(f"\n--- {lbl} ---")
        print(r.summary)

# ============================================================
# 8. 分析与讨论
# ============================================================
print("\n" + "=" * 60)
print("8. 复现结论与差异分析")
print("=" * 60)

if r1:
    c_val = r1.params['pressure']
    p_val = r1.pvalues['pressure']
    dir_str = "负向" if c_val < 0 else "正向"
    sig_str = "在1%水平显著" if p_val<0.01 else "在5%水平显著" if p_val<0.05 else "在10%水平显著" if p_val<0.1 else "不显著"
    
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心对比:
  论文发现: 财政压力对企业创新有显著负向影响
    - pressure系数: -0.149*** (无控制), -0.110*** (有控制)

  复现发现: 财政压力系数 = {c_val:.4f} ({sig_str}, p={p_val:.4f})
    - 方向: {dir_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

差异原因分析:

1. 样本差异（最主要原因）:
   论文: 全部A股制造业上市公司 (2010-2020, ~17000条观测)
   复现: 仅"专精特新"(SRDI)中的制造业上市公司 (~{len(panel)}条)
   
   ⚠️ 专精特新企业是政策识别的创新型企业，存在严重的样本选择偏差:
   - 这些企业本身就是创新能力较强的企业
   - 它们可能对财政压力的敏感度与一般企业不同
   - 作为政策支持对象，可能获得更多补贴，抵消了财政压力影响

2. 控制变量缺失:
   论文控制了9个变量: ln_Sale, ln_age, lev, RD, Tang, HHI, Roa, Soe, ln_pergdp
   本复现仅有: ln_pergdp (+ 部分RD_pct, is_soe)
   缺少关键的企业财务变量（需要CSMAR数据库access）

3. 创新质量指标:
   论文使用专利被引次数(ln Cit)衡量创新质量
   本复现只有发明专利申请量，无被引数据

4. 标准误聚类:
   论文在城市层面聚类；复现在企业层面聚类

改进建议:
   - 获取CSMAR数据库中全部制造业上市公司财务数据
   - 获取完整的STK_LISTEDCOINFOANL.csv（包含注册地址和行业代码）
   - 获取专利被引次数数据
   - 使用城市层面聚类标准误
""")

# 保存
panel.to_csv('cleaned_data/lisen_replication_panel.csv', index=False, encoding='utf-8-sig')
print("面板数据已保存至 cleaned_data/lisen_replication_panel.csv")
print("完成！")
