import pandas as pd
import numpy as np

# 1. Debug R&D data
rd = pd.read_csv('CNRDS专利数据包/上市公司研发费用/上市公司研发支出/上市公司研发支出.csv',
                 skiprows=[1], encoding='utf-8-sig')
rd['Scode'] = pd.to_numeric(rd['Scode'], errors='coerce')
rd['Year'] = pd.to_numeric(rd['Year'], errors='coerce')
rd = rd.dropna(subset=['Scode','Year'])
rd['Scode'] = rd['Scode'].astype(int)
rd['Year'] = rd['Year'].astype(int)

# Use R&Deapoinr (研发支出占营业收入比例)
rd['RD'] = pd.to_numeric(rd['R&Deapoinr'], errors='coerce')
rd_clean = rd[['Scode','Year','RD']].dropna()
rd_clean = rd_clean[(rd_clean['Year'] >= 2010) & (rd_clean['Year'] <= 2020)]
print(f"R&D data: {len(rd_clean)} rows, {rd_clean['Scode'].nunique()} firms")
print(f"Year range: {rd_clean['Year'].min()}-{rd_clean['Year'].max()}")

# Also use R&Dexp (研发支出) and R&Dpr
rd['RD_total'] = pd.to_numeric(rd['R&Dexp'], errors='coerce')
rd_total = rd[['Scode','Year','RD_total']].dropna()
rd_total = rd_total[(rd_total['Year'] >= 2010) & (rd_total['Year'] <= 2020)]
print(f"R&D total expenditure: {len(rd_total)} rows, {rd_total['Scode'].nunique()} firms")

# 2. Debug city matching
mapping = pd.read_csv('cleaned_data/firm_city_mapping.csv', encoding='utf-8-sig')
print(f"\nMapping: {len(mapping)} firms")
print("Map city samples:", sorted(mapping['city_clean'].unique())[:20])

# Check fiscal cities
fiscal_rev = pd.read_csv('地级市财政收入.csv', encoding='utf-8-sig')
rev_cities = set(c.split(':')[-1].strip() for c in fiscal_rev.columns[1:])
map_cities = set(mapping['city_clean'].unique())
overlap = map_cities & rev_cities
print(f"\nMap cities: {len(map_cities)}")
print(f"Fiscal cities: {len(rev_cities)}")
print(f"Overlap: {len(overlap)}")
missing = sorted(map_cities - rev_cities)
print(f"Missing ({len(missing)}): {missing[:30]}")

# 3. Check if we can get ALL listed firms (not just SRDI)
# Count patent firms that are in CNRDS but not in our mapping
patent = pd.read_csv(
    'CNRDS专利数据包/上市公司专利申请与获得/上市公司专利申请情况/上市公司专利申请情况.csv',
    skiprows=[1], encoding='utf-8-sig'
)
patent = patent[patent['Ftyp'] == '上市公司本身']
patent['Scode'] = pd.to_numeric(patent['Scode'], errors='coerce').dropna().astype(int)
all_patent_firms = set(patent['Scode'].unique())
mapped_firms = set(mapping['Scode'].unique())
print(f"\nTotal firms in patent data: {len(all_patent_firms)}")
print(f"Mapped firms: {len(mapped_firms)}")
print(f"Patent firms also in mapping: {len(all_patent_firms & mapped_firms)}")
print(f"Patent firms NOT in mapping: {len(all_patent_firms - mapped_firms)}")

# 4. Try to get all listed company info from SRDI_EntInfo_Full
# including non-SRDI firms
info = pd.read_csv('csmar_data_export/SRDI_EntInfo_Full.csv',
                   encoding='utf-8-sig', low_memory=False, on_bad_lines='skip',
                   usecols=['InstitutionID','InstitutionName','CityName','ProvinceName',
                           'GBCode2017MainClass','EnterpriseNature'])
listed_all = info[info['EnterpriseNature'].str.contains('上市', na=False)]
print(f"\nAll listed companies in EntInfo: {listed_all['InstitutionID'].nunique()}")
mfg_listed = listed_all[listed_all['GBCode2017MainClass'].str.startswith('C', na=False)]
print(f"Listed manufacturing: {mfg_listed['InstitutionID'].nunique()}")

# Get ISIN/Symbol
ident = pd.read_csv('csmar_data_export/SRDI_EntIdentInfo.csv', encoding='utf-8-sig', low_memory=False)
# Also get firms where IsListed=0 but they might still be listed
# The EntInfo has InstitutionID which we can try to link
all_listed_ids = set(listed_all['InstitutionID'].unique())
ident_listed = ident[ident['InstitutionID'].isin(all_listed_ids)]
with_symbol = ident_listed[ident_listed['Symbol'].notna()]
print(f"Listed firms with symbol via Ident: {with_symbol['Symbol'].nunique()}")

# Alternative: use EntInfo for city mapping directly
# Many companies have InstitutionID but no Symbol
print(f"\nNon-SRDI listed mfg firms without symbol: need CSMAR or other source")
