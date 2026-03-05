import os
import pandas as pd
import numpy as np

def build_final_dataset():
    # 1. Load the cleaned PE dataset
    # We load the originally cleaned one. Since extract_srdi_samples.py might have modified it,
    # it's fine. We will enforce the logic strictly here.
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
    
    # 4. Flag PE investments (Relaxed Temporal Match)
    # As long as the enterprise was eventually certified as SRDI, we count investments from 2013 onwards
    pe_df['Target_Company'] = pe_df['Target_Company'].fillna('')
    pe_df['Is_SRDI'] = pe_df['Target_Company'].apply(lambda x: 1 if x in srdi_names else 0)
    
    matches = pe_df['Is_SRDI'].sum()
    print(f"Success! Dynamically matched {matches} PE investments to valid SRDI enterprises out of {len(pe_df)} PE records (post 2013).")
    
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
        
        # User requested: "对应城市当年The所有基金投资行为次数做成一个比例的指数"
        # We'll calculate both ratio by Amount and ratio by Count
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
            'SRDI_Investment_Ratio_Count': ratio_cnt,  # added for specific prompt
            'Early_Stage_Ratio': early_ratio
        })
        
    city_year_pe = grouped.apply(calculate_metrics).reset_index()
    
    # 6. Bring in Fiscal Data (The independent variable)
    fiscal_file = 'cleaned_data/city_fiscal_panel.csv'
    print(f"Loading {fiscal_file}...")
    fiscal_df = pd.read_csv(fiscal_file)
    
    city_year_pe['Year'] = city_year_pe['Year'].astype(int)
    fiscal_df['Year'] = pd.to_numeric(fiscal_df['Year'], errors='coerce')
    fiscal_df = fiscal_df.dropna(subset=['Year'])
    fiscal_df['Year'] = fiscal_df['Year'].astype(int)
    
    print("Merging Fiscal Panel with PE Panel...")
    final_panel = pd.merge(city_year_pe, fiscal_df, on=['City', 'Year'], how='inner')
    
    print("Calculating Lead Variables (t+1)...")
    final_panel = final_panel.sort_values(['City', 'Year'])
    
    fiscal_lead = fiscal_df[['City', 'Year', 'Fiscal_Gap']].copy()
    # To get t+1 (lead), the fiscal data of Year T should be matched with PE data of Year T-1
    fiscal_lead['Year'] = fiscal_lead['Year'] - 1
    fiscal_lead = fiscal_lead.rename(columns={'Fiscal_Gap': 'F1_Fiscal_Gap'})
    
    final_panel = pd.merge(final_panel, fiscal_lead, on=['City', 'Year'], how='left')
    
    # Translate columns to Chinese
    rename_map = {
        'City': '城市',
        'Year': '年份',
        'Total_Inv_Amount': '全部基金投资总金额',
        'Total_Inv_Count': '全部基金投资总次数',
        'SRDI_Inv_Amount': '专精特新企业投资金额',
        'SRDI_Inv_Count': '专精特新企业投资次数',
        'Early_Stage_Amount': '早期投资金额',
        'SRDI_Investment_Ratio_Amt': '专精特新投资金额占比',
        'SRDI_Investment_Ratio_Count': '专精特新投资次数占比',
        'Early_Stage_Ratio': '早期投资金额占比',
        'Fiscal_Gap': '当期财政资金缺口',
        'F1_Fiscal_Gap': '提前一期财政资金缺口'
    }
    final_panel = final_panel.rename(columns=rename_map)
    
    # Output to disk
    out_dir = 'cleaned_data'
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'final_regression_dataset.csv')
    final_panel.to_csv(out_file, index=False, encoding='utf-8-sig')
    
    print(f"\n---- Final Analysis Dataset Built ----")
    print(f"Total Rows (City-Year observations): {len(final_panel)}")
    print(f"Output saved to: {out_file}")

if __name__ == "__main__":
    build_final_dataset()
