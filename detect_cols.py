import pandas as pd
import codecs

with codecs.open(r'c:\Users\21288\Desktop\DACHUANG\dachuang\cols.txt', 'w', encoding='utf-8') as f:
    df1 = pd.read_csv(r'c:\Users\21288\Desktop\DACHUANG\dachuang\清科政府引导基金投资事件截止到2024年\政府引导基金投资1999.csv', nrows=2)
    f.write("Investment columns:\n")
    for c in df1.columns:
        f.write(c + "\n")
        
    df2 = pd.read_csv(r'c:\Users\21288\Desktop\DACHUANG\dachuang\政府引导基金相关信息\政府引导基金1 的副本.csv', nrows=2)
    f.write("\nGuidance fund info columns:\n")
    for c in df2.columns:
        f.write(c + "\n")
