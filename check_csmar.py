import pandas as pd

ci = pd.read_csv('cleaned_data/csmar_firm_info.csv', encoding='utf-8-sig')
print('Shape:', ci.shape)
print(ci.head(5).to_string())
print('\nind2_csrc distribution:')
print(ci['ind2_csrc'].value_counts().head(15))

panel = pd.read_csv('cleaned_data/lisen_replication_panel.csv', encoding='utf-8-sig')
p_firms = set(panel['Scode'].unique())
c_firms = set(ci['Scode'].unique())
overlap = p_firms & c_firms
print(f'\nPanel: {len(p_firms)}, CSMAR: {len(c_firms)}, Overlap: {len(overlap)}')
