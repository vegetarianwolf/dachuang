import os
import pandas as pd

folder_path = r"c:\Users\21288\Desktop\DACHUANG\dachuang\清科政府引导基金投资事件截止到2024年"

for filename in os.listdir(folder_path):
    if filename.endswith(".xls"):
        xls_path = os.path.join(folder_path, filename)
        csv_filename = filename[:-4] + ".csv"
        csv_path = os.path.join(folder_path, csv_filename)
        print(f"Converting {filename} to {csv_filename}...")
        try:
            df = pd.read_excel(xls_path)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig') # use utf-8 with BOM for excel compatibility
            print(f"Success: {csv_filename}")
        except Exception as e:
            print(f"Failed to convert {filename}: {e}")
