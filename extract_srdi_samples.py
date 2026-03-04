import pandas as pd
import os

def mark_and_extract_srdi():
    pe_file = 'cleaned_data/PE_investment_events_cleaned.csv'
    csmar_file = 'csmar_data_export/SRDI_EntIdentInfo.csv'
    
    print(f"Loading {pe_file}...")
    pe_df = pd.read_csv(pe_file)
    
    print(f"Loading {csmar_file}...")
    srdi_df = pd.read_csv(csmar_file, usecols=['InstitutionName', 'IdentifyYear'])
    
    # 1. Find the earliest IdentifyYear for each SRDI enterprise
    # Some enterprises may be certified multiple times (e.g. city level then national level)
    # The earliest year is when they first became recognized as an SRDI
    srdi_min_year = srdi_df.groupby('InstitutionName')['IdentifyYear'].min().reset_index()
    # Clean the names up from CSMAR
    srdi_min_year['Target_Company'] = srdi_min_year['InstitutionName'].dropna().astype(str).str.strip()
    
    # Create a dictionary mapping Company Name -> First Identify Year
    srdi_year_dict = dict(zip(srdi_min_year['Target_Company'], srdi_min_year['IdentifyYear']))
    
    # 2. Annotate the original PE CSV dynamically
    pe_df['Target_Company'] = pe_df['Target_Company'].fillna('')
    
    def check_dynamic_srdi(row):
        company = row['Target_Company']
        inv_year = row['Year']
        
        # If it's not even an SRDI or we don't have the investment year, return 0
        if company not in srdi_year_dict or pd.isna(inv_year):
            return 0
            
        first_srdi_yr = srdi_year_dict[company]
        
        # Post-2013 logic: the investment object in the corresponding year was selected as SRDI.
        # This means Investment Year >= Identify Year
        if inv_year >= first_srdi_yr:
            return 1
        return 0
        
    pe_df['Is_SRDI'] = pe_df.apply(check_dynamic_srdi, axis=1)
    
    # Specifically for the user's ratio request later, filter out pre-2013 globally
    # "专精特新评定是13年才开始的... 把13年之后的挑出来"
    pe_df_post2013 = pe_df[pe_df['Year'] >= 2013].copy()
    
    # Save the annotated version back to the cleaned data file
    pe_df_post2013.to_csv(pe_file, index=False, encoding='utf-8-sig')
    print(f"Added dynamic 'Is_SRDI' column and filtered >= 2013, saved back to {pe_file}")
    
    # 3. Extract only the marked samples into a new table
    srdi_only_df = pe_df_post2013[pe_df_post2013['Is_SRDI'] == 1].copy()
    
    out_file = 'cleaned_data/PE_investment_events_SRDI_only.csv'
    srdi_only_df.to_csv(out_file, index=False, encoding='utf-8-sig')
    print(f"Extracted {len(srdi_only_df)} SRDI investment samples to {out_file}")

if __name__ == "__main__":
    mark_and_extract_srdi()
