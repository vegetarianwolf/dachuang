"""
rebuild_panel_v5.py
===================
Build final_regression_panel_v5.csv with corrected X and M variables.

Key changes from v4:
  1. NEW X variable: fiscal_self_sufficiency = revenue / expenditure
     - Cleaner measure of fiscal constraint (avoids conflating spending intensity)
     - Also add transfer_dependency = 1 - fiscal_self_sufficiency
  2. IMPROVED M matching: use 基金注册地区 field from enhanced dataset
     - Parse "中国|省|市" to extract prefecture-level city
     - Also use 地区 (investee location) as secondary matching
  3. EXPANDED M definitions:
     - M_has_fund: dummy for any government fund investment
     - M_log_count: log(1 + total fund investment count)
     - M_log_amount: log(1 + total fund investment amount in millions)
     - M_early_dummy: dummy for any early-stage fund investment
     - M_early_ratio: early count / total count (original approach, for robustness)
     - All fill zeros for cities without fund activity (NOT NaN)
  4. Leave-one-out provincial average IV for fiscal constraint
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
print("Rebuild Panel v5: Corrected X and M Variables")
print("=" * 80)

# ============================================================
# 1. Load v4 panel as base (already has patents, fiscal, controls)
# ============================================================
print("\n1. Loading v4 panel...")
v4_path = os.path.join(CLEANED_DIR, 'final_regression_panel_v4.csv')
panel = pd.read_csv(v4_path, encoding='utf-8-sig')
print(f"   v4 panel: {panel.shape[0]} rows x {panel.shape[1]} cols")
print(f"   Years: {panel['年份'].min()}-{panel['年份'].max()}")
print(f"   Cities: {panel['城市'].nunique()}")

# ============================================================
# 2. PHASE 1: Construct fiscal_self_sufficiency
# ============================================================
print("\n2. Phase 1: Constructing fiscal self-sufficiency rate...")

panel['财政自给率'] = np.where(
    (panel['财政支出'].notna()) & (panel['财政支出'] > 0),
    panel['财政收入'] / panel['财政支出'],
    np.nan
)

panel['转移支付依赖度'] = np.where(
    panel['财政自给率'].notna(),
    1 - panel['财政自给率'],
    np.nan
)

panel = panel.sort_values(['城市', '年份'])
panel['财政自给率_滞后一期'] = panel.groupby('城市')['财政自给率'].shift(1)
panel['转移支付依赖度_滞后一期'] = panel.groupby('城市')['转移支付依赖度'].shift(1)

n_valid = panel['财政自给率'].notna().sum()
n_valid_l1 = panel['财政自给率_滞后一期'].notna().sum()
print(f"   财政自给率: {n_valid} valid ({n_valid/len(panel)*100:.1f}%)")
print(f"   财政自给率_L1: {n_valid_l1} valid ({n_valid_l1/len(panel)*100:.1f}%)")

desc = panel['财政自给率'].describe()
print(f"   Stats: mean={desc['mean']:.4f}, median={desc['50%']:.4f}, "
      f"min={desc['min']:.4f}, max={desc['max']:.4f}")

# ============================================================
# 3. PHASE 1.3: Leave-one-out provincial average IV
# ============================================================
print("\n3. Constructing leave-one-out provincial IV...")

prov_group = panel.groupby(['省份', '年份'])

def leave_one_out_mean(group, col):
    """For each city, compute mean of col across all OTHER cities in same province-year."""
    vals = group[col].values
    n = len(vals)
    total = np.nansum(vals)
    counts = np.sum(~np.isnan(vals))
    result = np.empty(n)
    for i in range(n):
        if np.isnan(vals[i]):
            if counts > 0:
                result[i] = total / counts
            else:
                result[i] = np.nan
        else:
            other_total = total - vals[i]
            other_count = counts - 1
            if other_count > 0:
                result[i] = other_total / other_count
            else:
                result[i] = np.nan
    return result

iv_selfsuff = []
iv_gap = []

for (prov, year), grp in prov_group:
    idx = grp.index
    loo_ss = leave_one_out_mean(grp, '财政自给率')
    loo_gap = leave_one_out_mean(grp, '财政缺口率')
    for i, ix in enumerate(idx):
        iv_selfsuff.append((ix, loo_ss[i]))
        iv_gap.append((ix, loo_gap[i]))

iv_ss_df = pd.DataFrame(iv_selfsuff, columns=['idx', 'IV_财政自给率_省内均值'])
iv_gap_df = pd.DataFrame(iv_gap, columns=['idx', 'IV_财政缺口率_省内均值'])

panel = panel.merge(iv_ss_df.set_index('idx'), left_index=True, right_index=True, how='left')
panel = panel.merge(iv_gap_df.set_index('idx'), left_index=True, right_index=True, how='left')

panel = panel.sort_values(['城市', '年份'])
panel['IV_财政自给率_省内均值_滞后一期'] = panel.groupby('城市')['IV_财政自给率_省内均值'].shift(1)
panel['IV_财政缺口率_省内均值_滞后一期'] = panel.groupby('城市')['IV_财政缺口率_省内均值'].shift(1)

n_iv = panel['IV_财政自给率_省内均值_滞后一期'].notna().sum()
print(f"   IV (fiscal self-suff, LOO provincial mean, L1): {n_iv} valid")

# ============================================================
# 4. PHASE 2: Re-parse investment data with 基金注册地区
# ============================================================
print("\n4. Phase 2: Re-parsing investment data with fund registration area...")

invest_dir = os.path.join(BASE_DIR, '清科政府引导基金投资事件_加注册地区')
all_files = sorted([
    os.path.join(invest_dir, f)
    for f in os.listdir(invest_dir)
    if f.endswith('.csv') and '匹配' not in f
])

dfs = []
for fpath in all_files:
    fname = os.path.basename(fpath)
    try:
        df = pd.read_csv(fpath, encoding='utf-8-sig', low_memory=False)
        df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
        print(f"   {fname}: {len(df)} rows")
        dfs.append(df)
    except Exception as e:
        print(f"   {fname}: FAILED - {e}")

raw_invest = pd.concat(dfs, ignore_index=True)
raw_invest = raw_invest[raw_invest['投资阶段'] != '投资阶段'].copy()
raw_invest = raw_invest[raw_invest['投资阶段'] != '地区'].copy()
print(f"   Total investment records: {len(raw_invest)}")

# Parse year
def parse_year(date_str):
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    m = re.match(r'(\d{4})', date_str.strip())
    return int(m.group(1)) if m else None

raw_invest['年份'] = raw_invest['投资时间'].apply(parse_year)
raw_invest = raw_invest[raw_invest['年份'].between(2014, 2024)].copy()
print(f"   2014-2024 records: {len(raw_invest)}")

# ============================================================
# 5. Extract city from 基金注册地区 and 地区 fields
# ============================================================
print("\n5. Extracting cities from location fields...")

city_list = sorted(panel['城市'].unique().tolist())
city_set = set(city_list)

MUNICIPALITIES = {'北京市', '天津市', '上海市', '重庆市'}

def parse_location_field(loc_str):
    """Parse '中国|省|市' or '中国|省|市|区' to extract prefecture-level city."""
    if pd.isna(loc_str) or not isinstance(loc_str, str):
        return None
    loc_str = loc_str.strip()
    if loc_str in ('未匹配', '--', ''):
        return None

    parts = [p.strip() for p in loc_str.split('|')]
    if len(parts) < 2:
        return None

    for part in parts:
        if part in MUNICIPALITIES:
            return f"__MUNI_{part}__"

    for part in parts:
        if part in city_set:
            return part
        if part + '市' in city_set:
            return part + '市'

    if len(parts) >= 3:
        candidate = parts[2]
        if candidate.endswith('区') or candidate.endswith('县'):
            pass
        elif candidate in city_set:
            return candidate
        elif candidate + '市' in city_set:
            return candidate + '市'

    return None

# Primary: use 基金注册地区 for fund-jurisdiction matching
raw_invest['基金所在城市'] = raw_invest['基金注册地区'].apply(parse_location_field)

# Secondary: use 地区 for investee-location matching
raw_invest['企业所在城市'] = raw_invest['地区'].apply(parse_location_field)

# Also try investor name matching as fallback
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
city_match_list.sort(key=lambda x: len(x[0]), reverse=True)

MUNI_SHORT = {'北京', '天津', '上海', '重庆'}
NATIONAL_KW = ['国家', '中央', '国有']

def extract_city_from_name(name):
    if pd.isna(name) or not isinstance(name, str):
        return None
    name = name.strip()
    for m in MUNI_SHORT:
        if m in name:
            return f"__MUNI_{m}市__"
    for short, std in city_match_list:
        if short in name:
            return std
    for kw in NATIONAL_KW:
        if kw in name:
            return f"__NATIONAL__"
    return None

raw_invest['投资方匹配城市'] = raw_invest['投资方全称'].apply(extract_city_from_name)

# Combine: priority = 基金注册地区 > 投资方名称匹配 > 企业所在地
def is_valid_city(c):
    return c is not None and not str(c).startswith('__')

raw_invest['匹配城市_基金'] = raw_invest['基金所在城市'].where(
    raw_invest['基金所在城市'].apply(is_valid_city), None
)
raw_invest['匹配城市_投资方'] = raw_invest['投资方匹配城市'].where(
    raw_invest['投资方匹配城市'].apply(is_valid_city), None
)
raw_invest['匹配城市_企业'] = raw_invest['企业所在城市'].where(
    raw_invest['企业所在城市'].apply(is_valid_city), None
)

raw_invest['最终匹配城市'] = (
    raw_invest['匹配城市_基金']
    .fillna(raw_invest['匹配城市_投资方'])
    .fillna(raw_invest['匹配城市_企业'])
)

n_total = len(raw_invest)
n_fund = raw_invest['匹配城市_基金'].notna().sum()
n_inv = raw_invest['匹配城市_投资方'].notna().sum()
n_ent = raw_invest['匹配城市_企业'].notna().sum()
n_final = raw_invest['最终匹配城市'].notna().sum()

print(f"\n   Matching results (total={n_total}):")
print(f"   基金注册地区 matched: {n_fund} ({n_fund/n_total*100:.1f}%)")
print(f"   投资方名称 matched:   {n_inv} ({n_inv/n_total*100:.1f}%)")
print(f"   企业所在地区 matched: {n_ent} ({n_ent/n_total*100:.1f}%)")
print(f"   Final combined:       {n_final} ({n_final/n_total*100:.1f}%)")

invest_matched = raw_invest[raw_invest['最终匹配城市'].notna()].copy()
invest_matched = invest_matched.rename(columns={'最终匹配城市': '城市'})

# ============================================================
# 6. Parse investment amounts and mark early-stage
# ============================================================
print("\n6. Parsing amounts and marking early-stage investments...")

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

invest_matched['投资金额_百万'] = invest_matched['投资金额(RMB/M)'].apply(parse_amount)
invest_matched['是否早期'] = invest_matched['投资阶段'].isin(['种子期', '初创期']).astype(int)

print(f"   Total matched records: {len(invest_matched)}")
print(f"   Early-stage (seed+startup): {invest_matched['是否早期'].sum()}")
print(f"   Investment stage distribution:")
print(invest_matched['投资阶段'].value_counts().to_string())

# ============================================================
# 7. Aggregate by city-year
# ============================================================
print("\n7. Aggregating by city-year...")

total_stats = invest_matched.groupby(['城市', '年份']).agg(
    基金投资总次数=('投资阶段', 'count'),
    基金投资总金额_百万=('投资金额_百万', 'sum')
).reset_index()

early_data = invest_matched[invest_matched['是否早期'] == 1]
early_stats = early_data.groupby(['城市', '年份']).agg(
    早期投资次数=('投资阶段', 'count'),
    早期投资金额_百万=('投资金额_百万', 'sum')
).reset_index()

city_year_stats = total_stats.merge(early_stats, on=['城市', '年份'], how='left')
city_year_stats['早期投资次数'] = city_year_stats['早期投资次数'].fillna(0).astype(int)
city_year_stats['早期投资金额_百万'] = city_year_stats['早期投资金额_百万'].fillna(0)

city_year_stats['早期投资次数占比'] = city_year_stats['早期投资次数'] / city_year_stats['基金投资总次数']
city_year_stats['早期投资金额占比'] = np.where(
    city_year_stats['基金投资总金额_百万'] > 0,
    city_year_stats['早期投资金额_百万'] / city_year_stats['基金投资总金额_百万'],
    np.nan
)

n_cy = len(city_year_stats)
n_cities = city_year_stats['城市'].nunique()
print(f"   City-year records: {n_cy}, Cities: {n_cities}")

# Save intermediate
mid_path = os.path.join(CLEANED_DIR, 'city_year_fund_investment_stats_v5.csv')
city_year_stats.to_csv(mid_path, index=False, encoding='utf-8-sig')

# ============================================================
# 8. Create lagged variables and merge to panel
# ============================================================
print("\n8. Creating lagged M variables and merging...")

city_year_stats['年份_lag'] = city_year_stats['年份'] + 1

lag_cols = {
    '基金投资总次数': 'v5_基金投资总次数_L1',
    '基金投资总金额_百万': 'v5_基金投资总金额_百万_L1',
    '早期投资次数': 'v5_早期投资次数_L1',
    '早期投资金额_百万': 'v5_早期投资金额_百万_L1',
    '早期投资次数占比': 'v5_早期投资次数占比_L1',
    '早期投资金额占比': 'v5_早期投资金额占比_L1',
}

lag_df = city_year_stats[['城市', '年份_lag'] + list(lag_cols.keys())].copy()
lag_df = lag_df.rename(columns={'年份_lag': '年份', **lag_cols})
lag_df = lag_df[lag_df['年份'].between(2015, 2024)]

panel = panel.merge(lag_df, on=['城市', '年份'], how='left')

# Fill zeros for cities without fund activity
for col in ['v5_基金投资总次数_L1', 'v5_早期投资次数_L1']:
    panel[col] = panel[col].fillna(0).astype(int)
for col in ['v5_基金投资总金额_百万_L1', 'v5_早期投资金额_百万_L1']:
    panel[col] = panel[col].fillna(0)

# ============================================================
# 9. PHASE 2.2: Construct expanded M variable definitions
# ============================================================
print("\n9. Constructing expanded M variable definitions...")

# M1: Has any fund investment (extensive margin)
panel['M_has_fund_L1'] = (panel['v5_基金投资总次数_L1'] > 0).astype(int)

# M2: Log total fund investment count
panel['M_log_count_L1'] = np.log1p(panel['v5_基金投资总次数_L1'])

# M3: Log total fund investment amount
panel['M_log_amount_L1'] = np.log1p(panel['v5_基金投资总金额_百万_L1'])

# M4: Has any early-stage investment (extensive margin)
panel['M_early_dummy_L1'] = (panel['v5_早期投资次数_L1'] > 0).astype(int)

# M5: Early investment ratio (only for cities with fund activity)
panel['M_early_ratio_L1'] = np.where(
    panel['v5_基金投资总次数_L1'] > 0,
    panel['v5_早期投资次数_L1'] / panel['v5_基金投资总次数_L1'],
    np.nan
)

# M6: Early ratio filled with 0 for no-fund cities
panel['M_early_ratio_filled_L1'] = np.where(
    panel['v5_基金投资总次数_L1'] > 0,
    panel['v5_早期投资次数_L1'] / panel['v5_基金投资总次数_L1'],
    0
)

# Coverage report
print(f"   M_has_fund_L1: {panel['M_has_fund_L1'].sum()} cities with fund / {len(panel)} total")
print(f"   M_early_dummy_L1: {panel['M_early_dummy_L1'].sum()} cities with early investment")
print(f"   M_early_ratio_L1 (fund-only): {panel['M_early_ratio_L1'].notna().sum()} valid")
print(f"   M_early_ratio_filled_L1 (all): {panel['M_early_ratio_filled_L1'].notna().sum()} valid")

# ============================================================
# 10. Drop old v4 M columns to avoid confusion, keep for comparison
# ============================================================
old_m_cols = [
    '基金投资总次数_滞后一期', '基金投资总金额_百万_滞后一期',
    '早期投资次数_滞后一期', '早期投资金额_百万_滞后一期',
    '早期投资次数占比_滞后一期', '早期投资金额占比_滞后一期',
]

for col in old_m_cols:
    if col in panel.columns:
        panel = panel.rename(columns={col: 'v4_' + col})

# ============================================================
# 11. Output
# ============================================================
output_path = os.path.join(CLEANED_DIR, 'final_regression_panel_v5.csv')
panel.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"\n{'='*80}")
print(f"Output: {output_path}")
print(f"Dimensions: {panel.shape[0]} rows x {panel.shape[1]} cols")
print(f"\nNew columns added:")

new_cols = [
    '财政自给率', '财政自给率_滞后一期',
    '转移支付依赖度', '转移支付依赖度_滞后一期',
    'IV_财政自给率_省内均值_滞后一期', 'IV_财政缺口率_省内均值_滞后一期',
    'M_has_fund_L1', 'M_log_count_L1', 'M_log_amount_L1',
    'M_early_dummy_L1', 'M_early_ratio_L1', 'M_early_ratio_filled_L1',
]
for col in new_cols:
    if col in panel.columns:
        n_valid = panel[col].notna().sum()
        print(f"   {col}: {n_valid} valid ({n_valid/len(panel)*100:.1f}%)")

# Summary statistics for key new variables
print(f"\n{'='*80}")
print("Summary Statistics for Key New Variables")
print("=" * 80)
key_vars = ['财政自给率_滞后一期', '转移支付依赖度_滞后一期',
            'M_has_fund_L1', 'M_log_count_L1', 'M_early_dummy_L1',
            'M_early_ratio_filled_L1']
for v in key_vars:
    if v in panel.columns:
        s = panel[v].dropna()
        print(f"\n{v}:")
        print(f"  N={len(s)}, mean={s.mean():.4f}, sd={s.std():.4f}, "
              f"min={s.min():.4f}, p50={s.median():.4f}, max={s.max():.4f}")

print(f"\nDone!")
