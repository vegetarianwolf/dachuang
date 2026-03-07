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
    print(f"Number of distinct cities: {df['城市'].nunique()}")
    print(f"Years covered: {df['年份'].min()} - {df['年份'].max()}")
    
    print("\n" + "-" * 50)
    print("2. MISSING VALUE ANALYSIS (Missings per Column)")
    print("-" * 50)
    missing_stats = df.isnull().sum()
    print(missing_stats[missing_stats > 0] if missing_stats.sum() > 0 else "No missing values!")
    
    print("\n" + "-" * 50)
    print("3. DESCRIPTIVE STATISTICS (Key Variables)")
    print("-" * 50)
    key_cols = [c for c in ['早期投资金额占比', '早期投资事件占比', '加权风险偏好指数',
                            '当期财政缺口', '滞后一期财政缺口',
                            'ln_发明专利申请数', 'ln_专利申请受理数', 'ln_专利授权数']
                if c in df.columns]
    desc = df[key_cols].describe()
    print(desc.round(3))
    
    print("\n" + "-" * 50)
    print("4. PANEL BALANCE CHECK")
    print("-" * 50)
    obs_per_city = df.groupby('城市')['年份'].count()
    print(f"Observations per city: min={obs_per_city.min()}, max={obs_per_city.max()}, "
          f"median={obs_per_city.median():.0f}")
    
    if '滞后一期财政缺口' in df.columns:
        valid_lags = df['滞后一期财政缺口'].notnull().sum()
        print(f"Valid L1_Fiscal_Gap observations: {valid_lags} ({valid_lags/len(df)*100:.2f}%)")

if __name__ == "__main__":
    audit_dataset()
