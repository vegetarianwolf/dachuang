"""
优化的实证回归数据面板构建脚本
正确处理带元数据的宽格式数据
"""

import pandas as pd
import numpy as np
import warnings
import os
import glob
warnings.filterwarnings('ignore')

os.makedirs('cleaned_data', exist_ok=True)

def parse_wide_format_with_metadata(filepath, encoding='utf-8-sig', skiprows=5):
    """
    读取带元数据的宽格式数据
    跳过前几行元数据，从实际数据开始读取
    """
    try:
        df = pd.read_csv(filepath, encoding=encoding, skiprows=skiprows)
    except:
        try:
            df = pd.read_csv(filepath, encoding='gbk', skiprows=skiprows)
        except:
            df = pd.read_csv(filepath, encoding='gb18030', skiprows=skiprows)
    
    return df

def extract_city_from_column(col_name):
    """从列名中提取城市名"""
    # 列名格式：'财政收入:地方:一般公共预算收入:河北:石家庄'
    if ':' not in str(col_name):
        return None, None
    
    parts = str(col_name).split(':')
    if len(parts) >= 2:
        city = parts[-1]  # 最后一部分是城市名
        # 处理直辖市（只有一个部分）和地级市（有省份:城市）
        if len(parts) >= 3 and parts[-2] not in ['地方', '一般公共预算收入', '科学', '国内生产总值', '第二产业']:
            province = parts[-2]  # 倒数第二部分可能是省份
        else:
            province = city  # 直辖市
        
        return province, city
    return None, None

def wide_to_long_optimized(df, value_name):
    """优化的宽转长函数"""
    # 第一列是时间
    time_col = df.columns[0]
    df = df.rename(columns={time_col: '时间'})
    
    # 转为长格式
    df_long = df.melt(id_vars=['时间'], var_name='列名', value_name=value_name)
    
    # 解析城市
    city_info = [extract_city_from_column(col) for col in df_long['列名']]
    df_long['省份'] = [x[0] for x in city_info]
    df_long['城市'] = [x[1] for x in city_info]
    
    # 删除无法解析的
    df_long = df_long.dropna(subset=['城市'])
    
    # 处理时间
    df_long['时间'] = pd.to_datetime(df_long['时间'], errors='coerce')
    df_long['年份'] = df_long['时间'].dt.year
    
    # 筛选2014-2024
    df_long = df_long[(df_long['年份'] >= 2014) & (df_long['年份'] <= 2024)]
    
    # 转换数值
    df_long[value_name] = pd.to_numeric(df_long[value_name], errors='coerce')
    
    # 标准化城市名（加"市"后缀）
    df_long['城市'] = df_long['城市'].apply(lambda x: x if x.endswith('市') else x + '市')
    
    return df_long[['省份', '城市', '年份', value_name]]

print("="*80)
print("实证回归数据面板构建（优化版）")
print("="*80)
print()

# 1. 专利数据（基础面板）
print("1. 读取专利数据...")
patent = pd.read_csv('CNRDS专利数据包/各省市创新专利情况/各省市专利申请情况/各省市专利申请情况.csv',
                     skiprows=1, names=['省份', '城市', '年份', '发明申请数', '实用新型申请数', '外观设计申请数'])

patent['年份'] = pd.to_numeric(patent['年份'], errors='coerce')
patent = patent.dropna(subset=['年份', '城市'])
patent = patent[(patent['年份'] >= 2014) & (patent['年份'] <= 2024)]

for col in ['发明申请数', '实用新型申请数', '外观设计申请数']:
    patent[col] = pd.to_numeric(patent[col], errors='coerce').fillna(0)

patent['专利申请总数'] = patent['发明申请数'] + patent['实用新型申请数'] + patent['外观设计申请数']
patent['ln_inv_patent'] = np.log(patent['发明申请数'] + 1)
patent['ln_patent_apply'] = np.log(patent['专利申请总数'] + 1)
patent['inv_share'] = patent['发明申请数'] / patent['专利申请总数'].replace(0, np.nan)
patent['年份'] = patent['年份'].astype(int)

print(f"  [OK] {len(patent)} 条，{patent['城市'].nunique()} 个城市")

panel = patent[['省份', '城市', '年份', '发明申请数', '专利申请总数', 'ln_inv_patent', 'ln_patent_apply', 'inv_share']].copy()

# 2. 财政数据
print("\n2. 读取并合并财政数据...")

datasets = [
    ('地级市财政收入.csv', '财政收入'),
    ('地级市财政支出.csv', '财政支出'),
    ('地级市总GDP.csv', 'GDP'),
    ('地级市人均GDP.csv', '人均GDP'),
    ('地级市第二产业.csv', '第二产业增加值'),
    ('地方政府债务：地级市：余额.csv', '政府债务余额'),
    ('财政支出：科学：地级市.csv', '科技支出'),
]

for filename, varname in datasets:
    try:
        df = parse_wide_format_with_metadata(filename)
        df_long = wide_to_long_optimized(df, varname)
        
        before = len(panel)
        panel = pd.merge(panel, df_long, on=['省份', '城市', '年份'], how='left')
        matched = panel[varname].notna().sum()
        
        print(f"  [OK] {varname:12s}: {len(df_long):4d} 条 -> 匹配 {matched:4d} / {before:4d}")
    except Exception as e:
        print(f"  [FAIL] {varname:12s}: {str(e)[:50]}")

# 3. 其他经济数据（编码问题的文件）
print("\n3. 读取其他经济数据...")

for filename, varname, enc in [
    ('常住人口.csv', '常住人口', 'gb18030'),
    ('实际利用外资.csv', '实际利用外资', 'gb18030'),
    ('金融机构贷款余额.csv', '金融机构贷款余额', 'gb18030'),
]:
    try:
        df = pd.read_csv(filename, encoding=enc, skiprows=5)
        df_long = wide_to_long_optimized(df, varname)
        
        panel = pd.merge(panel, df_long, on=['省份', '城市', '年份'], how='left')
        matched = panel[varname].notna().sum()
        
        print(f"  [OK] {varname:12s}: 匹配 {matched} 条")
    except Exception as e:
        print(f"  [FAIL] {varname:12s}: {str(e)[:50]}")

# 4. 计算派生变量
print("\n4. 计算派生变量...")

# 财政缺口率
if '财政收入' in panel.columns and '财政支出' in panel.columns and 'GDP' in panel.columns:
    panel['fiscal_gap'] = (panel['财政支出'] - panel['财政收入']) / panel['GDP']
    print(f"  [OK] fiscal_gap（缺失{panel['fiscal_gap'].isna().sum()}条）")

# 债务率
if '政府债务余额' in panel.columns and '财政收入' in panel.columns:
    panel['debt_ratio'] = panel['政府债务余额'] / panel['财政收入']
    print(f"  [OK] debt_ratio")

# 科技支出占比
if '科技支出' in panel.columns and '财政支出' in panel.columns:
    panel['tech_expend_ratio'] = panel['科技支出'] / panel['财政支出']
    print(f"  [OK] tech_expend_ratio")

# 产业结构
if '第二产业增加值' in panel.columns and 'GDP' in panel.columns:
    panel['industry_structure'] = panel['第二产业增加值'] / panel['GDP']
    print(f"  [OK] industry_structure")

# 其他比率
if '实际利用外资' in panel.columns and 'GDP' in panel.columns:
    panel['fdi_ratio'] = panel['实际利用外资'] / panel['GDP']
    print(f"  [OK] fdi_ratio")

if '金融机构贷款余额' in panel.columns and 'GDP' in panel.columns:
    panel['finance_depth'] = panel['金融机构贷款余额'] / panel['GDP']
    print(f"  [OK] finance_depth")

if '人均GDP' in panel.columns:
    panel['gdp_percap'] = np.log(panel['人均GDP'].replace(0, np.nan))
    print(f"  [OK] gdp_percap（对数）")

if '专利申请总数' in panel.columns and '常住人口' in panel.columns:
    panel['patent_per_capita'] = panel['专利申请总数'] / panel['常住人口'] * 10000  # 每万人
    print(f"  [OK] patent_per_capita")

# 5. 滞后变量
print("\n5. 生成滞后变量...")
panel = panel.sort_values(['城市', '年份'])

for var in ['fiscal_gap', 'debt_ratio']:
    if var in panel.columns:
        panel[f'{var}_l1'] = panel.groupby('城市')[var].shift(1)
        print(f"  [OK] {var}_l1")

# 6. 保存
print("\n6. 保存数据...")
panel.to_csv('cleaned_data/final_regression_panel.csv', index=False, encoding='utf-8-sig')
print(f"  [OK] 保存到 cleaned_data/final_regression_panel.csv")
print(f"  面板大小：{len(panel)} 行 x {len(panel.columns)} 列")

# 7. 数据质量报告
print("\n" + "="*80)
print("数据质量报告")
print("="*80)

print(f"\n总体情况：")
print(f"  观测值数：{len(panel)}")
print(f"  城市数：{panel['城市'].nunique()}")
print(f"  年份范围：{panel['年份'].min()}-{panel['年份'].max()}")

print(f"\n主要变量覆盖率：")
key_vars = ['ln_inv_patent', 'fiscal_gap', 'gdp_percap', 'industry_structure', 'tech_expend_ratio']
for var in key_vars:
    if var in panel.columns:
        coverage = 100 * panel[var].notna().sum() / len(panel)
        print(f"  {var:20s}: {coverage:5.1f}%")

print(f"\n按年份统计：")
year_stats = panel.groupby('年份').agg({
    '城市': 'count',
    'ln_inv_patent': lambda x: x.notna().sum(),
    'fiscal_gap': lambda x: x.notna().sum() if 'fiscal_gap' in panel.columns else 0
})
year_stats.columns = ['记录数', '专利数', '财政缺口']  
print(year_stats)

print("\n" + "="*80)
print("完成！")
print("="*80)
