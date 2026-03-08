"""
创建完整的实证回归数据面板
根据大致思路.md的研究设计
时间范围：2014-2024年
"""

import pandas as pd
import numpy as np
import warnings
import os
import glob
from datetime import datetime
warnings.filterwarnings('ignore')

# 创建输出目录
os.makedirs('cleaned_data', exist_ok=True)

# 数据报告列表
data_report = {
    '数据源': [],
    '状态': [],
    '记录数': [],
    '时间范围': [],
    '说明': []
}

def add_report(name, status, count, time_range, note):
    """添加数据报告"""
    data_report['数据源'].append(name)
    data_report['状态'].append(status)
    data_report['记录数'].append(count)
    data_report['时间范围'].append(time_range)
    data_report['说明'].append(note)

def parse_city_name(col_name):
    """从列名中解析城市名"""
    # 格式：'国内生产总值:河北:石家庄' -> ('河北', '石家庄')
    parts = col_name.split(':')
    if len(parts) >= 3:
        return parts[-2], parts[-1]
    elif len(parts) == 2:
        return None, parts[-1]
    return None, None

def wide_to_long(df, value_name):
    """将宽格式数据转换为长格式"""
    # 第一列通常是时间
    df = df.copy()
    time_col = df.columns[0]
    
    # 重命名第一列
    df = df.rename(columns={time_col: '时间'})
    
    # 转换为长格式
    df_long = df.melt(id_vars=['时间'], var_name='城市列', value_name=value_name)
    
    # 解析省份和城市
    city_info = df_long['城市列'].apply(parse_city_name)
    df_long['省份'] = [x[0] for x in city_info]
    df_long['城市'] = [x[1] for x in city_info]
    
    # 删除无法解析的行
    df_long = df_long.dropna(subset=['城市'])
    
    # 处理时间列
    df_long['时间'] = pd.to_datetime(df_long['时间'], errors='coerce')
    df_long['年份'] = df_long['时间'].dt.year
    
    # 筛选2014-2024年
    df_long = df_long[(df_long['年份'] >= 2014) & (df_long['年份'] <= 2024)]
    
    # 转换数值
    df_long[value_name] = pd.to_numeric(df_long[value_name], errors='coerce')
    
    # 选择需要的列
    df_long = df_long[['省份', '城市', '年份', value_name]].copy()
    
    return df_long

print("=" * 80)
print("政府引导基金与地区创新—实证回归数据面板构建")
print("=" * 80)
print()

# ============================================================================
# 1. 被解释变量：专利数据
# ============================================================================
print("1. 读取专利数据（发明专利申请数，2014-2024）")
print("-" * 80)

try:
    patent_apply = pd.read_csv('CNRDS专利数据包/各省市创新专利情况/各省市专利申请情况/各省市专利申请情况.csv', 
                              skiprows=1,
                              names=['省份', '城市', '年份', '发明申请数', '实用新型申请数', '外观设计申请数'])
    
    # 数据清洗
    patent_apply['年份'] = pd.to_numeric(patent_apply['年份'], errors='coerce')
    patent_apply['发明申请数'] = pd.to_numeric(patent_apply['发明申请数'], errors='coerce').fillna(0)
    patent_apply['实用新型申请数'] = pd.to_numeric(patent_apply['实用新型申请数'], errors='coerce').fillna(0)
    patent_apply['外观设计申请数'] = pd.to_numeric(patent_apply['外观设计申请数'], errors='coerce').fillna(0)
    
    # 筛选时间和删除缺失
    patent_apply = patent_apply.dropna(subset=['年份', '城市'])
    patent_apply = patent_apply[(patent_apply['年份'] >= 2014) & (patent_apply['年份'] <= 2024)]
    
    # 计算指标
    patent_apply['专利申请总数'] = patent_apply['发明申请数'] + patent_apply['实用新型申请数'] + patent_apply['外观设计申请数']
    patent_apply['ln_inv_patent'] = np.log(patent_apply['发明申请数'] + 1)
    patent_apply['ln_patent_apply'] = np.log(patent_apply['专利申请总数'] + 1)
    patent_apply['inv_share'] = patent_apply['发明申请数'] / patent_apply['专利申请总数'].replace(0, np.nan)
    
    patent_apply['年份'] = patent_apply['年份'].astype(int)
    
    print(f"✓ 成功读取：{len(patent_apply)} 条记录")
    print(f"  覆盖城市：{patent_apply['城市'].nunique()} 个")
    print(f"  时间范围：{patent_apply['年份'].min()}-{patent_apply['年份'].max()}")
    
    add_report('专利申请数据', '✓', len(patent_apply), 
               f"{patent_apply['年份'].min()}-{patent_apply['年份'].max()}", 
               f"覆盖{patent_apply['城市'].nunique()}个城市")
    
except Exception as e:
    print(f"✗ 读取失败：{e}")
    patent_apply = pd.DataFrame()
    add_report('专利申请数据', '✗', 0, '-', str(e))

print()

# 以专利数据为基础建立面板
panel = patent_apply[['省份', '城市', '年份', '发明申请数', '专利申请总数', 
                      'ln_inv_patent', 'ln_patent_apply', 'inv_share']].copy()

print(f"基础面板建立：{len(panel)} 条记录，{panel['年份'].min()}-{panel['年份'].max()}")
print()

# ============================================================================
# 2. 核心解释变量：财政数据
# ============================================================================
print("2. 读取财政数据")
print("-" * 80)

# 2.1 财政收入
try:
    fiscal_rev = pd.read_csv('地级市财政收入.csv', encoding='utf-8-sig')
    fiscal_rev = wide_to_long(fiscal_rev, '财政收入')
    fiscal_rev = fiscal_rev[fiscal_rev['年份'] >= 2014]
    
    panel = pd.merge(panel, fiscal_rev, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 财政收入：{len(fiscal_rev)} 条记录")
    add_report('财政收入', '✓', len(fiscal_rev), 
               f"{fiscal_rev['年份'].min()}-{fiscal_rev['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 财政收入：{e}")
    add_report('财政收入', '✗', 0, '-', str(e))

# 2.2 财政支出
try:
    fiscal_exp = pd.read_csv('地级市财政支出.csv', encoding='utf-8-sig')
    fiscal_exp = wide_to_long(fiscal_exp, '财政支出')
    fiscal_exp = fiscal_exp[fiscal_exp['年份'] >= 2014]
    
    panel = pd.merge(panel, fiscal_exp, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 财政支出：{len(fiscal_exp)} 条记录")
    add_report('财政支出', '✓', len(fiscal_exp), 
               f"{fiscal_exp['年份'].min()}-{fiscal_exp['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 财政支出：{e}")
    add_report('财政支出', '✗', 0, '-', str(e))

# 2.3 政府债务
try:
    debt = pd.read_csv('地方政府债务：地级市：余额.csv', encoding='utf-8-sig')
    debt = wide_to_long(debt, '政府债务余额')
    debt = debt[debt['年份'] >= 2014]
    
    panel = pd.merge(panel, debt, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 政府债务：{len(debt)} 条记录")
    add_report('政府债务', '✓', len(debt), 
               f"{debt['年份'].min()}-{debt['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 政府债务：{e}")
    add_report('政府债务', '✗', 0, '-', str(e))

# 2.4 科技支出
try:
    tech_exp = pd.read_csv('财政支出：科学：地级市.csv', encoding='utf-8-sig')
    tech_exp = wide_to_long(tech_exp, '科技支出')
    tech_exp = tech_exp[tech_exp['年份'] >= 2014]
    
    panel = pd.merge(panel, tech_exp, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 科技支出：{len(tech_exp)} 条记录")
    add_report('科技支出', '✓', len(tech_exp), 
               f"{tech_exp['年份'].min()}-{tech_exp['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 科技支出：{e}")
    add_report('科技支出', '✗', 0, '-', str(e))

print()

# ============================================================================
# 3. 控制变量：经济数据
# ============================================================================
print("3. 读取经济数据")
print("-" * 80)

# 3.1 GDP
try:
    gdp = pd.read_csv('地级市总GDP.csv', encoding='utf-8-sig')
    gdp = wide_to_long(gdp, 'GDP')
    gdp = gdp[gdp['年份'] >= 2014]
    
    panel = pd.merge(panel, gdp, on=['省份', '城市', '年份'], how='left')
    print(f"✓ GDP：{len(gdp)} 条记录")
    add_report('GDP', '✓', len(gdp), 
               f"{gdp['年份'].min()}-{gdp['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ GDP：{e}")
    add_report('GDP', '✗', 0, '-', str(e))

# 3.2 人均GDP
try:
    gdp_pc = pd.read_csv('地级市人均GDP.csv', encoding='utf-8-sig')
    gdp_pc = wide_to_long(gdp_pc, '人均GDP')
    gdp_pc = gdp_pc[gdp_pc['年份'] >= 2014]
    
    panel = pd.merge(panel, gdp_pc, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 人均GDP：{len(gdp_pc)} 条记录")
    add_report('人均GDP', '✓', len(gdp_pc), 
               f"{gdp_pc['年份'].min()}-{gdp_pc['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 人均GDP：{e}")
    add_report('人均GDP', '✗', 0, '-', str(e))

# 3.3 第二产业
try:
    industry = pd.read_csv('地级市第二产业.csv', encoding='utf-8-sig')
    industry = wide_to_long(industry, '第二产业增加值')
    industry = industry[industry['年份'] >= 2014]
    
    panel = pd.merge(panel, industry, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 第二产业：{len(industry)} 条记录")
    add_report('第二产业', '✓', len(industry), 
               f"{industry['年份'].min()}-{industry['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 第二产业：{e}")
    add_report('第二产业', '✗', 0, '-', str(e))

# 3.4 常住人口
try:
    pop = pd.read_csv('常住人口.csv', encoding='gb18030')
    pop = wide_to_long(pop, '常住人口')
    pop = pop[pop['年份'] >= 2014]
    
    panel = pd.merge(panel, pop, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 常住人口：{len(pop)} 条记录")
    add_report('常住人口', '✓', len(pop), 
               f"{pop['年份'].min()}-{pop['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 常住人口：{e}")
    add_report('常住人口', '✗', 0, '-', str(e))

# 3.5 外资
try:
    fdi = pd.read_csv('实际利用外资.csv', encoding='gb18030')
    fdi = wide_to_long(fdi, '实际利用外资')
    fdi = fdi[fdi['年份'] >= 2014]
    
    panel = pd.merge(panel, fdi, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 实际利用外资：{len(fdi)} 条记录")
    add_report('实际利用外资', '✓', len(fdi), 
               f"{fdi['年份'].min()}-{fdi['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 实际利用外资：{e}")
    add_report('实际利用外资', '✗', 0, '-', str(e))

# 3.6 金融机构贷款余额
try:
    finance = pd.read_csv('金融机构贷款余额.csv', encoding='gb18030')
    finance = wide_to_long(finance, '金融机构贷款余额')
    finance = finance[finance['年份'] >= 2014]
    
    panel = pd.merge(panel, finance, on=['省份', '城市', '年份'], how='left')
    print(f"✓ 金融机构贷款：{len(finance)} 条记录")
    add_report('金融机构贷款', '✓', len(finance), 
               f"{finance['年份'].min()}-{finance['年份'].max()}", '宽格式转换')
except Exception as e:
    print(f"✗ 金融机构贷款：{e}")
    add_report('金融机构贷款', '✗', 0, '-', str(e))

print()

# ============================================================================
# 4. 机制变量：引导基金投资数据
# ============================================================================
print("4. 读取引导基金投资数据")
print("-" * 80)

try:
    # 读取所有引导基金文件
    gf_files = glob.glob('清科政府引导基金投资事件截止到2024年/政府引导基金投资*.csv')
    gf_list = []
    
    for file in gf_files:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig', low_memory=False)
            gf_list.append(df)
        except:
            try:
                df = pd.read_csv(file, encoding='gbk', low_memory=False)
                gf_list.append(df)
            except Exception as e:
                print(f"  ! {file} 读取失败")
    
    if gf_list:
        gf = pd.concat(gf_list, ignore_index=True)
        
        # 检查列名
        print(f"  引导基金数据列名：{gf.columns.tolist()[:10]}")
        
        # 保存原始数据供后续分析
        gf.to_csv('cleaned_data/government_fund_raw.csv', index=False, encoding='utf-8-sig')
        
        print(f"✓ 引导基金投资：{len(gf)} 条记录")
        print(f"  （需要进一步处理：匹配城市、计算早期投资占比）")
        add_report('引导基金投资', '✓', len(gf), '-', '需进一步处理匹配城市')
    else:
        print("✗ 未能读取引导基金数据")
        add_report('引导基金投资', '✗', 0, '-', '文件读取失败')
        
except Exception as e:
    print(f"✗ 引导基金投资：{e}")
    add_report('引导基金投资', '✗', 0, '-', str(e))

print()

# ============================================================================
# 5. 调节变量：市场化指数
# ============================================================================
print("5. 读取市场化指数")
print("-" * 80)

try:
    market_idx = pd.read_csv('1997-2024年市场化指数和各分项指数 的副本.csv', encoding='gbk')
    
    print(f"  市场化指数列名：{market_idx.columns.tolist()[:10]}")
    market_idx.to_csv('cleaned_data/market_index_raw.csv', index=False, encoding='utf-8-sig')
    
    print(f"✓ 市场化指数：{len(market_idx)} 条记录")
    print(f"  （需要进一步处理：省级数据匹配到城市）")
    add_report('市场化指数', '✓', len(market_idx), '-', '省级数据，需匹配到城市')
    
except Exception as e:
    print(f"✗ 市场化指数：{e}")
    add_report('市场化指数', '✗', 0, '-', str(e))

print()

# ============================================================================
# 6. 计算派生变量
# ============================================================================
print("6. 计算派生变量")
print("-" * 80)

# 财政缺口率
if '财政收入' in panel.columns and '财政支出' in panel.columns and 'GDP' in panel.columns:
    panel['fiscal_gap'] = (panel['财政支出'] - panel['财政收入']) / panel['GDP']
    print("✓ fiscal_gap（财政缺口率）")
else:
    print("✗ fiscal_gap：缺少必要数据")

# 债务率
if '政府债务余额' in panel.columns and '财政收入' in panel.columns:
    panel['debt_ratio'] = panel['政府债务余额'] / panel['财政收入']
    print("✓ debt_ratio（债务率）")
else:
    print("✗ debt_ratio：缺少必要数据")

# 科技支出占比
if '科技支出' in panel.columns and '财政支出' in panel.columns:
    panel['tech_expend'] = panel['科技支出'] / panel['财政支出']
    print("✓ tech_expend（科技支出占比）")
else:
    print("✗ tech_expend：缺少必要数据")

# 产业结构
if '第二产业增加值' in panel.columns and 'GDP' in panel.columns:
    panel['industry_structure'] = panel['第二产业增加值'] / panel['GDP']
    print("✓ industry_structure（第二产业占比）")
else:
    print("✗ industry_structure：缺少必要数据")

# 外资依存度
if '实际利用外资' in panel.columns and 'GDP' in panel.columns:
    panel['fdi_ratio'] = panel['实际利用外资'] / panel['GDP']
    print("✓ fdi_ratio（外资依存度）")
else:
    print("✗ fdi_ratio：缺少必要数据")

# 金融深度
if '金融机构贷款余额' in panel.columns and 'GDP' in panel.columns:
    panel['finance_depth'] = panel['金融机构贷款余额'] / panel['GDP']
    print("✓ finance_depth（金融深度）")
else:
    print("✗ finance_depth：缺少必要数据")

# 人均GDP对数
if '人均GDP' in panel.columns:
    panel['gdp_percap'] = np.log(panel['人均GDP'].replace(0, np.nan))
    print("✓ gdp_percap（人均GDP对数）")
else:
    print("✗ gdp_percap：缺少必要数据")

# 人均专利
if '专利申请总数' in panel.columns and '常住人口' in panel.columns:
    panel['patent_per_capita'] = panel['专利申请总数'] / panel['常住人口']
    print("✓ patent_per_capita（人均专利）")
else:
    print("✗ patent_per_capita：缺少必要数据")

print()

# ============================================================================
# 7. 保存最终面板
# ============================================================================
print("7. 保存最终面板")
print("-" * 80)

# 保存完整面板
panel.to_csv('cleaned_data/final_regression_panel.csv', index=False, encoding='utf-8-sig')
print(f"✓ 完整面板已保存：cleaned_data/final_regression_panel.csv")
print(f"  记录数：{len(panel)}")
print(f"  变量数：{len(panel.columns)}")

# 滞后一期的核心解释变量
panel = panel.sort_values(['城市', '年份'])
for var in ['fiscal_gap', 'debt_ratio']:
    if var in panel.columns:
        panel[f'{var}_l1'] = panel.groupby('城市')[var].shift(1)

panel.to_csv('cleaned_data/final_regression_panel_with_lags.csv', index=False, encoding='utf-8-sig')
print(f"✓ 含滞后项面板已保存：cleaned_data/final_regression_panel_with_lags.csv")

print()

# ============================================================================
# 8. 数据质量报告
# ============================================================================
print("=" * 80)
print("数据质量报告")
print("=" * 80)
print()

# 8.1 数据源汇总
report_df = pd.DataFrame(data_report)
print("8.1 数据源汇总")
print("-" * 80)
print(report_df.to_string(index=False))
print()

# 8.2 面板平衡性
print("8.2 面板平衡性")
print("-" * 80)
city_counts = panel.groupby('城市')['年份'].count()
print(f"完全平衡（11年数据）的城市：{(city_counts == 11).sum()}")
print(f"不完全平衡的城市：{(city_counts < 11).sum()}")
print()

# 8.3 主要变量描述统计
print("8.3 主要变量描述统计")
print("-" * 80)
key_vars = ['ln_inv_patent', 'fiscal_gap', 'debt_ratio', 'gdp_percap', 
            'industry_structure', 'tech_expend', 'finance_depth']
available_vars = [v for v in key_vars if v in panel.columns]
if available_vars:
    print(panel[available_vars].describe().round(4))
print()

# 8.4 缺失值报告
print("8.4 缺失值报告")
print("-" * 80)
missing = panel.isnull().sum()
missing_pct = 100 * missing / len(panel)
missing_df = pd.DataFrame({
    '变量': panel.columns,
    '缺失数': missing.values,
    '缺失率%': missing_pct.values
})
missing_df = missing_df[missing_df['缺失数'] > 0].sort_values('缺失数', ascending=False)
print(missing_df.to_string(index=False))
print()

# 8.5 各年份覆盖情况
print("8.5 各年份覆盖情况")
print("-" * 80)
year_summary = panel.groupby('年份').agg({
    '城市': 'count',
    'ln_inv_patent': lambda x: x.notna().sum(),
    'fiscal_gap': lambda x: x.notna().sum() if 'fiscal_gap' in panel.columns else 0,
    'gdp_percap': lambda x: x.notna().sum() if 'gdp_percap' in panel.columns else 0
})
year_summary.columns = ['总记录数', '专利数据', '财政缺口', '人均GDP']
print(year_summary)
print()

# 保存报告
report_df.to_csv('cleaned_data/data_quality_report.csv', index=False, encoding='utf-8-sig')
print("✓ 数据质量报告已保存：cleaned_data/data_quality_report.csv")
print()

print("=" * 80)
print("数据面板构建完成！")
print("=" * 80)
