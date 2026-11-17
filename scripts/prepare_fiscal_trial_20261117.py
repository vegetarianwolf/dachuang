"""Join calendar-year covariates and generate a fixed, fully reported Stata trial."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '实证结果/fiscal_fund_trial_20261117'
PANEL = ROOT / '面板数据'
CTRL = ['l_gdp', 'l_secondary']


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'samples').mkdir(exist_ok=True)
    macro = pd.read_csv(PANEL / 'fiscal_macro_trial_20261117.csv')
    fund = pd.read_csv(PANEL / 'fund_trial_20261117.csv')
    assert not macro.duplicated(['city', 'year']).any()
    assert not fund.duplicated(['sample', 'city', 'year']).any()
    lag_map = {'fiscal_gap': 'p', 'debt_ratio': 'd', 'ln_gdp': 'l_gdp',
               'secondary_share': 'l_secondary', 'ln_scitech': 'l_scitech'}
    lag = macro[['city', 'year', *lag_map]].rename(columns=lag_map)
    lag['year'] += 1
    data = fund.merge(lag, on=['city', 'year'], how='left', validate='many_to_one')
    for h in (1, 2):
        f = macro[['city', 'year', 'ln_pat_apply', 'ln_pat_grant']].copy()
        f['year'] -= h
        f = f.rename(columns={'ln_pat_apply': f'y{h}', 'ln_pat_grant': f'grant{h}'})
        data = data.merge(f, on=['city', 'year'], how='left', validate='many_to_one')
    data['g'] = np.log1p(data.inv_count)
    data['ln_amount'] = np.log1p(data.complete_amount_rmb_m)
    data['city_id'] = pd.Categorical(data.city).codes + 1
    # Distinct panel IDs for the two overlapping geographical definitions.
    data['panel_id'] = pd.Categorical(data['sample'] + ':' + data.city).codes + 1
    c = ' '.join(CTRL)
    specs = [
        ('I1', 'y1', 'c.g##c.p', 'c.g#c.p', ['y1', 'g', 'p', *CTRL], 2022, '', 1),
        ('I2', 'y1', f'c.g##c.p {c}', 'c.g#c.p', ['y1', 'g', 'p', *CTRL], 2022, '', 1),
        ('I3', 'y1', f'c.g##c.p {c}', 'c.g#c.p', ['y1', 'y2', 'g', 'p', *CTRL], 2021, '', 1),
        ('I4', 'y2', f'c.g##c.p {c}', 'c.g#c.p', ['y1', 'y2', 'g', 'p', *CTRL], 2021, '', 1),
        ('I5', 'y1', f'c.g##c.p {c}', 'c.g#c.p', ['y1', 'g', 'p', 'd', *CTRL], 2022, '', 1),
        ('I6', 'y1', f'c.g##c.p##c.d {c}', 'c.g#c.p#c.d', ['y1', 'g', 'p', 'd', *CTRL], 2022, '', 2),
        ('I7a', 'y1', f'c.g##c.p {c}', 'c.g#c.p', ['y1', 'g', 'p', 'l_scitech', *CTRL], 2022, '', 1),
        ('I7', 'y1', f'c.g##c.p {c} l_scitech', 'c.g#c.p', ['y1', 'g', 'p', 'l_scitech', *CTRL], 2022, '', 1),
        ('I8', 'grant1', f'c.g##c.p {c}', 'c.g#c.p', ['grant1', 'g', 'p', *CTRL], 2022, '', 1),
        ('I9', 'y1', f'early_share g p {c}', 'early_share', ['y1', 'early_share', 'g', 'p', *CTRL], 2022, '', 0),
        ('I10', 'y1', f'c.g##c.p {c}', 'c.g#c.p', ['y1', 'g', 'p', *CTRL], 2023, '', 1),
        ('B1', 'g', f'p {c}', 'p', ['g', 'p', *CTRL], 2024, '', 0),
        ('B2', 'early_share', f'p {c}', 'p', ['early_share', 'p', *CTRL], 2024, '', 0),
        ('B3', 'early_share', f'p {c}', 'p', ['early_share', 'p', *CTRL], 2024, 'known_count', 0),
        ('B4', 'early_share', f'p {c} electronic_share biomedical_share industry_known_share', 'p',
         ['early_share', 'p', *CTRL, 'electronic_share', 'biomedical_share', 'industry_known_share'], 2024, '', 0),
        ('B5', 'early_share', f'c.p##c.d {c}', 'c.p#c.d', ['early_share', 'p', 'd', *CTRL], 2024, '', 0),
        ('B6', 'ln_amount', f'p {c}', 'p', ['ln_amount', 'p', *CTRL], 2024, '', 0),
        ('B7', 'known_share', f'p {c}', 'p', ['known_share', 'p', *CTRL], 2024, '', 0),
    ]
    attrition, manifest = [], []
    for model, y, rhs, target, required, maxyear, weight, margin in specs:
        eligible = data[required].notna().all(axis=1) & data.year.between(2015, maxyear)
        group_n = eligible.groupby([data['sample'], data.city]).transform('sum')
        data[f'use_{model}'] = (eligible & (group_n >= 2)).astype(int)
        for scope in ['municipal', 'broad']:
            s = data['sample'].eq(scope)
            chosen = data[s & data[f'use_{model}'].eq(1)]
            attrition.append(dict(scope=scope, model=model, observed_city_years=int(s.sum()),
                                  complete_before_singletons=int((s & eligible).sum()),
                                  singleton_rows_removed=int((s & eligible & (group_n < 2)).sum()),
                                  N=len(chosen), cities=chosen.city.nunique()))
        manifest.append(dict(model=model, outcome=y, rhs=rhs, target=target,
                             required=required, investment_year_max=maxyear, weight=weight))
    assert np.isfinite(data.select_dtypes('number').to_numpy()[~data.select_dtypes('number').isna()]).all()
    data.to_csv(PANEL / 'fiscal_fund_trial_20261117.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(attrition).to_csv(OUT / 'sample_attrition.csv', index=False)
    (OUT / 'model_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    files = ['fund_trial_20261117.csv', 'fiscal_macro_trial_20261117.csv', 'fiscal_fund_trial_20261117.csv']
    (OUT / 'analysis_input_hashes.json').write_text(json.dumps({f: hashlib.sha256((PANEL/f).read_bytes()).hexdigest() for f in files}, indent=2))
    template = (ROOT / 'scripts/fiscal_trial_stata_template.do').read_text()
    calls = []
    for scope in ['municipal', 'broad']:
        for model, y, rhs, target, required, maxyear, weight, margin in specs:
            w = f' weight({weight})' if weight else ''
            calls.append(f'trial, scope({scope}) model({model}) outcome({y}) rhs("{rhs}") target("{target}") flag(use_{model}) margin({margin}){w}')
    text = template.replace('* MODEL_CALLS', '\n'.join(calls))
    dofile = ROOT / '运行日志与do代码/xtreg_fiscal_fund_trial_20261117.do'
    dofile.write_text(text, encoding='utf-8')
    print(pd.DataFrame(attrition).to_string(index=False))
    print(dofile)


if __name__ == '__main__':
    main()
