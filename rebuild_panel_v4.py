"""
重建 final_regression_panel_v4.csv
===================================
将专利申请量全部改为专利受理量，并重建面板数据。

步骤：
1. 读取 final_regression_panel_v3_cityfiltered.csv（已有所有控制变量）
2. 将所有"申请"相关的专利列名改为"受理"
3. 读取清科政府引导基金投资事件数据，构建早期投资变量（含滞后一期）
4. 合并输出 final_regression_panel_v4.csv
"""

import pandas as pd
import numpy as np
import os
import re
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_DIR = os.path.join(BASE_DIR, 'cleaned_data')

print("=" * 80)
print("重建 final_regression_panel_v4.csv（专利申请→受理）")
print("=" * 80)

# ============================================================
# 1. 读取 v3 面板并重命名专利列
# ============================================================
print("\n1. 读取 v3 面板数据...")
v3_path = os.path.join(CLEANED_DIR, 'final_regression_panel_v3_cityfiltered.csv')
panel = pd.read_csv(v3_path, encoding='utf-8-sig')
print(f"   原始面板: {panel.shape[0]} 行, {panel.shape[1]} 列")
print(f"   年份范围: {panel['年份'].min()}-{panel['年份'].max()}")
print(f"   城市数: {panel['城市'].nunique()}")
print(f"   原始列名: {list(panel.columns)}")

# 定义重命名映射：申请 → 受理
rename_map = {
    '发明申请数':          '发明受理数',
    '专利申请总数':        '专利受理总数',
    '发明专利申请量_对数': '发明专利受理量_对数',
    '专利申请总量_对数':   '专利受理总量_对数',
    '人均专利申请量':      '人均专利受理量',
}

# 只对实际存在的列进行重命名
actual_rename = {k: v for k, v in rename_map.items() if k in panel.columns}
panel = panel.rename(columns=actual_rename)
print(f"\n   已重命名 {len(actual_rename)} 列：")
for old, new in actual_rename.items():
    print(f"     {old} → {new}")
print(f"   新列名: {list(panel.columns)}")

# ============================================================
# 2. 获取城市列表（用于匹配投资方）
# ============================================================
city_list = sorted(panel['城市'].unique().tolist())
print(f"\n2. 面板中的城市数量: {len(city_list)}")

# 构建城市名匹配器
city_match_list = []
for city in city_list:
    if city.endswith('市'):
        short_name = city[:-1]
    elif city.endswith('自治州'):
        short_name = city
    elif city.endswith('盟'):
        short_name = city[:-1]
    elif city.endswith('地区'):
        short_name = city[:-2]
    else:
        short_name = city
    city_match_list.append((short_name, city))

# 按名称长度降序排列，优先匹配长名称
city_match_list.sort(key=lambda x: len(x[0]), reverse=True)

# 直辖市和国家级关键词（用于剔除）
MUNICIPALITIES = {'北京', '天津', '上海', '重庆'}
NATIONAL_KEYWORDS = ['国家', '中央', '国有']


def extract_city_from_investor(investor_name):
    """从投资方全称中提取地级市名称"""
    if pd.isna(investor_name) or not isinstance(investor_name, str):
        return None
    investor_name = investor_name.strip()
    for muni in MUNICIPALITIES:
        if muni in investor_name:
            return f"__MUNICIPALITY_{muni}__"
    for short_name, std_name in city_match_list:
        if short_name in investor_name:
            return std_name
    for kw in NATIONAL_KEYWORDS:
        if kw in investor_name:
            return f"__NATIONAL_{kw}__"
    return None


# ============================================================
# 3. 读取清科政府引导基金投资事件数据
# ============================================================
print("\n3. 读取清科政府引导基金投资事件数据...")
invest_dir = os.path.join(BASE_DIR, '清科政府引导基金投资事件截止到2024年')
all_files = [os.path.join(invest_dir, f)
             for f in os.listdir(invest_dir) if f.endswith('.csv')]

dfs = []
for fpath in sorted(all_files):
    fname = os.path.basename(fpath)
    try:
        df = pd.read_csv(fpath, encoding='utf-8-sig', low_memory=False)
        df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
        print(f"   {fname}: {len(df)} 行")
        dfs.append(df)
    except Exception as e:
        print(f"   {fname}: 读取失败 - {e}")

raw_invest = pd.concat(dfs, ignore_index=True)
raw_invest = raw_invest[raw_invest['投资阶段'] != '投资阶段'].copy()
raw_invest = raw_invest[raw_invest['投资阶段'] != '地区'].copy()
print(f"   合并清洗后: {len(raw_invest)} 行")

# ============================================================
# 4. 提取年份
# ============================================================
def parse_year(date_str):
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    m = re.match(r'(\d{4})', date_str.strip())
    return int(m.group(1)) if m else None

raw_invest['年份'] = raw_invest['投资时间'].apply(parse_year)
raw_invest = raw_invest[raw_invest['年份'].between(2014, 2024)].copy()
print(f"   2014-2024年数据: {len(raw_invest)} 行")

# ============================================================
# 5. 匹配城市
# ============================================================
print("\n4. 从投资方全称匹配地级市...")
raw_invest['匹配城市'] = raw_invest['投资方全称'].apply(extract_city_from_investor)

matched_city = raw_invest['匹配城市'].notna() & ~raw_invest['匹配城市'].str.startswith('__', na=True)
invest_city = raw_invest[matched_city].copy()
print(f"   匹配到地级市: {matched_city.sum()}/{len(raw_invest)}")

# ============================================================
# 6. 解析投资金额、标记早期
# ============================================================
def parse_amount(amt):
    if pd.isna(amt):
        return np.nan
    amt = str(amt).strip().replace('(e)', '').strip()
    if amt in ('--', '', '-'):
        return np.nan
    try:
        return float(amt)
    except ValueError:
        return np.nan

invest_city['投资金额_百万'] = invest_city['投资金额(RMB/M)'].apply(parse_amount)
invest_city['是否早期'] = invest_city['投资阶段'].isin(['种子期', '初创期']).astype(int)

print(f"   早期投资(种子期+初创期): {invest_city['是否早期'].sum()} 条")

# ============================================================
# 7. 按城市-年份汇总
# ============================================================
print("\n5. 按城市-年份汇总...")

total_stats = invest_city.groupby(['匹配城市', '年份']).agg(
    基金投资总次数=('投资阶段', 'count'),
    基金投资总金额_百万=('投资金额_百万', 'sum')
).reset_index()

early_data = invest_city[invest_city['是否早期'] == 1]
early_stats = early_data.groupby(['匹配城市', '年份']).agg(
    早期投资次数=('投资阶段', 'count'),
    早期投资金额_百万=('投资金额_百万', 'sum')
).reset_index()

city_year_stats = total_stats.merge(early_stats, on=['匹配城市', '年份'], how='left')
city_year_stats['早期投资次数'] = city_year_stats['早期投资次数'].fillna(0).astype(int)
city_year_stats['早期投资金额_百万'] = city_year_stats['早期投资金额_百万'].fillna(0)

city_year_stats['早期投资次数占比'] = city_year_stats['早期投资次数'] / city_year_stats['基金投资总次数']
city_year_stats['早期投资金额占比'] = np.where(
    city_year_stats['基金投资总金额_百万'] > 0,
    city_year_stats['早期投资金额_百万'] / city_year_stats['基金投资总金额_百万'],
    np.nan
)
city_year_stats = city_year_stats.rename(columns={'匹配城市': '城市'})
print(f"   城市-年份汇总: {len(city_year_stats)} 条, {city_year_stats['城市'].nunique()} 个城市")

# 保存中间文件
mid_output = os.path.join(CLEANED_DIR, 'city_year_fund_investment_stats.csv')
city_year_stats.to_csv(mid_output, index=False, encoding='utf-8-sig')

# ============================================================
# 8. 滞后一期
# ============================================================
print("\n6. 构建滞后一期变量...")
city_year_stats['年份_滞后'] = city_year_stats['年份'] + 1

lag_vars = city_year_stats[['城市', '年份_滞后',
                             '基金投资总次数', '基金投资总金额_百万',
                             '早期投资次数', '早期投资金额_百万',
                             '早期投资次数占比', '早期投资金额占比']].copy()
lag_vars = lag_vars.rename(columns={'年份_滞后': '年份'})

lag_rename = {
    '基金投资总次数': '基金投资总次数_滞后一期',
    '基金投资总金额_百万': '基金投资总金额_百万_滞后一期',
    '早期投资次数': '早期投资次数_滞后一期',
    '早期投资金额_百万': '早期投资金额_百万_滞后一期',
    '早期投资次数占比': '早期投资次数占比_滞后一期',
    '早期投资金额占比': '早期投资金额占比_滞后一期',
}
lag_vars = lag_vars.rename(columns=lag_rename)
lag_vars = lag_vars[lag_vars['年份'].between(2015, 2024)].copy()
print(f"   滞后变量: {len(lag_vars)} 条, 年份 {lag_vars['年份'].min()}-{lag_vars['年份'].max()}")

# ============================================================
# 9. 合并到面板
# ============================================================
print("\n7. 合并到面板...")
panel_filtered = panel[panel['年份'].between(2015, 2024)].copy()
print(f"   面板(2015-2024): {len(panel_filtered)} 行, {panel_filtered['城市'].nunique()} 城市")

merged = panel_filtered.merge(lag_vars, on=['城市', '年份'], how='left')

# 填充缺失值
for col in ['基金投资总次数_滞后一期', '早期投资次数_滞后一期']:
    merged[col] = merged[col].fillna(0).astype(int)
for col in ['基金投资总金额_百万_滞后一期', '早期投资金额_百万_滞后一期']:
    merged[col] = merged[col].fillna(0)

merged['早期投资次数占比_滞后一期'] = np.where(
    merged['基金投资总次数_滞后一期'] > 0,
    merged['早期投资次数_滞后一期'] / merged['基金投资总次数_滞后一期'],
    0
)
merged['早期投资金额占比_滞后一期'] = np.where(
    merged['基金投资总金额_百万_滞后一期'] > 0,
    merged['早期投资金额_百万_滞后一期'] / merged['基金投资总金额_百万_滞后一期'],
    np.nan
)

print(f"   合并后面板: {len(merged)} 行, {merged.shape[1]} 列")

# ============================================================
# 10. 输出
# ============================================================
output_path = os.path.join(CLEANED_DIR, 'final_regression_panel_v4.csv')
merged.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"\n{'='*80}")
print(f"输出文件: {output_path}")
print(f"面板维度: {merged.shape[0]} 行 x {merged.shape[1]} 列")
print(f"列名: {list(merged.columns)}")

# ============================================================
# 11. 概要统计
# ============================================================
print(f"\n{'='*80}")
print("新面板概要统计")
print("=" * 80)

# 专利受理相关变量
patent_cols = [c for c in merged.columns if '受理' in c]
print(f"\n专利受理相关列:\n{merged[patent_cols].describe().to_string()}")

# 投资变量
inv_cols = [c for c in merged.columns if '滞后一期' in c]
print(f"\n投资变量(滞后一期):\n{merged[inv_cols].describe().to_string()}")

has_invest = (merged['基金投资总次数_滞后一期'] > 0).sum()
has_early = (merged['早期投资次数_滞后一期'] > 0).sum()
print(f"\n有基金投资活动的城市-年份: {has_invest}/{len(merged)} ({has_invest/len(merged)*100:.1f}%)")
print(f"有早期投资活动的城市-年份: {has_early}/{len(merged)} ({has_early/len(merged)*100:.1f}%)")

print(f"\n完成! 所有'专利申请'相关列已改为'专利受理'。")
