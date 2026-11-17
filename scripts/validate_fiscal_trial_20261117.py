"""Independent calendar, sample, hash, and fixed-effects regression validation.

Uses NumPy dummy-variable OLS/WLS, not Stata or the model-generating code.
Only reproduces already specified models; no specification search is performed.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '实证结果/fiscal_fund_trial_20261117'
PANEL = ROOT / '面板数据'


def beta_fraction(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularized incomplete beta function."""
    tiny = 1e-300
    qab, qap, qam = a+b, a+1, a-1
    c, d = 1., 1.-qab*x/qap
    d = 1./(d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 301):
        aa = m*(b-m)*x/((qam+2*m)*(a+2*m))
        d = 1.+aa*d
        c = 1.+aa/c
        d = 1./(d if abs(d) > tiny else tiny)
        c = c if abs(c) > tiny else tiny
        h *= d*c
        aa = -(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m))
        d = 1.+aa*d
        c = 1.+aa/c
        d = 1./(d if abs(d) > tiny else tiny)
        c = c if abs(c) > tiny else tiny
        delta = d*c
        h *= delta
        if abs(delta-1.) < 2e-14:
            return h
    raise AssertionError('Incomplete-beta continued fraction did not converge')


def beta_regularized(a: float, b: float, x: float) -> float:
    if x <= 0:
        return 0.
    if x >= 1:
        return 1.
    factor = math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)
                      + a*math.log(x) + b*math.log1p(-x))
    if x < (a+1)/(a+b+2):
        return factor*beta_fraction(a, b, x)/a
    return 1-factor*beta_fraction(b, a, 1-x)/b


def t_pvalue(value: float, df: int) -> float:
    return beta_regularized(df/2, .5, df/(df+value*value))


def t_critical(df: int) -> float:
    low, high = 0., 100.
    for _ in range(70):
        mid = (low+high)/2
        if t_pvalue(mid, df) > .05:
            low = mid
        else:
            high = mid
    return (low+high)/2


def assert_close(actual, expected, message, atol=1e-8, rtol=1e-8):
    assert np.allclose(actual, expected, atol=atol, rtol=rtol, equal_nan=True), message


def regression_check(scope, model, results):
    data = pd.read_csv(OUT / f'samples/{scope}_{model}.csv')
    if model == 'I2':
        outcome = 'y1'
        terms = ['g', 'p', 'gp', 'l_gdp', 'l_secondary']
        target = 'gp'
    elif model == 'I6':
        outcome = 'y1'
        terms = ['g', 'p', 'd', 'gp', 'gd', 'pd', 'gpd', 'l_gdp', 'l_secondary']
        target = 'gpd'
    else:
        outcome = 'g' if model == 'B1' else 'early_share'
        terms, target = ['p', 'l_gdp', 'l_secondary'], 'p'
    data['gp'], data['gd'], data['pd'] = data.g*data.p, data.g*data.d, data.p*data.d
    data['gpd'] = data.g*data.p*data.d
    y = data[outcome].to_numpy()
    design = pd.concat([data[terms], pd.get_dummies(data.year, prefix='year', drop_first=True, dtype=float),
                        pd.get_dummies(data.city, prefix='city', drop_first=True, dtype=float)], axis=1)
    design.insert(0, 'constant', 1.)
    x = design.to_numpy(dtype=float)
    weights = data.known_count.to_numpy() if model == 'B3' else np.ones(len(data))
    beta = np.linalg.lstsq(x*np.sqrt(weights[:, None]), y*np.sqrt(weights), rcond=None)[0]
    resid = y-x@beta
    bread = np.linalg.pinv(x.T@(weights[:, None]*x), rcond=1e-14)
    scores = np.vstack([(x[data.city.eq(city)]*(weights*resid)[data.city.eq(city), None]).sum(axis=0)
                        for city in data.city.unique()])
    n, clusters = len(data), data.city.nunique()
    rank = np.linalg.matrix_rank(x)
    # Stata xtreg excludes absorbed city degrees of freedom when clustered by city.
    # areg counts them, giving its documented, more conservative WLS correction.
    k = rank if model == 'B3' else rank-(clusters-1)
    correction = clusters/(clusters-1)*(n-1)/(n-k)
    covariance = (bread@(scores.T@scores)@bread)*correction
    j = design.columns.get_loc(target)
    b, se = beta[j], math.sqrt(covariance[j, j])
    p = t_pvalue(b/se, clusters-1)
    critical = t_critical(clusters-1)
    row = results.query('scope == @scope and model == @model').iloc[0]
    assert_close(b, row.b, f'{scope} {model} coefficient', atol=2e-8)
    assert_close(se, row.se, f'{scope} {model} clustered SE', atol=1e-7)
    assert_close(p, row.p, f'{scope} {model} p value', atol=1e-7)
    assert_close([b-critical*se, b+critical*se], [row.lo, row.hi],
                 f'{scope} {model} confidence interval', atol=3e-7)
    assert n == row.N and clusters == row.clusters
    margin_error = None
    if model == 'I2':
        margins = pd.read_csv(OUT / 'marginal_effects.csv')
        selected = margins.query('scope == @scope and model == @model')
        errors = []
        for m in selected.itertuples():
            vector = np.zeros(len(beta))
            vector[design.columns.get_loc('g')] = 1.
            vector[j] = m.p_value
            estimate = vector@beta
            margin_se = math.sqrt(vector@covariance@vector)
            assert data.p.min() <= m.p_value <= data.p.max()
            assert_close(estimate, m.estimate, 'Marginal slope', atol=2e-8)
            assert_close(margin_se, m.se, 'Marginal slope SE', atol=1e-7)
            errors.append(abs(estimate-m.estimate))
        margin_error = max(errors)
    return dict(scope=scope, model=model, N=n, clusters=clusters, coefficient=float(b),
                stata_coefficient=float(row.b), coefficient_error=float(abs(b-row.b)),
                clustered_se=float(se), stata_clustered_se=float(row.se), se_error=float(abs(se-row.se)),
                p=float(p), p_error=float(abs(p-row.p)), finite_sample_correction=float(correction),
                marginal_coefficient_max_error=margin_error)


def main():
    macro = pd.read_csv(PANEL / 'fiscal_macro_trial_20261117.csv')
    fund = pd.read_csv(PANEL / 'fund_trial_20261117.csv')
    analysis = pd.read_csv(PANEL / 'fiscal_fund_trial_20261117.csv')
    results = pd.read_csv(OUT / 'model_results.csv')
    manifests = json.loads((OUT / 'model_manifest.json').read_text())
    hash_checks = {}
    for name, expected in json.loads((OUT / 'analysis_input_hashes.json').read_text()).items():
        actual = hashlib.sha256((PANEL / name).read_bytes()).hexdigest()
        assert actual == expected, name
        hash_checks[name] = actual
    for name, expected in json.loads((OUT / 'macro_audit.json').read_text())['inputs_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    audit = json.loads((OUT / 'event_audit.json').read_text())
    assert hashlib.sha256((ROOT / audit['source']).read_bytes()).hexdigest() == audit['source_sha256']
    assert not macro.duplicated(['city', 'year']).any()
    assert not fund.duplicated(['sample', 'city', 'year']).any()
    assert len(fund) == len(analysis)
    assert (fund.inv_count > 0).all()
    assert (fund.early_count <= fund.known_count).all()
    assert (fund.known_count <= fund.inv_count).all()
    assert_close(fund.early_share, fund.early_count/fund.known_count.replace(0, np.nan), 'Known-stage denominator')
    assert_close(fund.known_share, fund.known_count/fund.inv_count, 'Stage disclosure denominator')
    assert fund.complete_amount_rmb_m.notna().eq(fund.amount_complete.eq(1)).all()
    assert fund.amount_complete.eq(fund.amount_known_count.eq(fund.inv_count).astype(int)).all()
    assert_close(macro.fiscal_gap, 1-macro.fiscal_revenue_10k/macro.fiscal_expenditure_10k, 'Fiscal gap formula')
    assert_close(macro.fiscal_gap+macro.fiscal_selfsuff, np.where(macro.fiscal_gap.notna(), 1., np.nan), 'Opposite coding')
    macro_index = macro.set_index(['city', 'year'])
    lookup = [('p', 'fiscal_gap', -1), ('d', 'debt_ratio', -1), ('l_gdp', 'ln_gdp', -1),
              ('l_secondary', 'secondary_share', -1), ('l_scitech', 'ln_scitech', -1),
              ('y1', 'ln_pat_apply', 1), ('y2', 'ln_pat_apply', 2),
              ('grant1', 'ln_pat_grant', 1), ('grant2', 'ln_pat_grant', 2)]
    for column, source, shift in lookup:
        keys = pd.MultiIndex.from_arrays([analysis.city, analysis.year+shift], names=['city', 'year'])
        expected = macro_index[source].reindex(keys).to_numpy()
        assert_close(analysis[column], expected, f'Calendar lookup {column}')
    assert_close(analysis.g, np.log1p(analysis.inv_count), 'Fund activity transform')
    assert len(results) == 2*len(manifests) == 36
    assert not results.status.str.startswith('stata_error').any()
    assert set(results.loc[results.status.ne('ok'), ['scope', 'model']].itertuples(index=False, name=None)) == {('municipal', 'B6')}
    for spec in manifests:
        eligible = analysis[spec['required']].notna().all(axis=1) & analysis.year.between(2015, spec['investment_year_max'])
        n_by_city = eligible.groupby([analysis['sample'], analysis.city]).transform('sum')
        assert analysis[f"use_{spec['model']}"].eq((eligible & (n_by_city >= 2)).astype(int)).all()
    sample_checks = []
    for row in results.itertuples():
        chosen = analysis.loc[analysis['sample'].eq(row.scope) & analysis[f'use_{row.model}'].eq(1)]
        assert len(chosen) == row.N and chosen.city.nunique() == row.clusters
        if row.status == 'ok':
            saved = pd.read_csv(OUT / f'samples/{row.scope}_{row.model}.csv')
            assert set(zip(saved.city, saved.year)) == set(zip(chosen.city, chosen.year))
        sample_checks.append(dict(scope=row.scope, model=row.model, N=int(row.N), clusters=int(row.clusters), status=row.status))
    for left, right in [('I1', 'I2'), ('I3', 'I4'), ('I5', 'I6'), ('I7a', 'I7'), ('B2', 'B3'), ('B2', 'B4')]:
        assert analysis[f'use_{left}'].eq(analysis[f'use_{right}']).all(), (left, right)
    regression_checks = [regression_check(scope, model, results) for scope in ['municipal', 'broad']
                         for model in ['I2', 'I6', 'B1', 'B2', 'B3']]
    textlog = (ROOT / '运行日志与do代码/xtreg_fiscal_fund_trial_20261117.log').read_text()
    assert 'TRIAL_COMPLETED' in textlog
    output = dict(status='passed', hash_checks=hash_checks, source_hashes='all_match',
                  exact_calendar_joins=[item[0] for item in lookup], common_sample_pairs=['I1/I2', 'I3/I4', 'I5/I6', 'I7a/I7', 'B2/B3/B4'],
                  sample_checks=sample_checks, regression_checks=regression_checks,
                  independent_method='NumPy full city/year dummy OLS or WLS; city-cluster sandwich covariance; independent t-distribution calculation',
                  interpretation_notes=['Fund geography is a registration-city proxy, not verified fiscal sponsor.',
                                        'Only observed positive-event city-years enter; no extensive-margin zero claim.',
                                        'areg WLS and xtreg have different documented finite-sample covariance corrections.'])
    (OUT / 'validation.json').write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': 'passed', 'models': len(results), 'independent_regressions': len(regression_checks),
                      'max_coefficient_error': max(r['coefficient_error'] for r in regression_checks),
                      'max_se_error': max(r['se_error'] for r in regression_checks)}, indent=2))


if __name__ == '__main__':
    main()
