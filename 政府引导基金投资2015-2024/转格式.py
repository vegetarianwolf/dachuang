import os
import glob
import pandas as pd

def batch_convert_xls_to_csv(folder_path):
    # 使用 glob 获取该目录下所有的 .xls 文件
    search_pattern = os.path.join(folder_path, "*.xls")
    xls_files = glob.glob(search_pattern)

    if not xls_files:
        print(f"在 {folder_path} 中未找到任何 .xls 文件，请检查路径。")
        return

    print(f"共找到 {len(xls_files)} 个 .xls 文件，开始转换...\n")
    print("-" * 40)

    success_count = 0
    fail_count = 0

    for file in xls_files:
        try:
            # 读取 .xls 文件
            df = pd.read_excel(file, engine='xlrd')
            
            # 构造输出的 .csv 文件路径（替换扩展名）
            csv_file = os.path.splitext(file)[0] + ".csv"
            
            # 保存为 .csv 文件
            # encoding='utf-8-sig' 可以确保带有中文字符的 CSV 在 Excel 中打开时不会乱码
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            print(f"[\u2713] 成功: {os.path.basename(file)} -> {os.path.basename(csv_file)}")
            success_count += 1
            
        except Exception as e:
            print(f"[\u2717] 失败: 无法转换 {os.path.basename(file)}。错误信息: {e}")
            fail_count += 1

    print("-" * 40)
    print(f"转换任务结束！成功: {success_count} 个，失败: {fail_count} 个。")

if __name__ == "__main__":
    # 你指定的文件夹路径
    target_folder = r"C:\Users\21288\Desktop\DACHUANG\dachuang\政府引导基金投资2015-2024"
    
    batch_convert_xls_to_csv(target_folder)