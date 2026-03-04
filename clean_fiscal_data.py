import os
import pandas as pd

def clean_fiscal_data(filepath, value_name):
    # Read CSV, skip the metadata rows (first 9 rows are usually metadata, row 0 is header)
    # The actual data starts after some descriptive rows. Let's inspect rows first
    df = pd.read_csv(filepath)
    
    # In CEIC data, typically row 0 is "区域", row 1 "次国家", row 2 "频率", row 3 "单位", row 4 "数据来源", row 5 "状态", row 6 "数列ID", row 7 "SR码"
    # Starting from row 8 are the dates (years) and values. Let's slice the dataframe
    
    # We want the values from row 8 onwards
    dates = df.iloc[np.arange(8, len(df))]
    
    # Let's write a robust parser
    return df

def process_ceic_fiscal_data(filepath, value_name):
    print(f"Loading {filepath}...")
    # Load all rows
    raw_df = pd.read_csv(filepath)
    
    # Column 0 is the "date" or "metadata label"
    # Column 1 to N are the cities. The column names look like "财政支出:地方:一般公共预算支出:河北:石家庄"
    
    cols = raw_df.columns
    date_col = cols[0]
    city_cols = cols[1:]
    
    # Extract city name from the long column name
    # e.g. "财政支出:地方:一般公共预算支出:河北:石家庄" -> "石家庄"
    # e.g. "财政支出:地方:一般公共预算支出:重庆" -> "重庆"
    new_cols = {}
    for c in city_cols:
        parts = c.split(":")
        city_name = parts[-1] 
        new_cols[c] = city_name
        
    raw_df.rename(columns=new_cols, inplace=True)
    
    # The actual data usually starts around row 8. 
    # Let's filter out rows where the first column is not a valid year string (e.g. "2023", "2022")
    # A valid year is usually 4 digits or looks like a date format.
    
    def is_year_row(val):
        try:
            # check if it converts to float and is > 1900
            val_str = str(val).strip()
            # In CEIC it might be "2023" or "01-12-2023"
            # Let's just try to extract the year
            if "20" in val_str or "19" in val_str:
                return True
            return False
        except:
            return False

    data_rows = raw_df[raw_df[date_col].apply(is_year_row)].copy()
    
    # Clean the date column to just Year
    def extract_year(val):
        val_str = str(val)
        if '-' in val_str: # e.g. 01-12-2023
            return int(val_str.split('-')[-1])
        elif '/' in val_str:
            return int(val_str.split('/')[-1])
        else:
            try:
                return int(val_str)
            except:
                return val_str
                
    data_rows['Year'] = data_rows[date_col].apply(extract_year)
    data_rows.drop(columns=[date_col], inplace=True)
    
    # Now it is wide format with 'Year' and columns of cities.
    # Melt it into long format
    long_df = data_rows.melt(id_vars=['Year'], var_name='City', value_name=value_name)
    
    # Clean up NA values
    long_df.dropna(subset=[value_name], inplace=True)
    
    # Ensure types
    long_df['Year'] = pd.to_numeric(long_df['Year'], errors='coerce')
    long_df[value_name] = pd.to_numeric(long_df[value_name], errors='coerce')
    long_df.dropna(subset=['Year', value_name], inplace=True)
    
    # Format city name uniformly (remove '市')
    long_df['City'] = long_df['City'].str.replace('市', '')
    
    return long_df

def main():
    exp_file = '地级市财政支出.csv'
    rev_file = '地级市财政收入.csv'
    
    print("Processing Expenditure...")
    df_exp = process_ceic_fiscal_data(exp_file, 'Fiscal_Expenditure')
    print("Processing Revenue...")
    df_rev = process_ceic_fiscal_data(rev_file, 'Fiscal_Revenue')
    
    # Merge them
    print("Merging panels...")
    df_merged = pd.merge(df_exp, df_rev, on=['City', 'Year'], how='outer')
    
    # Calculate Fiscal Gap
    df_merged['Fiscal_Gap'] = df_merged['Fiscal_Expenditure'] - df_merged['Fiscal_Revenue']
    df_merged = df_merged.sort_values(['City', 'Year'])
    
    # Output
    out_dir = 'cleaned_data'
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'city_fiscal_panel.csv')
    df_merged.to_csv(out_file, index=False, encoding='utf-8-sig')
    print(f"Done! Saved to {out_file}")
    
    print("\nSample Data:")
    print(df_merged.head())
    print("\nSummary:")
    print(f"Total Rows: {len(df_merged)}")
    print(f"Unique Cities: {df_merged['City'].nunique()}")
    print(f"Years: {df_merged['Year'].min()} - {df_merged['Year'].max()}")

if __name__ == '__main__':
    main()
