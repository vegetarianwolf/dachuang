# -*- coding: utf-8 -*-
"""将当前目录下所有 .xlsx 和 .xls 文件转为 CSV"""
import os
import pandas as pd

def convert_excel_to_csv():
    folder = os.path.dirname(os.path.abspath(__file__))
    os.chdir(folder)
    
    for f in os.listdir(folder):
        if not (f.endswith('.xlsx') or f.endswith('.xls')):
            continue
        if f.startswith('~$'):  # 跳过 Excel 临时文件
            continue
        path = os.path.join(folder, f)
        base = os.path.splitext(f)[0]
        try:
            if f.endswith('.xlsx'):
                xl = pd.ExcelFile(path, engine='openpyxl')
            else:
                xl = pd.ExcelFile(path, engine='xlrd')
            for i, sheet in enumerate(xl.sheet_names):
                df = pd.read_excel(xl, sheet_name=sheet, header=None)
                if len(xl.sheet_names) == 1:
                    out = os.path.join(folder, base + '.csv')
                else:
                    out = os.path.join(folder, f'{base}_sheet{i+1}_{sheet}.csv')
                df.to_csv(out, index=False, encoding='utf-8-sig')
                print(f'已生成: {os.path.basename(out)}')
        except Exception as e:
            print(f'失败 {f}: {e}')

if __name__ == '__main__':
    convert_excel_to_csv()
