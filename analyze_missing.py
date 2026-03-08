# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

df = pd.read_csv('cleaned_data/final_regression_panel_v2.csv', encoding='utf-8-sig')
total = len(df)

print('='*70)
print('一、各变量缺失情况总览')
print('='*70)
for col in df.columns:
    m = df[col].isna().sum()
    if m > 0:
        print('  {:20s}: 缺失 {:5d} 条 ({:5.1f}%)'.format(col, m, m/total*100))

print()
print('='*70)
print('二、哪些城市完全没有CEIC经济数据？')
print('='*70)
cities_no_gdp = df.groupby('城市')['地区生产总值'].apply(lambda x: x.isna().all())
missing_cities = sorted(cities_no_gdp[cities_no_gdp].index.tolist())
print('  完全无GDP数据的城市: {}个'.format(len(missing_cities)))
non_city = [c for c in missing_cities if not c.endswith('市')]
city_type = [c for c in missing_cities if c.endswith('市')]
if non_city:
    print('  其中 非市建制 ({}个):'.format(len(non_city)))
    for i in range(0, len(non_city), 4):
        print('    ' + ', '.join(non_city[i:i+4]))
if city_type:
    print('  其中 市建制但CEIC无数据 ({}个):'.format(len(city_type)))
    for c in city_type:
        print('    ' + c)

print()
print('='*70)
print('三、按年份分析核心变量缺失')
print('='*70)
vars_check = ['财政缺口率','债务率','人均GDP_对数','第二产业占比',
              '科技支出占比','外资依存度','金融深度','人均专利申请量']
for var in vars_check:
    print('  [{}]'.format(var))
    for yr in sorted(df['年份'].unique()):
        sub = df[df['年份']==yr]
        m = sub[var].isna().sum()
        t = len(sub)
        bar = '#' * int(m/t*40)
        print('    {}: 缺失 {:3d}/{:3d} ({:5.1f}%) {}'.format(yr, m, t, m/t*100, bar))
    print()

print('='*70)
print('四、缺失来源归类')
print('='*70)

# 4.1 债务数据
print('  [债务率]')
debt_city = df.groupby('城市')['债务率'].apply(lambda x: x.notna().sum())
print('    有债务数据的城市: {}个'.format((debt_city>0).sum()))
print('    完全无债务数据: {}个'.format((debt_city==0).sum()))
debt_yr = df.groupby('年份')['债务率'].apply(lambda x: x.notna().sum())
for y,n in sorted(debt_yr.items()):
    print('      {}年: {}个城市有数据'.format(y, n))

# 4.2 金融深度
print('  [金融深度]')
fin_city = df.groupby('城市')['金融深度'].apply(lambda x: x.notna().sum())
print('    有数据的城市: {}个'.format((fin_city>0).sum()))
fin_yr = df.groupby('年份')['金融深度'].apply(lambda x: x.notna().sum())
for y,n in sorted(fin_yr.items()):
    print('      {}年: {}个城市有数据'.format(y, n))

# 4.3 外资
print('  [外资依存度]')
fdi_city = df.groupby('城市')['外资依存度'].apply(lambda x: x.notna().sum())
print('    有数据的城市: {}个'.format((fdi_city>0).sum()))
fdi_yr = df.groupby('年份')['外资依存度'].apply(lambda x: x.notna().sum())
for y,n in sorted(fdi_yr.items()):
    print('      {}年: {}个城市有数据'.format(y, n))

# 4.4 常住人口
print('  [常住人口]')
pop_yr = df.groupby('年份')['常住人口'].apply(lambda x: x.notna().sum())
for y,n in sorted(pop_yr.items()):
    print('      {}年: {}个城市有数据'.format(y, n))

print()
print('='*70)
print('五、回归可行性评估（同时非缺失的观测数）')
print('='*70)

combos = [
    ('基准回归(无debt)', ['发明专利申请量_对数','财政缺口率_滞后一期','人均GDP_对数','第二产业占比']),
    ('基准+科技支出', ['发明专利申请量_对数','财政缺口率_滞后一期','人均GDP_对数','第二产业占比','科技支出占比']),
    ('加入债务率', ['发明专利申请量_对数','财政缺口率_滞后一期','债务率_滞后一期','人均GDP_对数','第二产业占比']),
    ('全部控制变量', ['发明专利申请量_对数','财政缺口率_滞后一期','人均GDP_对数','第二产业占比','科技支出占比','外资依存度','金融深度','人均专利申请量']),
]
for name, cols in combos:
    c = df.dropna(subset=cols)
    print('  {}:'.format(name))
    print('    观测数: {:,}/{:,} ({:.1f}%)'.format(len(c), total, len(c)/total*100))
    print('    城市数: {}'.format(c['城市'].nunique()))
    print('    年份: {}-{}'.format(c['年份'].min(), c['年份'].max()))
    print()
