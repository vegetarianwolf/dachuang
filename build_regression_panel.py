# -*- coding: utf-8 -*-
"""
Updated build_regression_panel.py
Incorporates patent data (innovation output) per 新思路.md framework:
  财政约束(X) → 政府风险偏好(M) → 地区创新产出(Y)
"""
import os
import pandas as pd
import numpy as np

# ============================================================
# City -> Province AreaCode mapping
# Patent data uses 6-digit AreaCodes: province=XX0000, city=XXYY00
# ============================================================
CITY_PROVINCE_MAP = {
    # Province-level cities (直辖市) - map city name to patent AreaCode directly
    '北京': 110000, '天津': 120000, '上海': 310000, '重庆': 500000,
    
    # Cities that have their own patent data (副省级城市)
    '沈阳': 210100, '大连': 210200,
    '长春': 220100,
    '哈尔滨': 230100,
    '南京': 320100,
    '杭州': 330100, '宁波': 330200,
    '厦门': 350200,
    '济南': 370100, '青岛': 370200,
    '武汉': 420100,
    '广州': 440100, '深圳': 440300,
    '成都': 510100,
    '西安': 610100,
    
    # 河北省 130000
    '石家庄': 130000, '唐山': 130000, '秦皇岛': 130000, '邯郸': 130000,
    '邢台': 130000, '保定': 130000, '张家口': 130000, '沧州': 130000,
    '廊坊': 130000, '衡水': 130000,
    
    # 山西省 140000
    '太原': 140000, '大同': 140000, '临汾': 140000, '晋城': 140000,
    '忻州': 140000, '运城': 140000, '吕梁': 140000,
    
    # 内蒙古 150000
    '呼和浩特': 150000, '包头': 150000, '乌兰察布': 150000, '赤峰': 150000,
    '鄂尔多斯': 150000, '呼伦贝尔': 150000, '通辽': 150000,
    
    # 辽宁省 210000 (non-副省级)
    '鞍山': 210000, '丹东': 210000, '锦州': 210000, '辽阳': 210000,
    '朝阳': 210000, '辽源': 210000,
    
    # 吉林省 220000 (non-副省级)
    '吉林': 220000, '通化': 220000,
    
    # 黑龙江省 230000 (non-副省级)
    '牡丹江': 230000, '大庆': 230000, '佳木斯': 230000, '齐齐哈尔': 230000,
    '黑河': 230000,
    
    # 江苏省 320000 (non-副省级)
    '无锡': 320000, '徐州': 320000, '常州': 320000, '苏州': 320000,
    '南通': 320000, '连云港': 320000, '淮安': 320000, '盐城': 320000,
    '扬州': 320000, '镇江': 320000, '泰州': 320000, '宿迁': 320000,
    
    # 浙江省 330000 (non-副省级)
    '温州': 330000, '嘉兴': 330000, '湖州': 330000, '绍兴': 330000,
    '金华': 330000, '衢州': 330000, '舟山': 330000, '台州': 330000,
    '丽水': 330000,
    
    # 安徽省 340000
    '合肥': 340000, '芜湖': 340000, '蚌埠': 340000, '淮北': 340000,
    '铜陵': 340000, '安庆': 340000, '滁州': 340000, '六安': 340000,
    '马鞍山': 340000, '池州': 340000, '宣城': 340000, '亳州': 340000,
    '阜阳': 340000, '宿州': 340000, '黄山': 340000,
    
    # 福建省 350000 (non-副省级)
    '福州': 350000, '莆田': 350000, '泉州': 350000, '漳州': 350000,
    '南平': 350000, '龙岩': 350000, '宁德': 350000,
    
    # 江西省 360000
    '南昌': 360000, '九江': 360000, '赣州': 360000, '吉安': 360000,
    '上饶': 360000, '抚州': 360000, '新余': 360000,
    
    # 山东省 370000 (non-副省级)
    '淄博': 370000, '枣庄': 370000, '东营': 370000, '烟台': 370000,
    '潍坊': 370000, '泰安': 370000, '威海': 370000, '日照': 370000,
    '德州': 370000, '滨州': 370000, '菏泽': 370000, '临沂': 370000,
    
    # 河南省 410000
    '郑州': 410000, '开封': 410000, '洛阳': 410000, '平顶山': 410000,
    '安阳': 410000, '新乡': 410000, '焦作': 410000, '濮阳': 410000,
    '许昌': 410000, '漯河': 410000, '三门峡': 410000, '南阳': 410000,
    '商丘': 410000, '周口': 410000, '鹤壁': 410000,
    
    # 湖北省 420000 (non-副省级)
    '宜昌': 420000, '襄阳': 420000, '十堰': 420000, '荆州': 420000,
    '荆门': 420000, '孝感': 420000, '黄冈': 420000, '咸宁': 420000,
    '鄂州': 420000,
    
    # 湖南省 430000
    '长沙': 430000, '株洲': 430000, '湘潭': 430000, '衡阳': 430000,
    '邵阳': 430000, '岳阳': 430000, '常德': 430000, '益阳': 430000,
    '郴州': 430000,
    
    # 广东省 440000 (non-副省级)
    '珠海': 440000, '汕头': 440000, '佛山': 440000, '江门': 440000,
    '湛江': 440000, '茂名': 440000, '肇庆': 440000, '惠州': 440000,
    '梅州': 440000, '河源': 440000, '清远': 440000, '东莞': 440000,
    '中山': 440000, '潮州': 440000, '揭阳': 440000, '云浮': 440000,
    
    # 广西壮族自治区 450000
    '南宁': 450000, '柳州': 450000, '北海': 450000, '钦州': 450000,
    '贺州': 450000,
    
    # 海南省 460000
    '海口': 460000, '三亚': 460000,
    
    # 四川省 510000 (non-副省级)
    '德阳': 510000, '绵阳': 510000, '宜宾': 510000, '泸州': 510000,
    '乐山': 510000, '自贡': 510000, '攀枝花': 510000, '广安': 510000,
    '遂宁': 510000, '雅安': 510000, '眉山': 510000, '巴中': 510000,
    
    # 贵州省 520000
    '贵阳': 520000, '六盘水': 520000, '遵义': 520000, '安顺': 520000,
    '毕节': 520000, '铜仁': 520000,
    
    # 云南省 530000
    '昆明': 530000, '曲靖': 530000, '玉溪': 530000,
    
    # 西藏自治区 540000
    '拉萨': 540000, '山南': 540000,
    
    # 陕西省 610000 (non-副省级)
    '咸阳': 610000, '宝鸡': 610000, '渭南': 610000, '铜川': 610000,
    '榆林': 610000, '安康': 610000,
    
    # 甘肃省 620000
    '兰州': 620000, '天水': 620000, '白银': 620000, '定西': 620000,
    '张掖': 620000, '嘉峪关': 620000, '武威': 620000, '陇南': 620000,
    
    # 青海省 630000
    '西宁': 630000,
    
    # 宁夏回族自治区 640000
    '银川': 640000, '吴忠': 640000, '石嘴山': 640000,
    
    # 新疆维吾尔自治区 650000
    '乌鲁木齐': 650000, '克拉玛依': 650000, '吐鲁番': 650000,
}

# 副省级城市 AreaCodes (have their own city-level patent data)
CITY_LEVEL_PATENT_CODES = {
    210100, 210200, 220100, 230100, 320100, 330100, 330200,
    350200, 370100, 370200, 420100, 440100, 440300, 510100, 610100,
    # 直辖市 also have city-level data
    110000, 120000, 310000, 500000,
}


def load_patent_data():
    """Load and process patent data from CSMAR dataset."""
    patent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        '分地区国内三种专利申请受理授权数232514400(仅供南开大学使用)(1)')
    csv_path = os.path.join(patent_dir, 'INN_DAREAARGY.csv')
    
    df = pd.read_csv(csv_path, encoding='gb18030', skiprows=[1, 2])
    df = df[pd.to_numeric(df['SgnYear'], errors='coerce').notnull()].copy()
    df['SgnYear'] = df['SgnYear'].astype(int)
    df['Accumulated'] = pd.to_numeric(df['Accumulated'], errors='coerce')
    
    # Filter to 2013-2024
    df = df[(df['SgnYear'] >= 2013) & (df['SgnYear'] <= 2024)]
    
    # Create pivot: for each (AreaCode, Year), get patent counts
    # StatisticalTypeCode: 1=申请 (covers all years 2013-2024)
    #                      2=受理 (only 2013-2016, incomplete)
    #                      3=授权 (covers all years 2013-2024)
    # PatentTypeCode: 1=总计, 2=发明, 3=实用新型, 4=外观设计
    
    results = []
    for area_code in df['AreaCode'].unique():
        for year in df[df['AreaCode'] == area_code]['SgnYear'].unique():
            subset = df[(df['AreaCode'] == area_code) & (df['SgnYear'] == year)]
            
            row = {'AreaCode': area_code, 'Year': year}
            
            # 申请-总计 (专利申请数)
            val = subset[(subset['StatisticalTypeCode'] == 1) & (subset['PatentTypeCode'] == 1)]['Accumulated']
            row['patent_apply'] = val.values[0] if len(val) > 0 else np.nan
            
            # 申请-发明 (发明专利申请数)
            val = subset[(subset['StatisticalTypeCode'] == 1) & (subset['PatentTypeCode'] == 2)]['Accumulated']
            row['inv_patent_apply'] = val.values[0] if len(val) > 0 else np.nan
            
            # 授权-总计 (专利授权数)
            val = subset[(subset['StatisticalTypeCode'] == 3) & (subset['PatentTypeCode'] == 1)]['Accumulated']
            row['patent_grant'] = val.values[0] if len(val) > 0 else np.nan
            
            # 授权-发明 (发明专利授权数)
            val = subset[(subset['StatisticalTypeCode'] == 3) & (subset['PatentTypeCode'] == 2)]['Accumulated']
            row['inv_patent_grant'] = val.values[0] if len(val) > 0 else np.nan
            
            results.append(row)
    
    patent_pivot = pd.DataFrame(results)
    print(f"Patent data loaded: {len(patent_pivot)} area-year observations")
    return patent_pivot


def merge_patent_data(city_year_panel, patent_pivot):
    """Merge patent data into city-year panel using city-level data where available,
    falling back to province-level data."""
    
    merged_rows = []
    missing_cities = set()
    
    for _, row in city_year_panel.iterrows():
        city = row['City']
        year = row['Year']
        
        patent_row = {'patent_apply': np.nan, 'inv_patent_apply': np.nan,
                      'patent_grant': np.nan, 'inv_patent_grant': np.nan,
                      'patent_source': ''}
        
        if city not in CITY_PROVINCE_MAP:
            missing_cities.add(city)
            merged_rows.append(patent_row)
            continue
        
        area_code = CITY_PROVINCE_MAP[city]
        
        # Determine source label
        if area_code in CITY_LEVEL_PATENT_CODES:
            patent_row['patent_source'] = '城市级'
        else:
            patent_row['patent_source'] = '省级'
        
        # Look up patent data
        match = patent_pivot[(patent_pivot['AreaCode'] == area_code) & (patent_pivot['Year'] == year)]
        if len(match) > 0:
            for col in ['patent_apply', 'inv_patent_apply', 'patent_grant', 'inv_patent_grant']:
                patent_row[col] = match.iloc[0][col]
        
        merged_rows.append(patent_row)
    
    if missing_cities:
        print(f"WARNING: {len(missing_cities)} cities not found in mapping: {missing_cities}")
    
    patent_df = pd.DataFrame(merged_rows)
    
    # Compute log transforms: ln(x + 1)
    for col in ['patent_apply', 'inv_patent_apply', 'patent_grant', 'inv_patent_grant']:
        patent_df['ln_' + col] = np.log(patent_df[col] + 1)
    
    result = pd.concat([city_year_panel.reset_index(drop=True), patent_df.reset_index(drop=True)], axis=1)
    
    matched = patent_df['patent_apply'].notna().sum()
    print(f"Patent data merged: {matched}/{len(result)} rows have patent data")
    city_level = (patent_df['patent_source'] == '城市级').sum()
    prov_level = (patent_df['patent_source'] == '省级').sum()
    print(f"  City-level: {city_level}, Province-level: {prov_level}")
    
    return result


def build_final_dataset():
    # 1. Load the cleaned PE dataset
    pe_file = 'cleaned_data/PE_investment_events_cleaned.csv'
    print(f"Loading {pe_file}...")
    pe_df = pd.read_csv(pe_file)
    
    # 2. Filter to 2013 and onwards
    pe_df = pe_df[pe_df['Year'] >= 2013].copy()
    
    # 3. Load the CSMAR SRDI Name Roster
    csmar_file = 'csmar_data_export/SRDI_EntIdentInfo.csv'
    print(f"Loading {csmar_file}...")
    srdi_df = pd.read_csv(csmar_file, usecols=['InstitutionName'])
    
    # Store all unique SRDI names
    srdi_names = set(srdi_df['InstitutionName'].dropna().astype(str).str.strip())
    
    # 4. Flag PE investments
    pe_df['Target_Company'] = pe_df['Target_Company'].fillna('')
    pe_df['Is_SRDI'] = pe_df['Target_Company'].apply(lambda x: 1 if x in srdi_names else 0)
    
    matches = pe_df['Is_SRDI'].sum()
    print(f"Matched {matches} PE investments to SRDI enterprises out of {len(pe_df)} records.")
    
    # 5. Collapse to Panel (City - Year)
    print("\nCollapsing PE events to City-Year panel...")
    pe_panel_ready = pe_df.dropna(subset=['Year', 'City']).copy()
    pe_panel_ready['Inv_Amount_RMB_M'] = pd.to_numeric(pe_panel_ready['Inv_Amount_RMB_M'], errors='coerce').fillna(0)
    
    grouped = pe_panel_ready.groupby(['City', 'Year'])
    
    def calculate_metrics(group):
        total_amt = group['Inv_Amount_RMB_M'].sum()
        total_cnt = len(group)
        
        srdi_mask = group['Is_SRDI'] == 1
        srdi_amt = group.loc[srdi_mask, 'Inv_Amount_RMB_M'].sum()
        srdi_cnt = srdi_mask.sum()
        
        early_mask = group['投资阶段'].astype(str).str.contains('种子期|初创期|天使轮|A轮', na=False)
        early_amt = group.loc[early_mask, 'Inv_Amount_RMB_M'].sum()
        
        ratio_amt = srdi_amt / total_amt if total_amt > 0 else 0
        ratio_cnt = srdi_cnt / total_cnt if total_cnt > 0 else 0
        early_ratio = early_amt / total_amt if total_amt > 0 else 0
        
        return pd.Series({
            'Total_Inv_Amount': total_amt,
            'Total_Inv_Count': total_cnt,
            'SRDI_Inv_Amount': srdi_amt,
            'SRDI_Inv_Count': srdi_cnt,
            'Early_Stage_Amount': early_amt,
            'SRDI_Investment_Ratio_Amt': ratio_amt,
            'SRDI_Investment_Ratio_Count': ratio_cnt,
            'Early_Stage_Ratio': early_ratio
        })
    
    city_year_pe = grouped.apply(calculate_metrics).reset_index()
    
    # 6. Bring in Fiscal Data
    fiscal_file = 'cleaned_data/city_fiscal_panel.csv'
    print(f"Loading {fiscal_file}...")
    fiscal_df = pd.read_csv(fiscal_file)
    
    city_year_pe['Year'] = city_year_pe['Year'].astype(int)
    fiscal_df['Year'] = pd.to_numeric(fiscal_df['Year'], errors='coerce')
    fiscal_df = fiscal_df.dropna(subset=['Year'])
    fiscal_df['Year'] = fiscal_df['Year'].astype(int)
    
    print("Merging Fiscal Panel with PE Panel...")
    final_panel = pd.merge(city_year_pe, fiscal_df, on=['City', 'Year'], how='inner')
    
    # Lead fiscal gap
    print("Calculating Lead Variables (t+1)...")
    final_panel = final_panel.sort_values(['City', 'Year'])
    
    fiscal_lead = fiscal_df[['City', 'Year', 'Fiscal_Gap']].copy()
    fiscal_lead['Year'] = fiscal_lead['Year'] - 1
    fiscal_lead = fiscal_lead.rename(columns={'Fiscal_Gap': 'F1_Fiscal_Gap'})
    
    final_panel = pd.merge(final_panel, fiscal_lead, on=['City', 'Year'], how='left')
    
    # 7. NEW: Load and merge patent data
    print("\n--- Loading Patent Data (Innovation Output) ---")
    patent_pivot = load_patent_data()
    final_panel = merge_patent_data(final_panel, patent_pivot)
    
    # 8. Rename columns to Chinese
    rename_map = {
        'City': '城市',
        'Year': '年份',
        
        # Original columns mappings to Chinese
        'Fiscal_Expenditure': '一般公共预算支出',
        'Fiscal_Revenue': '一般公共预算收入',
        'Fiscal_Gap': '当期财政资金缺口',
        'F1_Fiscal_Gap': '提前一期财政资金缺口',
        
        'Early_Stage_Ratio': '早期投资占比',
        'Early_Stage_Amount': '早期投资金额',
        
        'Total_Inv_Amount': '全部基金投资总金额',
        'Total_Inv_Count': '全部基金投资总次数',
        'SRDI_Inv_Amount': '专精特新企业投资金额',
        'SRDI_Inv_Count': '专精特新企业投资次数',
        'SRDI_Investment_Ratio_Amt': '专精特新投资金额占比',
        'SRDI_Investment_Ratio_Count': '专精特新投资次数占比',
        
        # New patent data columns to Chinese
        'patent_apply': '专利申请受理数',
        'ln_patent_apply': 'ln_专利申请受理数',
        'inv_patent_apply': '发明专利申请数',
        'ln_inv_patent_apply': 'ln_发明专利申请数',
        'patent_grant': '专利授权数',
        'ln_patent_grant': 'ln_专利授权数',
        'inv_patent_grant': '发明专利授权数',
        'ln_inv_patent_grant': 'ln_发明专利授权数',
        'patent_source': '专利数据来源'
    }
    final_panel = final_panel.rename(columns=rename_map)
    
    # 9. Reorder columns per framework: 城市→年份→Y→X→M→Controls
    col_order = [
        # Identifiers
        '城市', '年份',
        # Y: Innovation Output (被解释变量)
        '专利申请受理数', 'ln_专利申请受理数', 
        '发明专利申请数', 'ln_发明专利申请数',
        '专利授权数', 'ln_专利授权数',
        '发明专利授权数', 'ln_发明专利授权数',
        '专利数据来源',
        # X: Fiscal Constraint (核心解释变量)
        '一般公共预算支出', '一般公共预算收入',
        '当期财政资金缺口', '提前一期财政资金缺口',
        # M: Risk Preference (机制变量)
        '早期投资占比', '早期投资金额',
        # Controls: Fund-level
        '全部基金投资总金额', '全部基金投资总次数',
        '专精特新企业投资金额', '专精特新企业投资次数',
        '专精特新投资金额占比', '专精特新投资次数占比',
    ]
    # Only include columns that actually exist
    col_order = [c for c in col_order if c in final_panel.columns]
    # Add any remaining columns not in col_order
    remaining = [c for c in final_panel.columns if c not in col_order]
    final_panel = final_panel[col_order + remaining]
    
    # 10. Output
    out_dir = 'cleaned_data'
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'final_regression_dataset.csv')
    final_panel.to_csv(out_file, index=False, encoding='utf-8-sig')
    
    print(f"\n{'='*60}")
    print(f"Final Dataset Built (新思路 Framework)")
    print(f"{'='*60}")
    print(f"Total Rows (City-Year observations): {len(final_panel)}")
    print(f"Total Columns: {len(final_panel.columns)}")
    print(f"Columns: {list(final_panel.columns)}")
    print(f"\nInnovation Output Coverage:")
    print(f"  patent_apply non-null: {final_panel['专利申请受理数'].notna().sum()}/{len(final_panel)}")
    print(f"  inv_patent_apply non-null: {final_panel['发明专利申请数'].notna().sum()}/{len(final_panel)}")
    print(f"Output saved to: {out_file}")


if __name__ == "__main__":
    build_final_dataset()
