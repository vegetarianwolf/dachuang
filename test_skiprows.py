"""快速诊断数据读取问题"""
import pandas as pd

# 测试不同的skiprows
for skip in [0, 1, 2, 3, 4, 5, 6]:
    print(f"\n=== skiprows={skip} ===")
    try:
        df = pd.read_csv('地级市财政收入.csv', encoding='utf-8-sig', skiprows=skip, nrows=3)
        print("列名:", df.columns.tolist()[:3])
        print("前2行:")
        print(df.iloc[:2, :3])
    except Exception as e:
        print(f"错误: {e}")
