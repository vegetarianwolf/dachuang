"""
build_regression_panel.py  (v2 — 完整控制变量版)
===================================================
按照 新思路.md 方案重建 final_regression_dataset.csv:
  被解释变量: 地区创新产出 (专利数据)
  核心解释变量: 财政缺口率 (支出-收入)/GDP
  机制变量: 早期投资占比 / 加权风险偏好指数
  控制变量: 人均GDP, 金融深度, 产业结构, 科技支出占比, 外资, 债务率, 人口
"""

import os
import re
import pandas as pd
import numpy as np

# =====================================================================
# 通用解析函数
# =====================================================================

def parse_ceic_wide(filepath, col_filter_fn=None, encoding='utf-8-sig'):
    """
    解析 CEIC 宽表:
      行 = 元数据(前28行左右) + 年份数据
      列 = 各城市(列名含城市名, 如 '国内生产总值:河北:石家庄')
    返回长格式 DataFrame: [City, Year, Value]
    """
    df = pd.read_csv(filepath, encoding=encoding)
    date_col = df.columns[0]
    city_cols = list(df.columns[1:])

    if col_filter_fn:
        city_cols = [c for c in city_cols if col_filter_fn(c)]

    col_to_city = {}
    for c in city_cols:
        parts = c.split(':')
        city = parts[-1].strip()
        col_to_city[c] = city

    year_mask = df[date_col].apply(
        lambda x: str(x).strip().isdigit() and len(str(x).strip()) == 4
                  and int(str(x).strip()) >= 1949)
    data = df[year_mask].copy()
    data['Year'] = data[date_col].astype(int)

    result = data[['Year'] + city_cols].melt(
        id_vars='Year', var_name='col_name', value_name='Value')
    result['City'] = result['col_name'].map(col_to_city)
    result['Value'] = pd.to_numeric(result['Value'], errors='coerce')
    result = result.dropna(subset=['Value'])
    return result[['City', 'Year', 'Value']].copy()


def parse_yearbook_single(filepath, encoding='gbk'):
    """
    解析年鉴式宽表 (每年仅一个指标):
      列 = 年份(如 '1990年'), 行 = 城市. 行0 = 指标描述, 行1+ = 数据
    """
    df = pd.read_csv(filepath, encoding=encoding)
    yr_cols = [c for c in df.columns if '年' in str(c)]
    records = []
    for row_idx in range(1, len(df)):
        city = str(df.iloc[row_idx, 0]).strip()
        if not city or city == 'nan':
            continue
        city_clean = city.replace('市', '')
        for yc in yr_cols:
            year = int(str(yc).replace('年', ''))
            val = df.iloc[row_idx, df.columns.get_loc(yc)]
            records.append({'City': city_clean, 'Year': year, 'Value': val})
    result = pd.DataFrame(records)
    result['Value'] = pd.to_numeric(
        result['Value'].astype(str).str.replace('--', '').str.strip(),
        errors='coerce')
    result = result.dropna(subset=['Value'])
    return result


def parse_yearbook_multi(filepath, indicator_keyword, encoding='gbk'):
    """
    解析年鉴式宽表 (每年有多个子指标):
      列 = '1990年', Unnamed:2, ..., '1991年', ...
      行0 = 各子指标名称. 按 indicator_keyword 筛选所需子列.
    """
    df = pd.read_csv(filepath, encoding=encoding)
    indicators = df.iloc[0]
    current_year = None
    target_col_indices = []
    target_years = []
    for i, col_name in enumerate(df.columns):
        if i == 0:
            continue
        if '年' in str(col_name):
            current_year = int(str(col_name).replace('年', ''))
        indicator = str(indicators.iloc[i])
        if indicator_keyword in indicator:
            target_col_indices.append(i)
            target_years.append(current_year)
    records = []
    for row_idx in range(1, len(df)):
        city = str(df.iloc[row_idx, 0]).strip()
        if not city or city == 'nan':
            continue
        city_clean = city.replace('市', '')
        for col_idx, year in zip(target_col_indices, target_years):
            val = df.iloc[row_idx, col_idx]
            records.append({'City': city_clean, 'Year': year, 'Value': val})
    result = pd.DataFrame(records)
    result['Value'] = pd.to_numeric(
        result['Value'].astype(str).str.replace('--', '').str.strip(),
        errors='coerce')
    result = result.dropna(subset=['Value'])
    return result


# =====================================================================
# 城市名标准化
# =====================================================================

def normalize_city(name):
    """统一到不带'市'的短形式"""
    s = str(name).strip()
    for suf in ['市', '地区', '自治州', '盟']:
        s = s.replace(suf, '')
    return s


# =====================================================================
# 专利数据 (地级市层面, 2000-2023)
# =====================================================================

def load_city_patent_data():
    """
    加载地级市专利申请、授权数据 (2000-2023).
    数据源: 马克数据网, 包含 300 个地级市.
    """
    fp = '地级市专利申请、授权数据（2000-2023年）/地级市专利申请、授权数据（2000-2023年）.csv'
    df = pd.read_csv(fp, encoding='gbk')
    df = df.dropna(subset=['年份']).copy()
    df['年份'] = df['年份'].astype(int)
    df['City'] = df['地区'].apply(normalize_city)
    df['Year'] = df['年份']

    # 重命名专利字段
    patent_cols = {
        '专利申请总量': 'patent_apply',
        '专利申请_发明专利': 'inv_patent_apply',
        '专利申请_实用新型': 'utility_patent_apply',
        '专利申请_外观设计': 'design_patent_apply',
        '专利授权总量': 'patent_grant',
        '专利授权_发明专利': 'inv_patent_grant',
        '专利授权_实用新型': 'utility_patent_grant',
        '专利授权_外观设计': 'design_patent_grant',
    }
    for cn, en in patent_cols.items():
        df[en] = pd.to_numeric(df[cn], errors='coerce').fillna(0)

    # 取对数
    df['ln_patent_apply']      = np.log(df['patent_apply'] + 1)
    df['ln_inv_patent']        = np.log(df['inv_patent_apply'] + 1)
    df['ln_patent_grant']      = np.log(df['patent_grant'] + 1)
    df['ln_inv_patent_grant']  = np.log(df['inv_patent_grant'] + 1)

    keep_cols = ['City', 'Year',
                 'patent_apply', 'inv_patent_apply', 'patent_grant', 'inv_patent_grant',
                 'ln_patent_apply', 'ln_inv_patent', 'ln_patent_grant', 'ln_inv_patent_grant']
    result = df[keep_cols].copy()
    print(f"  City-level patent data: {len(result)} obs, {result['City'].nunique()} cities, "
          f"years {result['Year'].min()}-{result['Year'].max()}")
    return result


# =====================================================================
# PE 数据聚合
# =====================================================================

def load_and_aggregate_pe():
    pe_file = 'cleaned_data/PE_investment_events_cleaned.csv'
    print(f"  Loading {pe_file} ...")
    pe_df = pd.read_csv(pe_file, low_memory=False)
    pe_df = pe_df.dropna(subset=['Year', 'City']).copy()
    pe_df['Year'] = pe_df['Year'].astype(int)
    pe_df['Inv_Amount_RMB_M'] = pd.to_numeric(
        pe_df['Inv_Amount_RMB_M'], errors='coerce').fillna(0)

    stage_weight = {'种子期': 4, '初创期': 3, '扩张期': 2, '成熟期': 1}

    def calc_metrics(grp):
        total_amt = grp['Inv_Amount_RMB_M'].sum()
        total_cnt = len(grp)
        early_mask = grp['投资阶段'].astype(str).str.contains('种子期|初创期', na=False)
        early_amt = grp.loc[early_mask, 'Inv_Amount_RMB_M'].sum()
        early_cnt = early_mask.sum()
        early_ratio = early_amt / total_amt if total_amt > 0 else np.nan
        early_deal_ratio = early_cnt / total_cnt if total_cnt > 0 else np.nan
        valid = grp[grp['投资阶段'].isin(stage_weight.keys())]
        risk_index = valid['投资阶段'].map(stage_weight).mean() if len(valid) > 0 else np.nan
        return pd.Series({
            'Total_Inv_Amount': total_amt,
            'Total_Inv_Count': total_cnt,
            'Early_Stage_Amount': early_amt,
            'Early_Stage_Count': early_cnt,
            'Early_Stage_Ratio': early_ratio,
            'Early_Deal_Ratio': early_deal_ratio,
            'Risk_Index': risk_index,
        })

    print("  Collapsing PE events to City-Year panel ...")
    city_year_pe = pe_df.groupby(['City', 'Year']).apply(calc_metrics).reset_index()
    return pe_df, city_year_pe


# =====================================================================
# 加载并解析所有宏观数据
# =====================================================================

def load_macro_data():
    """加载所有宏观控制变量数据, 返回 city-year 长面板"""

    print("  [1] Loading GDP ...")
    gdp = parse_ceic_wide('地级市总GDP.csv')
    gdp = gdp.rename(columns={'Value': 'GDP_十亿'})
    gdp['City'] = gdp['City'].apply(normalize_city)
    print(f"      GDP: {len(gdp)} obs, {gdp['City'].nunique()} cities")

    print("  [2] Loading Per-Capita GDP ...")
    gdp_pc = parse_ceic_wide('地级市人均GDP.csv')
    gdp_pc = gdp_pc.rename(columns={'Value': 'GDPPC_元'})
    gdp_pc['City'] = gdp_pc['City'].apply(normalize_city)
    print(f"      PerCapGDP: {len(gdp_pc)} obs")

    print("  [3] Loading Industry2 GDP ...")
    ind2 = parse_ceic_wide('地级市第二产业.csv')
    ind2 = ind2.rename(columns={'Value': 'GDP2_十亿'})
    ind2['City'] = ind2['City'].apply(normalize_city)
    print(f"      Industry2: {len(ind2)} obs")

    print("  [4] Loading Fiscal Expenditure (CEIC) ...")
    fexp = parse_ceic_wide('地级市财政支出.csv')
    fexp = fexp.rename(columns={'Value': 'FiscalExp_百万'})
    fexp['City'] = fexp['City'].apply(normalize_city)
    print(f"      FiscalExp: {len(fexp)} obs")

    print("  [5] Loading Fiscal Revenue (CEIC) ...")
    frev = parse_ceic_wide('地级市财政收入.csv')
    frev = frev.rename(columns={'Value': 'FiscalRev_百万'})
    frev['City'] = frev['City'].apply(normalize_city)
    print(f"      FiscalRev: {len(frev)} obs")

    print("  [6] Loading Science Expenditure ...")
    sci = parse_ceic_wide('财政支出：科学：地级市.csv')
    sci = sci.rename(columns={'Value': 'SciExp_百万'})
    sci['City'] = sci['City'].apply(normalize_city)
    print(f"      SciExp: {len(sci)} obs")

    print("  [7] Loading Debt Balance ...")
    def debt_total_filter(col_name):
        return ':一般:' not in col_name and ':专项:' not in col_name
    debt = parse_ceic_wide('地方政府债务：地级市：余额.csv', col_filter_fn=debt_total_filter)
    debt = debt.rename(columns={'Value': 'Debt_百万'})
    debt['City'] = debt['City'].apply(normalize_city)
    print(f"      Debt: {len(debt)} obs, years {debt['Year'].min()}-{debt['Year'].max()}")

    print("  [8] Loading Population ...")
    pop = parse_yearbook_single('常住人口.csv', encoding='gbk')
    pop = pop.rename(columns={'Value': 'Pop_万人'})
    pop['City'] = pop['City'].apply(normalize_city)
    print(f"      Population: {len(pop)} obs")

    print("  [9] Loading Loan Balance ...")
    # 优先用覆盖率更高的 "年末金融机构各项贷款余额(万元)", 再用 "本外币" 补充
    loan_main = parse_yearbook_multi('金融机构贷款余额.csv', '年末金融机构各项贷款余额', encoding='gbk')
    loan_main['Value'] = loan_main['Value'] / 10000  # 万元 -> 亿元
    loan_alt = parse_yearbook_multi('金融机构贷款余额.csv', '本外币各项贷款余额', encoding='gbk')
    # 合并: 优先 loan_main, 缺失时用 loan_alt 补充
    loan_main['City'] = loan_main['City'].apply(normalize_city)
    loan_alt['City'] = loan_alt['City'].apply(normalize_city)
    loan = loan_main.rename(columns={'Value': 'Loan_亿'})
    loan_alt = loan_alt.rename(columns={'Value': 'Loan_亿'})
    # 仅补充 loan 中没有的 (City, Year) 组合
    existing_keys = set(zip(loan['City'], loan['Year']))
    supplement = loan_alt[~loan_alt.apply(lambda r: (r['City'], r['Year']) in existing_keys, axis=1)]
    loan = pd.concat([loan, supplement], ignore_index=True)
    print(f"      Loan (combined): {len(loan)} obs")

    print("  [10] Loading FDI ...")
    fdi = parse_yearbook_multi('实际利用外资.csv', '实际利用外资额', encoding='gbk')
    fdi = fdi.rename(columns={'Value': 'FDI_万美元'})
    fdi['City'] = fdi['City'].apply(normalize_city)
    print(f"      FDI: {len(fdi)} obs")

    # ---- 合并 ----
    print("  Merging macro variables ...")
    macro = gdp.merge(gdp_pc, on=['City', 'Year'], how='outer')
    macro = macro.merge(ind2,  on=['City', 'Year'], how='outer')
    macro = macro.merge(fexp,  on=['City', 'Year'], how='outer')
    macro = macro.merge(frev,  on=['City', 'Year'], how='outer')
    macro = macro.merge(sci,   on=['City', 'Year'], how='outer')
    macro = macro.merge(debt,  on=['City', 'Year'], how='outer')
    macro = macro.merge(pop,   on=['City', 'Year'], how='outer')
    macro = macro.merge(loan,  on=['City', 'Year'], how='outer')
    macro = macro.merge(fdi,   on=['City', 'Year'], how='outer')

    # ---- 派生变量 (统一亿元口径) ----
    GDP_亿     = macro['GDP_十亿'] * 10
    FiscalExp_亿 = macro['FiscalExp_百万'] / 100
    FiscalRev_亿 = macro['FiscalRev_百万'] / 100
    SciExp_亿    = macro['SciExp_百万'] / 100
    Debt_亿      = macro['Debt_百万'] / 100

    macro['fiscal_gap_rate']   = (FiscalExp_亿 - FiscalRev_亿) / GDP_亿
    macro['finance_depth']     = macro['Loan_亿'] / GDP_亿
    macro['industry2_share']   = macro['GDP2_十亿'] / macro['GDP_十亿']
    macro['tech_share']        = macro['SciExp_百万'] / macro['FiscalExp_百万']
    macro['fdi_ratio']         = macro['FDI_万美元'] / (macro['GDP_十亿'] * 100000)
    macro['debt_rate']         = Debt_亿 / GDP_亿
    macro['ln_gdp_percap']     = np.log(macro['GDPPC_元'].clip(lower=1))
    macro['ln_population']     = np.log(macro['Pop_万人'].clip(lower=0.01))

    print(f"  Macro panel: {len(macro)} obs, {macro['City'].nunique()} cities, "
          f"years {macro['Year'].min()}-{macro['Year'].max()}")
    return macro


# =====================================================================
# 主构建函数
# =====================================================================

def build_final_dataset():
    # --- 1. 专利面板 (地级市层面) ---
    print("=" * 60)
    print("[1/5] Loading city-level patent data ...")
    patent_panel = load_city_patent_data()

    # --- 2. PE 面板 ---
    print("=" * 60)
    print("[2/5] Loading & aggregating PE data ...")
    pe_df, city_year_pe = load_and_aggregate_pe()
    print(f"  City-Year PE panel: {len(city_year_pe)} rows, "
          f"{city_year_pe['City'].nunique()} cities")

    # --- 3. 宏观数据面板 ---
    print("=" * 60)
    print("[3/5] Loading macro data (GDP, fiscal, controls) ...")
    macro = load_macro_data()

    # --- 4. 合并 ---
    print("=" * 60)
    print("[4/5] Merging panels ...")
    city_year_pe['City'] = city_year_pe['City'].apply(normalize_city)
    city_year_pe['Year'] = city_year_pe['Year'].astype(int)

    panel = pd.merge(city_year_pe, macro, on=['City', 'Year'], how='inner')
    print(f"  After PE x Macro merge: {len(panel)} rows, {panel['City'].nunique()} cities")

    # 滞后一期
    panel = panel.sort_values(['City', 'Year'])
    panel['L1_fiscal_gap_rate'] = panel.groupby('City')['fiscal_gap_rate'].shift(1)
    panel['L1_debt_rate']       = panel.groupby('City')['debt_rate'].shift(1)

    # 匹配专利数据 (直接按城市名 + 年份匹配)
    panel = panel.merge(
        patent_panel,
        on=['City', 'Year'],
        how='left'
    )
    matched = panel['ln_inv_patent'].notna().sum()
    print(f"  Patent matched: {matched}/{len(panel)} ({matched/len(panel)*100:.1f}%)")

    # --- 5. 输出 ---
    print("=" * 60)
    print("[5/5] Saving dataset ...")

    rename_map = {
        'City': '城市', 'Year': '年份',
        'Total_Inv_Amount': '全部基金投资总金额',
        'Total_Inv_Count': '全部基金投资总次数',
        'Early_Stage_Amount': '早期投资金额',
        'Early_Stage_Count': '早期投资次数',
        'Early_Stage_Ratio': '早期投资金额占比',
        'Early_Deal_Ratio': '早期投资事件占比',
        'Risk_Index': '加权风险偏好指数',
        'FiscalExp_百万': '财政支出_百万',
        'FiscalRev_百万': '财政收入_百万',
        'fiscal_gap_rate': '当期财政缺口率',
        'L1_fiscal_gap_rate': '滞后一期财政缺口率',
        'GDP_十亿': 'GDP_十亿',
        'GDPPC_元': '人均GDP_元',
        'ln_gdp_percap': 'ln_人均GDP',
        'finance_depth': '金融深度',
        'industry2_share': '第二产业占比',
        'tech_share': '科技支出占比',
        'fdi_ratio': '外资占比',
        'debt_rate': '债务率',
        'L1_debt_rate': '滞后一期债务率',
        'Pop_万人': '常住人口_万人',
        'ln_population': 'ln_人口',
        'Loan_亿': '贷款余额_亿',
        'FDI_万美元': '实际利用外资_万美元',
        'GDP2_十亿': '第二产业GDP_十亿',
        'SciExp_百万': '科技支出_百万',
        'Debt_百万': '政府债务余额_百万',
        'patent_apply': '专利申请受理数',
        'inv_patent_apply': '发明专利申请数',
        'patent_grant': '专利授权数',
        'inv_patent_grant': '发明专利授权数',
        'ln_patent_apply': 'ln_专利申请受理数',
        'ln_inv_patent': 'ln_发明专利申请数',
        'ln_patent_grant': 'ln_专利授权数',
        'ln_inv_patent_grant': 'ln_发明专利授权数',
    }
    panel = panel.rename(columns=rename_map)

    out_dir = 'cleaned_data'
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'final_regression_dataset.csv')
    panel.to_csv(out_file, index=False, encoding='utf-8-sig')

    print("\n" + "=" * 60)
    print("FINAL DATASET SUMMARY")
    print("=" * 60)
    print(f"  Total rows (City-Year): {len(panel)}")
    print(f"  Distinct cities:        {panel['城市'].nunique()}")
    print(f"  Year range:             {panel['年份'].min()} - {panel['年份'].max()}")
    print(f"  Output:                 {out_file}")
    print()
    print("Column coverage:")
    for c in panel.columns:
        non_null = panel[c].notna().sum()
        pct = non_null / len(panel) * 100
        print(f"  {c:30s}  {non_null:>5d}/{len(panel)}  ({pct:.0f}%)")

    print()
    print("Key variable descriptive stats:")
    key_cols = [c for c in [
        '当期财政缺口率', '滞后一期财政缺口率',
        '早期投资金额占比', '早期投资事件占比', '加权风险偏好指数',
        'ln_发明专利申请数', 'ln_专利申请受理数', 'ln_专利授权数',
        'ln_人均GDP', '金融深度', '第二产业占比', '科技支出占比',
        '外资占比', '债务率', 'ln_人口',
    ] if c in panel.columns]
    print(panel[key_cols].describe().round(4).to_string())

    return panel


if __name__ == "__main__":
    build_final_dataset()
