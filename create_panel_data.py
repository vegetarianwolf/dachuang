"""
创建实证回归数据面板
根据大致思路.md的研究设计，整合各类数据源
时间范围：2014-2024年
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. 读取专利数据（被解释变量）
# ============================================================================
print("=" * 80)
print("第1步：读取并处理专利数据（2014-2024年发明专利）")
print("=" * 80)

# 读取专利申请数据
patent_apply = pd.read_csv('CNRDS专利数据包/各省市创新专利情况/各省市专利申请情况/各省市专利申请情况.csv', 
                          skiprows=1,
                          names=['省份', '城市', '年份', '发明申请数', '实用新型申请数', '外观设计申请数'])

# 转换数据类型
patent_apply['年份'] = pd.to_numeric(patent_apply['年份'], errors='coerce')
patent_apply['发明申请数'] = pd.to_numeric(patent_apply['发明申请数'], errors='coerce')
patent_apply['实用新型申请数'] = pd.to_numeric(patent_apply['实用新型申请数'], errors='coerce')
patent_apply['外观设计申请数'] = pd.to_numeric(patent_apply['外观设计申请数'], errors='coerce')

# 删除无效行
patent_apply = patent_apply.dropna(subset=['年份'])

# 筛选2014-2024年
patent_apply = patent_apply[(patent_apply['年份'] >= 2014) & (patent_apply['年份'] <= 2024)].copy()

# 计算专利相关指标
patent_apply['专利申请总数'] = patent_apply['发明申请数'] + patent_apply['实用新型申请数'] + patent_apply['外观设计申请数']
patent_apply['ln_inv_patent'] = np.log(patent_apply['发明申请数'] + 1)
patent_apply['ln_patent_apply'] = np.log(patent_apply['专利申请总数'] + 1)
patent_apply['inv_share'] = patent_apply['发明申请数'] / patent_apply['专利申请总数'].replace(0, np.nan)

print(f"专利数据：{len(patent_apply)} 条记录")
print(f"时间范围：{patent_apply['年份'].min()}-{patent_apply['年份'].max()}")
print(f"覆盖城市数：{patent_apply['城市'].nunique()}")
print()

# ============================================================================
# 2. 读取财政数据（核心解释变量）
# ============================================================================
print("=" * 80)
print("第2步：读取并处理财政数据")
print("=" * 80)

# 读取财政收入
try:
    fiscal_revenue = pd.read_csv('地级市财政收入.csv', encoding='utf-8-sig')
    print(f"✓ 财政收入数据：{len(fiscal_revenue)} 条")
except Exception as e:
    print(f"✗ 财政收入数据读取失败：{e}")
    fiscal_revenue = pd.DataFrame()

# 读取财政支出
try:
    fiscal_expend = pd.read_csv('地级市财政支出.csv', encoding='utf-8-sig')
    print(f"✓ 财政支出数据：{len(fiscal_expend)} 条")
except Exception as e:
    print(f"✗ 财政支出数据读取失败：{e}")
    fiscal_expend = pd.DataFrame()

# 读取政府债务
try:
    debt = pd.read_csv('地方政府债务：地级市：余额.csv', encoding='utf-8-sig')
    print(f"✓ 政府债务数据：{len(debt)} 条")
except Exception as e:
    print(f"✗ 政府债务数据读取失败：{e}")
    debt = pd.DataFrame()

# 读取科技支出
try:
    tech_expend = pd.read_csv('财政支出：科学：地级市.csv', encoding='utf-8-sig')
    print(f"✓ 科技支出数据：{len(tech_expend)} 条")
except Exception as e:
    print(f"✗ 科技支出数据读取失败：{e}")
    tech_expend = pd.DataFrame()

print()

# ============================================================================
# 3. 读取经济数据（控制变量）
# ============================================================================
print("=" * 80)
print("第3步：读取并处理经济数据")
print("=" * 80)

# 读取GDP
try:
    gdp = pd.read_csv('地级市总GDP.csv', encoding='utf-8-sig')
    print(f"✓ GDP数据：{len(gdp)} 条")
except Exception as e:
    print(f"✗ GDP数据读取失败：{e}")
    gdp = pd.DataFrame()

# 读取人均GDP
try:
    gdp_percap = pd.read_csv('地级市人均GDP.csv', encoding='utf-8-sig')
    print(f"✓ 人均GDP数据：{len(gdp_percap)} 条")
except Exception as e:
    print(f"✗ 人均GDP数据读取失败：{e}")
    gdp_percap = pd.DataFrame()

# 读取第二产业
try:
    industry = pd.read_csv('地级市第二产业.csv', encoding='utf-8-sig')
    print(f"✓ 第二产业数据：{len(industry)} 条")
except Exception as e:
    print(f"✗ 第二产业数据读取失败：{e}")
    industry = pd.DataFrame()

# 读取人口
try:
    population = pd.read_csv('常住人口.csv', encoding='utf-8-sig')
    print(f"✓ 人口数据：{len(population)} 条")
except Exception as e:
    print(f"✗ 人口数据读取失败：{e}")
    population = pd.DataFrame()

# 读取外资
try:
    fdi = pd.read_csv('实际利用外资.csv', encoding='utf-8-sig')
    print(f"✓ 外资数据：{len(fdi)} 条")
except Exception as e:
    print(f"✗ 外资数据读取失败：{e}")
    fdi = pd.DataFrame()

# 读取金融机构贷款
try:
    finance = pd.read_csv('金融机构贷款余额.csv', encoding='utf-8-sig')
    print(f"✓ 金融机构贷款数据：{len(finance)} 条")
except Exception as e:
    print(f"✗ 金融机构贷款数据读取失败：{e}")
    finance = pd.DataFrame()

print()

# ============================================================================
# 4. 读取引导基金数据（机制变量）
# ============================================================================
print("=" * 80)
print("第4步：读取并处理引导基金投资数据")
print("=" * 80)

import glob

# 读取所有引导基金投资数据
gf_files = glob.glob('清科政府引导基金投资事件截止到2024年/政府引导基金投资*.csv')
gf_data_list = []

for file in gf_files:
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')
        gf_data_list.append(df)
    except Exception as e:
        print(f"读取 {file} 失败：{e}")

if gf_data_list:
    gf_investment = pd.concat(gf_data_list, ignore_index=True)
    print(f"✓ 引导基金投资数据：{len(gf_investment)} 条")
    print(f"  时间范围：{gf_investment.get('投资时间', pd.Series()).min() if '投资时间' in gf_investment.columns else 'N/A'}")
else:
    print("✗ 引导基金投资数据读取失败")
    gf_investment = pd.DataFrame()

print()

# ============================================================================
# 5. 读取市场化指数（调节变量）
# ============================================================================
print("=" * 80)
print("第5步：读取市场化指数数据")
print("=" * 80)

try:
    market_index = pd.read_csv('1997-2024年市场化指数和各分项指数 的副本.csv', encoding='utf-8-sig')
    print(f"✓ 市场化指数数据：{len(market_index)} 条")
except Exception as e:
    print(f"✗ 市场化指数数据读取失败：{e}")
    market_index = pd.DataFrame()

print()

# ============================================================================
# 6. 数据标准化和合并
# ============================================================================
print("=" * 80)
print("第6步：标准化并合并所有数据")
print("=" * 80)

# 以专利数据为基础面板
panel = patent_apply[['省份', '城市', '年份', '发明申请数', '专利申请总数', 'ln_inv_patent', 'ln_patent_apply', 'inv_share']].copy()

print(f"基础面板：{len(panel)} 条记录")
print(f"城市数：{panel['城市'].nunique()}")
print(f"年份范围：{panel['年份'].min()}-{panel['年份'].max()}")

# 定义一个标准化合并函数
def standardize_and_merge(base_df, new_df, data_name, merge_keys=['城市', '年份']):
    """标准化数据格式并合并"""
    if new_df.empty:
        print(f"  ✗ {data_name} 数据为空，跳过")
        return base_df
    
    # 检查是否有需要的列
    if not all(key in new_df.columns for key in merge_keys):
        # 尝试根据列索引推断
        if len(new_df.columns) >= len(merge_keys) + 1:
            print(f"  ! {data_name} 列名不匹配，尝试自动推断...")
            # 假设前面是地区信息，后面是年份和值
        else:
            print(f"  ✗ {data_name} 列名不匹配，跳过")
            return base_df
    
    try:
        before_count = len(base_df.columns)
        base_df = pd.merge(base_df, new_df, on=merge_keys, how='left')
        after_count = len(base_df.columns)
        print(f"  ✓ {data_name} 合并完成，新增 {after_count - before_count} 列")
        return base_df
    except Exception as e:
        print(f"  ✗ {data_name} 合并失败：{e}")
        return base_df

print("\n开始合并数据...")

# 这里需要先检查每个数据文件的实际格式
# 由于不同数据源格式可能不同，我们先输出数据信息供检查
print("\n" + "="*80)
print("数据格式检查（前5行和列名）")
print("="*80)

# ============================================================================
# 7. 保存中间结果
# ============================================================================
print("\n" + "="*80)
print("第7步：保存基础面板数据")
print("="*80)

panel.to_csv('cleaned_data/regression_panel_base.csv', index=False, encoding='utf-8-sig')
print(f"✓ 基础面板已保存到：cleaned_data/regression_panel_base.csv")
print(f"  包含 {len(panel)} 条记录，{len(panel.columns)} 列")

# ============================================================================
# 8. 数据质量报告
# ============================================================================
print("\n" + "="*80)
print("数据面板摘要")
print("="*80)

print("\n基础统计：")
print(panel.describe())

print("\n各年份记录数：")
print(panel['年份'].value_counts().sort_index())

print("\n各省份城市数：")
print(panel.groupby('省份')['城市'].nunique().sort_values(ascending=False))

print("\n缺失值情况：")
missing = panel.isnull().sum()
missing_pct = 100 * missing / len(panel)
missing_df = pd.DataFrame({'缺失数': missing, '缺失率%': missing_pct})
print(missing_df[missing_df['缺失数'] > 0])

print("\n" + "="*80)
print("处理完成!")
print("="*80)
