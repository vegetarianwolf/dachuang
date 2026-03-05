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
    
    # 2. Extract City
    # Relax geographical restriction: A government guidance fund from City A can invest in an enterprise in City B.
    # Therefore, we should identify the city of the *Fund* itself first.
    try:
        valid_cities_df = pd.read_csv('cleaned_data/city_fiscal_panel.csv', usecols=['City'])
        valid_cities = valid_cities_df['City'].dropna().unique().tolist()
    except Exception:
        valid_cities = []
        
    city_map = {}
    for c in valid_cities:
        base = c.replace('市', '').replace('地区', '').replace('自治州', '')
        if len(base) >= 2:
            city_map[base] = c

    def extract_city(row):
        # 1. Try to find the fund's city from its names (e.g. 投资方全称, 基金全称, 机构全称)
        names_to_check = [str(row.get('投资方全称', '')), str(row.get('基金全称', '')), 
                          str(row.get('投资方', '')), str(row.get('机构全称', ''))]
        
        for name in names_to_check:
            if name and name.strip() not in ['nan', '--', '']:
                for base, full_city in city_map.items():
                    if base in name:
                        return full_city
        
        # 2. If no city is found in the fund's name, fallback to extracting from the event's region (legacy fallback)
        loc_str = row.get('地区')
        if pd.isna(loc_str) or str(loc_str).strip() in ['--', '']:
            return np.nan
        parts = str(loc_str).split('|')
        city_clean = parts[-1].strip()
        
        for suffix in ['市', '地区', '自治州', '省']:
            city_clean = city_clean.replace(suffix, '')
            
        # Optional: return the formatted full_city if we want consistency
        if city_clean in city_map:
            return city_map[city_clean]
        
        # Add '市' suffix blindly to match panel format if not in map
        return city_clean + '市' if city_clean else np.nan
        
    full_pe_df['City'] = full_pe_df.apply(extract_city, axis=1)
    
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
