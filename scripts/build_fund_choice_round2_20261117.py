"""Prepare fixed within-fund allocation diagnostics; preserve all specified results."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import pandas as pd
from build_fund_trial_20261117 import SOURCE_REL, METADATA, KNOWN_STAGES, EARLY, MISSING, city_of, year_of

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '实证结果/fiscal_fund_design_round2_20261117'


def prune(data, required, effects):
    keep = data[required].notna().all(axis=1)
    while True:
        previous = keep.copy()
        for effect in effects:
            n = data.loc[keep].groupby(effect).size()
            keep &= data[effect].map(n).fillna(0).ge(2)
        ny = data.loc[keep].groupby('fund_id').year.nunique()
        keep &= data.fund_id.map(ny).fillna(0).ge(2)
        if previous.equals(keep):
            return keep


def residualize_target(data, target, others, effects):
    blocks = [np.ones((len(data), 1))]
    blocks += [data[others].to_numpy()] if others else []
    blocks += [pd.get_dummies(data[c], drop_first=True, dtype=float).to_numpy() for c in effects]
    x = np.column_stack(blocks)
    y = data[target].to_numpy()
    residual = y - x @ np.linalg.lstsq(x, y, rcond=None)[0]
    sums = pd.Series(residual**2).groupby(data.source_id.to_numpy()).sum()
    return {'residual_sd': float(np.std(residual)), 'supporting_source_cities': int(sums.gt(1e-10).sum()), 'design_rank': int(np.linalg.matrix_rank(x))}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / SOURCE_REL
    with source.open(encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        fields = [c for c in reader.fieldnames if c not in METADATA]
        raw = list(reader)
    seen, rows = set(), []
    for i, r in enumerate(raw, 2):
        key = tuple(r[c] for c in fields) + tuple(r[c] for c in ['基金级别', '基金分类', '注册地区_基金目录'])
        if key in seen:
            continue
        seen.add(key)
        year, city = year_of(r['投资时间']), city_of(r['注册地区_基金目录'])
        if year is None or not 2015 <= year <= 2024 or city is None or r['基金级别'] != '地市级':
            continue
        name = r['基金全称'] if r['基金全称'] not in MISSING else r['基金名称']
        if name in MISSING:
            continue
        rows.append(dict(event_id=i, fund_name=name, source_city=city, recipient_city=city_of(r['地区']),
                         sector=r['行业(清科)'].split('|')[0], year=year,
                         early=int(r['投资阶段'] in EARLY) if r['投资阶段'] in KNOWN_STAGES else np.nan))
    d = pd.DataFrame(rows)
    macro = pd.read_csv(ROOT / '面板数据/fiscal_macro_trial_20261117.csv')
    rename = {'city': 'source_city', 'fiscal_gap': 'p', 'debt_ratio': 'debt', 'ln_gdp': 'l_gdp', 'secondary_share': 'l_secondary'}
    lag = macro[['city', 'year', 'fiscal_gap', 'debt_ratio', 'ln_gdp', 'secondary_share']].rename(columns=rename)
    lag.year += 1
    d = d.merge(lag, on=['source_city', 'year'], how='left', validate='many_to_one')
    for new, value in [('fund_id', d.fund_name + '|' + d.source_city), ('source_id', d.source_city),
                       ('sector_id', d.sector), ('destination_year', d.recipient_city.fillna('__missing__') + '|' + d.year.astype(str))]:
        d[new] = pd.Categorical(value).codes + 1
    d['pd'] = d.p * d.debt
    base = ['early', 'p', 'l_gdp', 'l_secondary']
    effects1 = ['fund_id', 'year', 'sector_id']
    effects2 = ['fund_id', 'destination_year', 'sector_id']
    d['use_F1'] = prune(d, base, effects1).astype(int)
    d['use_F2'] = prune(d, base + ['recipient_city'], effects2).astype(int)
    d['use_F2a'] = d.use_F2
    d['use_F3'] = prune(d, base + ['debt'], effects1).astype(int)
    d['use_F3a'] = d.use_F3
    models = [
        ('F1', 'p', ['l_gdp','l_secondary'], effects1, 'p l_gdp l_secondary i.year i.sector_id'),
        ('F2a', 'p', ['l_gdp','l_secondary'], effects1, 'p l_gdp l_secondary i.year i.sector_id'),
        ('F2', 'p', ['l_gdp','l_secondary'], effects2, 'p l_gdp l_secondary i.destination_year i.sector_id'),
        ('F3a', 'p', ['l_gdp','l_secondary'], effects1, 'p l_gdp l_secondary i.year i.sector_id'),
        ('F3', 'pd', ['p','debt','l_gdp','l_secondary'], effects1, 'p debt pd l_gdp l_secondary i.year i.sector_id'),
    ]
    audit = []
    for model, target, controls, effects, rhs in models:
        s = d[d[f'use_{model}'].eq(1)]
        diag = residualize_target(s, target, controls, effects)
        audit.append(dict(model=model, N=len(s), funds=s.fund_id.nunique(), cities=s.source_id.nunique(),
                          years=[int(s.year.min()), int(s.year.max())], target=target, rhs=rhs, **diag))
    outfile = ROOT / '面板数据/fund_choice_round2_20261117.csv'
    d.to_csv(outfile, index=False, encoding='utf-8-sig')
    payload = {'input_source': str(SOURCE_REL), 'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'output_sha256': hashlib.sha256(outfile.read_bytes()).hexdigest(),
               'raw_municipal_events_with_names': len(d), 'known_stage_events': int(d.early.notna().sum()),
               'models': audit, 'fund_identity': 'exact fund full name (fallback short name) plus registration city',
               'zero_filling': False, 'geography': 'fund registration proxy; recipient city never used to fill source city'}
    (OUT / 'fund_choice_audit.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
