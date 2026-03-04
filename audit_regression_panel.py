import pandas as pd
import numpy as np

def audit_dataset():
    file_path = 'cleaned_data/final_regression_dataset.csv'
    print(f"Loading {file_path} for audit...")
    df = pd.read_csv(file_path)
    
    print("-" * 50)
    print("1. DATASET SHAPE & BASIC INFO")
    print("-" * 50)
    print(f"Total Observations (City-Years): {len(df)}")
    print(f"Number of distinct cities: {df['City'].nunique()}")
    print(f"Years covered: {df['Year'].min()} - {df['Year'].max()}")
    
    print("\n" + "-" * 50)
    print("2. MISSING VALUE ANALYSIS (Missings per Column)")
    print("-" * 50)
    missing_stats = df.isnull().sum()
    print(missing_stats[missing_stats > 0] if missing_stats.sum() > 0 else "No missing values!")
    
    print("\n" + "-" * 50)
    print("3. DESCRIPTIVE STATISTICS (Key Variables)")
    print("-" * 50)
    desc = df[['SRDI_Investment_Ratio', 'SRDI_Inv_Count', 'Fiscal_Gap', 'L1_Fiscal_Gap', 'Early_Stage_Ratio']].describe()
    print(desc.round(3))
    
    print("\n" + "-" * 50)
    print("4. ZERO / NON-ZERO ANALYSIS")
    print("-" * 50)
    non_zero_pct = (df['SRDI_Inv_Count'] > 0).mean() * 100
    print(f"Percentage of City-Year observations with at least 1 SRDI investment: {non_zero_pct:.2f}%")
    
    if 'L1_Fiscal_Gap' in df.columns:
        valid_lags = df['L1_Fiscal_Gap'].notnull().sum()
        print(f"Valid L1_Fiscal_Gap observations: {valid_lags} ({valid_lags/len(df)*100:.2f}%)")

if __name__ == "__main__":
    audit_dataset()
