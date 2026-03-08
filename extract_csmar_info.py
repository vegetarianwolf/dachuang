"""提取CSMAR行业代码并合并到面板"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Read CSMAR
stk = pd.read_excel(
    'CNRDS专利数据包/【赠品】上市公司基本信息年度表(csmar，2024)/STK_LISTEDCOINFOANL.xlsx',
    skiprows=[1, 2],
    engine='openpyxl',
    usecols=['Symbol', 'EndDate', 'IndustryCodeC', 'LISTINGDATE', 'LISTINGSTATE', 'CITY', 'PROVINCE'],
    dtype=str
)
print(f'Total rows: {len(stk)}')

stk['Scode'] = pd.to_numeric(stk['Symbol'], errors='coerce')
stk['EndDate'] = pd.to_datetime(stk['EndDate'], errors='coerce')
stk['Year'] = stk['EndDate'].dt.year
stk['LISTINGDATE'] = pd.to_datetime(stk['LISTINGDATE'], errors='coerce')
stk['listing_year'] = stk['LISTINGDATE'].dt.year
stk = stk.dropna(subset=['Scode', 'Year'])
stk['Scode'] = stk['Scode'].astype(int)
stk['Year'] = stk['Year'].astype(int)

stk['csrc_ind'] = stk['IndustryCodeC'].astype(str).str.strip()
mfg = stk[stk['csrc_ind'].str.startswith('C', na=False)].copy()
print(f'Manufacturing firm-years: {len(mfg)}')
print(f'Manufacturing firms: {mfg["Scode"].nunique()}')

mfg['ind2_csrc'] = mfg['csrc_ind'].str[:3]
print(f'Industry 2-digit codes: {mfg["ind2_csrc"].nunique()}')
print(mfg['ind2_csrc'].value_counts().head(15))

# Save
mapping = mfg[['Scode', 'Year', 'ind2_csrc', 'listing_year', 'CITY', 'PROVINCE', 'LISTINGSTATE']].copy()
mapping.to_csv('cleaned_data/csmar_firm_info.csv', index=False, encoding='utf-8-sig')
print(f'\nSaved: {len(mapping)} rows')

# Check overlap
panel = pd.read_csv('cleaned_data/lisen_replication_panel.csv', encoding='utf-8-sig')
panel_scodes = set(panel['Scode'].unique())
csmar_scodes = set(mfg['Scode'].unique())
overlap = panel_scodes & csmar_scodes
print(f'\nPanel: {len(panel_scodes)} firms, CSMAR mfg: {len(csmar_scodes)} firms, Overlap: {len(overlap)}')
