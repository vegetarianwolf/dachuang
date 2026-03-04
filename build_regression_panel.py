import os
import pandas as pd
import numpy as np

def build_final_dataset():
    # 1. Load the cleaned PE dataset
    pe_file = 'cleaned_data/PE_investment_events_cleaned.csv'
    print(f"Loading {pe_file}...")
    pe_df = pd.read_csv(pe_file)
    
    # 2. Load the CSMAR SRDI Name Roster (we only need InstitutionName to flag)
    # The roster is in SRDI_EntIdentInfo.csv usually, but let's load all unique valid names
    csmar_file = 'csmar_data_export/SRDI_EntIdentInfo.csv'
    print(f"Loading {csmar_file}...")
    srdi_df = pd.read_csv(csmar_file, usecols=['InstitutionName'])
    
    # Clean the names up
    srdi_names = set(srdi_df['InstitutionName'].dropna().astype(str).str.strip())
    print(f"Total unique Specialized and Innovative (SRDI) enterprises from CSMAR: {len(srdi_names)}")
    
    # 3. Flag PE investments
    # Target_Company in pe_df
    # Is_SRDI = 1 if Target_Company is in srdi_names else 0
    pe_df['Target_Company'] = pe_df['Target_Company'].fillna('')
    pe_df['Is_SRDI'] = pe_df['Target_Company'].apply(lambda x: 1 if x in srdi_names else 0)
    
    matches = pe_df['Is_SRDI'].sum()
    print(f"Success! Matched {matches} PE investments to SRDI enterprises out of {len(pe_df)} total PE records.")
    
    # 4. Collapse to Panel (City - Year)
    # We need to aggregate PE data by (City, Year)
    print("\nCollapsing PE events to City-Year panel...")
    
    # Drop rows without year or city
    pe_panel_ready = pe_df.dropna(subset=['Year', 'City']).copy()
    
    # Amount logic
    pe_panel_ready['Inv_Amount_RMB_M'] = pd.to_numeric(pe_panel_ready['Inv_Amount_RMB_M'], errors='coerce').fillna(0)
    
    # Let's compute:
    # Y1: SRDI_Investment_Ratio (专精特新金额占比) = sum(Inv_Amount_RMB_M where Is_SRDI==1) / sum(Inv_Amount_RMB_M)
    # Y2: SRDI_Investment_Count (专精特新投资数量) = sum(Is_SRDI==1)
    # Total_Investment_Amount = sum(Inv_Amount_RMB_M)
    # Total_Investment_Count = count()
    
    # Group by City and Year
    grouped = pe_panel_ready.groupby(['City', 'Year'])
    
    def calculate_metrics(group):
        total_amt = group['Inv_Amount_RMB_M'].sum()
        total_cnt = len(group)
        
        srdi_mask = group['Is_SRDI'] == 1
        srdi_amt = group.loc[srdi_mask, 'Inv_Amount_RMB_M'].sum()
        srdi_cnt = srdi_mask.sum()
        
        # M1 early stage preference. '阶段' usually has '种子期', '初创期' etc.
        # Check if 投资阶段 column contains early stage keywords
        early_mask = group['投资阶段'].astype(str).str.contains('种子期|初创期|天使轮|A轮', na=False)
        early_amt = group.loc[early_mask, 'Inv_Amount_RMB_M'].sum()
        
        ratio = srdi_amt / total_amt if total_amt > 0 else 0
        early_ratio = early_amt / total_amt if total_amt > 0 else 0
        
        return pd.Series({
            'Total_Inv_Amount': total_amt,
            'Total_Inv_Count': total_cnt,
            'SRDI_Inv_Amount': srdi_amt,
            'SRDI_Inv_Count': srdi_cnt,
            'Early_Stage_Amount': early_amt,
            'SRDI_Investment_Ratio': ratio,
            'Early_Stage_Ratio': early_ratio
        })
        
    city_year_pe = grouped.apply(calculate_metrics).reset_index()
    
    # 5. Bring in Fiscal Data (The independent variable)
    fiscal_file = 'cleaned_data/city_fiscal_panel.csv'
    print(f"Loading {fiscal_file}...")
    fiscal_df = pd.read_csv(fiscal_file)
    
    # Ensure year types match
    city_year_pe['Year'] = city_year_pe['Year'].astype(int)
    fiscal_df['Year'] = pd.to_numeric(fiscal_df['Year'], errors='coerce')
    fiscal_df = fiscal_df.dropna(subset=['Year'])
    fiscal_df['Year'] = fiscal_df['Year'].astype(int)
    
    # Merge City-Year
    print("Merging Fiscal Panel with PE Panel...")
    final_panel = pd.merge(city_year_pe, fiscal_df, on=['City', 'Year'], how='inner')
    
    # The paper's core explanatory variable is FiscalPressure(c, t-1)
    # So we need to create a lagged Fiscal_Gap column.
    print("Calculating Lagged Variables (t-1)...")
    final_panel = final_panel.sort_values(['City', 'Year'])
    
    # Group by city and shift the Fiscal_Gap by 1 row (since it's sorted by year)
    # To be perfectly safe against missing years, it's better to self merge on year-1
    fiscal_lag = fiscal_df[['City', 'Year', 'Fiscal_Gap']].copy()
    fiscal_lag['Year'] = fiscal_lag['Year'] + 1  # 2022's gap becomes 2023's L1 gap
    fiscal_lag = fiscal_lag.rename(columns={'Fiscal_Gap': 'L1_Fiscal_Gap'})
    
    final_panel = pd.merge(final_panel, fiscal_lag, on=['City', 'Year'], how='left')
    
    # Output to disk
    out_dir = 'cleaned_data'
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'final_regression_dataset.csv')
    final_panel.to_csv(out_file, index=False, encoding='utf-8-sig')
    
    print(f"\n---- Final Analysis Dataset Built ----")
    print(f"Total Rows (City-Year observations): {len(final_panel)}")
    print(f"Output saved to: {out_file}")
    
    # Print a sample where there is an SRDI investment
    sample = final_panel[final_panel['SRDI_Inv_Count'] > 0].head()
    print("\nSample Data (Where SRDI investments occurred):")
    cols_to_show = ['City', 'Year', 'Fiscal_Gap', 'L1_Fiscal_Gap', 'SRDI_Inv_Count', 'SRDI_Investment_Ratio']
    print(sample[cols_to_show])

if __name__ == "__main__":
    build_final_dataset()
