# -*- coding: utf-8 -*-
import pandas as pd
import os

patent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
    '分地区国内三种专利申请受理授权数232514400(仅供南开大学使用)(1)')
csv_path = os.path.join(patent_dir, 'INN_DAREAARGY.csv')

df = pd.read_csv(csv_path, encoding='gb18030', skiprows=[1, 2])
df = df[pd.to_numeric(df['SgnYear'], errors='coerce').notnull()].copy()
df['SgnYear'] = df['SgnYear'].astype(int)
df = df[(df['SgnYear'] >= 2013) & (df['SgnYear'] <= 2024)]

with open('debug_patent.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total rows after filter: {len(df)}\n")
    f.write(f"Unique AreaCodes: {sorted(df['AreaCode'].unique())}\n")
    f.write(f"Unique Years: {sorted(df['SgnYear'].unique())}\n")
    
    # Check areas * years
    areas = df['AreaCode'].unique()
    years = df['SgnYear'].unique()
    f.write(f"\nAreas: {len(areas)}, Years: {len(years)}\n")
    f.write(f"Expected combos: {len(areas) * len(years)}\n")
    
    # Check province 440000 (广东) for year 2020
    subset = df[(df['AreaCode'] == 440000) & (df['SgnYear'] == 2020)]
    f.write(f"\n广东省 2020 data ({len(subset)} rows):\n")
    for _, row in subset.iterrows():
        f.write(f"  TypeCode={row['StatisticalTypeCode']}, PatentCode={row['PatentTypeCode']}, Val={row['Accumulated']}\n")
    
    # Check what StatisticalTypeCode=2 (受理) has
    apply_data = df[df['StatisticalTypeCode'] == 2]
    f.write(f"\n受理 (TypeCode=2) rows: {len(apply_data)}\n")
    f.write(f"受理 unique years: {sorted(apply_data['SgnYear'].unique())}\n")
    
    # Check TypeCode=1 (申请)
    apply1_data = df[df['StatisticalTypeCode'] == 1]
    f.write(f"\n申请 (TypeCode=1) rows: {len(apply1_data)}\n")
    f.write(f"申请 unique years: {sorted(apply1_data['SgnYear'].unique())}\n")
    
    # Check TypeCode=3 (授权)
    grant_data = df[df['StatisticalTypeCode'] == 3]
    f.write(f"\n授权 (TypeCode=3) rows: {len(grant_data)}\n")
    f.write(f"授权 unique years: {sorted(grant_data['SgnYear'].unique())}\n")
    
    # Missing city
    reg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cleaned_data', 'final_regression_dataset.csv')
    from build_regression_panel import CITY_PROVINCE_MAP
    
    reg_df = pd.read_csv(reg_path, encoding='utf-8-sig')
    cities = reg_df.iloc[:, 0].unique()
    unmapped = [c for c in cities if c not in CITY_PROVINCE_MAP]
    f.write(f"\nUnmapped cities: {unmapped}\n")

print("Written to debug_patent.txt")
