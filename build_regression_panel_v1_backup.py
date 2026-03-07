"""
build_regression_panel.py  (alternative_path branch)
=====================================================
按照 新思路.md 的方案重建 final_regression_dataset.csv:
  - 被解释变量: 地区创新产出 (专利数据, 省级 / 副省级城市)
  - 核心解释变量: 财政缺口率
  - 机制变量: 早期投资占比 / 加权风险偏好指数 等
  - 不再使用专精特新(SRDI)匹配, 不再限制 Year >= 2013
"""

import os
import pandas as pd
import numpy as np

# =====================================================================
# 城市 -> 省份 映射 (用于匹配省级专利数据)
# =====================================================================
# 专利数据中含有的城市级数据 (副省级城市 / 直辖市)
PATENT_CITY_LIST = [
    '北京', '天津', '上海', '重庆',
    '广州', '武汉', '西安', '沈阳', '大连', '哈尔滨',
    '青岛', '长春', '南京', '杭州', '济南', '成都',
    '厦门', '深圳', '宁波',
]

# PE/财政数据中的城市名 -> 专利数据中的地区名 (城市级专利数据直接匹配)
CITY_TO_PATENT_AREA = {
    '北京': '北京市', '天津': '天津市', '上海': '上海市', '重庆': '重庆市',
    '广州': '广州市', '深圳': '深圳市', '武汉': '武汉市', '西安': '西安市',
    '沈阳': '沈阳市', '大连': '大连市', '哈尔滨': '哈尔滨市', '青岛': '青岛市',
    '长春': '长春市', '南京': '南京市', '杭州': '杭州市', '济南': '济南市',
    '成都': '成都市', '厦门': '厦门市', '宁波': '宁波市',
}

PROVINCE_NAME_MAP = {
    '北京市': '北京市', '天津市': '天津市', '上海市': '上海市', '重庆市': '重庆市',
    '河北省': '河北省', '山西省': '山西省', '内蒙古自治区': '内蒙古自治区',
    '辽宁省': '辽宁省', '吉林省': '吉林省', '黑龙江省': '黑龙江省',
    '江苏省': '江苏省', '浙江省': '浙江省', '安徽省': '安徽省', '福建省': '福建省',
    '江西省': '江西省', '山东省': '山东省', '河南省': '河南省', '湖北省': '湖北省',
    '湖南省': '湖南省', '广东省': '广东省', '广西壮族自治区': '广西壮族自治区',
    '海南省': '海南省', '四川省': '四川省', '贵州省': '贵州省', '云南省': '云南省',
    '西藏自治区': '西藏自治区', '陕西省': '陕西省', '甘肃省': '甘肃省',
    '青海省': '青海省', '宁夏回族自治区': '宁夏回族自治区',
    '新疆维吾尔自治区': '新疆维吾尔自治区',
    '广西': '广西壮族自治区', '内蒙古': '内蒙古自治区',
    '西藏': '西藏自治区', '宁夏': '宁夏回族自治区', '新疆': '新疆维吾尔自治区',
}


def build_city_province_map(pe_df):
    """从 PE 数据的 '地区' 字段自动推导城市->省份(专利地区)映射"""
    mapping = dict(CITY_TO_PATENT_AREA)

    for loc in pe_df['地区'].dropna().unique():
        parts = str(loc).split('|')
        if len(parts) >= 3:
            province_raw = parts[1].strip()
            city_raw = parts[2].strip()
            city_base = city_raw
            for suf in ['市', '地区', '自治州', '盟']:
                city_base = city_base.replace(suf, '')
            if city_base and city_base not in mapping:
                prov_match = PROVINCE_NAME_MAP.get(province_raw)
                if prov_match:
                    mapping[city_base] = prov_match
        elif len(parts) == 2:
            province_raw = parts[1].strip()
            city_base = province_raw.replace('市', '')
            if city_base not in mapping:
                prov_match = PROVINCE_NAME_MAP.get(province_raw)
                if prov_match:
                    mapping[city_base] = prov_match
    return mapping


# =====================================================================
# 1. 加载专利数据
# =====================================================================
def load_patent_data():
    fp = '分地区国内三种专利申请受理授权数232514400(仅供南开大学使用)(1)/INN_DAREAARGY.csv'
    df = pd.read_csv(fp, encoding='gbk', header=0)
    df = df.iloc[2:].reset_index(drop=True)
    df.columns = ['Year', 'AreaCode', 'AreaName', 'StatTypeCode', 'StatType',
                  'PatTypeCode', 'PatType', 'Accumulated']
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Accumulated'] = pd.to_numeric(df['Accumulated'], errors='coerce')
    df = df.dropna(subset=['Year', 'Accumulated'])
    df['Year'] = df['Year'].astype(int)
    return df


def _get_application_data(df, pat_type):
    """
    获取专利申请数据: 优先使用 "申请"(2010-2024), 不足部分用 "受理"(1985-2016) 补充.
    对于重叠年份(2010-2016), 优先取 "申请" 以保持与2017+一致.
    """
    apply_df = df[(df['StatType'] == '申请') & (df['PatType'] == pat_type)][
        ['AreaName', 'Year', 'Accumulated']].copy()
    accept_df = df[(df['StatType'] == '受理') & (df['PatType'] == pat_type)][
        ['AreaName', 'Year', 'Accumulated']].copy()

    # 把早于2010年的"受理"数据补上 (2010+全部用"申请")
    early_accept = accept_df[~accept_df.set_index(['AreaName', 'Year']).index.isin(
        apply_df.set_index(['AreaName', 'Year']).index)]
    combined = pd.concat([apply_df, early_accept], ignore_index=True)
    return combined


def _get_grant_data(df, pat_type):
    """
    获取专利授权数据.
    对于 '总计' 类型: 如果原始数据有"总计"就直接用, 没有的年份则手动求和(发明+实用新型+外观设计).
    """
    if pat_type != '总计':
        return df[(df['StatType'] == '授权') & (df['PatType'] == pat_type)][
            ['AreaName', 'Year', 'Accumulated']].copy()

    # 先取已有的"总计"
    total_df = df[(df['StatType'] == '授权') & (df['PatType'] == '总计')][
        ['AreaName', 'Year', 'Accumulated']].copy()

    # 对所有 授权-非总计 的记录按 (AreaName, Year) 求和, 作为补充
    detail_types = ['发明', '实用新型', '外观设计']
    detail_df = df[(df['StatType'] == '授权') & (df['PatType'].isin(detail_types))].copy()
    detail_sum = detail_df.groupby(['AreaName', 'Year'])['Accumulated'].sum().reset_index()

    # 没有"总计"行的, 用手动求和补上
    existing_keys = set(zip(total_df['AreaName'], total_df['Year']))
    supplement = detail_sum[~detail_sum.apply(
        lambda r: (r['AreaName'], r['Year']) in existing_keys, axis=1)]

    combined = pd.concat([total_df, supplement], ignore_index=True)
    return combined


def build_patent_panel(patent_raw):
    """构建 地区-年 专利面板 (ln 转换).
    说明: "受理" 覆盖 1985-2016, "申请" 覆盖 2010-2024, "授权" 覆盖 1985-2024.
          对于专利申请类指标, 2010+ 使用"申请", <2010 使用"受理".
          对于授权 "总计", 2017+ 无"总计"行的年份手动求和(发明+实用新型+外观设计).
    """
    df = patent_raw.copy()

    inv_apply = _get_application_data(df, '发明').rename(columns={'Accumulated': 'inv_patent_apply'})
    total_apply = _get_application_data(df, '总计').rename(columns={'Accumulated': 'patent_apply'})

    total_grant = _get_grant_data(df, '总计').rename(columns={'Accumulated': 'patent_grant'})
    inv_grant = df[(df['StatType'] == '授权') & (df['PatType'] == '发明')][
        ['AreaName', 'Year', 'Accumulated']].rename(columns={'Accumulated': 'inv_patent_grant'})

    panel = total_apply.merge(inv_apply, on=['AreaName', 'Year'], how='outer')
    panel = panel.merge(total_grant, on=['AreaName', 'Year'], how='outer')
    panel = panel.merge(inv_grant, on=['AreaName', 'Year'], how='outer')

    for col in ['patent_apply', 'inv_patent_apply', 'patent_grant', 'inv_patent_grant']:
        panel[col] = panel[col].fillna(0)

    panel['ln_patent_apply'] = np.log(panel['patent_apply'] + 1)
    panel['ln_inv_patent'] = np.log(panel['inv_patent_apply'] + 1)
    panel['ln_patent_grant'] = np.log(panel['patent_grant'] + 1)
    panel['ln_inv_patent_grant'] = np.log(panel['inv_patent_grant'] + 1)

    return panel


# =====================================================================
# 2. 加载 PE 数据并聚合
# =====================================================================
def load_and_aggregate_pe():
    pe_file = 'cleaned_data/PE_investment_events_cleaned.csv'
    print(f"  Loading {pe_file} ...")
    pe_df = pd.read_csv(pe_file, low_memory=False)

    # *** 不再限制 Year >= 2013 ***
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
# 3. 主构建函数
# =====================================================================
def build_final_dataset():
    # --- 3.1 专利面板 ---
    print("=" * 60)
    print("[1/4] Loading patent data ...")
    patent_raw = load_patent_data()
    patent_panel = build_patent_panel(patent_raw)
    print(f"  Patent panel: {len(patent_panel)} rows, "
          f"years {patent_panel['Year'].min()}-{patent_panel['Year'].max()}")

    # --- 3.2 PE 面板 ---
    print("=" * 60)
    print("[2/4] Loading & aggregating PE investment data ...")
    pe_df, city_year_pe = load_and_aggregate_pe()
    print(f"  City-Year PE panel: {len(city_year_pe)} rows, "
          f"{city_year_pe['City'].nunique()} cities")

    # --- 3.3 财政面板 ---
    print("=" * 60)
    print("[3/4] Loading fiscal data ...")
    fiscal_file = 'cleaned_data/city_fiscal_panel.csv'
    fiscal_df = pd.read_csv(fiscal_file)
    fiscal_df['Year'] = pd.to_numeric(fiscal_df['Year'], errors='coerce')
    fiscal_df = fiscal_df.dropna(subset=['Year'])
    fiscal_df['Year'] = fiscal_df['Year'].astype(int)
    print(f"  Fiscal panel: {len(fiscal_df)} rows, "
          f"{fiscal_df['City'].nunique()} cities")

    # --- 3.4 合并 ---
    print("=" * 60)
    print("[4/4] Merging panels ...")
    city_year_pe['Year'] = city_year_pe['Year'].astype(int)
    panel = pd.merge(city_year_pe, fiscal_df, on=['City', 'Year'], how='inner')
    print(f"  After PE x Fiscal merge: {len(panel)} rows")

    # 滞后一期财政缺口 (t-1)
    panel = panel.sort_values(['City', 'Year'])
    panel['L1_Fiscal_Gap'] = panel.groupby('City')['Fiscal_Gap'].shift(1)

    # 匹配专利数据 (城市 -> 专利地区)
    city_province_map = build_city_province_map(pe_df)

    def city_to_patent_area(city_name):
        base = city_name
        for suf in ['市', '地区', '自治州']:
            base = base.replace(suf, '')
        return city_province_map.get(base, None)

    panel['Patent_Area'] = panel['City'].apply(city_to_patent_area)
    panel = panel.merge(
        patent_panel[['AreaName', 'Year',
                       'patent_apply', 'inv_patent_apply', 'patent_grant', 'inv_patent_grant',
                       'ln_patent_apply', 'ln_inv_patent', 'ln_patent_grant', 'ln_inv_patent_grant']],
        left_on=['Patent_Area', 'Year'],
        right_on=['AreaName', 'Year'],
        how='left'
    )
    matched = panel['ln_inv_patent'].notna().sum()
    print(f"  Patent matched: {matched}/{len(panel)} ({matched/len(panel)*100:.1f}%)")

    panel = panel.drop(columns=['AreaName', 'Patent_Area'], errors='ignore')

    # ---------- 列名翻译 ----------
    rename_map = {
        'City': '城市',
        'Year': '年份',
        'Total_Inv_Amount': '全部基金投资总金额',
        'Total_Inv_Count': '全部基金投资总次数',
        'Early_Stage_Amount': '早期投资金额',
        'Early_Stage_Count': '早期投资次数',
        'Early_Stage_Ratio': '早期投资金额占比',
        'Early_Deal_Ratio': '早期投资事件占比',
        'Risk_Index': '加权风险偏好指数',
        'Fiscal_Expenditure': '财政支出',
        'Fiscal_Revenue': '财政收入',
        'Fiscal_Gap': '当期财政缺口',
        'L1_Fiscal_Gap': '滞后一期财政缺口',
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

    # ---------- 输出 ----------
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
    print("Columns:")
    for c in panel.columns:
        non_null = panel[c].notna().sum()
        print(f"  {c:30s}  non-null: {non_null}/{len(panel)}")
    print()
    print("Descriptive statistics (key variables):")
    key_cols = [c for c in ['早期投资金额占比', '早期投资事件占比', '加权风险偏好指数',
                            '当期财政缺口', '滞后一期财政缺口',
                            'ln_发明专利申请数', 'ln_专利申请受理数', 'ln_专利授权数']
                if c in panel.columns]
    print(panel[key_cols].describe().round(3).to_string())

    return panel


if __name__ == "__main__":
    build_final_dataset()
