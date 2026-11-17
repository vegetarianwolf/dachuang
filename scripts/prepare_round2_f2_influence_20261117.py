"""Prepare every leave-one-source-city F2 check after the support audit.

The published F2 complete-case sample is the starting population. For each of
its source cities, remove that city and recursively remove fixed-effect
singletons and funds observed in fewer than two calendar years. All 40 variants
are run and reported; no p-value-based retention is performed.
"""
from pathlib import Path
import hashlib
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "实证结果/fiscal_fund_design_round2_20261117"
SOURCE = ROOT / "面板数据/fund_choice_round2_20261117.csv"
PANEL = ROOT / "面板数据/f2_influence_round2_20261117.csv"
DOFILE = ROOT / "运行日志与do代码/fiscal_round2_f2_influence_20261117.do"


def main():
    data = pd.read_csv(SOURCE)
    data = data[data.use_F2.eq(1)].copy()
    cities = sorted(data.source_city.unique())
    assert len(cities) == 40
    variants = []
    for i, city in enumerate(cities, 1):
        selected = data[data.source_city.ne(city)].copy()
        previous = None
        while previous != tuple(selected.index):
            previous = tuple(selected.index)
            keep = pd.Series(True, index=selected.index)
            for effect in ["fund_id", "destination_year", "sector_id"]:
                keep &= selected.groupby(effect)[effect].transform("size").ge(2)
            keep &= selected.groupby("fund_id").year.transform("nunique").ge(2)
            selected = selected[keep]
        flag = f"use_drop_{i:02d}"
        data[flag] = data.index.isin(selected.index).astype(int)
        variants.append(dict(variant=i, omitted_city=city, omitted_source_id=int(data.loc[data.source_city.eq(city), "source_id"].iloc[0]),
                             flag=flag, N=len(selected), clusters=selected.source_city.nunique(), funds=selected.fund_id.nunique(),
                             removed_city_events=int(data.source_city.eq(city).sum()),
                             additional_pruned_events=int(len(data) - data.source_city.eq(city).sum() - len(selected))))
    data.to_csv(PANEL, index=False, encoding="utf-8-sig")
    audit = dict(reason="Post-estimation support audit found concentrated residual fiscal variation in F2; report all leave-one-source-city results.",
                 initial_model="F2", initial_N=len(data), initial_source_cities=len(cities),
                 minimum_events=40, minimum_source_cities=20,
                 source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                 output_sha256=hashlib.sha256(PANEL.read_bytes()).hexdigest(), variants=variants)
    (OUT / "f2_influence_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        'version 18', 'clear all', 'set more off', 'set type double', 'capture log close',
        'args root', f'if `"`root\'"\' == "" local root "{ROOT}"',
        'local datafile "`root\'/面板数据/f2_influence_round2_20261117.csv"',
        'local outdir "`root\'/实证结果/fiscal_fund_design_round2_20261117"',
        'local basename "fiscal_round2_f2_influence_20261117"',
        'local logfile "`root\'/运行日志与do代码/`basename\'.log"',
        'log using "`logfile\'", replace text',
        'import delimited using "`datafile\'", clear varnames(1) encoding(UTF-8) case(preserve)',
        'tempname handle', 'tempfile results',
        'postfile `handle\' int variant str60 omitted_city long omitted_source_id str30 status double b se p lo hi N clusters funds r2 using `results\', replace',
    ]
    for variant in variants:
        i, city, source_id, flag = variant["variant"], variant["omitted_city"], variant["omitted_source_id"], variant["flag"]
        lines += [
            'preserve', f'keep if {flag} == 1', 'quietly count', 'local n=r(N)',
            'quietly egen __city_tag=tag(source_id)', 'quietly count if __city_tag==1', 'local clusters=r(N)',
            'quietly egen __fund_tag=tag(fund_id)', 'quietly count if __fund_tag==1', 'local funds=r(N)',
            'if `n\'<40 | `clusters\'<20 {',
            f'    post `handle\' ({i}) ("{city}") ({source_id}) ("insufficient_sample") (.) (.) (.) (.) (.) (`n\') (`clusters\') (`funds\') (.)',
            '}', 'else {',
            f'    display "F2_LEAVE_ONE_CITY {i} {city}"',
            '    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)',
            '    local rc=_rc', '    if `rc\'!=0 {',
            f'        post `handle\' ({i}) ("{city}") ({source_id}) ("stata_error_`rc\'") (.) (.) (.) (.) (.) (`n\') (`clusters\') (`funds\') (.)',
            '    }', '    else {',
            '        local b=_b[p]', '        local se=_se[p]',
            '        local pval=cond(`se\'>0,2*ttail(e(df_r),abs(`b\'/`se\')),.)',
            '        local crit=invttail(e(df_r),.025)', '        local status "ok"',
            '        if `se\'==0 local status "target_omitted"',
            f'        post `handle\' ({i}) ("{city}") ({source_id}) ("`status\'") (`b\') (`se\') (`pval\') (`b\'-`crit\'*`se\') (`b\'+`crit\'*`se\') (e(N)) (`clusters\') (`funds\') (e(r2))',
            '    }', '}', 'restore',
        ]
    lines += ['postclose `handle\'', 'use `results\', clear', 'export delimited using "`outdir\'/f2_leave_one_city.csv", replace',
              'list omitted_city status b se p N clusters, noobs', 'display "F2_INFLUENCE_COMPLETED"', 'log close']
    DOFILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(dict(variants=len(variants), panel=str(PANEL.relative_to(ROOT)), dofile=str(DOFILE.relative_to(ROOT)), N_range=[min(v["N"] for v in variants), max(v["N"] for v in variants)]), ensure_ascii=False))


if __name__ == "__main__":
    main()
