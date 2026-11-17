"""Prepare finite micro trajectory specifications and executable Stata models."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '实证结果/fiscal_fund_design_round2_20261117'


def main():
    (OUT / 'samples').mkdir(exist_ok=True)
    micro = pd.read_csv(ROOT / '面板数据/micro_fiscal_round2_20261117.csv')
    micro = micro[micro.scope.eq('municipal')].copy()
    assert not micro.duplicated(['firm_id', 'year']).any()
    meta = micro.drop_duplicates('firm_id').copy()
    cols = ['firm_id', 'firm_name', 'first_year', 'first_any_observed_fund_year', 'earlier_other_fund_observed',
            'source_city', 'n_initial_source_cities', 'p_initial', 'initial_ln_gdp', 'initial_secondary_share']
    d = meta[cols].rename(columns={'firm_id':'unit_id','firm_name':'unit_name','first_year':'year',
                                   'p_initial':'p','initial_ln_gdp':'l_gdp','initial_secondary_share':'l_secondary'})
    pivot = micro.pivot(index='firm_id', columns='relative_year', values='apply_invention')
    for h in [-3, -2, -1, 1, 2, 3]:
        key = ('pre' if h < 0 else 'post') + str(abs(h))
        d[key] = d.unit_id.map(np.log1p(pivot[h]))
    d['change1'] = d.post1 - d.pre1
    d['pretrend'] = d.pre1 - d.pre2
    six = ['pre3','pre2','pre1','post1','post2','post3']
    d['change3'] = (d[['post1','post2','post3']].mean(axis=1) - d[['pre1','pre2','pre3']].mean(axis=1)).where(d[six].notna().all(axis=1))
    common = d.year.between(2016, 2022) & d.n_initial_source_cities.eq(1) & d.earlier_other_fund_observed.eq(0)
    controls = ['p','l_gdp','l_secondary']
    rules = {'M1':['change1'], 'M2':['change1','pre1'], 'M3':['change1','pretrend'], 'M4':['change1','pretrend'], 'M5':six, 'M6':six}
    audit = []
    for model, req in rules.items():
        flag = common & d[controls + req].notna().all(axis=1)
        if model in ['M5','M6']:
            flag &= d.year.le(2020)
        d[f'use_{model}'] = flag.astype(int)
        s = d[flag]
        audit.append(dict(model=model,N=len(s),cities=s.source_city.nunique(),years=[int(s.year.min()), int(s.year.max())] if len(s) else []))
    d['obs_id'] = np.arange(1, len(d)+1)
    d['source_id'] = pd.Categorical(d.source_city).codes + 1
    outfile = ROOT / '面板数据/firm_changes_round2_20261117.csv'
    d.to_csv(outfile,index=False,encoding='utf-8-sig')
    payload = {'firm_count':len(d),'initial_unique_city':int(d.n_initial_source_cities.eq(1).sum()),
               'earlier_other_observed_excluded':int(d.earlier_other_fund_observed.sum()),
               'models':audit,'window3':'six non-event years complete; does not require patent observation in event year',
               'source_sha256':hashlib.sha256((ROOT/'面板数据/micro_fiscal_round2_20261117.csv').read_bytes()).hexdigest(),
               'output_sha256':hashlib.sha256(outfile.read_bytes()).hexdigest()}
    (OUT/'firm_changes_audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    template=(ROOT/'scripts/round2_stata_template.do').read_text()
    fund=json.loads((OUT/'fund_choice_audit.json').read_text())['models']
    calls=['import delimited using "`root\'/面板数据/fund_choice_round2_20261117.csv", clear varnames(1) encoding(UTF-8) case(preserve)',
           'rename event_id obs_id', 'rename fund_id unit_id','rename fund_name unit_name']
    for f in fund:
        calls.append(f'est, group(fund) model({f["model"]}) y(early) rhs("{f["rhs"]}") target({f["target"]}) flag(use_{f["model"]}) absorb(unit_id)')
    calls += ['import delimited using "`root\'/面板数据/firm_changes_round2_20261117.csv", clear varnames(1) encoding(UTF-8) case(preserve)']
    for model in rules:
        y = 'pretrend' if model == 'M4' else 'change3' if model == 'M5' else 'change1'
        rhs='p l_gdp l_secondary i.year' + (' pre1' if model=='M2' else '')
        calls.append(f'est, group(firm) model({model}) y({y}) rhs("{rhs}") target(p) flag(use_{model})')
    (ROOT/'运行日志与do代码/fiscal_fund_micro_round2_20261117.do').write_text(template.replace('* MODEL_CALLS','\n'.join(calls)),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
