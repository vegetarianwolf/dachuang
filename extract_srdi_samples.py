import pandas as pd
import os

def mark_and_extract_srdi():
    pe_file = 'cleaned_data/PE_investment_events_cleaned.csv'
    csmar_file = 'csmar_data_export/SRDI_EntIdentInfo.csv'
    
    print(f"Loading {pe_file}...")
    pe_df = pd.read_csv(pe_file)
    
    print(f"Loading {csmar_file}...")
    srdi_df = pd.read_csv(csmar_file, usecols=['InstitutionName'])
    
    # Store all unique SRDI names
    srdi_names = set(srdi_df['InstitutionName'].dropna().astype(str).str.strip())
    
    # 2. Annotate the original PE CSV dynamically
    pe_df['Target_Company'] = pe_df['Target_Company'].fillna('')
    
    # Relaxed Post-2013 logic: the enterprise was eventually selected as SRDI.
    pe_df['Is_SRDI'] = pe_df['Target_Company'].apply(lambda x: 1 if x in srdi_names else 0)
    
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
