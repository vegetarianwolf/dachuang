import os
import glob
import pandas as pd
import numpy as np

def clean_pe_data():
    input_dir = '清科政府引导基金投资事件截止到2024年'
    # There are both CSV and XLS files. We will read the CSVs.
    files = glob.glob(os.path.join(input_dir, '*.csv'))
    
    print(f"Found {len(files)} CSV files in {input_dir}")
    
    df_list = []
    
    for f in files:
        # Some old CSVs might be gbk, some utf-8. We use a fallback reading approach
        try:
            df = pd.read_csv(f, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(f, encoding='gbk')
            except Exception as e:
                print(f"Failed to read {f}: {e}")
                continue
        df_list.append(df)
        
    if not df_list:
        print("No data parsed.")
        return None
        
    full_pe_df = pd.concat(df_list, ignore_index=True)
    print(f"Concatenated full PE dataset: {len(full_pe_df)} rows")
    
    # 1. Standardize Time -> `Year`
    # Format typically "2023-12-15" or similar.
    full_pe_df['Date'] = pd.to_datetime(full_pe_df['投资时间'], errors='coerce')
    full_pe_df['Year'] = full_pe_df['Date'].dt.year
    
    def extract_city(loc_str):
        if pd.isna(loc_str) or str(loc_str).strip() in ['--', '']:
            return np.nan
        parts = str(loc_str).split('|')
        
        # Taking the last part which is typically the city
        city_clean = parts[-1].strip()
        
        # Remove suffixes
        for suffix in ['市', '地区', '自治州', '省']:
            city_clean = city_clean.replace(suffix, '')
            
        return city_clean
        
    full_pe_df['City'] = full_pe_df['地区'].apply(extract_city)
    # 3. Standardize Investment Amount
    # Using '投资金额(RMB/M)' which is already in millions RMB, if missing use another proxy if wanted
    def clean_amount(val):
        if pd.isna(val) or str(val).strip() in ['--', '']:
            return np.nan
        # Remove commas
        val_str = str(val).replace(',', '').strip()
        try:
            return float(val_str)
        except:
            return np.nan
            
    full_pe_df['Inv_Amount_RMB_M'] = full_pe_df['投资金额(RMB/M)'].apply(clean_amount)
    
    # Fill NAs in amount with 0 for aggregation purposes if they occurred, or drop them based on methodology
    # For now we keep them as NaN to know it's missing, but for sum() they are treated as 0
    
    # 4. Standardize Company Name for merging
    full_pe_df['Target_Company'] = full_pe_df['融资主体'].astype(str).str.strip()
    
    print("\nPE Data Sample:")
    print(full_pe_df[['Year', 'City', 'Target_Company', 'Inv_Amount_RMB_M']].head())
    
    return full_pe_df

def main():
    cleaned_pe = clean_pe_data()
    
    if cleaned_pe is not None:
        out_dir = 'cleaned_data'
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'PE_investment_events_cleaned.csv')
        cleaned_pe.to_csv(out_file, index=False, encoding='utf-8-sig')
        print(f"\nSaved standardized PE investment data to {out_file}")

if __name__ == "__main__":
    main()
