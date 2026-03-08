"""诊断数据合并问题"""
import pandas as pd
import numpy as np

# 读取生成的数据
panel = pd.read_csv('cleaned_data/final_regression_panel.csv', encoding='utf-8-sig')
patent = pd.read_csv('CNRDS专利数据包/各省市创新专利情况/各省市专利申请情况/各省市专利申请情况.csv', 
                      skiprows=1, names=['省份', '城市', '年份', '发明申请数', '实用新型申请数', '外观设计申请数'])

fiscal_rev = pd.read_csv('地级市财政收入.csv', encoding='utf-8-sig')

print("=" * 80)
print("数据诊断")
print("=" * 80)

# 1. 专利数据城市样例
print("\n1. 专利数据城市样例（前20个）：")
print(patent[(patent['年份'] == '2020')]['城市'].head(20).tolist())

# 2. 财政数据列名样例
print("\n2. 财政数据列名样例（前5列）：")
print(fiscal_rev.columns[:5].tolist())

# 3. 专利数据中的省份和城市
print("\n3. 一些专利数据样例：")
patent_clean = patent[patent['年份'].notna()].copy()
patent_clean['年份'] = pd.to_numeric(patent_clean['年份'], errors='coerce')
patent_sample = patent_clean[(patent_clean['年份'] == 2020)][['省份', '城市', '年份', '发明申请数']].head(10)
print(patent_sample)

# 4. 检查城市列表匹配
print("\n4. 面板数据城市样例：")
print(panel['城市'].head(20).tolist())

# 5. 城市名称对比
patent_cities = set(patent_clean['城市'].dropna().unique())
panel_cities = set(panel['城市'].dropna().unique())

print(f"\n5. 城市数量统计：")
print(f"专利数据城市数：{len(patent_cities)}")
print(f"面板数据城市数：{len(panel_cities)}")
print(f"交集：{len(patent_cities & panel_cities)}")

# 6. 检查fiscal_rev数据解析
print("\n6. 检查财政数据第一行（时间列）：")
print(fiscal_rev.iloc[0, :5])
