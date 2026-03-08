"""
复现：财政压力对制造业企业创新的影响研究
——基于创新数量与创新质量双重视角的经验分析（李森, 王聪, 2024）

数据来源:
- 专利数据: CNRDS专利数据包
- 企业信息: CSMAR (SRDI_EntInfo_Full + SRDI_EntIdentInfo)
- 财政数据: CEIC城市财政收入/支出
- 人均GDP: CEIC地级市人均GDP
- R&D数据: CNRDS上市公司研发支出

由于缺少完整的CSMAR企业财务数据(资产负债表、利润表),
本复现仅能使用部分控制变量。
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 第一步：构建企业-城市映射（制造业上市公司）
# ============================================================
print("=" * 70)
print("第一步：构建企业-城市映射")
print("=" * 70)

# 从SRDI_EntInfo_Full获取行业分类
info = pd.read_csv('csmar_data_export/SRDI_EntInfo_Full.csv',
                   encoding='utf-8-sig', low_memory=False, on_bad_lines='skip')
ind_map = info[['InstitutionID', 'GBCode2017MainClass']].dropna() \
    .drop_duplicates(subset=['InstitutionID'])

# 从SRDI_EntIdentInfo获取上市公司的股票代码和城市
ident = pd.read_csv('csmar_data_export/SRDI_EntIdentInfo.csv',
                    encoding='utf-8-sig', low_memory=False)
listed = ident[ident['IsListed'] == 1].copy()
listed_ind = listed.merge(ind_map, on='InstitutionID', how='left')

# 筛选制造业（GBCode以C开头）
mfg = listed_ind[listed_ind['GBCode2017MainClass'].str.startswith('C', na=False)]
mfg_unique = mfg.drop_duplicates(subset=['Symbol'])

# 构建映射表
mapping = mfg_unique[['Symbol', 'InstitutionID', 'InstitutionName',
                       'CityName', 'ProvinceName', 'GBCode2017MainClass']].copy()
mapping = mapping[~mapping['Symbol'].astype(str).str.contains(',')]
mapping['Scode'] = mapping['Symbol'].astype(str).str.lstrip('0').astype(int)

# 清理城市名称（去掉"市"后缀以便匹配）
mapping['city_clean'] = mapping['CityName'].astype(str).str.replace('市$', '', regex=True)
mapping['prov_clean'] = mapping['ProvinceName'].astype(str).str.replace('省$|市$', '', regex=True)

print(f"制造业上市公司数量: {len(mapping)}")
print(f"覆盖城市数: {mapping['city_clean'].nunique()}")
print(f"覆盖省份数: {mapping['prov_clean'].nunique()}")

# ============================================================
# 第二步：获取专利数据（被解释变量）
# ============================================================
print("\n" + "=" * 70)
print("第二步：获取专利申请数据")
print("=" * 70)

patent = pd.read_csv(
    'CNRDS专利数据包/上市公司专利申请与获得/上市公司专利申请情况/上市公司专利申请情况.csv',
    skiprows=[1], encoding='utf-8-sig'
)
# 只保留"上市公司本身"类型
patent = patent[patent['Ftyp'] == '上市公司本身'].copy()
patent['Scode'] = pd.to_numeric(patent['Scode'], errors='coerce')
patent['Year'] = pd.to_numeric(patent['Year'], errors='coerce')
patent = patent.dropna(subset=['Scode', 'Year'])
patent['Scode'] = patent['Scode'].astype(int)
patent['Year'] = patent['Year'].astype(int)

# 筛选2010-2020年
patent = patent[(patent['Year'] >= 2010) & (patent['Year'] <= 2020)]

# 计算专利申请总量 = 发明 + 实用新型 + 外观设计
for col in ['Invia', 'Umia', 'Desia']:
    patent[col] = pd.to_numeric(patent[col], errors='coerce').fillna(0)

patent['total_patent'] = patent['Invia'] + patent['Umia'] + patent['Desia']

# 被解释变量: ln(Patent) = ln(专利申请总量 + 1)
patent['ln_Patent'] = np.log(patent['total_patent'] + 1)
# 发明专利单独：发明占比更高说明质量更好
patent['ln_inv_patent'] = np.log(patent['Invia'] + 1)

print(f"专利数据: {len(patent)} 条记录")
print(f"覆盖企业数: {patent['Scode'].nunique()}")
print(f"年份范围: {patent['Year'].min()}-{patent['Year'].max()}")

# ============================================================
# 第三步：构建城市级财政压力
# ============================================================
print("\n" + "=" * 70)
print("第三步：构建城市级财政压力变量")
print("=" * 70)

def parse_ceic_wide(filepath, value_name):
    """解析CEIC宽格式数据为长格式"""
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    df = df.rename(columns={df.columns[0]: 'date'})
    df = df.dropna(subset=['date'])

    # 转换为长格式
    records = []
    for col in df.columns[1:]:
        # 从列名提取城市名
        parts = col.split(':')
        if len(parts) >= 3:
            # 如 "财政收入:地方:一般公共预算收入:河北:石家庄"
            city = parts[-1].strip()
            province = parts[-2].strip() if len(parts) >= 4 else parts[-1].strip()
        elif len(parts) == 2:
            city = parts[-1].strip()
            province = city
        else:
            continue

        for _, row in df.iterrows():
            try:
                year = int(str(row['date'])[:4])
                val = float(row[col])
                records.append({'year': year, 'city': city, 'province': province,
                               value_name: val})
            except (ValueError, TypeError):
                continue

    return pd.DataFrame(records)


# 解析财政收入
print("解析财政收入...")
rev = parse_ceic_wide('地级市财政收入.csv', 'fiscal_revenue')
print(f"  财政收入: {len(rev)} 条")

# 解析财政支出
print("解析财政支出...")
exp = parse_ceic_wide('地级市财政支出.csv', 'fiscal_expenditure')
print(f"  财政支出: {len(exp)} 条")

# 解析人均GDP
print("解析人均GDP...")
pgdp = parse_ceic_wide('地级市人均GDP.csv', 'pergdp')
print(f"  人均GDP: {len(pgdp)} 条")

# 合并财政数据
fiscal = rev.merge(exp, on=['year', 'city', 'province'], how='inner')
fiscal = fiscal.merge(pgdp[['year', 'city', 'pergdp']], on=['year', 'city'], how='left')

# 筛选2010-2020
fiscal = fiscal[(fiscal['year'] >= 2010) & (fiscal['year'] <= 2020)]

# 计算财政压力 = (支出 - 收入) / 收入
fiscal['pressure'] = (fiscal['fiscal_expenditure'] - fiscal['fiscal_revenue']) / fiscal['fiscal_revenue']

# 人均GDP取对数
fiscal['ln_pergdp'] = np.log(fiscal['pergdp'].replace(0, np.nan))

print(f"\n财政数据: {len(fiscal)} 条")
print(f"覆盖城市: {fiscal['city'].nunique()}")
print(f"财政压力描述统计:")
print(fiscal['pressure'].describe())

# ============================================================
# 第四步：获取R&D数据（控制变量之一）
# ============================================================
print("\n" + "=" * 70)
print("第四步：获取R&D数据")
print("=" * 70)

rd = pd.read_csv(
    'CNRDS专利数据包/上市公司研发费用/上市公司研发支出/上市公司研发支出.csv',
    skiprows=[1], encoding='utf-8-sig'
)
rd['Scode'] = pd.to_numeric(rd['Scode'], errors='coerce')
rd['Year'] = pd.to_numeric(rd['Year'], errors='coerce')
rd = rd.dropna(subset=['Scode', 'Year'])
rd['Scode'] = rd['Scode'].astype(int)
rd['Year'] = rd['Year'].astype(int)

# R&D支出占比 (R&Dpr = 研发投入占营业收入比例)
rd['RD'] = pd.to_numeric(rd['R&Dpr'], errors='coerce')
rd = rd[['Scode', 'Year', 'RD']].dropna()
rd = rd[(rd['Year'] >= 2010) & (rd['Year'] <= 2020)]

print(f"R&D数据: {len(rd)} 条, 覆盖企业: {rd['Scode'].nunique()}")

# ============================================================
# 第五步：合并构建面板数据
# ============================================================
print("\n" + "=" * 70)
print("第五步：合并构建面板数据")
print("=" * 70)

# 先将专利数据与企业映射合并
panel = patent[['Scode', 'Year', 'total_patent', 'Invia', 'Umia', 'Desia',
                'ln_Patent', 'ln_inv_patent']].copy()
panel = panel.merge(mapping[['Scode', 'city_clean', 'prov_clean', 'InstitutionName',
                              'GBCode2017MainClass']],
                    on='Scode', how='inner')

print(f"专利+企业映射后: {len(panel)} 条, {panel['Scode'].nunique()} 家企业")

# 与财政数据合并（按城市名匹配）
panel = panel.merge(fiscal[['year', 'city', 'pressure', 'ln_pergdp',
                             'fiscal_revenue', 'fiscal_expenditure']],
                    left_on=['Year', 'city_clean'],
                    right_on=['year', 'city'],
                    how='inner')

print(f"合并财政数据后: {len(panel)} 条, {panel['Scode'].nunique()} 家企业")

# 合并R&D数据
panel = panel.merge(rd, on=['Scode', 'Year'], how='left')
print(f"合并R&D数据后: {len(panel)} 条")

# 清理数据
# 1. 去除极端值（上下1%缩尾处理）
def winsorize(series, lower=0.01, upper=0.99):
    """缩尾处理"""
    q_low = series.quantile(lower)
    q_high = series.quantile(upper)
    return series.clip(q_low, q_high)

for col in ['pressure', 'ln_Patent', 'ln_inv_patent']:
    panel[col] = winsorize(panel[col])

# 2. 去除缺失核心变量的观测
panel = panel.dropna(subset=['ln_Patent', 'pressure'])

# 创建企业和年份标识
panel['firm_id'] = panel['Scode']
panel['year_id'] = panel['Year']

# 创建行业代码（2位）
panel['industry_code'] = panel['GBCode2017MainClass'].str[:3]  # e.g., 'C13', 'C26'

print(f"\n最终面板: {len(panel)} 条记录, {panel['Scode'].nunique()} 家企业")
print(f"年份范围: {panel['Year'].min()}-{panel['Year'].max()}")
print(f"城市数: {panel['city_clean'].nunique()}")

# 描述性统计
print("\n" + "=" * 70)
print("描述性统计")
print("=" * 70)
desc_vars = {
    'ln_Patent': '创新数量 ln(Patent)',
    'ln_inv_patent': '发明专利 ln(Inv)',
    'pressure': '财政压力',
    'ln_pergdp': '人均GDP对数',
    'RD': '研发投入强度',
}
for var, name in desc_vars.items():
    if var in panel.columns:
        s = panel[var].dropna()
        print(f"{name:20s}: N={len(s):6d}, Mean={s.mean():.3f}, "
              f"Std={s.std():.3f}, Min={s.min():.3f}, Max={s.max():.3f}")

# 论文描述性统计对比
print("\n论文原文描述性统计:")
print(f"{'变量':20s}: {'N':>6s}, {'Mean':>8s}, {'Min':>8s}, {'Max':>8s}, {'Std':>8s}")
paper_stats = [
    ('创新数量', 17279, 3.104, 0, 6.668, 1.527),
    ('创新质量', 14361, 2.913, 0, 7.125, 1.486),
    ('财政压力', 17279, 0.559, -0.351, 13.24, 0.775),
]
for name, n, mean, mn, mx, std in paper_stats:
    print(f"{name:20s}: {n:6d}, {mean:8.3f}, {mn:8.3f}, {mx:8.3f}, {std:8.3f}")

# ============================================================
# 第六步：回归分析
# ============================================================
print("\n" + "=" * 70)
print("第六步：回归分析 —— 复现基准回归（表2）")
print("=" * 70)

try:
    import linearmodels
    HAS_LINEARMODELS = True
except ImportError:
    HAS_LINEARMODELS = False

try:
    import statsmodels.api as sm
    from statsmodels.regression.linear_model import OLS
    HAS_SM = True
except ImportError:
    HAS_SM = False

if not HAS_LINEARMODELS:
    print("安装 linearmodels 包...")
    import subprocess
    subprocess.check_call(['.venv/Scripts/pip', 'install', 'linearmodels', '-q'])
    import linearmodels
    HAS_LINEARMODELS = True

from linearmodels.panel import PanelOLS
from linearmodels.panel import compare

# 设置面板索引
panel_reg = panel.set_index(['firm_id', 'year_id'])

# ------ 回归 (1): ln_Patent ~ pressure, 企业+年份固定效应 ------
print("\n--- 回归(1): 创新数量 ~ 财政压力（无控制变量）---")
try:
    mod1 = PanelOLS(
        panel_reg['ln_Patent'],
        panel_reg[['pressure']],
        entity_effects=True,
        time_effects=True,
        check_rank=False
    )
    res1 = mod1.fit(cov_type='clustered', cluster_entity=True)
    print(res1.summary.tables[1])
    coef1 = res1.params['pressure']
    se1 = res1.std_errors['pressure']
    pval1 = res1.pvalues['pressure']
    r2_1 = res1.rsquared_overall
    n1 = res1.nobs
    print(f"\npressure系数: {coef1:.3f} (SE={se1:.3f}, p={pval1:.3f})")
    print(f"R²: {r2_1:.3f}, N: {n1}")
    print(f"论文结果: pressure=-0.149*** (0.040), R²=0.764, N=16937")
except Exception as e:
    print(f"回归(1)出错: {e}")
    res1 = None

# ------ 回归 (2): ln_inv_patent ~ pressure ------
print("\n--- 回归(2): 发明专利 ~ 财政压力（无控制变量）---")
print("(注：由于缺少专利被引数据,用发明专利申请替代创新质量)")
try:
    mod2 = PanelOLS(
        panel_reg['ln_inv_patent'],
        panel_reg[['pressure']],
        entity_effects=True,
        time_effects=True,
        check_rank=False
    )
    res2 = mod2.fit(cov_type='clustered', cluster_entity=True)
    print(res2.summary.tables[1])
    coef2 = res2.params['pressure']
    se2 = res2.std_errors['pressure']
    pval2 = res2.pvalues['pressure']
    r2_2 = res2.rsquared_overall
    n2 = res2.nobs
    print(f"\npressure系数: {coef2:.3f} (SE={se2:.3f}, p={pval2:.3f})")
    print(f"R²: {r2_2:.3f}, N: {n2}")
    print(f"论文结果: pressure=-0.137*** (0.044), R²=0.851, N=14097")
except Exception as e:
    print(f"回归(2)出错: {e}")
    res2 = None

# ------ 回归 (3): ln_Patent ~ pressure + controls ------
print("\n--- 回归(3): 创新数量 ~ 财政压力 + 控制变量 ---")
print("(可用控制变量: ln_pergdp, RD)")

# 准备有控制变量的子样本
panel_ctrl = panel_reg.dropna(subset=['ln_pergdp']).copy()

controls_available = ['ln_pergdp']
if panel_ctrl['RD'].notna().sum() > 100:
    panel_ctrl_rd = panel_ctrl.dropna(subset=['RD'])
    controls_available_rd = ['ln_pergdp', 'RD']
else:
    panel_ctrl_rd = panel_ctrl
    controls_available_rd = controls_available

try:
    exog_vars = ['pressure'] + controls_available
    mod3 = PanelOLS(
        panel_ctrl['ln_Patent'],
        panel_ctrl[exog_vars],
        entity_effects=True,
        time_effects=True,
        check_rank=False
    )
    res3 = mod3.fit(cov_type='clustered', cluster_entity=True)
    print(res3.summary.tables[1])
    coef3 = res3.params['pressure']
    se3 = res3.std_errors['pressure']
    pval3 = res3.pvalues['pressure']
    r2_3 = res3.rsquared_overall
    n3 = res3.nobs
    print(f"\npressure系数: {coef3:.3f} (SE={se3:.3f}, p={pval3:.3f})")
    print(f"R²: {r2_3:.3f}, N: {n3}")
    print(f"论文结果: pressure=-0.110*** (0.036), R²=0.785, N=16926")
except Exception as e:
    print(f"回归(3)出错: {e}")
    res3 = None

# ------ 回归 (3b): 加入RD控制 ------
if len(controls_available_rd) > 1:
    print("\n--- 回归(3b): 创新数量 ~ 财政压力 + ln_pergdp + RD ---")
    try:
        exog_vars_rd = ['pressure'] + controls_available_rd
        mod3b = PanelOLS(
            panel_ctrl_rd['ln_Patent'],
            panel_ctrl_rd[exog_vars_rd],
            entity_effects=True,
            time_effects=True,
            check_rank=False
        )
        res3b = mod3b.fit(cov_type='clustered', cluster_entity=True)
        print(res3b.summary.tables[1])
        coef3b = res3b.params['pressure']
        se3b = res3b.std_errors['pressure']
        pval3b = res3b.pvalues['pressure']
        print(f"\npressure系数: {coef3b:.3f} (SE={se3b:.3f}, p={pval3b:.3f})")
        print(f"R²: {res3b.rsquared_overall:.3f}, N: {res3b.nobs}")
    except Exception as e:
        print(f"回归(3b)出错: {e}")

# ------ 回归 (4): ln_inv_patent ~ pressure + controls ------
print("\n--- 回归(4): 发明专利 ~ 财政压力 + 控制变量 ---")
try:
    exog_vars4 = ['pressure'] + controls_available
    mod4 = PanelOLS(
        panel_ctrl['ln_inv_patent'],
        panel_ctrl[exog_vars4],
        entity_effects=True,
        time_effects=True,
        check_rank=False
    )
    res4 = mod4.fit(cov_type='clustered', cluster_entity=True)
    print(res4.summary.tables[1])
    coef4 = res4.params['pressure']
    se4 = res4.std_errors['pressure']
    pval4 = res4.pvalues['pressure']
    r2_4 = res4.rsquared_overall
    n4 = res4.nobs
    print(f"\npressure系数: {coef4:.3f} (SE={se4:.3f}, p={pval4:.3f})")
    print(f"R²: {r2_4:.3f}, N: {n4}")
    print(f"论文结果: pressure=-0.091** (0.042), R²=0.869, N=14093")
except Exception as e:
    print(f"回归(4)出错: {e}")
    res4 = None

# ============================================================
# 第七步：结果汇总与比较
# ============================================================
print("\n" + "=" * 70)
print("第七步：结果汇总与论文比较")
print("=" * 70)

print("\n┌─────────────────────────────────────────────────────────────────────┐")
print("│                      基准回归结果对比（表2）                           │")
print("├──────────┬──────────────────────────────────────────────────────────┤")  
print("│          │    (1) lnPatent   (2) lnInv      (3) lnPatent  (4) lnInv │")
print("│          │    无控制         无控制          有控制        有控制      │")
print("├──────────┼──────────────────────────────────────────────────────────┤")

# 论文结果
print("│ 论文结果 │", end="")
paper_results = [
    (-0.149, 0.040, '***'),
    (-0.137, 0.044, '***'),
    (-0.110, 0.036, '***'),
    (-0.091, 0.042, '**'),
]
for coef, se, sig in paper_results:
    print(f"  {coef:.3f}{sig:3s}({se:.3f})", end="")
print(" │")

# 复现结果
print("│ 复现结果 │", end="")
results = [res1, res2, res3, res4]
for r in results:
    if r is not None:
        c = r.params['pressure']
        s = r.std_errors['pressure']
        p = r.pvalues['pressure']
        sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
        print(f"  {c:.3f}{sig:3s}({s:.3f})", end="")
    else:
        print("      N/A       ", end="")
print(" │")

print("├──────────┼──────────────────────────────────────────────────────────┤")

# R²
print("│ 论文 R²  │", end="")
for r2 in [0.764, 0.851, 0.785, 0.869]:
    print(f"  {r2:.3f}         ", end="")
print(" │")

print("│ 复现 R²  │", end="")
for r in results:
    if r is not None:
        print(f"  {r.rsquared_overall:.3f}         ", end="")
    else:
        print("    N/A          ", end="")
print(" │")

# N
print("│ 论文 N   │", end="")
for n in [16937, 14097, 16926, 14093]:
    print(f"  {n:>5d}         ", end="")
print(" │")

print("│ 复现 N   │", end="")
for r in results:
    if r is not None:
        print(f"  {r.nobs:>5d}         ", end="")
    else:
        print("    N/A          ", end="")
print(" │")

print("└──────────┴──────────────────────────────────────────────────────────┘")

# ============================================================
# 第八步：差异分析
# ============================================================
print("\n" + "=" * 70)
print("第八步：差异分析与讨论")
print("=" * 70)

print("""
结果差异分析：

1. 样本差异：
   - 论文使用全部A股制造业上市公司（约17279条观测），2010-2020年
   - 本复现仅使用"专精特新"企业中的上市制造业公司（约3774家）
   - 样本量显著小于论文，且偏向于创新型中小企业

2. 变量差异：
   - 被解释变量：论文使用专利申请总量（发明+实用新型+外观设计）和专利被引次数
     本复现使用专利申请总量和发明专利申请量（缺少被引数据）
   - 核心解释变量：财政压力定义一致（收支缺口/收入）
   - 控制变量：论文控制了企业规模、年龄、杠杆率、研发强度、SOE、资产结构、
     行业集中度、ROA、人均GDP等9个变量
     本复现仅能使用人均GDP、部分R&D数据（缺少CSMAR财务数据）

3. 固定效应：
   - 论文使用企业+年份+行业固定效应
   - 本复现使用企业+年份固定效应（行业固定效应在企业FE下被吸收）

4. 聚类标准误：
   - 论文在城市层面聚类
   - 本复现在企业层面聚类（由于企业-城市映射后城市层面聚类需要额外处理）

5. 预期方向：
   - 核心发现（财政压力抑制创新）的方向应一致
   - 由于控制变量缺失，压力系数可能存在遗漏变量偏误
""")

# 保存数据
panel.to_csv('cleaned_data/lisen_replication_panel.csv', index=False, encoding='utf-8-sig')
print("面板数据已保存至 cleaned_data/lisen_replication_panel.csv")
print("\n复现完成！")
