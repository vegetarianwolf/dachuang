import os
import glob
import pandas as pd

# Directories
SOURCE_INFO_DIR = r"c:\Users\21288\Desktop\DACHUANG\dachuang\政府引导基金相关信息"
SOURCE_INVEST_DIR = r"c:\Users\21288\Desktop\DACHUANG\dachuang\清科政府引导基金投资事件截止到2024年"
OUTPUT_DIR = r"c:\Users\21288\Desktop\DACHUANG\dachuang\清科政府引导基金投资事件_加注册地区"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_mapping():
    mapping = {}
    info_files = glob.glob(os.path.join(SOURCE_INFO_DIR, "*.csv"))
    
    total_fund_records = 0
    mapped_funds = 0
    
    for file in info_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file, encoding='gbk')
            
        if '注册地区' in df.columns:
            has_short = '基金简称' in df.columns
            has_full = '基金全称' in df.columns
            
            for _, row in df.iterrows():
                region = str(row['注册地区']).strip()
                if region == 'nan':
                    continue
                
                added = False
                if has_short:
                    short_name = str(row['基金简称']).strip()
                    if short_name != 'nan' and len(short_name) > 1: # avoid matching single characters
                        mapping[short_name] = region
                        added = True
                        
                if has_full:
                    full_name = str(row['基金全称']).strip()
                    if full_name != 'nan' and len(full_name) > 1:
                        mapping[full_name] = region
                        added = True
                        
                if added:
                    mapped_funds += 1
                total_fund_records += 1
    
    print(f"Loaded {len(info_files)} info files.")
    print(f"Parsed {total_fund_records} records, built {len(mapping)} unique mappings.")
    
    # Sort mapping keys by length descending to match the longest (most specific) string first
    sorted_mapping = {k: v for k, v in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True)}
    return sorted_mapping

def find_match(investor_name, mapping):
    if not isinstance(investor_name, str) or investor_name == 'nan':
        return "未匹配"
    
    investor_name = investor_name.strip()
    
    # 1. Exact match
    if investor_name in mapping:
        return mapping[investor_name]
        
    # 2. Substring match: fund name is in investor name
    for fund_name, region in mapping.items():
        if fund_name in investor_name:
            return region
            
    # 3. Substring match: investor name is in fund name
    for fund_name, region in mapping.items():
        if len(investor_name) > 3 and investor_name in fund_name:
            return region
            
    return "未匹配"

def process_investments(mapping):
    invest_files = glob.glob(os.path.join(SOURCE_INVEST_DIR, "*.csv"))
    
    total_rows = 0
    matched_rows = 0
    file_stats = []
    
    for file in invest_files:
        filename = os.path.basename(file)
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except Exception:
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except Exception:
                df = pd.read_csv(file, encoding='gbk')
        
        file_total = len(df)
        file_matched = 0
        
        if '投资方' in df.columns:
            df['基金注册地区'] = df['投资方'].apply(lambda x: find_match(str(x), mapping))
            file_matched = (df['基金注册地区'] != "未匹配").sum()
        
        output_file = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        file_stats.append({
            '文件名': filename,
            '总行数': file_total,
            '匹配成功行数': file_matched,
            '匹配率(%)': round(file_matched / file_total * 100, 2) if file_total > 0 else 0
        })
        
        total_rows += file_total
        matched_rows += file_matched
        print(f"Processed {filename}: {file_matched}/{file_total} matched.")
        
    return total_rows, matched_rows, file_stats

def write_summary(total_rows, matched_rows, file_stats):
    summary_file = os.path.join(OUTPUT_DIR, "匹配情况说明.md")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# 政府引导基金投资事件匹配情况说明\n\n")
        f.write("## 总体汇总\n")
        f.write(f"- **总处理事件数 (Total Rows)**: {total_rows}\n")
        f.write(f"- **匹配成功事件数 (Matched Rows)**: {matched_rows}\n")
        f.write(f"- **总体匹配率**: {round(matched_rows / total_rows * 100, 2) if total_rows > 0 else 0}%\n\n")
        f.write("> **匹配逻辑说明**：\n> 1. 数据源：同时使用了引导基金的“**基金简称**”和“**基金全称**”作为匹配关键字库。\n> 2. 精确匹配：投资方名称与基金简称或全称完全一致。\n> 3. 包含匹配：投资方名称包含基金简称或全称（优先匹配较长的基金名称以提高准确率）。\n> 4. 反向包含匹配：投资方名称（长度>3）被包含在基金简称或全称中。\n\n")
        
        f.write("## 各文件匹配详情\n")
        f.write("| 文件名 | 总行数 | 匹配成功数 | 匹配率(%) |\n")
        f.write("| --- | --- | --- | --- |\n")
        for stat in file_stats:
            f.write(f"| {stat['文件名']} | {stat['总行数']} | {stat['匹配成功行数']} | {stat['匹配率(%)']} |\n")
            
    print(f"Summary generated at {summary_file}")

if __name__ == "__main__":
    print("Building Fund Mappings...")
    fund_mapping = build_mapping()
    
    print("\nProcessing Investment Files...")
    total_r, matched_r, stats = process_investments(fund_mapping)
    
    print("\nWriting Summary...")
    write_summary(total_r, matched_r, stats)
    
    print("Done!")
