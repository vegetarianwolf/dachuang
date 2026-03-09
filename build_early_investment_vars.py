"""
构建政府引导基金早期投资变量并合并到面板数据
============================================
逻辑：
1. 读取清科政府引导基金投资事件数据（所有年份）
2. 从"投资方全称"中匹配地级市名称
3. 将"种子期"和"初创期"标记为早期投资
4. 剔除四个直辖市及不含地级市名的"国家""中央""国有"投资方
5. 按城市-年份汇总：总投资次数、总投资金额、早期投资次数、早期投资金额
6. 计算早期投资次数占比和金额占比
7. 滞后一期后合并到 final_regression_panel_v3_cityfiltered.csv
8. 输出 final_regression_panel_v4.csv
"""

import pandas as pd
import numpy as np
import os
import re
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_DIR = os.path.join(BASE_DIR, 'cleaned_data')

# ============================================================
# 1. 从面板数据获取地级市列表（已去掉直辖市）
# ============================================================
panel_path = os.path.join(CLEANED_DIR, 'final_regression_panel_v3_cityfiltered.csv')
panel = pd.read_csv(panel_path, encoding='utf-8-sig')
print(f"面板数据: {panel.shape[0]} 行, {panel.shape[1]} 列")
print(f"年份范围: {panel['年份'].min()}-{panel['年份'].max()}")
print(f"城市数: {panel['城市'].nunique()}")

# 获取所有地级市名称（带"市"后缀的标准格式）
city_list = sorted(panel['城市'].unique().tolist())
print(f"\n面板中的城市数量: {len(city_list)}")
print(f"示例城市: {city_list[:10]}")

# ============================================================
# 2. 构建城市名匹配器
# ============================================================
# 为了从"投资方全称"中匹配地级市，需要用城市名（去"市"后缀）搜索
# 但要注意：有些城市名很短（如"鹤市"=>"鹤"），可能导致误匹配
# 策略：优先匹配长名称，且要求完整匹配

# 构建匹配列表：(不带后缀的名称, 标准全名, 名称长度)
city_match_list = []
for city in city_list:
    # 去掉"市"后缀用于匹配
    if city.endswith('市'):
        short_name = city[:-1]
    elif city.endswith('自治州'):
        short_name = city  # 自治州保留全名匹配
    elif city.endswith('盟'):
        short_name = city[:-1]
    elif city.endswith('地区'):
        short_name = city[:-2]
    else:
        short_name = city
    city_match_list.append((short_name, city))

# 按名称长度降序排列，优先匹配长名称（避免"长春"匹配到"长"等短名问题）
city_match_list.sort(key=lambda x: len(x[0]), reverse=True)

print(f"\n构建了 {len(city_match_list)} 个城市匹配项")
print(f"最长匹配名: {city_match_list[0]}")
print(f"最短匹配名: {city_match_list[-1]}")

# 四个直辖市关键词（用于剔除）
MUNICIPALITIES = {'北京', '天津', '上海', '重庆'}
# 需要剔除的国家级关键词
NATIONAL_KEYWORDS = ['国家', '中央', '国有']


def extract_city_from_investor(investor_name):
    """
    从投资方全称中提取地级市名称。
    
    返回: 标准城市名（如"合肥市"）或 None
    """
    if pd.isna(investor_name) or not isinstance(investor_name, str):
        return None
    
    investor_name = investor_name.strip()
    
    # 检查是否包含直辖市名称（如果包含则后续会被剔除）
    for muni in MUNICIPALITIES:
        if muni in investor_name:
            return f"__MUNICIPALITY_{muni}__"
    
    # 检查是否为国家/中央/国有级别且不含地级市名
    # 先尝试匹配地级市
    for short_name, std_name in city_match_list:
        if short_name in investor_name:
            return std_name
    
    # 没有匹配到地级市，检查是否包含国家级关键词
    for kw in NATIONAL_KEYWORDS:
        if kw in investor_name:
            return f"__NATIONAL_{kw}__"
    
    # 没有匹配到任何城市
    return None


# ============================================================
# 3. 读取所有年份的投资事件数据
# ============================================================
invest_dir = os.path.join(BASE_DIR, '清科政府引导基金投资事件截止到2024年')
all_files = []
for f in os.listdir(invest_dir):
    if f.endswith('.csv'):
        all_files.append(os.path.join(invest_dir, f))

print(f"\n发现 {len(all_files)} 个投资数据文件")

dfs = []
for fpath in sorted(all_files):
    fname = os.path.basename(fpath)
    try:
        df = pd.read_csv(fpath, encoding='utf-8-sig', low_memory=False)
        # 清除可能的空列
        df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
        print(f"  {fname}: {len(df)} 行")
        dfs.append(df)
    except Exception as e:
        print(f"  {fname}: 读取失败 - {e}")

raw_invest = pd.concat(dfs, ignore_index=True)
print(f"\n合并后总行数: {len(raw_invest)}")

# 清除脏数据行（如表头行混入数据）
raw_invest = raw_invest[raw_invest['投资阶段'] != '投资阶段'].copy()
raw_invest = raw_invest[raw_invest['投资阶段'] != '地区'].copy()
print(f"清除脏数据后: {len(raw_invest)}")

# ============================================================
# 4. 提取年份
# ============================================================
def parse_year(date_str):
    """从投资时间中提取年份"""
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    m = re.match(r'(\d{4})', date_str)
    if m:
        return int(m.group(1))
    return None

raw_invest['年份'] = raw_invest['投资时间'].apply(parse_year)
print(f"\n年份分布:")
print(raw_invest['年份'].value_counts().sort_index())

# 限定到2014-2024（需要2014年数据来生成2015年的滞后变量）
raw_invest = raw_invest[raw_invest['年份'].between(2014, 2024)].copy()
print(f"\n2014-2024年数据: {len(raw_invest)} 行")

# ============================================================
# 5. 从"投资方全称"匹配城市
# ============================================================
print("\n正在从投资方全称匹配地级市...")
raw_invest['匹配城市'] = raw_invest['投资方全称'].apply(extract_city_from_investor)

# 统计匹配结果
total = len(raw_invest)
matched_city = raw_invest['匹配城市'].notna() & ~raw_invest['匹配城市'].str.startswith('__', na=True)
matched_muni = raw_invest['匹配城市'].str.startswith('__MUNICIPALITY_', na=False)
matched_national = raw_invest['匹配城市'].str.startswith('__NATIONAL_', na=False)
no_match = raw_invest['匹配城市'].isna()

print(f"匹配结果:")
print(f"  匹配到地级市: {matched_city.sum()} ({matched_city.sum()/total*100:.1f}%)")
print(f"  匹配到直辖市(将剔除): {matched_muni.sum()} ({matched_muni.sum()/total*100:.1f}%)")
print(f"  匹配到国家级(将剔除): {matched_national.sum()} ({matched_national.sum()/total*100:.1f}%)")
print(f"  未匹配: {no_match.sum()} ({no_match.sum()/total*100:.1f}%)")

# 打印一些未匹配的投资方全称示例
unmatched_investors = raw_invest.loc[no_match, '投资方全称'].dropna().unique()
print(f"\n未匹配的投资方全称示例 (共{len(unmatched_investors)}个):")
for inv in unmatched_investors[:20]:
    print(f"  - {inv}")

# 只保留匹配到地级市的记录
invest_city = raw_invest[matched_city].copy()
print(f"\n保留地级市匹配记录: {len(invest_city)} 行")

# ============================================================
# 6. 解析投资金额
# ============================================================
def parse_amount(amt):
    """解析投资金额，单位：百万元RMB"""
    if pd.isna(amt):
        return np.nan
    amt = str(amt).strip()
    if amt == '--' or amt == '' or amt == '-':
        return np.nan
    # 去掉 (e) 估算值标记，仍使用该数值
    amt = amt.replace('(e)', '').strip()
    try:
        return float(amt)
    except ValueError:
        return np.nan

invest_city['投资金额_百万'] = invest_city['投资金额(RMB/M)'].apply(parse_amount)

# 统计金额缺失情况
has_amount = invest_city['投资金额_百万'].notna().sum()
print(f"\n投资金额有效值: {has_amount}/{len(invest_city)} ({has_amount/len(invest_city)*100:.1f}%)")

# ============================================================
# 7. 标记早期投资
# ============================================================
invest_city['是否早期'] = invest_city['投资阶段'].isin(['种子期', '初创期']).astype(int)

print(f"\n投资阶段分布（地级市匹配后）:")
print(invest_city['投资阶段'].value_counts())
print(f"\n早期投资(种子期+初创期): {invest_city['是否早期'].sum()} 条")

# ============================================================
# 8. 按城市-年份汇总
# ============================================================
print("\n按城市-年份汇总...")

# 8.1 总投资次数和总投资金额
total_stats = invest_city.groupby(['匹配城市', '年份']).agg(
    基金投资总次数=('投资阶段', 'count'),
    基金投资总金额_百万=('投资金额_百万', 'sum')  # 注意：sum会自动忽略NaN
).reset_index()

# 8.2 早期投资次数和早期投资金额
early_data = invest_city[invest_city['是否早期'] == 1]
early_stats = early_data.groupby(['匹配城市', '年份']).agg(
    早期投资次数=('投资阶段', 'count'),
    早期投资金额_百万=('投资金额_百万', 'sum')
).reset_index()

# 合并
city_year_stats = total_stats.merge(early_stats, on=['匹配城市', '年份'], how='left')

# 填充无早期投资的城市年份
city_year_stats['早期投资次数'] = city_year_stats['早期投资次数'].fillna(0).astype(int)
city_year_stats['早期投资金额_百万'] = city_year_stats['早期投资金额_百万'].fillna(0)

# 8.3 有效金额次数（用来判断金额占比是否可靠）
amount_valid_total = invest_city.groupby(['匹配城市', '年份'])['投资金额_百万'].apply(
    lambda x: x.notna().sum()
).reset_index(name='有金额记录总数')

amount_valid_early = early_data.groupby(['匹配城市', '年份'])['投资金额_百万'].apply(
    lambda x: x.notna().sum()
).reset_index(name='有金额记录早期数')

city_year_stats = city_year_stats.merge(amount_valid_total, on=['匹配城市', '年份'], how='left')
city_year_stats = city_year_stats.merge(amount_valid_early, on=['匹配城市', '年份'], how='left')
city_year_stats['有金额记录总数'] = city_year_stats['有金额记录总数'].fillna(0).astype(int)
city_year_stats['有金额记录早期数'] = city_year_stats['有金额记录早期数'].fillna(0).astype(int)

# 8.4 计算占比
city_year_stats['早期投资次数占比'] = city_year_stats['早期投资次数'] / city_year_stats['基金投资总次数']

# 金额占比：只有当总金额 > 0 时才计算
city_year_stats['早期投资金额占比'] = np.where(
    city_year_stats['基金投资总金额_百万'] > 0,
    city_year_stats['早期投资金额_百万'] / city_year_stats['基金投资总金额_百万'],
    np.nan  # 总金额为0或全部缺失时，占比设为NaN
)

# 重命名城市列
city_year_stats = city_year_stats.rename(columns={'匹配城市': '城市'})

print(f"\n城市-年份汇总表: {len(city_year_stats)} 条记录")
print(f"涉及城市: {city_year_stats['城市'].nunique()} 个")
print(f"\n汇总统计:")
print(city_year_stats[['基金投资总次数', '基金投资总金额_百万', '早期投资次数', 
                        '早期投资金额_百万', '早期投资次数占比', '早期投资金额占比']].describe())

# ============================================================
# 9. 滞后一期处理
# ============================================================
print("\n\n构建滞后一期变量...")
# 需要将 t 年的投资数据对应到 t+1 年的面板（即面板中2015年使用2014年数据）
city_year_stats['年份_滞后'] = city_year_stats['年份'] + 1

# 选择需要合并到面板的变量
lag_vars = city_year_stats[['城市', '年份_滞后', 
                             '基金投资总次数', '基金投资总金额_百万',
                             '早期投资次数', '早期投资金额_百万',
                             '早期投资次数占比', '早期投资金额占比']].copy()
lag_vars = lag_vars.rename(columns={'年份_滞后': '年份'})

# 添加"_滞后一期"后缀以区分
rename_map = {
    '基金投资总次数': '基金投资总次数_滞后一期',
    '基金投资总金额_百万': '基金投资总金额_百万_滞后一期',
    '早期投资次数': '早期投资次数_滞后一期',
    '早期投资金额_百万': '早期投资金额_百万_滞后一期',
    '早期投资次数占比': '早期投资次数占比_滞后一期',
    '早期投资金额占比': '早期投资金额占比_滞后一期',
}
lag_vars = lag_vars.rename(columns=rename_map)

# 限定面板年份范围 2015-2024
lag_vars = lag_vars[lag_vars['年份'].between(2015, 2024)].copy()

print(f"滞后变量数据: {len(lag_vars)} 条, 覆盖年份 {lag_vars['年份'].min()}-{lag_vars['年份'].max()}")

# ============================================================
# 10. 合并到面板数据
# ============================================================
print("\n合并到面板数据...")

# 只保留 2015-2024 年份的面板数据
panel_filtered = panel[panel['年份'].between(2015, 2024)].copy()
print(f"面板数据(2015-2024): {len(panel_filtered)} 行, {panel_filtered['城市'].nunique()} 城市")

# 合并
merged = panel_filtered.merge(lag_vars, on=['城市', '年份'], how='left')

# 对于面板中有但投资数据中没有的城市-年份，投资次数填0，金额填0，占比填NaN
fill_zero_cols = ['基金投资总次数_滞后一期', '早期投资次数_滞后一期']
fill_zero_amount_cols = ['基金投资总金额_百万_滞后一期', '早期投资金额_百万_滞后一期']

for col in fill_zero_cols:
    merged[col] = merged[col].fillna(0).astype(int)

for col in fill_zero_amount_cols:
    merged[col] = merged[col].fillna(0)

# 占比: 如果总次数为0，则占比设为0（该城市当年无引导基金投资）
merged['早期投资次数占比_滞后一期'] = np.where(
    merged['基金投资总次数_滞后一期'] > 0,
    merged['早期投资次数_滞后一期'] / merged['基金投资总次数_滞后一期'],
    0
)
merged['早期投资金额占比_滞后一期'] = np.where(
    merged['基金投资总金额_百万_滞后一期'] > 0,
    merged['早期投资金额_百万_滞后一期'] / merged['基金投资总金额_百万_滞后一期'],
    np.nan  # 总金额为0时金额占比不可计算
)

print(f"\n合并后面板: {len(merged)} 行, {merged.shape[1]} 列")

# ============================================================
# 11. 输出
# ============================================================
output_path = os.path.join(CLEANED_DIR, 'final_regression_panel_v4.csv')
merged.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"\n✅ 输出文件: {output_path}")

# 打印新变量的概要统计
print("\n" + "="*60)
print("新增变量概要统计（2015-2024, 滞后一期）")
print("="*60)
new_cols = [
    '基金投资总次数_滞后一期', '基金投资总金额_百万_滞后一期',
    '早期投资次数_滞后一期', '早期投资金额_百万_滞后一期',
    '早期投资次数占比_滞后一期', '早期投资金额占比_滞后一期'
]
print(merged[new_cols].describe().to_string())

# 有投资活动的城市-年份数
has_invest = (merged['基金投资总次数_滞后一期'] > 0).sum()
has_early = (merged['早期投资次数_滞后一期'] > 0).sum()
print(f"\n有基金投资活动的城市-年份: {has_invest}/{len(merged)} ({has_invest/len(merged)*100:.1f}%)")
print(f"有早期投资活动的城市-年份: {has_early}/{len(merged)} ({has_early/len(merged)*100:.1f}%)")

# 按年份看覆盖情况
print("\n各年份投资覆盖情况:")
for year in range(2015, 2025):
    yr_data = merged[merged['年份'] == year]
    yr_invest = (yr_data['基金投资总次数_滞后一期'] > 0).sum()
    yr_early = (yr_data['早期投资次数_滞后一期'] > 0).sum()
    yr_total = len(yr_data)
    print(f"  {year}: {yr_total} 城市, 有投资 {yr_invest} 城市, 有早期投资 {yr_early} 城市")

# 也单独保存城市年份投资汇总中间文件
mid_output = os.path.join(CLEANED_DIR, 'city_year_fund_investment_stats.csv')
city_year_stats.to_csv(mid_output, index=False, encoding='utf-8-sig')
print(f"\n中间文件: {mid_output}")
