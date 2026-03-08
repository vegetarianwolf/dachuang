"""
处理财政经济数据和控制变量，合并到面板数据集中。

数据来源：
- CEIC格式（城市为列、年份为行）：财政收入、财政支出、GDP、政府债务、人均GDP、第二产业、科技支出
- 统计年鉴格式（城市为行、年份为列）：实际利用外资、金融机构贷款余额、常住人口

输出：
- cleaned_data/final_regression_panel_v2.csv  —— 包含所有变量的面板数据
- cleaned_data/data_quality_report_v2.csv     —— 数据质量报告
"""

import pandas as pd
import numpy as np
import re
import os

# ============================================================
# Part 1: CEIC 格式解析器（城市为列，年份为行）
# ============================================================

def parse_ceic_wide(filepath, encoding='utf-8-sig'):
    """
    解析 CEIC 导出的宽格式 CSV 文件。
    - 列名格式：'XX:XX:省份:城市' 或 'XX:直辖市名'
    - 行29+为年份数据
    
    返回长格式 DataFrame: [城市, 年份, value]
    """
    raw = pd.read_csv(filepath, encoding=encoding, header=None)
    
    # 找到年份数据起始行
    data_start = None
    for i in range(raw.shape[0]):
        val = str(raw.iloc[i, 0]).strip()
        if val[:4].isdigit():
            data_start = i
            break
    
    if data_start is None:
        raise ValueError(f"无法找到数据起始行: {filepath}")
    
    # 提取列名和城市信息
    col_headers = raw.iloc[0, 1:].tolist()  # 第0行是变量名
    
    # 从列名提取城市
    cities = []
    for h in col_headers:
        h = str(h).strip()
        parts = h.split(':')
        # 最后一个部分是城市名（地级市）或省/直辖市名
        city = parts[-1].strip()
        cities.append(city)
    
    # 提取年份和数据
    years = raw.iloc[data_start:, 0].astype(str).str.strip()
    data_values = raw.iloc[data_start:, 1:]
    
    # 构建长格式
    records = []
    for row_idx in range(len(years)):
        year_str = years.iloc[row_idx]
        try:
            year = int(float(year_str))
        except:
            continue
        if year < 2013 or year > 2025:  # 只保留需要的年份范围
            continue
        for col_idx in range(len(cities)):
            val = data_values.iloc[row_idx, col_idx]
            city = cities[col_idx]
            records.append({
                '城市_raw': city,
                '年份': year,
                'value': val
            })
    
    df = pd.DataFrame(records)
    
    # 数值转换
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    return df


def standardize_city_name(name):
    """标准化城市名：确保以'市'结尾，处理特殊情况"""
    name = str(name).strip()
    
    # 特殊处理
    special_mapping = {
        '北京': '北京市', '天津': '天津市', '上海': '上海市', '重庆': '重庆市',
        '巴音郭楞': '巴音郭楞蒙古自治州', '博尔塔拉': '博尔塔拉蒙古自治州',
        '昌吉': '昌吉回族自治州', '大兴安岭': '大兴安岭地区',
        '海东': '海东市', '海西': '海西蒙古族藏族自治州',
        '哈密地区': '哈密市', '吐鲁番地区': '吐鲁番市',
        '襄樊': '襄阳市', '巢湖': '巢湖市',
        '伊犁': '伊犁哈萨克自治州', '恩施': '恩施土家族苗族自治州',
        '湘西': '湘西土家族苗族自治州', '延边': '延边朝鲜族自治州',
        '甘南': '甘南藏族自治州', '临夏': '临夏回族自治州',
        '凉山': '凉山彝族自治州', '黔东南': '黔东南苗族侗族自治州',
        '黔南': '黔南布依族苗族自治州', '黔西南': '黔西南布依族苗族自治州',
        '文山': '文山壮族苗族自治州', '西双版纳': '西双版纳傣族自治州',
        '大理': '大理白族自治州', '德宏': '德宏傣族景颇族自治州',
        '红河': '红河哈尼族彝族自治州', '怒江': '怒江傈僳族自治州',
        '迪庆': '迪庆藏族自治州', '楚雄': '楚雄彝族自治州',
        '阿坝': '阿坝藏族羌族自治州', '甘孜': '甘孜藏族自治州',
        '海北': '海北藏族自治州', '海南藏族': '海南藏族自治州',
        '果洛': '果洛藏族自治州', '玉树': '玉树藏族自治州',
        '黄南': '黄南藏族自治州',
        '阿里地区': '阿里地区', '那曲地区': '那曲市', '那曲': '那曲市',
        '山南地区': '山南市', '山南': '山南市',
        '日喀则地区': '日喀则市', '日喀则': '日喀则市',
        '昌都地区': '昌都市', '昌都': '昌都市',
        '林芝地区': '林芝市', '林芝': '林芝市',
        '毕节地区': '毕节市', '毕节': '毕节市',
        '铜仁地区': '铜仁市', '铜仁': '铜仁市',
        '吕梁地区': '吕梁市',
        '阿拉善': '阿拉善盟', '兴安': '兴安盟', '锡林郭勒': '锡林郭勒盟',
        '乌兰察布': '乌兰察布市',
        '克拉玛依': '克拉玛依市', '哈密': '哈密市', '吐鲁番': '吐鲁番市',
        '阿克苏': '阿克苏地区', '喀什': '喀什地区', '和田': '和田地区',
        '塔城': '塔城地区', '阿勒泰': '阿勒泰地区',
        '克孜勒苏': '克孜勒苏柯尔克孜自治州',
        '儋州': '儋州市', '三沙': '三沙市',
    }
    
    if name in special_mapping:
        return special_mapping[name]
    
    # 一般城市处理逻辑：
    # 1. 以"市"结尾 → 保持不变
    # 2. 以"自治州"结尾 → 保持不变（自治州不需要加"市"）
    # 3. 以"盟"结尾 → 保持不变
    # 4. 以"地区"结尾 → 保持不变
    # 5. 以"州"结尾但不是"自治州"（如兰州、广州、苏州）→ 加"市"
    # 6. 其他 → 加"市"
    if name.endswith('市') or name.endswith('自治州') or name.endswith('盟') or name.endswith('地区'):
        pass  # 保持不变
    else:
        name = name + '市'
    
    return name


# ============================================================
# Part 2: 统计年鉴格式解析器（城市为行，年份为列）
# ============================================================

def parse_yearbook_format(filepath, target_variable_keyword=None, encoding='gbk'):
    """
    解析统计年鉴格式 CSV 文件。
    - 第0行: 年份 (如 '2014年')
    - 第1行: 子变量名 (如 '实际利用外资额(万美元)')
    - 第2行+: 城市数据 (城市名在第0列)
    
    如果一年有多个子变量列，需要通过 target_variable_keyword 选择。
    
    返回长格式 DataFrame: [城市, 年份, value]
    """
    raw = pd.read_csv(filepath, encoding=encoding, header=None)
    
    year_row = raw.iloc[0, 1:].tolist()
    var_row = raw.iloc[1, 1:].tolist()
    
    # 确定每列的年份（向前填充）
    current_year = None
    col_years = []
    for y in year_row:
        y_str = str(y).strip()
        m = re.match(r'(\d{4})', y_str)
        if m:
            current_year = int(m.group(1))
        col_years.append(current_year)
    
    # 确定目标列（根据关键词匹配子变量名）
    target_cols = []
    for i, (yr, var) in enumerate(zip(col_years, var_row)):
        if yr is None:
            continue
        if yr < 2013 or yr > 2025:
            continue
        var_str = str(var).strip()
        if target_variable_keyword:
            if target_variable_keyword in var_str:
                target_cols.append((i, yr, var_str))
        else:
            target_cols.append((i, yr, var_str))
    
    # 提取数据
    records = []
    for row_idx in range(2, raw.shape[0]):
        city = raw.iloc[row_idx, 0]
        if pd.isna(city):
            continue
        city = str(city).strip()
        for col_idx, yr, var_name in target_cols:
            val = raw.iloc[row_idx, col_idx + 1]  # +1 因为 year_row 从第1列开始
            records.append({
                '城市_raw': city,
                '年份': yr,
                'value': val
            })
    
    df = pd.DataFrame(records)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    return df


# ============================================================
# Part 3: 加载和处理所有数据文件
# ============================================================

def load_all_data():
    """加载所有 CEIC 和统计年鉴数据文件"""
    
    results = {}
    
    # --- CEIC 格式文件 ---
    ceic_files = {
        '财政收入': '地级市财政收入.csv',
        '财政支出': '地级市财政支出.csv',
        'GDP': '地级市总GDP.csv',
        '政府债务余额': '地方政府债务：地级市：余额.csv',
        '人均GDP': '地级市人均GDP.csv',
        '第二产业增加值': '地级市第二产业.csv',
        '科技支出': '财政支出：科学：地级市.csv',
    }
    
    for var_name, filename in ceic_files.items():
        print(f"  处理 CEIC 文件: {filename} -> {var_name}")
        try:
            df = parse_ceic_wide(filename)
            df['城市'] = df['城市_raw'].apply(standardize_city_name)
            df = df.rename(columns={'value': var_name})
            df = df[['城市', '年份', var_name]]
            # 去重：同一城市同一年份取第一个
            df = df.drop_duplicates(subset=['城市', '年份'], keep='first')
            results[var_name] = df
            print(f"    -> {len(df)} 条记录, {df['城市'].nunique()} 个城市")
        except Exception as e:
            print(f"    !! 错误: {e}")
    
    # --- 统计年鉴格式文件 ---
    yearbook_files = {
        '实际利用外资': ('实际利用外资.csv', '实际利用外资额(万美元)'),
        '金融机构贷款余额': ('金融机构贷款余额.csv', '各项贷款余额(万元)'),
        '常住人口': ('常住人口.csv', '常住人口(万人)'),
    }
    
    for var_name, (filename, keyword) in yearbook_files.items():
        print(f"  处理统计年鉴文件: {filename} -> {var_name} (关键词: {keyword})")
        try:
            df = parse_yearbook_format(filename, target_variable_keyword=keyword, encoding='gbk')
            df['城市'] = df['城市_raw'].apply(standardize_city_name)
            df = df.rename(columns={'value': var_name})
            df = df[['城市', '年份', var_name]]
            df = df.drop_duplicates(subset=['城市', '年份'], keep='first')
            results[var_name] = df
            print(f"    -> {len(df)} 条记录, {df['城市'].nunique()} 个城市")
        except Exception as e:
            print(f"    !! 错误: {e}")
    
    return results


# ============================================================
# Part 4: 合并面板数据并计算变量
# ============================================================

def build_regression_panel():
    """构建完整回归面板数据"""
    
    print("=" * 60)
    print("Step 1: 加载现有面板数据")
    print("=" * 60)
    
    panel = pd.read_csv('cleaned_data/final_regression_panel.csv', encoding='utf-8-sig')
    print(f"现有面板: {panel.shape[0]} 条, {panel['城市'].nunique()} 个城市, 年份 {panel['年份'].min()}-{panel['年份'].max()}")
    
    # 记录已有列（专利相关，兼容英文和中文列名）
    patent_cols = ['省份', '城市', '年份', '发明申请数', '专利申请总数', 
                   'ln_inv_patent', 'ln_patent_apply', 'inv_share',
                   '发明专利申请量_对数', '专利申请总量_对数', '发明专利占比']
    
    # 只保留专利核心列（其他列将从新数据重新填充）
    keep_cols = [c for c in patent_cols if c in panel.columns]
    panel = panel[keep_cols]
    
    # 重命名英文列为中文（如果源文件仍是英文列名）
    panel.rename(columns={
        'ln_inv_patent': '发明专利申请量_对数',
        'ln_patent_apply': '专利申请总量_对数',
        'inv_share': '发明专利占比',
    }, inplace=True)
    
    print(f"保留列: {panel.columns.tolist()}")
    
    print("\n" + "=" * 60)
    print("Step 2: 加载和解析所有经济/财政数据")
    print("=" * 60)
    
    data_dict = load_all_data()
    
    print("\n" + "=" * 60)
    print("Step 3: 合并数据到面板")
    print("=" * 60)
    
    panel_cities = set(panel['城市'].unique())
    
    for var_name, df in data_dict.items():
        # 匹配检查
        data_cities = set(df['城市'].unique())
        matched = panel_cities & data_cities
        unmatched_panel = panel_cities - data_cities
        
        print(f"\n--- {var_name} ---")
        print(f"  数据城市数: {len(data_cities)}")
        print(f"  面板匹配: {len(matched)}/{len(panel_cities)}")
        
        if len(unmatched_panel) > 0 and len(unmatched_panel) <= 20:
            print(f"  未匹配城市: {sorted(unmatched_panel)}")
        elif len(unmatched_panel) > 20:
            print(f"  未匹配城市数: {len(unmatched_panel)}")
        
        # 合并
        panel = panel.merge(df, on=['城市', '年份'], how='left')
    
    print("\n" + "=" * 60)
    print("Step 4: 计算核心解释变量和控制变量")
    print("=" * 60)
    
    # --- 单位统一（全部转为亿元人民币） ---
    # CEIC数据单位:
    #   财政收入/支出/债务/科技支出: 百万人民币 → ÷100 = 亿元
    #   GDP/第二产业增加值: 十亿人民币 → ×10 = 亿元
    #   人均GDP: 人民币（元），保持不变
    # 统计年鉴数据单位:
    #   实际利用外资: 万美元，保持不变
    #   金融机构贷款余额: 万元 → ÷10000 = 亿元
    #   常住人口: 万人，保持不变
    
    print("\n  单位转换:")
    for col in ['财政收入', '财政支出', '政府债务余额', '科技支出']:
        if col in panel.columns:
            panel[col] = panel[col] / 100  # 百万 → 亿
            print(f"    {col}: 百万→亿元")
    
    panel.rename(columns={'GDP': '地区生产总值'}, inplace=True)
    for col in ['地区生产总值', '第二产业增加值']:
        if col in panel.columns:
            panel[col] = panel[col] * 10  # 十亿 → 亿
            print(f"    {col}: 十亿→亿元")
    
    if '金融机构贷款余额' in panel.columns:
        panel['金融机构贷款余额'] = panel['金融机构贷款余额'] / 10000  # 万元 → 亿元
        print(f"    金融机构贷款余额: 万元→亿元")
    
    # --- 核心解释变量 ---
    
    # 财政缺口率 = (财政支出 - 财政收入) / 地区生产总值 （均为亿元）
    panel['财政缺口率'] = np.where(
        panel['地区生产总值'].notna() & (panel['地区生产总值'] != 0),
        (panel['财政支出'] - panel['财政收入']) / panel['地区生产总值'],
        np.nan
    )
    print(f"\n财政缺口率: {panel['财政缺口率'].notna().sum()} 非缺失 ({panel['财政缺口率'].notna().mean()*100:.1f}%)")
    
    # 债务率 = 政府债务余额 / 财政收入 （均为亿元，无量纲比值）
    panel['债务率'] = np.where(
        panel['财政收入'].notna() & (panel['财政收入'] != 0),
        panel['政府债务余额'] / panel['财政收入'],
        np.nan
    )
    print(f"债务率: {panel['债务率'].notna().sum()} 非缺失 ({panel['债务率'].notna().mean()*100:.1f}%)")
    
    # --- 控制变量 ---
    
    # 人均GDP_对数 —— 单位为元
    panel['人均GDP_对数'] = np.where(
        panel['人均GDP'].notna() & (panel['人均GDP'] > 0),
        np.log(panel['人均GDP']),
        np.nan
    )
    print(f"人均GDP_对数: {panel['人均GDP_对数'].notna().sum()} 非缺失 ({panel['人均GDP_对数'].notna().mean()*100:.1f}%)")
    
    # 第二产业占比 = 第二产业增加值 / 地区生产总值 （均为亿元）
    panel['第二产业占比'] = np.where(
        panel['地区生产总值'].notna() & (panel['地区生产总值'] != 0),
        panel['第二产业增加值'] / panel['地区生产总值'],
        np.nan
    )
    print(f"第二产业占比: {panel['第二产业占比'].notna().sum()} 非缺失 ({panel['第二产业占比'].notna().mean()*100:.1f}%)")
    
    # 科技支出占比 = 科技支出 / 财政支出 （均为亿元）
    panel['科技支出占比'] = np.where(
        panel['财政支出'].notna() & (panel['财政支出'] != 0),
        panel['科技支出'] / panel['财政支出'],
        np.nan
    )
    print(f"科技支出占比: {panel['科技支出占比'].notna().sum()} 非缺失 ({panel['科技支出占比'].notna().mean()*100:.1f}%)")
    
    # 外资依存度 = 实际利用外资(万美元) / 地区生产总值(亿元)
    # 保持原始比值，量纲为 万美元/亿元人民币，可直接反映相对依存度
    panel['外资依存度'] = np.where(
        panel['地区生产总值'].notna() & (panel['地区生产总值'] != 0) & panel['实际利用外资'].notna(),
        panel['实际利用外资'] / panel['地区生产总值'],
        np.nan
    )
    print(f"外资依存度: {panel['外资依存度'].notna().sum()} 非缺失 ({panel['外资依存度'].notna().mean()*100:.1f}%)")
    
    # 金融深度 = 金融机构贷款余额(亿元) / 地区生产总值(亿元)
    panel['金融深度'] = np.where(
        panel['地区生产总值'].notna() & (panel['地区生产总值'] != 0) & panel['金融机构贷款余额'].notna(),
        panel['金融机构贷款余额'] / panel['地区生产总值'],
        np.nan
    )
    print(f"金融深度: {panel['金融深度'].notna().sum()} 非缺失 ({panel['金融深度'].notna().mean()*100:.1f}%)")
    
    # 人均专利申请量 = 专利申请数 / 常住人口(万人)
    panel['人均专利申请量'] = np.where(
        panel['常住人口'].notna() & (panel['常住人口'] > 0),
        panel['专利申请总数'] / panel['常住人口'],
        np.nan
    )
    print(f"人均专利申请量: {panel['人均专利申请量'].notna().sum()} 非缺失 ({panel['人均专利申请量'].notna().mean()*100:.1f}%)")
    
    print("\n" + "=" * 60)
    print("Step 5: 生成滞后变量")
    print("=" * 60)
    
    # 按城市排序
    panel = panel.sort_values(['城市', '年份']).reset_index(drop=True)
    
    # 生成滞后一期
    lag_vars = ['财政缺口率', '债务率']
    for var in lag_vars:
        lag_name = f'{var}_滞后一期'
        panel[lag_name] = panel.groupby('城市')[var].shift(1)
        non_null = panel[lag_name].notna().sum()
        print(f"{lag_name}: {non_null} 非缺失 ({non_null/len(panel)*100:.1f}%)")
    
    print("\n" + "=" * 60)
    print("Step 6: 输出面板数据")
    print("=" * 60)
    
    # 定义最终列顺序
    final_cols = [
        # 标识
        '省份', '城市', '年份',
        # 被解释变量
        '发明申请数', '专利申请总数', '发明专利申请量_对数', '专利申请总量_对数', '发明专利占比',
        # 核心解释变量
        '财政缺口率', '财政缺口率_滞后一期', '债务率', '债务率_滞后一期',
        # 原始经济数据
        '财政收入', '财政支出', '地区生产总值', '政府债务余额',
        # 控制变量
        '人均GDP_对数', '第二产业占比', '科技支出占比', 
        '外资依存度', '金融深度', '人均专利申请量',
        # 原始控制变量数据
        '人均GDP', '第二产业增加值', '科技支出', 
        '实际利用外资', '金融机构贷款余额', '常住人口',
    ]
    
    # 只保留存在的列
    final_cols = [c for c in final_cols if c in panel.columns]
    panel = panel[final_cols]
    
    # 保存
    output_path = 'cleaned_data/final_regression_panel_v2.csv'
    panel.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n已保存: {output_path}")
    print(f"维度: {panel.shape}")
    print(f"城市数: {panel['城市'].nunique()}")
    print(f"年份: {panel['年份'].min()}-{panel['年份'].max()}")
    
    return panel


# ============================================================
# Part 5: 数据质量报告
# ============================================================

def generate_quality_report(panel):
    """生成数据质量报告"""
    
    print("\n" + "=" * 60)
    print("数据质量报告")
    print("=" * 60)
    
    # 变量覆盖率
    print("\n--- 变量覆盖率 ---")
    coverage_records = []
    for col in panel.columns:
        if col in ['省份', '城市', '年份']:
            continue
        total = len(panel)
        non_null = panel[col].notna().sum()
        coverage = non_null / total * 100
        
        # 按年份的覆盖率
        yearly = panel.groupby('年份')[col].apply(lambda x: x.notna().mean() * 100)
        
        record = {
            '变量': col,
            '非缺失数': non_null,
            '覆盖率(%)': round(coverage, 1),
            '最小值': round(panel[col].min(), 4) if panel[col].notna().any() else None,
            '中位数': round(panel[col].median(), 4) if panel[col].notna().any() else None,
            '最大值': round(panel[col].max(), 4) if panel[col].notna().any() else None,
        }
        
        # 添加各年覆盖率
        for yr in sorted(panel['年份'].unique()):
            record[f'{yr}年覆盖率'] = round(yearly.get(yr, 0), 1)
        
        coverage_records.append(record)
        print(f"  {col:25s}: {non_null:5d}/{total} ({coverage:5.1f}%)")
    
    coverage_df = pd.DataFrame(coverage_records)
    coverage_df.to_csv('cleaned_data/data_quality_report_v2.csv', index=False, encoding='utf-8-sig')
    print(f"\n质量报告已保存: cleaned_data/data_quality_report_v2.csv")
    
    # 核心变量描述统计
    print("\n--- 核心变量描述统计 ---")
    core_vars = ['发明专利申请量_对数', '财政缺口率', '财政缺口率_滞后一期', '债务率', '债务率_滞后一期',
                 '人均GDP_对数', '第二产业占比', '科技支出占比', 
                 '外资依存度', '金融深度', '人均专利申请量']
    core_vars = [v for v in core_vars if v in panel.columns]
    
    print(panel[core_vars].describe().round(4).to_string())
    
    # 缺失值汇总
    print("\n--- 缺失值最严重的变量 ---")
    missing = panel.isnull().sum().sort_values(ascending=False)
    for col, cnt in missing.items():
        if cnt > 0 and col not in ['省份']:
            print(f"  {col}: {cnt} 缺失 ({cnt/len(panel)*100:.1f}%)")
    
    return coverage_df


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 60)
    print("开始处理财政经济数据和控制变量")
    print("=" * 60)
    
    panel = build_regression_panel()
    report = generate_quality_report(panel)
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
